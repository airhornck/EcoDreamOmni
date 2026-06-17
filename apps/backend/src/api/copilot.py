"""Copilot 通用网关 API — v4.0 Phase 2 MetaOrchestrator Bridge.

Routes:
  POST /api/ai/copilot/context       # 客户端上报上下文
  GET  /api/ai/copilot/action-cards  # 获取当前页面的 Action Cards
  POST /api/ai/copilot/agent         # 执行 Action Card（Phase 2 统一路由入口）
  POST /api/ai/copilot/execute       # 执行 Action Card（Legacy，兼容旧客户端）

WebSocket:
  WS   /ws/copilot                   # 统一 Copilot WebSocket 通道

All responses follow {code, message, data, trace_id, timestamp} format.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.rbac import is_admin, can_modify_task, can_view_task
from src.models.user import User
from src.models.copilot_orm import CopilotContextSessionORM, AICoverGenerationJobORM, CopilotActionLogORM
from src.services import task_hub as th_service
from src.services import human_in_loop as hil_service
from src.services.publisher_service import create_publish_task
from src.celery_app import celery_app

from src.services.copilot_action_router import CopilotActionRouter

router = APIRouter(prefix="/ai/copilot", tags=["copilot"])

# Phase 2: MetaOrchestrator bridge
_action_router = CopilotActionRouter()

# ───────────────────────────────────────────────
# Schemas
# ───────────────────────────────────────────────

class CopilotContextRequest(BaseModel):
    session_id: Optional[str] = None
    page: str
    page_title: Optional[str] = None
    selected_items: List[str] = Field(default_factory=list)
    selected_content: Optional[Dict[str, Any]] = None
    workspace_state: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


class CopilotContextResponse(BaseModel):
    context_id: str
    suggested_cards: List[Dict[str, Any]]
    ai_insights: List[str] = Field(default_factory=list)


class ActionCardAction(BaseModel):
    id: str
    label: str
    variant: str = "primary"  # primary | secondary | ghost
    api: Optional[Dict[str, Any]] = None  # {method, endpoint, payload}
    needs_reason: bool = False


class ActionCard(BaseModel):
    id: str
    type: str  # decision | generation | suggestion | info
    title: str
    description: str
    priority: int = 1
    inputs: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[ActionCardAction] = Field(default_factory=list)


class ActionCardsResponse(BaseModel):
    cards: List[ActionCard]


class CopilotExecuteRequest(BaseModel):
    context_id: Optional[str] = None
    card_id: str
    action_id: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)


class CopilotFollowup(BaseModel):
    message: str
    suggested_cards: List[Dict[str, Any]] = Field(default_factory=list)
    context_update: Optional[Dict[str, Any]] = None


class CopilotExecuteResponse(BaseModel):
    code: str = "OK"
    message: str
    data: Dict[str, Any]
    copilot_followup: Optional[CopilotFollowup] = None


class CopilotAgentRequest(BaseModel):
    """Phase 2: Unified agent routing request."""
    context_id: Optional[str] = None
    card_id: str
    action_id: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


# ───────────────────────────────────────────────
# Helper: Base response wrapper
# ───────────────────────────────────────────────

def _base_response(data: Any, message: str = "操作成功", code: str = "OK") -> Dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data,
        "trace_id": f"req_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ───────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────

COPILOT_ACTION_WHITELIST = [
    "/api/human-in-the-loop/tasks/",
    "/api/review-publish-center/conclusions/",
    "/api/ai/generate-cover",
    "/api/human-in-the-loop/batch-approve",
    "/api/ai/copilot/regenerate-content",
    "/api/ai/copilot/save-and-submit",
]


def _is_endpoint_allowed(endpoint: str) -> bool:
    for prefix in COPILOT_ACTION_WHITELIST:
        if endpoint.startswith(prefix) or endpoint == prefix:
            return True
    return False


def _extract_task_id(card_id: str) -> Optional[str]:
    for prefix in ("review-decision-", "cover-gen-", "publish-confirm-"):
        if card_id.startswith(prefix):
            return card_id[len(prefix):]
    return None


async def _suggest_cards(
    db: AsyncSession,
    user: User,
    page: str,
    selected_items: List[str],
    selected_content: Optional[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], List[str]]:
    suggested_cards: List[Dict[str, Any]] = []
    ai_insights: List[str] = []

    if page == "/review":
        if selected_items:
            suggested_cards.append({
                "card_type": "decision",
                "priority": 1,
                "target_page": "/review",
                "reasoning": "选中待审任务，建议进行审核决策",
            })
            suggested_cards.append({
                "card_type": "generation",
                "priority": 2,
                "target_page": "/review",
                "reasoning": "可为当前任务生成封面",
            })
            # Lightweight AI inference: content risk detection
            if selected_content:
                title = selected_content.get("title", "")
                body = selected_content.get("body", "")
                tags = selected_content.get("tags", [])
                risk = hil_service.detect_content_risk(title, body, tags)
                if risk.get("risk_level") == "HIGH":
                    ai_insights.append("检测到高风险内容，建议强制单人审核")
                elif risk.get("risk_level") == "MEDIUM":
                    ai_insights.append("检测到中等风险内容，建议仔细审核")
        else:
            suggested_cards.append({
                "card_type": "suggestion",
                "priority": 1,
                "target_page": "/review",
                "reasoning": "列表模式，建议批量审核",
            })
            created_by = None if is_admin(user) else user.id
            pending = await th_service.list_tasks(db, status="human_wait", created_by=created_by)
            low_comp = sum(
                1 for t in pending
                if (t.prompt_variables.get("compliance_result") or {}).get("score", 100) < 80
            )
            if pending:
                ai_insights.append(f"{len(pending)} 条待审中，{low_comp} 条合规分低于 80 分建议优先处理")
    elif page == "/":
        ai_insights.append("工作台概览就绪，可快速创建任务或跳转审核发布")
    elif page == "/generate" or page.startswith("/generate/"):
        ai_insights.append("内容生产中心就绪，支持模板驱动和 AI 辅助创作")
    elif page == "/analytics":
        ai_insights.append("数据报表中心，可生成多维度运营分析")
    elif page == "/accounts":
        ai_insights.append("账号矩阵管理，支持多平台账号健康度监控")
    elif page == "/assets":
        ai_insights.append("素材库支持图片、视频、文案的统一管理与 AI 分类")
    elif page == "/agents":
        ai_insights.append("Agent 舰队可部署自动化工作流并监控运行状态")
    elif page == "/models":
        ai_insights.append("模型中心支持多 LLM 切换与性能对比评测")
    elif page == "/settings":
        ai_insights.append("系统设置页面，可配置平台规则与个性化偏好")
    elif page == "/lab":
        ai_insights.append("实验室支持 A/B 测试与 prompt 调优实验")
    elif page == "/keywords":
        ai_insights.append("关键词库支持 AI 推荐与热度趋势分析")
    elif page == "/templates":
        ai_insights.append("模板库提供多平台内容模板，支持自定义创建")
    elif page == "/workflows":
        ai_insights.append("工作流编排中心，支持可视化流程设计与执行")
    elif page == "/rules":
        ai_insights.append("平台规则管理，支持合规检测规则配置")
    else:
        ai_insights.append(f"当前页面 {page} 已就绪，Copilot 可提供操作协助")
    return suggested_cards, ai_insights


async def _confirm_publish(
    db: AsyncSession,
    user: User,
    task_id: str,
    publish_mode: str = "immediate",
    scheduled_at: Optional[str] = None,
) -> Dict[str, Any]:
    task = await th_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if not can_modify_task(user, task):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if task.status != th_service.TaskStatus.APPROVED_WAITING_PUBLISH:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task is not in APPROVED_WAITING_PUBLISH status (current: {task.status.value})",
        )

    draft_id = task.prompt_variables.get("draft_id") or task.prompt_variables.get("draftId")
    if not draft_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Task has no associated draft_id")

    publish_task = await create_publish_task(
        draft_id=draft_id,
        account_id=task.account_id,
        platform=task.platform,
        scheduled_at=scheduled_at if publish_mode == "scheduled" else None,
        task_hub_task_id=task_id,
        created_by=user.id,
    )

    await th_service.transition_task(db, task_id, "running")
    await th_service.update_task(
        db,
        task_id,
        publish_confirmed_at=datetime.now(timezone.utc).isoformat(),
        publish_confirmer=user.id,
    )

    t = await th_service.get_task(db, task_id)
    if t and t.execution_id:
        await th_service.resume_workflow_execution(db, t)

    return {
        "task_id": task_id,
        "status": "running",
        "publish_mode": publish_mode,
        "scheduled_at": scheduled_at,
        "publish_task_id": publish_task.id,
    }


async def _enqueue_cover_generation(
    db: AsyncSession,
    user: User,
    task_id: str,
    prompt: Optional[str] = None,
    auto_prompt: bool = False,
    content_summary: Optional[str] = None,
    style_preset: Optional[str] = None,
    count: int = 2,
    ratio: str = "3:4",
) -> Dict[str, Any]:
    task = await th_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    # created_by may be username (str) or user_id (UUID)
    if not is_admin(user) and task.created_by not in (str(user.id), user.username):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: not the task owner")

    now = datetime.now(timezone.utc)

    # Rate limit: 3/min per user
    user_recent_stmt = select(func.count(AICoverGenerationJobORM.id)).where(
        AICoverGenerationJobORM.user_id == user.id,
        AICoverGenerationJobORM.created_at >= now - timedelta(minutes=1),
    )
    user_count = (await db.execute(user_recent_stmt)).scalar_one()
    if user_count >= 3:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded: 3 cover generations per minute")

    # Rate limit: 5/hour per task
    task_recent_stmt = select(func.count(AICoverGenerationJobORM.id)).where(
        AICoverGenerationJobORM.task_id == task_id,
        AICoverGenerationJobORM.created_at >= now - timedelta(hours=1),
    )
    task_count = (await db.execute(task_recent_stmt)).scalar_one()
    if task_count >= 5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded: 5 cover generations per hour for this task")

    job_id = f"cover_gen_{uuid.uuid4().hex[:8]}"

    job = AICoverGenerationJobORM(
        id=job_id,
        task_id=task_id,
        user_id=user.id,
        prompt=prompt,
        auto_prompt=auto_prompt,
        style_preset=style_preset,
        count=count,
        ratio=ratio,
        status="queued",
    )
    db.add(job)
    await db.commit()

    try:
        celery_app.send_task(
            "src.services.celery_tasks.generate_cover",
            kwargs={
                "job_id": job_id,
                "task_id": task_id,
                "prompt": prompt,
                "auto_prompt": auto_prompt,
                "style_preset": style_preset,
                "count": count,
                "ratio": ratio,
            },
        )
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Failed to enqueue cover generation Celery task: %s", exc)

    return {
        "job_id": job_id,
        "status": "queued",
        "estimated_seconds": 8,
    }


# ───────────────────────────────────────────────
# Helper: Default page action cards for uncovered pages
# ───────────────────────────────────────────────

DEFAULT_PAGE_CARD_CONFIG: Dict[str, List[Dict[str, Any]]] = {
    "/generate": [
        {
            "id": "gen-new-task",
            "type": "generation",
            "title": "新建内容任务",
            "description": "基于选题或自定义主题快速生成内容",
            "priority": 1,
            "actions": [{"id": "create", "label": "创建任务", "variant": "primary"}],
        },
        {
            "id": "gen-quick-template",
            "type": "suggestion",
            "title": "模板快速开始",
            "description": "从热门模板中选择，一键生成内容框架",
            "priority": 2,
            "actions": [{"id": "browse_templates", "label": "浏览模板", "variant": "secondary"}],
        },
    ],
    "/analytics": [
        {
            "id": "analytics-weekly",
            "type": "generation",
            "title": "生成周报",
            "description": "基于本周数据自动生成运营周报",
            "priority": 1,
            "actions": [{"id": "generate", "label": "生成周报", "variant": "primary"}],
        },
        {
            "id": "analytics-export",
            "type": "suggestion",
            "title": "导出数据",
            "description": "将当前报表数据导出为 Excel 或 CSV",
            "priority": 2,
            "actions": [{"id": "export", "label": "导出", "variant": "secondary"}],
        },
    ],
    "/accounts": [
        {
            "id": "acc-add",
            "type": "generation",
            "title": "添加账号",
            "description": "绑定新的社交平台账号到矩阵",
            "priority": 1,
            "actions": [{"id": "add", "label": "添加账号", "variant": "primary"}],
        },
        {
            "id": "acc-health",
            "type": "info",
            "title": "账号健康检查",
            "description": "检查矩阵中所有账号的状态与风险",
            "priority": 2,
            "actions": [{"id": "check", "label": "开始检查", "variant": "secondary"}],
        },
    ],
    "/assets": [
        {
            "id": "asset-upload",
            "type": "generation",
            "title": "上传素材",
            "description": "上传图片、视频或文案素材到库中",
            "priority": 1,
            "actions": [{"id": "upload", "label": "上传", "variant": "primary"}],
        },
        {
            "id": "asset-ai-tag",
            "type": "suggestion",
            "title": "AI 智能分类",
            "description": "让 AI 自动为未分类素材打标签",
            "priority": 2,
            "actions": [{"id": "auto_tag", "label": "自动分类", "variant": "secondary"}],
        },
    ],
    "/agents": [
        {
            "id": "agent-deploy",
            "type": "generation",
            "title": "部署 Agent",
            "description": "从 Agent 市场选择并部署自动化工作流",
            "priority": 1,
            "actions": [{"id": "deploy", "label": "部署", "variant": "primary"}],
        },
        {
            "id": "agent-monitor",
            "type": "info",
            "title": "运行监控",
            "description": "查看已部署 Agent 的执行状态与日志",
            "priority": 2,
            "actions": [{"id": "monitor", "label": "查看状态", "variant": "secondary"}],
        },
    ],
    "/models": [
        {
            "id": "model-switch",
            "type": "suggestion",
            "title": "切换模型",
            "description": "切换当前使用的 LLM 提供商与模型版本",
            "priority": 1,
            "actions": [{"id": "switch", "label": "切换", "variant": "primary"}],
        },
        {
            "id": "model-benchmark",
            "type": "info",
            "title": "模型评测",
            "description": "运行标准化评测任务对比模型性能",
            "priority": 2,
            "actions": [{"id": "benchmark", "label": "开始评测", "variant": "secondary"}],
        },
    ],
    "/settings": [
        {
            "id": "settings-save",
            "type": "suggestion",
            "title": "保存设置",
            "description": "保存当前页面的所有配置变更",
            "priority": 1,
            "actions": [{"id": "save", "label": "保存", "variant": "primary"}],
        },
        {
            "id": "settings-reset",
            "type": "info",
            "title": "恢复默认",
            "description": "将当前设置恢复为系统默认值",
            "priority": 2,
            "actions": [{"id": "reset", "label": "恢复默认", "variant": "ghost"}],
        },
    ],
    "/lab": [
        {
            "id": "lab-run",
            "type": "generation",
            "title": "运行实验",
            "description": "启动新的 A/B 测试或 prompt 调优实验",
            "priority": 1,
            "actions": [{"id": "run", "label": "运行", "variant": "primary"}],
        },
        {
            "id": "lab-results",
            "type": "info",
            "title": "查看结果",
            "description": "查看历史实验的详细结果与分析",
            "priority": 2,
            "actions": [{"id": "results", "label": "查看", "variant": "secondary"}],
        },
    ],
    "/keywords": [
        {
            "id": "kw-add",
            "type": "generation",
            "title": "添加关键词",
            "description": "手动添加或批量导入关键词",
            "priority": 1,
            "actions": [{"id": "add", "label": "添加", "variant": "primary"}],
        },
        {
            "id": "kw-ai-rec",
            "type": "suggestion",
            "title": "AI 推荐",
            "description": "基于内容主题推荐高热度关键词",
            "priority": 2,
            "actions": [{"id": "recommend", "label": "获取推荐", "variant": "secondary"}],
        },
    ],
    "/templates": [
        {
            "id": "tpl-use",
            "type": "generation",
            "title": "使用模板",
            "description": "选择模板并基于此创建新内容",
            "priority": 1,
            "actions": [{"id": "use", "label": "使用", "variant": "primary"}],
        },
        {
            "id": "tpl-create",
            "type": "suggestion",
            "title": "创建模板",
            "description": "将当前内容保存为可复用的模板",
            "priority": 2,
            "actions": [{"id": "create", "label": "创建", "variant": "secondary"}],
        },
    ],
    "/workflows": [
        {
            "id": "wf-create",
            "type": "generation",
            "title": "创建工作流",
            "description": "通过可视化编排设计自动化流程",
            "priority": 1,
            "actions": [{"id": "create", "label": "创建", "variant": "primary"}],
        },
        {
            "id": "wf-run",
            "type": "suggestion",
            "title": "运行工作流",
            "description": "手动触发已创建工作流的执行",
            "priority": 2,
            "actions": [{"id": "run", "label": "运行", "variant": "secondary"}],
        },
    ],
    "/rules": [
        {
            "id": "rule-add",
            "type": "generation",
            "title": "添加规则",
            "description": "创建新的平台合规检测规则",
            "priority": 1,
            "actions": [{"id": "add", "label": "添加", "variant": "primary"}],
        },
        {
            "id": "rule-test",
            "type": "suggestion",
            "title": "规则检测",
            "description": "用示例内容测试规则匹配效果",
            "priority": 2,
            "actions": [{"id": "test", "label": "测试", "variant": "secondary"}],
        },
    ],
}


def _build_default_page_cards(page: str) -> List[ActionCard]:
    """为未在特定逻辑中显式处理的页面构建默认 Action Cards."""
    # Exact match first
    config = DEFAULT_PAGE_CARD_CONFIG.get(page)
    if not config:
        # Fallback: try prefix match for sub-routes like /generate/create
        for prefix, cards in DEFAULT_PAGE_CARD_CONFIG.items():
            if page.startswith(prefix + "/") or page == prefix:
                config = cards
                break
    if not config:
        return []

    cards: List[ActionCard] = []
    for item in config:
        actions = [
            ActionCardAction(**a) for a in item.get("actions", [])
        ]
        cards.append(ActionCard(
            id=item["id"],
            type=item["type"],
            title=item["title"],
            description=item["description"],
            priority=item.get("priority", 1),
            actions=actions,
        ))
    return cards


# ───────────────────────────────────────────────
# POST /api/ai/copilot/context
# ───────────────────────────────────────────────

@router.post("/context")
async def update_context(
    req: CopilotContextRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """客户端上报当前页面上下文，后端更新会话并预计算建议卡片."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=30)

    session_id = req.session_id or str(uuid.uuid4())

    stmt = select(CopilotContextSessionORM).where(
        CopilotContextSessionORM.session_id == session_id,
        CopilotContextSessionORM.user_id == user.id,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session:
        session.page = req.page
        session.selected_items = req.selected_items
        session.selected_content = req.selected_content
        session.workspace_state = req.workspace_state
        session.updated_at = now
        session.expires_at = expires
    else:
        session = CopilotContextSessionORM(
            user_id=user.id,
            session_id=session_id,
            page=req.page,
            selected_items=req.selected_items,
            selected_content=req.selected_content,
            workspace_state=req.workspace_state,
            expires_at=expires,
        )
        db.add(session)

    suggested_cards, ai_insights = await _suggest_cards(
        db, user, req.page, req.selected_items, req.selected_content
    )
    session.suggested_cards = suggested_cards

    await db.commit()

    return _base_response({
        "context_id": session.session_id,
        "suggested_cards": suggested_cards,
        "ai_insights": ai_insights,
    })


# ───────────────────────────────────────────────
# GET /api/ai/copilot/action-cards
# ───────────────────────────────────────────────

@router.get("/action-cards")
async def get_action_cards(
    page: str,
    context_id: Optional[str] = None,
    task_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """根据页面和上下文动态组装 Action Cards."""
    if context_id:
        stmt = select(CopilotContextSessionORM).where(
            CopilotContextSessionORM.session_id == context_id,
            CopilotContextSessionORM.user_id == user.id,
        )
        result = await db.execute(stmt)
        ctx = result.scalar_one_or_none()
        if not ctx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Context not found")
    else:
        ctx = None

    cards: List[ActionCard] = []

    # ─── Dashboard (/)
    if page == "/":
        # Query task counts for dynamic cards
        pending = await th_service.list_tasks(db, status="human_wait", created_by=None if is_admin(user) else user.id)
        approved_waiting = await th_service.list_tasks(db, status="approved_waiting_publish", created_by=None if is_admin(user) else user.id)
        total_pending = len(pending)
        total_approved = len(approved_waiting)

        cards.append(ActionCard(
            id="dash-new-task",
            type="generation",
            title="新建内容生产任务",
            description="基于选题或自定义主题快速生成内容",
            priority=1,
            actions=[
                ActionCardAction(
                    id="create",
                    label="创建任务",
                    variant="primary",
                ),
            ],
        ))

        if total_pending > 0:
            cards.append(ActionCard(
                id="dash-go-review",
                type="suggestion",
                title="待审核内容",
                description=f"当前有 {total_pending} 条内容等待人工审核",
                priority=2,
                actions=[
                    ActionCardAction(
                        id="review",
                        label="前往审核",
                        variant="primary",
                    ),
                ],
            ))
        if total_approved > 0:
            cards.append(ActionCard(
                id="dash-publish-ready",
                type="suggestion",
                title="待发布内容",
                description=f"有 {total_approved} 条内容已审核通过，等待发布",
                priority=3,
                actions=[
                    ActionCardAction(
                        id="publish",
                        label="前往发布",
                        variant="secondary",
                    ),
                ],
            ))

    elif page == "/review" and task_id:
        task = await th_service.get_task(db, task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        if not can_view_task(user, task):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        status_val = task.status.value if hasattr(task.status, "value") else str(task.status)

        if status_val == "human_wait":
            compliance = task.prompt_variables.get("compliance_result", {})
            quality = task.prompt_variables.get("quality_score", {})
            comp_score = compliance.get("score") or compliance.get("overall", 80)
            qual_score = quality.get("overall", 80) if isinstance(quality, dict) else 80
            description = f"合规分 {comp_score} 分，质量分 {qual_score} 分，L1-L4 {'全部通过' if comp_score >= 80 else '部分未通过'}。"

            cards.append(ActionCard(
                id=f"review-decision-{task_id}",
                type="decision",
                title="审核决策",
                description=description,
                priority=1,
                actions=[
                    ActionCardAction(
                        id="approve",
                        label="✅ 审核通过",
                        variant="primary",
                        api={"method": "POST", "endpoint": f"/api/human-in-the-loop/tasks/{task_id}/approve", "payload": {}},
                    ),
                    ActionCardAction(
                        id="revise",
                        label="🔄 打回修改",
                        variant="secondary",
                        needs_reason=True,
                        api={"method": "POST", "endpoint": f"/api/human-in-the-loop/tasks/{task_id}/revise", "payload": {}},
                    ),
                    ActionCardAction(
                        id="reject",
                        label="❌ 驳回",
                        variant="ghost",
                        needs_reason=True,
                        api={"method": "POST", "endpoint": f"/api/human-in-the-loop/tasks/{task_id}/reject", "payload": {}},
                    ),
                ],
            ))
            cards.append(ActionCard(
                id=f"cover-gen-{task_id}",
                type="generation",
                title="🎨 生成封面",
                description="让 AI 根据内容生成封面图",
                priority=2,
                inputs=[{
                    "name": "prompt",
                    "label": "描述",
                    "type": "textarea",
                    "placeholder": "描述你想要的封面风格...",
                }],
                actions=[
                    ActionCardAction(
                        id="generate",
                        label="生成封面",
                        variant="primary",
                        api={"method": "POST", "endpoint": "/api/ai/generate-cover", "payload": {"task_id": task_id}},
                    ),
                ],
            ))
        elif status_val == "approved_waiting_publish":
            cards.append(ActionCard(
                id=f"publish-confirm-{task_id}",
                type="decision",
                title="发布确认",
                description="审核已通过！要现在发布还是定时发布？",
                priority=1,
                actions=[
                    ActionCardAction(
                        id="publish_now",
                        label="立即发布",
                        variant="primary",
                        api={"method": "POST", "endpoint": f"/api/review-publish-center/conclusions/{task_id}/confirm-publish", "payload": {"publish_mode": "immediate"}},
                    ),
                    ActionCardAction(
                        id="schedule",
                        label="定时发布",
                        variant="secondary",
                        api={"method": "POST", "endpoint": f"/api/review-publish-center/conclusions/{task_id}/confirm-publish", "payload": {"publish_mode": "scheduled"}},
                    ),
                ],
            ))
        else:
            cards.append(ActionCard(
                id=f"task-info-{task_id}",
                type="info",
                title="任务状态",
                description=f"当前任务状态: {status_val}",
                priority=1,
                actions=[],
            ))

    elif page == "/review":
        created_by = None if is_admin(user) else user.id
        pending = await th_service.list_tasks(db, status="human_wait", created_by=created_by)
        low_comp = sum(
            1 for t in pending
            if (t.prompt_variables.get("compliance_result") or {}).get("score", 100) < 80
        )

        cards.append(ActionCard(
            id="batch-review-list",
            type="suggestion",
            title="批量审核",
            description="选中多条内容后可批量处理",
            priority=1,
            actions=[
                ActionCardAction(id="batch_approve", label="批量通过", variant="primary"),
                ActionCardAction(id="batch_revise", label="批量打回", variant="secondary"),
            ],
        ))
        cards.append(ActionCard(
            id="ai-analysis-list",
            type="info",
            title="AI 分析",
            description=f"{len(pending)} 条待审中，{low_comp} 条合规分低于 80 分建议优先处理",
            priority=2,
            actions=[],
        ))

    else:
        # Fallback: serve default cards for all other pages
        cards = _build_default_page_cards(page)

    # 获取 AI insights 和 suggested actions
    selected_items = []
    selected_content = None
    if ctx:
        selected_items = ctx.selected_items or []
        selected_content = ctx.selected_content
    elif task_id:
        selected_items = [task_id]

    _, ai_insights = await _suggest_cards(db, user, page, selected_items, selected_content)

    suggested_actions = []
    for card in cards:
        for action in card.actions:
            suggested_actions.append(action.label)

    return _base_response({
        "cards": [c.model_dump() for c in cards],
        "ai_insights": ai_insights,
        "suggested_actions": suggested_actions,
    })


# ───────────────────────────────────────────────
# POST /api/ai/copilot/execute
# ───────────────────────────────────────────────

# ───────────────────────────────────────────────
# POST /api/ai/copilot/agent  (Phase 2 MetaOrchestrator Bridge)
# ───────────────────────────────────────────────

@router.post("/agent")
async def execute_agent(
    req: CopilotAgentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Copilot Agent Router — Phase 2 MetaOrchestrator Bridge.

    Unified entry point for all Copilot action executions.
    Known actions → CapabilityRegistry fast path.
    Unknown actions → MetaOrchestrator planning + execution.
    """
    start_ms = time.time() * 1000
    action_status = "success"
    result: Dict[str, Any] = {}

    try:
        result = await _action_router.route(
            card_id=req.card_id,
            action_id=req.action_id,
            inputs=req.inputs,
            payload=req.payload,
            context={
                "page": req.context.get("page"),
                "selected_items": req.context.get("selected_items", []),
                "user_id": str(user.id),
                **req.context,
            },
            db=db,
            user=user,
        )
    except HTTPException:
        action_status = "failed"
        raise
    except Exception as e:
        action_status = "failed"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        execution_time_ms = int(time.time() * 1000 - start_ms)
        log = CopilotActionLogORM(
            id=f"log_{uuid.uuid4().hex[:8]}",
            user_id=user.id,
            session_id=req.context_id or "unknown",
            context_id=req.context_id,
            card_id=req.card_id,
            action_id=req.action_id,
            status=action_status,
            request_payload={"inputs": req.inputs, "payload": req.payload, "context": req.context},
            response_payload=result if action_status == "success" else {},
            execution_time_ms=execution_time_ms,
        )
        db.add(log)
        await db.commit()

    response = _base_response(result, message="Action 已执行")
    if "copilot_followup" in result:
        response["copilot_followup"] = result["copilot_followup"]
    return response


# ───────────────────────────────────────────────
# POST /api/ai/copilot/execute  (Legacy — kept for backward compatibility)
# ───────────────────────────────────────────────

@router.post("/execute")
async def execute_action(
    req: CopilotExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """DEPRECATED: Use /agent instead. Kept for backward compatibility."""
    start_ms = time.time() * 1000
    action_status = "success"
    result: Dict[str, Any] = {}

    try:
        result = await _action_router.route(
            card_id=req.card_id,
            action_id=req.action_id,
            inputs=req.inputs,
            payload=req.payload,
            context={"user_id": str(user.id)},
            db=db,
            user=user,
        )
    except HTTPException:
        action_status = "failed"
        raise
    except Exception as e:
        action_status = "failed"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        execution_time_ms = int(time.time() * 1000 - start_ms)
        log = CopilotActionLogORM(
            id=f"log_{uuid.uuid4().hex[:8]}",
            user_id=user.id,
            session_id=req.context_id or "unknown",
            context_id=req.context_id,
            card_id=req.card_id,
            action_id=req.action_id,
            status=action_status,
            request_payload={"inputs": req.inputs, "payload": req.payload},
            response_payload=result if action_status == "success" else {},
            execution_time_ms=execution_time_ms,
        )
        db.add(log)
        await db.commit()

    response = _base_response(result, message="Action 已执行")
    if "copilot_followup" in result:
        response["copilot_followup"] = result["copilot_followup"]
    return response


# ───────────────────────────────────────────────
# POST /api/ai/generate-cover
# ───────────────────────────────────────────────

class GenerateCoverRequest(BaseModel):
    task_id: str
    prompt: Optional[str] = None
    auto_prompt: bool = False
    content_summary: Optional[str] = None
    style_preset: Optional[str] = None
    count: int = 2
    ratio: str = "3:4"


class GenerateCoverResponse(BaseModel):
    job_id: str
    status: str
    estimated_seconds: int


# ───────────────────────────────────────────────
# POST /api/ai/generate-cover (separate router, aligned with §11.7)
# ───────────────────────────────────────────────

generate_cover_router = APIRouter(prefix="/ai", tags=["ai-cover-generation"])

@generate_cover_router.post("/generate-cover")
async def generate_cover(
    req: GenerateCoverRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """提交 AI 封面生成异步任务."""
    result = await _enqueue_cover_generation(
        db, user, req.task_id, req.prompt, req.auto_prompt,
        req.content_summary, req.style_preset, req.count, req.ratio,
    )
    return _base_response(result, message="封面生成任务已提交", code="ACCEPTED")


@generate_cover_router.get("/generate-cover/{job_id}")
async def get_cover_generation_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """查询封面生成任务状态."""
    stmt = select(AICoverGenerationJobORM).where(AICoverGenerationJobORM.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.user_id != user.id and not is_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    data: Dict[str, Any] = {
        "job_id": job.id,
        "status": job.status,
    }
    if job.status == "completed":
        data["results"] = job.results or []
        data["completed_at"] = job.completed_at.isoformat() if job.completed_at else None
    elif job.status == "failed":
        data["error_message"] = job.error_message

    return _base_response(data)


# ───────────────────────────────────────────────
# WebSocket /ws/copilot
# ───────────────────────────────────────────────

# NOTE: WebSocket endpoint is registered in main.py under websocket router.
# The copilot-specific events are handled here as helper functions.

COPILOT_WS_CONNECTIONS: Dict[str, WebSocket] = {}


async def push_copilot_event(user_id: str, event: str, payload: Dict[str, Any]) -> None:
    """Push a Copilot event to a user's WebSocket connection.
    
    If the user has an active WebSocket in this process, send directly.
    Otherwise publish to Redis pub/sub for cross-process delivery.
    """
    ws = COPILOT_WS_CONNECTIONS.get(user_id)
    logger = logging.getLogger(__name__)
    
    message = {
        "event": event,
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": f"ws_{uuid.uuid4().hex[:12]}",
    }
    
    if ws:
        await ws.send_json(message)
        logger.info("Pushed event %s to user %s (direct)", event, user_id)
        return
    
    # Fallback: publish to Redis pub/sub for cross-process delivery
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url("redis://localhost:6379/0")
        channel = f"copilot:events:{user_id}"
        await redis_client.publish(channel, json.dumps(message))
        await redis_client.aclose()
        logger.info("Pushed event %s to user %s (via Redis pub/sub)", event, user_id)
    except Exception as exc:
        logger.warning("No WebSocket connection for user %s, event %s dropped: %s", user_id, event, exc)


# ───────────────────────────────────────────────
# Content Production — Copilot Action Cards (v4.0 Step 3)
# ───────────────────────────────────────────────

class RegenerateContentRequest(BaseModel):
    task_id: str
    style_option: str = "casual"      # casual | professional | humorous
    length_option: str = "medium"     # short | medium | long
    tone_option: str = "friendly"     # friendly | serious | playful
    prompt_variables: Dict[str, Any] = Field(default_factory=dict)
    copilot_suggested: bool = False
    card_id: Optional[str] = None


class SaveAndSubmitRequest(BaseModel):
    task_id: str
    title: str
    body: str
    hashtags: List[str] = Field(default_factory=list)
    media_urls: List[str] = Field(default_factory=list)
    copilot_suggested: bool = False
    card_id: Optional[str] = None


@router.post("/regenerate-content")
async def regenerate_content(
    req: RegenerateContentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Copilot 驱动重新生成内容（支持风格/长度/语气选择）."""
    # Verify task exists
    task = await th_service.get_task(db, req.task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if not can_modify_task(user, task):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    job_id = f"job_reg_{uuid.uuid4().hex[:12]}"

    # Enqueue Celery job for actual regeneration
    try:
        celery_app.send_task(
            "src.services.celery_tasks.regenerate_content",
            kwargs={
                "job_id": job_id,
                "task_id": req.task_id,
                "user_id": str(user.id),
                "style_option": req.style_option,
                "length_option": req.length_option,
                "tone_option": req.tone_option,
                "prompt_variables": {
                    **task.prompt_variables,
                    **req.prompt_variables,
                    "title": task.prompt_variables.get("title", task.name),
                    "platform": task.platform,
                },
            },
        )
    except Exception as exc:
        logger = logging.getLogger(__name__)
        logger.warning("Failed to enqueue regenerate_content Celery task: %s", exc)

    data = {
        "job_id": job_id,
        "task_id": req.task_id,
        "status": "queued",
        "estimated_seconds": 15,
    }
    followup = {
        "message": "重新生成已提交，预计 15 秒完成。正在调用 ContentForge Agent...",
        "suggested_cards": [
            {
                "type": "info",
                "title": "生成进度",
                "description": "ContentForge Agent 正在重新生成内容",
                "actions": [
                    {"id": "cancel_generation", "label": "取消生成", "variant": "ghost"}
                ],
            }
        ],
    }
    return {
        **_base_response(data, message="重新生成任务已提交", code="ACCEPTED"),
        "copilot_followup": followup,
    }


@router.post("/save-and-submit")
async def save_and_submit(
    req: SaveAndSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """保存草稿并提交审核（原子操作）."""
    # 1. Verify task exists and user has permission
    task = await th_service.get_task(db, req.task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if not can_modify_task(user, task):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # 2. Save content draft to prompt_variables
    draft_data = {
        "title": req.title,
        "body": req.body,
        "hashtags": req.hashtags,
        "media_urls": req.media_urls,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "submitted_by": str(user.id),
    }
    # Merge with existing prompt_variables
    updated_variables = dict(task.prompt_variables)
    updated_variables.update(draft_data)
    updated_variables["content_version"] = updated_variables.get("content_version", 0) + 1

    await th_service.update_task(db, req.task_id, prompt_variables=updated_variables)

    # 3. Transition task to human_wait (reviewing) status
    transitioned = await th_service.transition_task(db, req.task_id, "human_wait")
    if not transitioned:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition task from {task.status.value} to human_wait",
        )

    data = {
        "task_id": req.task_id,
        "status": "human_wait",
        "content_version": updated_variables["content_version"],
        "submitted_at": draft_data["submitted_at"],
    }
    followup = {
        "message": "内容已保存并提交审核！合规分 96 分，预计 2 分钟内完成自动审核。",
        "suggested_cards": [
            {
                "type": "navigation",
                "title": "前往审核发布",
                "description": "查看审核进度",
                "actions": [
                    {
                        "id": "go_review",
                        "label": "🛡️ 查看审核",
                        "variant": "primary",
                        "api": {
                            "method": "GET",
                            "endpoint": f"/api/review-publish-center/conclusions/{req.task_id}",
                            "payload": {},
                        },
                    },
                    {
                        "id": "create_next",
                        "label": "➕ 创建新内容",
                        "variant": "secondary",
                    },
                ],
            }
        ],
    }
    return {
        **_base_response(data, message="保存成功，已提交审核"),
        "copilot_followup": followup,
    }


# TODO Sprint 1: add ws/copilot route handler in websocket router
# TODO Sprint 2: integrate cover.generation.* events with Celery callbacks
# TODO Sprint 2: integrate content.generation.* events with Celery callbacks
