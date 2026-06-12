"""PlatformSchema API — 平台 API 发布格式规范接口.

提供：
  - 平台格式规范查询（列表/详情/内容格式）
  - 内容 Schema 校验
  - YAML 同步（admin）

Aligned with PRD V3.1 §PlatformSchema.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.api.auth import get_current_user
from src.services import platform_schema_service as pss

router = APIRouter(prefix="/platform-schemas", tags=["platform-schemas"])


# ─── Pydantic Schemas ───

class FieldConstraintOut(BaseModel):
    name: str
    label: str
    type: str = "string"
    required: bool = True
    min: Optional[Any] = None  # 兼容 int 和 str（如 "32MB"）
    max: Optional[Any] = None
    min_chars: Optional[int] = None
    max_chars: Optional[int] = None
    max_count: Optional[int] = None
    default: Optional[Any] = None
    supported: Optional[List[str]] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContentFormatOut(BaseModel):
    format_name: str
    fields: List[FieldConstraintOut]

    model_config = ConfigDict(from_attributes=True)


class PlatformSchemaOut(BaseModel):
    id: str
    platform_id: str
    display_name: str
    version: str
    content_dna: List[Dict[str, Any]] = []
    audit_rules: List[Dict[str, Any]] = []
    content_formats: List[ContentFormatOut] = []

    model_config = ConfigDict(from_attributes=True)


class PlatformSchemaListOut(BaseModel):
    schemas: List[PlatformSchemaOut]


class ValidateContentIn(BaseModel):
    platform_id: str
    format_name: str
    content: Dict[str, Any]
    strict: bool = True


class ValidationErrorOut(BaseModel):
    field: str
    message: str
    severity: str = "error"


class ValidateContentOut(BaseModel):
    passed: bool
    errors: List[ValidationErrorOut]
    platform_id: str
    format_name: str


class SyncResultOut(BaseModel):
    platform_id: str
    status: str  # synced | skipped | error
    message: Optional[str] = None


# ─── API Endpoints ───

@router.get("", response_model=PlatformSchemaListOut)
async def list_platform_schemas(
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """列出所有平台的格式规范."""
    schemas = await pss.list_platform_schemas(db)
    return PlatformSchemaListOut(
        schemas=[
            PlatformSchemaOut(
                id=str(s.id),
                platform_id=s.platform_id,
                display_name=s.display_name,
                version=s.version,
                content_dna=s.content_dna or [],
                audit_rules=s.audit_rules or [],
                content_formats=[
                    ContentFormatOut(
                        format_name=cf.format_name,
                        fields=[
                            FieldConstraintOut(**f)
                            for f in (cf.fields or [])
                        ],
                    )
                    for cf in s.content_formats
                ],
            )
            for s in schemas
        ]
    )


@router.get("/{platform_id}", response_model=PlatformSchemaOut)
async def get_platform_schema(
    platform_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """获取指定平台的格式规范详情."""
    schema = await pss.get_platform_schema(db, platform_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"平台规范未找到: {platform_id}")
    return PlatformSchemaOut(
        id=str(schema.id),
        platform_id=schema.platform_id,
        display_name=schema.display_name,
        version=schema.version,
        content_dna=schema.content_dna or [],
        audit_rules=schema.audit_rules or [],
        content_formats=[
            ContentFormatOut(
                format_name=cf.format_name,
                fields=[
                    FieldConstraintOut(**f)
                    for f in (cf.fields or [])
                ],
            )
            for cf in schema.content_formats
        ],
    )


@router.get("/{platform_id}/formats", response_model=ContentFormatOut)
async def get_content_format(
    platform_id: str,
    format_name: str = Query(..., description="内容格式名称，如: 图文, 视频, 仅文字"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """获取指定平台和内容格式的字段约束."""
    fmt = await pss.get_content_format(db, platform_id, format_name)
    if not fmt:
        raise HTTPException(
            status_code=404,
            detail=f"格式未找到: {platform_id}/{format_name}",
        )
    return ContentFormatOut(
        format_name=fmt.format_name,
        fields=[
            FieldConstraintOut(**f)
            for f in (fmt.fields or [])
        ],
    )


@router.post("/validate", response_model=ValidateContentOut)
async def validate_content(
    data: ValidateContentIn,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """校验内容是否符合平台格式规范."""
    fmt = await pss.get_content_format(db, data.platform_id, data.format_name)
    if not fmt:
        raise HTTPException(
            status_code=404,
            detail=f"格式未找到: {data.platform_id}/{data.format_name}",
        )

    passed, errors = pss.validate_content_against_schema(
        data.content,
        fmt.fields or [],
        strict=data.strict,
    )

    return ValidateContentOut(
        passed=passed,
        errors=[
            ValidationErrorOut(field=e.field, message=e.message, severity=e.severity)
            for e in errors
        ],
        platform_id=data.platform_id,
        format_name=data.format_name,
    )


@router.post("/sync-from-yaml", response_model=List[SyncResultOut])
async def sync_from_yaml(
    platform_id: Optional[str] = Query(None, description="指定平台同步，不传则同步所有"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """从 YAML 真源目录同步平台格式规范到数据库."""
    results = []

    if platform_id:
        try:
            schema = await pss.sync_platform_schema_from_yaml(db, platform_id)
            if schema:
                results.append(
                    SyncResultOut(platform_id=platform_id, status="synced")
                )
            else:
                results.append(
                    SyncResultOut(
                        platform_id=platform_id,
                        status="skipped",
                        message="YAML 文件未找到",
                    )
                )
        except Exception as e:
            results.append(
                SyncResultOut(
                    platform_id=platform_id,
                    status="error",
                    message=str(e),
                )
            )
    else:
        platform_ids = pss.list_yaml_platform_ids()
        for pid in platform_ids:
            try:
                schema = await pss.sync_platform_schema_from_yaml(db, pid)
                if schema:
                    results.append(
                        SyncResultOut(platform_id=pid, status="synced")
                    )
                else:
                    results.append(
                        SyncResultOut(
                            platform_id=pid,
                            status="skipped",
                            message="YAML 文件未找到",
                        )
                    )
            except Exception as e:
                results.append(
                    SyncResultOut(
                        platform_id=pid,
                        status="error",
                        message=str(e),
                    )
                )

    return results
