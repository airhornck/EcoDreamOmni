"""实验室 API — 爆款笔记分析引擎（ViralAnalyzer）

四层端点：
  1. POST /analyze   — 笔记分析 → AnalysisReport
  2. POST /template  — 生成模板 → ViralTemplate
  3. GET  /keywords  — 关键词库 → KeywordList
  4. GET  /categories — 分类列表 → CategoryList

关键词库管理（v4.0 新增）：
  POST /keywords      — 创建关键词
  PUT  /keywords/{id} — 更新关键词
  DELETE /keywords/{id} — 删除关键词
  GET  /keywords/changelog — 变更日志

保留旧端点（parse / generate / templates）向后兼容。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.api.auth import get_current_user
from src.services.viral_analyzer_service import (
    ViralAnalyzerService,
    NoteInput,
    AnalysisReport,
    get_viral_analyzer_service,
)
from src.models.viral_analyzer_orm import KeywordLibraryORM

router = APIRouter(prefix="/playground", tags=["playground"])


# ═══════════════════════════════════════════════════════
# Schemas (New)
# ═══════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    """笔记分析请求"""
    title: str
    content: str
    coverImage: Optional[str] = None
    metrics: Optional[Dict[str, int]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class KeywordItem(BaseModel):
    """关键词项"""
    keyword: str
    dimension: str
    weight: float


class KeywordCreate(BaseModel):
    """创建关键词请求"""
    keyword: str = Field(..., min_length=1, max_length=100)
    dimension: str = Field(..., pattern="^(structure|function|emotion|industry|effect)$")
    weight: float = Field(default=1.0, ge=0.1, le=5.0)
    applicable_structures: Optional[List[str]] = None


class KeywordUpdate(BaseModel):
    """更新关键词请求"""
    keyword: Optional[str] = Field(None, min_length=1, max_length=100)
    dimension: Optional[str] = Field(None, pattern="^(structure|function|emotion|industry|effect)$")
    weight: Optional[float] = Field(None, ge=0.1, le=5.0)
    applicable_structures: Optional[List[str]] = None
    is_active: Optional[bool] = None


class KeywordOut(BaseModel):
    """关键词输出"""
    id: int
    keyword: str
    dimension: str
    weight: float
    applicable_structures: Optional[List[str]]
    is_active: bool
    created_at: str
    updated_at: str


class KeywordChangelog(BaseModel):
    """关键词变更日志"""
    action: str  # CREATE / UPDATE / DELETE
    keyword_id: Optional[int]
    keyword_text: str
    changed_by: str
    changed_at: str
    before: Optional[Dict[str, Any]]
    after: Optional[Dict[str, Any]]


class CategoryItem(BaseModel):
    """分类项"""
    id: str
    name: str
    description: Optional[str] = None


class TemplateRequest(BaseModel):
    """模板生成请求"""
    report: Dict[str, Any]  # AnalysisReport JSON
    platform: str = "xiaohongshu"
    category: Optional[str] = None


class ExtractElementsRequest(BaseModel):
    """策略元素提取请求 (v4.0 Strategy Element Architecture)"""
    report: Dict[str, Any]  # AnalysisReport JSON
    platform: str = "xiaohongshu"
    save_to_library: bool = True  # 是否保存到策略元素库
    save_as_set: bool = False  # 是否同时保存为策略组合
    set_name: Optional[str] = None  # 策略组合名称（save_as_set=True 时必填）


class ExtractElementsResponse(BaseModel):
    """策略元素提取响应"""
    elements: List[Dict[str, Any]]
    saved_element_ids: List[str]
    strategy_set_id: Optional[str] = None


# ═══════════════════════════════════════════════════════
# Schemas (Legacy — kept for backward compat)
# ═══════════════════════════════════════════════════════

class ParseRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    screenshot: Optional[str] = None


class ParseResponse(BaseModel):
    hook_pattern: str
    body_structure: str
    cta_pattern: str
    tone: str
    keywords: List[str]


class TemplateVariable(BaseModel):
    key: str
    label: str
    default_value: str


class ContentTemplate(BaseModel):
    id: str
    name: str
    prompt_template: str
    variables: List[TemplateVariable]


class GenerateRequest(BaseModel):
    template_id: str
    variables: Dict[str, str]


class GenerateResponse(BaseModel):
    title: str
    body: str
    hashtags: List[str]


# ═══════════════════════════════════════════════════════
# In-memory changelog (MVP: will be replaced by DB table in Phase 2)
# ═══════════════════════════════════════════════════════

_keyword_changelog: List[Dict[str, Any]] = []


def _log_keyword_change(
    action: str,
    keyword_id: Optional[int],
    keyword_text: str,
    changed_by: str,
    before: Optional[Dict] = None,
    after: Optional[Dict] = None,
) -> None:
    """记录关键词变更日志（MVP 内存存储，Phase 2 迁移到 DB）"""
    _keyword_changelog.append({
        "action": action,
        "keyword_id": keyword_id,
        "keyword_text": keyword_text,
        "changed_by": changed_by,
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "before": before,
        "after": after,
    })


# ═══════════════════════════════════════════════════════
# Response wrapper
# ═══════════════════════════════════════════════════════

def _ok(data: Any) -> Dict[str, Any]:
    return {
        "code": "OK",
        "message": "操作成功",
        "data": data,
        "trace_id": f"req_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ═══════════════════════════════════════════════════════
# Mock data (Legacy)
# ═══════════════════════════════════════════════════════

MOCK_TEMPLATES: List[ContentTemplate] = [
    ContentTemplate(
        id="tmpl_001",
        name="驱虫种草模板",
        prompt_template="作为一名{{persona}}，我发现很多铲屎官都在为{{problem}}烦恼。今天分享一个{{solution}}，我家{{pet_name}}用了{{duration}}，效果{{effect}}。",
        variables=[
            TemplateVariable(key="persona", label="人设", default_value="省钱狗爸"),
            TemplateVariable(key="problem", label="痛点", default_value="狗狗驱虫贵"),
            TemplateVariable(key="solution", label="解决方案", default_value="平价驱虫药"),
            TemplateVariable(key="pet_name", label="宠物名", default_value="豆豆"),
            TemplateVariable(key="duration", label="使用时长", default_value="3个月"),
            TemplateVariable(key="effect", label="效果描述", default_value="非常好"),
        ],
    ),
    ContentTemplate(
        id="tmpl_002",
        name="测评对比模板",
        prompt_template="花了{{amount}}测评了{{product_count}}款{{category}}，结果发现{{finding}}。",
        variables=[
            TemplateVariable(key="amount", label="花费", default_value="500元"),
            TemplateVariable(key="product_count", label="产品数量", default_value="5"),
            TemplateVariable(key="category", label="品类", default_value="驱虫药"),
            TemplateVariable(key="finding", label="发现", default_value=" cheapest 的效果最好"),
        ],
    ),
]


# ═══════════════════════════════════════════════════════
# New Endpoints
# ═══════════════════════════════════════════════════════

@router.post("/analyze")
async def analyze_note(
    req: AnalyzeRequest,
    service: ViralAnalyzerService = Depends(get_viral_analyzer_service),
):
    """🔥 分析笔记内容，生成结构化分析报告。

    三层引擎：
      1. LLM 结构化分析（DeepSeek / 自定义配置）
      2. 规则校准（关键词库 + 结构定义）
      3. 报告组装
    """
    try:
        note_input = NoteInput(
            title=req.title,
            content=req.content,
            coverImage=req.coverImage,
            metrics=req.metrics,
            category=req.category,
            tags=req.tags,
        )

        report = await service.analyze_note(note_input)
        return _ok(report.model_dump(mode="json"))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"分析引擎异常: {str(exc)}",
        )


@router.post("/template")
async def generate_template(
    req: TemplateRequest,
    service: ViralAnalyzerService = Depends(get_viral_analyzer_service),
):
    """📝 基于分析报告生成爆款模板。

    输入分析报告 JSON，输出可复用的 ContentTemplate 结构。
    """
    try:
        # 从请求 JSON 重建 AnalysisReport
        report = AnalysisReport.model_validate(req.report)

        template = await service.generate_template(
            report,
            platform=req.platform,
            category=req.category,
        )
        return _ok(template.model_dump(mode="json"))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"模板生成异常: {str(exc)}",
        )


@router.post("/elements", response_model=ExtractElementsResponse)
async def extract_strategy_elements(
    req: ExtractElementsRequest,
    service: ViralAnalyzerService = Depends(get_viral_analyzer_service),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """🧩 从分析报告提取策略元素（v4.0 Strategy Element Architecture）.

    将爆款笔记分析结果拆解为多个独立的 StrategyElement，
    可直接保存到策略元素库供 Step 2「主题与策略」调用。
    """
    try:
        report = AnalysisReport.model_validate(req.report)
        elements = service.extract_strategy_elements(report, platform=req.platform)

        saved_ids: List[str] = []
        strategy_set_id: Optional[str] = None

        if req.save_to_library and elements:
            tenant_id = getattr(current_user, "tenant_id", None) or "default"
            created_by = getattr(current_user, "id", "system")
            saved_ids = await service.save_strategy_elements(
                elements, tenant_id=tenant_id, created_by=created_by, db=db
            )

            if req.save_as_set:
                set_name = req.set_name or f"{report.structureType}策略组合"
                strategy_set_id = await service.save_as_strategy_set(
                    elements,
                    name=set_name,
                    tenant_id=tenant_id,
                    created_by=created_by,
                    platform=req.platform,
                    db=db,
                )

        return ExtractElementsResponse(
            elements=elements,
            saved_element_ids=saved_ids,
            strategy_set_id=strategy_set_id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"策略元素提取异常: {str(exc)}",
        )


# ═══════════════════════════════════════════════════════
# Keyword Library Management (v4.0 新增)
# ═══════════════════════════════════════════════════════

@router.get("/keywords")
async def list_keywords(
    dimension: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """📚 获取爆款分析关键词库（支持分页和过滤）。"""
    query = select(KeywordLibraryORM)
    count_query = select(func.count()).select_from(KeywordLibraryORM)

    if dimension:
        query = query.where(KeywordLibraryORM.dimension == dimension)
        count_query = count_query.where(KeywordLibraryORM.dimension == dimension)
    if is_active is not None:
        query = query.where(KeywordLibraryORM.is_active == is_active)
        count_query = count_query.where(KeywordLibraryORM.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return _ok({
        "total": total,
        "page": page,
        "page_size": page_size,
        "keywords": [
            {
                "id": k.id,
                "keyword": k.keyword,
                "dimension": k.dimension,
                "weight": k.weight,
                "applicable_structures": k.applicable_structures,
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat() if k.created_at else "",
                "updated_at": k.updated_at.isoformat() if k.updated_at else "",
            }
            for k in items
        ],
    })


@router.post("/keywords", status_code=201)
async def create_keyword(
    req: KeywordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """ 创建关键词。"""
    user_id = getattr(current_user, "username", "system")

    keyword = KeywordLibraryORM(
        keyword=req.keyword,
        dimension=req.dimension,
        weight=req.weight,
        applicable_structures=req.applicable_structures,
        is_active=True,
    )
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)

    _log_keyword_change(
        action="CREATE",
        keyword_id=keyword.id,
        keyword_text=keyword.keyword,
        changed_by=user_id,
        after={
            "keyword": keyword.keyword,
            "dimension": keyword.dimension,
            "weight": keyword.weight,
            "applicable_structures": keyword.applicable_structures,
        },
    )

    return _ok({
        "id": keyword.id,
        "keyword": keyword.keyword,
        "dimension": keyword.dimension,
        "weight": keyword.weight,
        "applicable_structures": keyword.applicable_structures,
        "is_active": keyword.is_active,
        "created_at": keyword.created_at.isoformat() if keyword.created_at else "",
    })


@router.put("/keywords/{keyword_id}")
async def update_keyword(
    keyword_id: int,
    req: KeywordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """更新关键词。"""
    user_id = getattr(current_user, "username", "system")

    result = await db.execute(
        select(KeywordLibraryORM).where(KeywordLibraryORM.id == keyword_id)
    )
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    before = {
        "keyword": keyword.keyword,
        "dimension": keyword.dimension,
        "weight": keyword.weight,
        "applicable_structures": keyword.applicable_structures,
        "is_active": keyword.is_active,
    }

    if req.keyword is not None:
        keyword.keyword = req.keyword
    if req.dimension is not None:
        keyword.dimension = req.dimension
    if req.weight is not None:
        keyword.weight = req.weight
    if req.applicable_structures is not None:
        keyword.applicable_structures = req.applicable_structures
    if req.is_active is not None:
        keyword.is_active = req.is_active

    await db.commit()
    await db.refresh(keyword)

    after = {
        "keyword": keyword.keyword,
        "dimension": keyword.dimension,
        "weight": keyword.weight,
        "applicable_structures": keyword.applicable_structures,
        "is_active": keyword.is_active,
    }

    _log_keyword_change(
        action="UPDATE",
        keyword_id=keyword.id,
        keyword_text=keyword.keyword,
        changed_by=user_id,
        before=before,
        after=after,
    )

    return _ok({
        "id": keyword.id,
        "keyword": keyword.keyword,
        "dimension": keyword.dimension,
        "weight": keyword.weight,
        "applicable_structures": keyword.applicable_structures,
        "is_active": keyword.is_active,
        "updated_at": keyword.updated_at.isoformat() if keyword.updated_at else "",
    })


@router.delete("/keywords/{keyword_id}", status_code=200)
async def delete_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """删除关键词。"""
    user_id = getattr(current_user, "username", "system")

    result = await db.execute(
        select(KeywordLibraryORM).where(KeywordLibraryORM.id == keyword_id)
    )
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    _log_keyword_change(
        action="DELETE",
        keyword_id=keyword.id,
        keyword_text=keyword.keyword,
        changed_by=user_id,
        before={
            "keyword": keyword.keyword,
            "dimension": keyword.dimension,
            "weight": keyword.weight,
        },
        after=None,
    )

    await db.delete(keyword)
    await db.commit()

    return _ok({"deleted": True, "keyword_id": keyword_id})


@router.get("/keywords/changelog")
async def list_keyword_changelog(
    limit: int = Query(50, ge=1, le=200),
):
    """📜 获取关键词变更日志（MVP 内存存储）。"""
    logs = _keyword_changelog[-limit:][::-1]
    return _ok({
        "total": len(_keyword_changelog),
        "limit": limit,
        "logs": logs,
    })


@router.get("/categories")
async def list_categories():
    """🏷 获取笔记分类列表。"""
    categories = [
        CategoryItem(id="pet_care", name="宠物养护", description="宠物日常护理、健康等"),
        CategoryItem(id="pet_food", name="宠物食品", description="猫粮狗粮、零食、营养品"),
        CategoryItem(id="pet_health", name="宠物健康", description="驱虫、疫苗、疾病防治"),
        CategoryItem(id="pet_training", name="宠物训练", description="行为训练、技能教学"),
        CategoryItem(id="pet_lifestyle", name="宠物生活", description="宠物日常、穿搭、旅行"),
        CategoryItem(id="product_review", name="产品测评", description="宠物用品测评、对比"),
        CategoryItem(id="saving_tips", name="省钱攻略", description="养宠省钱技巧、平价替代"),
        CategoryItem(id="story", name="宠物故事", description="与宠物相关的真实故事"),
    ]
    return _ok([c.model_dump() for c in categories])


# ═══════════════════════════════════════════════════════
# Legacy Endpoints (Backward compatible)
# ═══════════════════════════════════════════════════════

@router.post("/parse")
async def parse_viral_content(req: ParseRequest):
    """解析爆款内容结构。（Legacy）"""
    return _ok(
        ParseResponse(
            hook_pattern="痛点反问式开场",
            body_structure="问题描述 → 解决方案 → 使用体验 → 效果对比",
            cta_pattern="引导评论互动 + 收藏暗示",
            tone="亲切/专业",
            keywords=["驱虫", "狗狗", "省钱", "养宠"],
        ).model_dump()
    )


@router.get("/templates")
async def list_templates():
    """获取预设 ContentTemplate 列表。（Legacy）"""
    return _ok([t.model_dump() for t in MOCK_TEMPLATES])


@router.post("/generate")
async def generate_content(req: GenerateRequest):
    """基于模板和变量一键生成内容。（Legacy）"""
    vars_map = req.variables
    return _ok(
        GenerateResponse(
            title=f"【{vars_map.get('pet_name', '狗狗')}驱虫攻略】{vars_map.get('solution', '平价方案')}大揭秘",
            body=f"作为一名{vars_map.get('persona', '铲屎官')}，我发现很多铲屎官都在为{vars_map.get('problem', '驱虫贵')}烦恼。\n\n今天分享一个{vars_map.get('solution', '平价驱虫药')}，我家{vars_map.get('pet_name', '豆豆')}用了{vars_map.get('duration', '3个月')}，效果{vars_map.get('effect', '非常好')}。\n\n大家有什么驱虫经验欢迎在评论区交流！",
            hashtags=["驱虫", "养狗", "省钱攻略", "宠物健康"],
        ).model_dump()
    )
