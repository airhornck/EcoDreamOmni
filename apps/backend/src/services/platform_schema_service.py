"""PlatformSchema Service — YAML 解析 + Schema 校验 + DB 同步.

职责：
  1. 从 D:\project\lumina\data\platforms\*.yml 读取平台格式规范
  2. 解析并同步到数据库（platform_schemas + platform_content_formats）
  3. 提供内容 Schema 校验（字段长度、数量、必填等）
  4. 供 Publisher 在发布前校验内容格式

Aligned with PRD V3.1 §PlatformSchema.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.platform_schema_orm import PlatformSchemaORM, PlatformContentFormatORM

# YAML 真源目录
YAML_PLATFORMS_DIR = Path("D:/project/lumina/data/platforms")

# 平台显示名称映射
PLATFORM_DISPLAY_NAMES = {
    "xiaohongshu": "小红书",
    "douyin": "抖音",
    "wechat_official": "微信公众号",
    "bilibili": "哔哩哔哩",
}


# ───────────────────────────────────────────────
# YAML 解析
# ───────────────────────────────────────────────

def _parse_yaml_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """解析单个平台 YAML 文件."""
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _normalize_field(
    field_name: str, field_value: Any, format_name: str
) -> Dict[str, Any]:
    """将 YAML 中的字段约束统一化为结构化字典.

    输入示例:
      title: {max_chars: 20, min_chars: 1, default: "15-20"}
    输出:
      {name: "title", label: "标题", type: "string", required: true,
       min_chars: 1, max_chars: 20, default: "15-20"}
    """
    if not isinstance(field_value, dict):
        return {"name": field_name, "label": field_name, "type": "unknown", "value": field_value}

    result: Dict[str, Any] = {
        "name": field_name,
        "label": _field_label_map.get(field_name, field_name),
        "type": "string",
        "required": False,
    }

    # 数值型约束
    if "min" in field_value:
        result["min"] = field_value["min"]
    if "max" in field_value:
        result["max"] = field_value["max"]
    if "min_chars" in field_value:
        result["min_chars"] = field_value["min_chars"]
    if "max_chars" in field_value:
        result["max_chars"] = field_value["max_chars"]
    if "max_count" in field_value:
        result["max_count"] = field_value["max_count"]

    # 默认值 / 推荐值
    if "default" in field_value:
        result["default"] = field_value["default"]
    if "recommended" in field_value:
        result["recommended"] = field_value["recommended"]

    # 枚举
    if "supported" in field_value:
        result["supported"] = field_value["supported"]
    if "options" in field_value:
        result["options"] = field_value["options"]

    # 尺寸/比例
    if "ratio" in field_value:
        result["ratio"] = field_value["ratio"]
    if "recommended" in field_value and isinstance(field_value["recommended"], str):
        if "x" in field_value["recommended"] or "*" in field_value["recommended"]:
            result["recommended_resolution"] = field_value["recommended"]

    # 描述
    if "description" in field_value:
        result["description"] = field_value["description"]
    if "note" in field_value:
        result["note"] = field_value["note"]
    if "usage" in field_value:
        result["usage"] = field_value["usage"]

    return result


_field_label_map = {
    "title": "标题",
    "content": "正文",
    "content_all": "全文内容",
    "tags": "标签",
    "pic_num": "图片数量",
    "pic_size": "图片大小",
    "pic_format": "图片格式",
    "pic_resolution": "图片分辨率",
    "pic_ratio": "图片比例",
    "video_size": "视频大小",
    "video_duration": "视频时长",
    "video_format": "视频格式",
    "video_resolution": "视频分辨率",
    "cover": "封面",
    "author": "作者",
    "summary": "摘要",
    "body_images": "正文图片",
    "videos": "视频",
    "audio": "音频",
    "music": "音乐",
    "miniprogram_cards": "小程序卡片",
    "official_account_cards": "公众号卡片",
    "template_id": "模板 ID",
    "content_layout": "内容排版",
    "publishing": "发布策略",
    "post_edit": "编辑限制",
}


def _parse_content_formats(content_formats_raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """解析 YAML 中的 content_formats 为统一结构."""
    result = []
    for format_name, format_fields in content_formats_raw.items():
        fields = []
        for field_name, field_value in format_fields.items():
            if isinstance(field_value, dict):
                fields.append(_normalize_field(field_name, field_value, format_name))
            elif isinstance(field_value, list):
                # 特殊处理如 thumbnail_display 等
                fields.append({
                    "name": field_name,
                    "label": _field_label_map.get(field_name, field_name),
                    "type": "object",
                    "value": field_value,
                })
            else:
                fields.append({
                    "name": field_name,
                    "label": _field_label_map.get(field_name, field_name),
                    "type": "string",
                    "value": field_value,
                })
        result.append({
            "format_name": format_name,
            "fields": fields,
        })
    return result


def load_platform_schema_from_yaml(platform_id: str) -> Optional[Dict[str, Any]]:
    """从 YAML 文件加载单个平台的格式规范."""
    file_path = YAML_PLATFORMS_DIR / f"{platform_id}_v2024.yml"
    if not file_path.exists():
        # 尝试不带 _v2024 后缀
        file_path = YAML_PLATFORMS_DIR / f"{platform_id}.yml"
        if not file_path.exists():
            return None

    data = _parse_yaml_file(file_path)
    if not data:
        return None

    return {
        "platform_id": data.get("platform_id", platform_id),
        "display_name": PLATFORM_DISPLAY_NAMES.get(
            data.get("platform_id", platform_id), data.get("platform_id", platform_id)
        ),
        "version": "v2024",
        "content_dna": data.get("content_dna", []),
        "audit_rules": data.get("audit_rules", []),
        "content_formats": _parse_content_formats(data.get("content_formats", {})),
    }


def list_yaml_platform_ids() -> List[str]:
    """列出 YAML 目录中所有平台标识."""
    if not YAML_PLATFORMS_DIR.exists():
        return []
    ids = []
    # 匹配 *_v2024.yml 和 *.yml（但不匹配 _v2024.yml 本身）
    for f in YAML_PLATFORMS_DIR.glob("*.yml"):
        stem = f.stem
        if stem.endswith("_v2024"):
            ids.append(stem.replace("_v2024", ""))
        else:
            ids.append(stem)
    return sorted(set(ids))


# ───────────────────────────────────────────────
# 数据库同步
# ───────────────────────────────────────────────

async def sync_platform_schema_from_yaml(
    db: AsyncSession, platform_id: str
) -> Optional[PlatformSchemaORM]:
    """从 YAML 同步单个平台规范到数据库（幂等）."""
    schema_data = load_platform_schema_from_yaml(platform_id)
    if not schema_data:
        return None

    # 查询或创建 PlatformSchema
    result = await db.execute(
        select(PlatformSchemaORM).where(PlatformSchemaORM.platform_id == platform_id)
    )
    schema = result.scalar_one_or_none()

    if schema is None:
        schema = PlatformSchemaORM(
            platform_id=schema_data["platform_id"],
            display_name=schema_data["display_name"],
            version=schema_data["version"],
            content_dna=schema_data["content_dna"],
            audit_rules=schema_data["audit_rules"],
        )
        db.add(schema)
        await db.flush()  # 获取 schema.id
    else:
        schema.display_name = schema_data["display_name"]
        schema.version = schema_data["version"]
        schema.content_dna = schema_data["content_dna"]
        schema.audit_rules = schema_data["audit_rules"]

    # 删除旧格式定义
    await db.execute(
        delete(PlatformContentFormatORM).where(
            PlatformContentFormatORM.schema_id == schema.id
        )
    )

    # 创建新格式定义
    for fmt in schema_data["content_formats"]:
        db.add(
            PlatformContentFormatORM(
                schema_id=schema.id,
                format_name=fmt["format_name"],
                fields=fmt["fields"],
            )
        )

    await db.commit()
    await db.refresh(schema)
    return schema


async def sync_all_platform_schemas(db: AsyncSession) -> List[PlatformSchemaORM]:
    """从 YAML 同步所有平台规范到数据库."""
    platform_ids = list_yaml_platform_ids()
    results = []
    for pid in platform_ids:
        schema = await sync_platform_schema_from_yaml(db, pid)
        if schema:
            results.append(schema)
    return results


async def clear_platform_schemas(db: AsyncSession) -> None:
    """清空平台规范数据（测试辅助）."""
    await db.execute(delete(PlatformContentFormatORM))
    await db.execute(delete(PlatformSchemaORM))
    await db.commit()


# ───────────────────────────────────────────────
# 查询
# ───────────────────────────────────────────────

async def get_platform_schema(
    db: AsyncSession, platform_id: str
) -> Optional[PlatformSchemaORM]:
    """获取指定平台的格式规范."""
    result = await db.execute(
        select(PlatformSchemaORM)
        .where(PlatformSchemaORM.platform_id == platform_id)
        .options(selectinload(PlatformSchemaORM.content_formats))
    )
    return result.scalar_one_or_none()


async def list_platform_schemas(db: AsyncSession) -> List[PlatformSchemaORM]:
    """列出所有平台的格式规范."""
    result = await db.execute(
        select(PlatformSchemaORM).options(selectinload(PlatformSchemaORM.content_formats))
    )
    return list(result.scalars().all())


async def get_content_format(
    db: AsyncSession, platform_id: str, format_name: str
) -> Optional[PlatformContentFormatORM]:
    """获取指定平台和内容格式的字段约束."""
    result = await db.execute(
        select(PlatformContentFormatORM)
        .join(PlatformSchemaORM)
        .where(PlatformSchemaORM.platform_id == platform_id)
        .where(PlatformContentFormatORM.format_name == format_name)
    )
    return result.scalar_one_or_none()


# ───────────────────────────────────────────────
# Schema 校验
# ───────────────────────────────────────────────

class SchemaValidationError:
    """单条校验错误."""

    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity  # error | warn

    def to_dict(self) -> Dict[str, str]:
        return {"field": self.field, "message": self.message, "severity": self.severity}


def validate_content_against_schema(
    content: Dict[str, Any],
    format_fields: List[Dict[str, Any]],
    strict: bool = True,
) -> Tuple[bool, List[SchemaValidationError]]:
    """校验内容是否符合平台格式规范.

    Args:
        content: 待发布内容，如 {"title": "xxx", "body": "yyy", "images": [...]}
        format_fields: 平台格式字段定义列表
        strict: 严格模式（False 时仅警告，不阻断）

    Returns:
        (是否通过, 错误列表)
    """
    errors: List[SchemaValidationError] = []

    for field_def in format_fields:
        field_name = field_def.get("name", "")
        field_value = content.get(field_name)

        # 1. 必填检查
        if field_def.get("required", False) and (field_value is None or field_value == ""):
            errors.append(
                SchemaValidationError(
                    field=field_name,
                    message=f"{field_def.get('label', field_name)} 为必填项",
                    severity="error" if strict else "warn",
                )
            )
            continue

        # 值为空且非必填 → 跳过后续校验
        if field_value is None or field_value == "":
            continue

        # 2. 字符串长度检查
        if isinstance(field_value, str):
            if "min_chars" in field_def:
                min_chars = field_def["min_chars"]
                if len(field_value) < min_chars:
                    errors.append(
                        SchemaValidationError(
                            field=field_name,
                            message=f"{field_def.get('label', field_name)} 至少需要 {min_chars} 个字符（当前 {len(field_value)}）",
                            severity="error" if strict else "warn",
                        )
                    )
            if "max_chars" in field_def:
                max_chars = field_def["max_chars"]
                if len(field_value) > max_chars:
                    errors.append(
                        SchemaValidationError(
                            field=field_name,
                            message=f"{field_def.get('label', field_name)} 最多 {max_chars} 个字符（当前 {len(field_value)}）",
                            severity="error" if strict else "warn",
                        )
                    )

        # 3. 列表数量检查（images, tags 等）
        if isinstance(field_value, list):
            if "max_count" in field_def:
                max_count = field_def["max_count"]
                if len(field_value) > max_count:
                    errors.append(
                        SchemaValidationError(
                            field=field_name,
                            message=f"{field_def.get('label', field_name)} 最多 {max_count} 项（当前 {len(field_value)}）",
                            severity="error" if strict else "warn",
                        )
                    )
            if "min" in field_def:
                min_count = field_def["min"]
                if len(field_value) < min_count:
                    errors.append(
                        SchemaValidationError(
                            field=field_name,
                            message=f"{field_def.get('label', field_name)} 至少需要 {min_count} 项（当前 {len(field_value)}）",
                            severity="error" if strict else "warn",
                        )
                    )

        # 4. 数值范围检查
        if isinstance(field_value, (int, float)):
            if "min" in field_def and field_value < field_def["min"]:
                errors.append(
                    SchemaValidationError(
                        field=field_name,
                        message=f"{field_def.get('label', field_name)} 最小值为 {field_def['min']}",
                        severity="error" if strict else "warn",
                    )
                )
            if "max" in field_def and field_value > field_def["max"]:
                errors.append(
                    SchemaValidationError(
                        field=field_name,
                        message=f"{field_def.get('label', field_name)} 最大值为 {field_def['max']}",
                        severity="error" if strict else "warn",
                    )
                )

        # 5. 枚举检查（图片格式、视频格式等）
        if "supported" in field_def and isinstance(field_value, str):
            supported = field_def["supported"]
            ext = field_value.lower().split(".")[-1] if "." in field_value else field_value.lower()
            if ext not in [s.lower() for s in supported]:
                errors.append(
                    SchemaValidationError(
                        field=field_name,
                        message=f"{field_def.get('label', field_name)} 不支持格式 '{ext}'，支持的格式: {', '.join(supported)}",
                        severity="error" if strict else "warn",
                    )
                )

    passed = not any(e.severity == "error" for e in errors) if strict else True
    return passed, errors
