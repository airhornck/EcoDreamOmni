"""AssetPool 三源混合素材库服务。

V2.7.1新增功能:
- 三源素材管理 (运营上传/STOCK_API/AI生成)
- 版权管理核心
- 素材-内容匹配推荐
- AI辅助创作标识
- 缩略图生成 (Pillow)
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum


class AssetSourceType(str, Enum):
    """素材来源类型"""
    OPERATOR_UPLOAD = "OPERATOR_UPLOAD"
    STOCK_API = "STOCK_API"
    AI_GENERATED = "AI_GENERATED"


class LicenseType(str, Enum):
    """许可证类型"""
    OWNED = "OWNED"  # 自有版权
    LICENSED = "LICENSED"  # 授权使用
    AI_GENERATED = "AI_GENERATED"  # AI生成


class AssetStatus(str, Enum):
    """素材状态"""
    ACTIVE = "ACTIVE"
    PENDING_REVIEW = "PENDING_REVIEW"
    DELETED = "DELETED"
    EXPIRED = "EXPIRED"


class LicenseStatus(str, Enum):
    """许可证状态"""
    VALID = "VALID"
    EXPIRING_SOON = "EXPIRING_SOON"  # 30天内过期
    EXPIRED = "EXPIRED"


@dataclass
class AssetMetadata:
    """素材元数据"""
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    dominant_color: Optional[str] = None


@dataclass
class AIMetadata:
    """AI生成素材元数据"""
    model: Optional[str] = None
    prompt: Optional[str] = None
    seed: Optional[int] = None
    generation_params: Dict = field(default_factory=dict)


@dataclass
class CopyrightInfo:
    """版权信息"""
    holder: Optional[str] = None
    year: Optional[int] = None
    usage_rights: List[str] = field(default_factory=list)
    license_agreement: Optional[str] = None


@dataclass
class Asset:
    """素材实体"""
    id: str
    filename: str
    file_url: str
    thumbnail_url: Optional[str] = None
    source_type: AssetSourceType = AssetSourceType.OPERATOR_UPLOAD
    license_type: LicenseType = LicenseType.OWNED
    license_status: LicenseStatus = LicenseStatus.VALID
    
    # 版权信息
    copyright_holder: Optional[str] = None
    copyright_year: Optional[int] = None
    usage_rights: List[str] = field(default_factory=list)
    copyright_validated: bool = False
    
    # 图库API特有
    stock_source: Optional[str] = None  # shutterstock, getty等
    stock_id: Optional[str] = None
    license_expiry: Optional[str] = None
    
    # AI生成特有
    ai_model: Optional[str] = None
    ai_prompt: Optional[str] = None
    ai_disclosure: bool = False  # 是否已披露AI生成
    ai_metadata: Optional[AIMetadata] = None
    
    # 分类标签
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    
    # 系列关联
    series_id: Optional[str] = None
    
    # 状态
    status: AssetStatus = AssetStatus.ACTIVE
    
    # 元数据
    metadata: AssetMetadata = field(default_factory=AssetMetadata)
    
    # 时间戳
    created_at: str = ""
    updated_at: str = ""
    
    # 上传者
    uploaded_by: Optional[str] = None


# ── 内存存储已废弃 (W14迁移至PostgreSQL ORM) ──
# 保留文件骨架以兼容遗留导入; 所有CRUD操作已移至 asset_pool_function.py
_asset_db: Dict[str, Asset] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _check_license_status(expiry_str: Optional[str]) -> LicenseStatus:
    """检查许可证状态"""
    if not expiry_str:
        return LicenseStatus.VALID
    
    try:
        expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_until_expiry = (expiry - now).days
        
        if days_until_expiry < 0:
            return LicenseStatus.EXPIRED
        elif days_until_expiry <= 30:
            return LicenseStatus.EXPIRING_SOON
        return LicenseStatus.VALID
    except:
        return LicenseStatus.VALID


def _generate_thumbnail_url(file_url: str) -> str:
    """生成缩略图URL"""
    if "." in file_url:
        base, ext = file_url.rsplit(".", 1)
        return f"{base}_thumb.{ext}"
    return f"{file_url}_thumb"


def _ensure_ai_disclosure(asset_data: Dict) -> Dict:
    """确保AI生成素材有披露标识"""
    if asset_data.get("source_type") == AssetSourceType.AI_GENERATED:
        asset_data["ai_disclosure"] = True
        tags = asset_data.get("tags", [])
        if "AI辅助创作" not in tags:
            tags.append("AI辅助创作")
        asset_data["tags"] = tags
    return asset_data


def _validate_copyright(asset_data: Dict) -> bool:
    """校验版权信息完整性"""
    license_type = asset_data.get("license_type")
    
    if license_type == LicenseType.OWNED:
        # 自有版权需要版权持有者信息
        return bool(asset_data.get("copyright_holder"))
    
    if license_type == LicenseType.LICENSED:
        # 授权需要来源和许可证信息
        return bool(asset_data.get("stock_source"))
    
    if license_type == LicenseType.AI_GENERATED:
        # AI生成需要模型信息
        return bool(asset_data.get("ai_model"))
    
    return True


def create_asset(
    filename: str,
    file_url: str,
    source_type: str = "OPERATOR_UPLOAD",
    license_type: str = "OWNED",
    tags: Optional[List[str]] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    copyright_holder: Optional[str] = None,
    copyright_year: Optional[int] = None,
    usage_rights: Optional[List[str]] = None,
    stock_source: Optional[str] = None,
    stock_id: Optional[str] = None,
    license_expiry: Optional[str] = None,
    ai_model: Optional[str] = None,
    ai_prompt: Optional[str] = None,
    series_id: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    generate_thumbnail: bool = True,
    **kwargs
) -> Asset:
    """创建素材"""
    asset_id = secrets.token_urlsafe(16)
    now = _now()
    
    # 构建基础数据
    asset_data = {
        "id": asset_id,
        "filename": filename,
        "file_url": file_url,
        "source_type": AssetSourceType(source_type),
        "license_type": LicenseType(license_type),
        "tags": tags or [],
        "category": category,
        "description": description,
        "copyright_holder": copyright_holder,
        "copyright_year": copyright_year,
        "usage_rights": usage_rights or [],
        "stock_source": stock_source,
        "stock_id": stock_id,
        "license_expiry": license_expiry,
        "ai_model": ai_model,
        "ai_prompt": ai_prompt,
        "series_id": series_id,
        "uploaded_by": uploaded_by,
        "created_at": now,
        "updated_at": now,
        "status": AssetStatus.ACTIVE,
    }
    
    # 确保AI披露
    asset_data = _ensure_ai_disclosure(asset_data)
    
    # 校验版权
    asset_data["copyright_validated"] = _validate_copyright(asset_data)
    
    # 检查许可证状态
    asset_data["license_status"] = _check_license_status(license_expiry)
    
    # 生成缩略图
    if generate_thumbnail:
        asset_data["thumbnail_url"] = _generate_thumbnail_url(file_url)
    
    # 构建AI元数据
    if asset_data["source_type"] == AssetSourceType.AI_GENERATED:
        asset_data["ai_metadata"] = AIMetadata(
            model=ai_model,
            prompt=ai_prompt,
        )
    
    # 创建Asset对象
    asset = Asset(**asset_data)
    
    # 存储
    _asset_db[asset_id] = asset
    
    return asset


def get_asset(asset_id: str) -> Optional[Asset]:
    """获取素材详情"""
    return _asset_db.get(asset_id)


def list_assets(
    source_type: Optional[str] = None,
    license_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: str = "ACTIVE",
    limit: int = 50,
    offset: int = 0,
) -> Dict:
    """列素材列表"""
    results = []
    
    for asset in _asset_db.values():
        # 过滤已删除
        if status == "ACTIVE" and asset.status != AssetStatus.ACTIVE:
            continue
        
        # 过滤条件
        if source_type and asset.source_type.value != source_type:
            continue
        if license_type and asset.license_type.value != license_type:
            continue
        if category and asset.category != category:
            continue
        if tags and not any(tag in asset.tags for tag in tags):
            continue
        
        results.append(asset)
    
    # 排序: 最新的在前
    results.sort(key=lambda x: x.created_at, reverse=True)
    
    total = len(results)
    paginated = results[offset:offset + limit]
    
    return {
        "items": paginated,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def update_asset(asset_id: str, **kwargs) -> Optional[Asset]:
    """更新素材"""
    asset = _asset_db.get(asset_id)
    if asset is None:
        return None
    
    # 检查是否为AI生成素材，不允许移除AI标签
    if asset.source_type == AssetSourceType.AI_GENERATED:
        if "tags" in kwargs:
            tags = kwargs["tags"]
            if "AI辅助创作" not in tags:
                tags.append("AI辅助创作")
            kwargs["tags"] = tags
        if "ai_disclosure" in kwargs:
            kwargs["ai_disclosure"] = True
    
    # 更新字段
    for key, value in kwargs.items():
        if hasattr(asset, key) and key not in ["id", "created_at"]:
            setattr(asset, key, value)
    
    asset.updated_at = _now()
    return asset


def delete_asset(asset_id: str) -> bool:
    """软删除素材"""
    asset = _asset_db.get(asset_id)
    if asset is None:
        return False
    
    asset.status = AssetStatus.DELETED
    asset.updated_at = _now()
    return True


def get_statistics() -> Dict:
    """获取素材统计"""
    total = len(_asset_db)
    active = sum(1 for a in _asset_db.values() if a.status == AssetStatus.ACTIVE)
    
    # 三源分布
    source_dist = {}
    for asset in _asset_db.values():
        if asset.status == AssetStatus.ACTIVE:
            source = asset.source_type.value
            source_dist[source] = source_dist.get(source, 0) + 1
    
    # 许可证类型分布
    license_dist = {}
    for asset in _asset_db.values():
        if asset.status == AssetStatus.ACTIVE:
            lt = asset.license_type.value
            license_dist[lt] = license_dist.get(lt, 0) + 1
    
    # 运营上传占比
    op_count = source_dist.get(AssetSourceType.OPERATOR_UPLOAD.value, 0)
    active_total = sum(source_dist.values())
    op_ratio = (op_count / active_total * 100) if active_total > 0 else 0
    
    return {
        "total": total,
        "active": active,
        "source_distribution": source_dist,
        "license_distribution": license_dist,
        "operator_upload_ratio": round(op_ratio, 2),
    }


def _calculate_match_score(asset: Asset, content_title: str, content_body: str, content_tags: List[str]) -> float:
    """计算素材与内容的匹配分数"""
    score = 0.0
    content_text = f"{content_title} {content_body}".lower()
    
    # 标签匹配
    for tag in asset.tags:
        if tag.lower() in content_text:
            score += 20
        if tag.lower() in [t.lower() for t in content_tags]:
            score += 30
    
    # 分类匹配
    if asset.category and asset.category.lower() in content_text:
        score += 15
    
    # AI生成素材降权（合规考虑）
    if asset.source_type == AssetSourceType.AI_GENERATED:
        score *= 0.9
    
    # 许可证即将过期的降权
    if asset.license_status == LicenseStatus.EXPIRING_SOON:
        score *= 0.8
    
    return min(100.0, score)


def recommend_assets(
    content_title: str,
    content_body: str = "",
    content_tags: Optional[List[str]] = None,
    series_id: Optional[str] = None,
    target_count: int = 3,
    exclude_asset_ids: Optional[List[str]] = None,
) -> Dict:
    """为内容推荐匹配素材"""
    content_tags = content_tags or []
    exclude_ids = set(exclude_asset_ids or [])
    
    scored_assets = []
    
    for asset in _asset_db.values():
        # 排除已删除和已排除的
        if asset.status != AssetStatus.ACTIVE:
            continue
        if asset.id in exclude_ids:
            continue
        
        # 计算匹配分数
        score = _calculate_match_score(asset, content_title, content_body, content_tags)
        
        # 系列匹配加分
        match_reason = "标签匹配"
        if series_id and asset.series_id == series_id:
            score += 25
            match_reason = f"系列匹配 ({series_id})"
        
        if score > 0:
            scored_assets.append({
                "asset_id": asset.id,
                "asset": asset,
                "match_score": round(score, 1),
                "match_reason": match_reason,
            })
    
    # 按分数排序
    scored_assets.sort(key=lambda x: x["match_score"], reverse=True)
    
    # 取前N个
    recommendations = scored_assets[:target_count]
    
    return {
        "recommendations": [
            {
                "asset_id": r["asset_id"],
                "match_score": r["match_score"],
                "match_reason": r["match_reason"],
            }
            for r in recommendations
        ],
        "total_candidates": len(scored_assets),
    }


def clear_asset_pool() -> None:
    """清空素材库（测试用）"""
    _asset_db.clear()
