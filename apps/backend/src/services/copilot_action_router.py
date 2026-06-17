"""Copilot Action Router — Phase 2 Bridge (MetaOrchestrator Integration).

Routes Copilot action executions through:
  1. CapabilityRegistry — known actions → fast path
  2. MetaOrchestrator — unknown / complex actions → planning + execution
  3. SkillHub / AgentOrchestra — actual execution layer

Architecture red line: Router delegates to services, never touches DB directly.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from src.core.rbac import is_admin, can_review_task, can_modify_task
from src.harness.meta_orchestrator import MetaOrchestrator, IntentType
from src.services import skill_hub
from src.services import agent_orchestra
from src.services import human_in_loop as hil_service
from src.services import task_hub as th_service
from src.services.publisher_service import create_publish_task

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# Capability Registry
# ═══════════════════════════════════════════════════════

@dataclass
class CopilotCapability:
    """Registered capability for a Copilot action."""

    action_id: str
    mode: str  # "service" | "orchestrate" | "direct_skill" | "fallback_api"
    # For service mode
    service_handler: Optional[str] = None
    # For orchestrate mode
    intent_type: Optional[str] = None
    query_template: Optional[str] = None
    # For direct_skill mode
    skill_id: Optional[str] = None
    # For fallback_api mode
    fallback_api_method: Optional[str] = None
    fallback_api_endpoint: Optional[str] = None
    # Common
    description: str = ""


CAPABILITY_REGISTRY: Dict[str, CopilotCapability] = {
    # ─── Review / HIL actions ───
    "approve": CopilotCapability(
        action_id="approve",
        mode="service",
        service_handler="_handle_approve",
        description="审核通过任务",
    ),
    "revise": CopilotCapability(
        action_id="revise",
        mode="service",
        service_handler="_handle_revise",
        description="打回修改任务",
    ),
    "reject": CopilotCapability(
        action_id="reject",
        mode="service",
        service_handler="_handle_reject",
        description="驳回任务",
    ),
    "batch_approve": CopilotCapability(
        action_id="batch_approve",
        mode="service",
        service_handler="_handle_batch_approve",
        description="批量审核通过",
    ),
    "batch_revise": CopilotCapability(
        action_id="batch_revise",
        mode="service",
        service_handler="_handle_batch_revise",
        description="批量打回修改",
    ),
    # ─── Cover generation ───
    "generate": CopilotCapability(
        action_id="generate",
        mode="service",
        service_handler="_handle_generate_cover",
        description="生成封面图",
    ),
    # ─── Publish ───
    "publish_now": CopilotCapability(
        action_id="publish_now",
        mode="service",
        service_handler="_handle_publish",
        description="立即发布",
    ),
    "schedule": CopilotCapability(
        action_id="schedule",
        mode="service",
        service_handler="_handle_publish",
        description="定时发布",
    ),
    # ─── Orchestrate PoC actions ───
    "create": CopilotCapability(
        action_id="create",
        mode="orchestrate",
        intent_type="content_creation",
        query_template="创建新的社交媒体内容任务",
        description="创建内容任务（Orchestrate 模式）",
    ),
    "generate_weekly_report": CopilotCapability(
        action_id="generate_weekly_report",
        mode="orchestrate",
        intent_type="data_analysis",
        query_template="生成本周运营数据周报",
        description="生成周报（Orchestrate 模式）",
    ),
    # ─── Non-core pages Copilot alignment (Task Group E) ───
    # Account pool
    "add_account": CopilotCapability(
        action_id="add_account",
        mode="orchestrate",
        intent_type="account_management",
        query_template="创建一个新的平台账号",
        description="账号矩阵：创建新账号",
    ),
    "generate_schedule": CopilotCapability(
        action_id="generate_schedule",
        mode="orchestrate",
        intent_type="account_management",
        query_template="为账号生成最佳发布计划",
        description="账号矩阵：生成发布计划",
    ),
    # Asset pool
    "upload_asset": CopilotCapability(
        action_id="upload_asset",
        mode="orchestrate",
        intent_type="content_creation",
        query_template="上传新的图片或视频素材",
        description="素材库：上传素材",
    ),
    "auto_tag_assets": CopilotCapability(
        action_id="auto_tag_assets",
        mode="orchestrate",
        intent_type="content_creation",
        query_template="为素材库中的未标签素材自动打标签",
        description="素材库：AI 批量打标签",
    ),
    "apply_to_task": CopilotCapability(
        action_id="apply_to_task",
        mode="orchestrate",
        intent_type="content_creation",
        query_template="将素材应用到新任务",
        description="素材库：应用到任务",
    ),
    # Agent orchestra
    "ack_alert": CopilotCapability(
        action_id="ack_alert",
        mode="orchestrate",
        intent_type="system_query",
        query_template="确认当前 Agent 告警",
        description="Agent 舰队：确认告警",
    ),
    "deploy_agent": CopilotCapability(
        action_id="deploy_agent",
        mode="orchestrate",
        intent_type="system_query",
        query_template="部署新的 AI Agent",
        description="Agent 舰队：部署 Agent",
    ),
    # AI engine / proxy
    "add_model": CopilotCapability(
        action_id="add_model",
        mode="orchestrate",
        intent_type="system_query",
        query_template="添加新的 AI 模型配置",
        description="AI 引擎：添加模型",
    ),
    "add_proxy": CopilotCapability(
        action_id="add_proxy",
        mode="orchestrate",
        intent_type="system_query",
        query_template="添加新的 HTTP/SOCKS5 代理",
        description="AI 引擎：添加代理",
    ),
    "view_cost": CopilotCapability(
        action_id="view_cost",
        mode="orchestrate",
        intent_type="data_analysis",
        query_template="查看 AI 模型调用成本",
        description="AI 引擎：查看成本",
    ),
    "view_logs": CopilotCapability(
        action_id="view_logs",
        mode="orchestrate",
        intent_type="system_query",
        query_template="查看模型调用日志",
        description="AI 引擎：查看日志",
    ),
    "create_proxy": CopilotCapability(
        action_id="create_proxy",
        mode="orchestrate",
        intent_type="system_query",
        query_template="创建新的代理配置",
        description="代理配置：创建代理",
    ),
    "test_first_proxy": CopilotCapability(
        action_id="test_first_proxy",
        mode="orchestrate",
        intent_type="system_query",
        query_template="测试第一个代理连通性",
        description="代理配置：测试首个代理",
    ),
    "toggle_first_proxy": CopilotCapability(
        action_id="toggle_first_proxy",
        mode="orchestrate",
        intent_type="system_query",
        query_template="切换第一个代理的启用/禁用状态",
        description="代理配置：切换首个代理状态",
    ),
    "goto_engine": CopilotCapability(
        action_id="goto_engine",
        mode="orchestrate",
        intent_type="system_query",
        query_template="跳转到 AI 引擎页面",
        description="代理配置：前往 AI 引擎",
    ),
    # Platform rules
    "create_rule": CopilotCapability(
        action_id="create_rule",
        mode="orchestrate",
        intent_type="system_query",
        query_template="创建新的平台风控规则",
        description="平台规则：新建规则",
    ),
    "test_rule": CopilotCapability(
        action_id="test_rule",
        mode="orchestrate",
        intent_type="system_query",
        query_template="试跑平台规则并查看命中结果",
        description="平台规则：规则试跑",
    ),
    "toggle_rule": CopilotCapability(
        action_id="toggle_rule",
        mode="orchestrate",
        intent_type="system_query",
        query_template="切换平台规则的启用/禁用状态",
        description="平台规则：切换规则状态",
    ),
    # Vet drug
    "create_drug": CopilotCapability(
        action_id="create_drug",
        mode="orchestrate",
        intent_type="system_query",
        query_template="录入新的兽药批文",
        description="兽药批文库：新增批文",
    ),
    "bulk_import": CopilotCapability(
        action_id="bulk_import",
        mode="orchestrate",
        intent_type="system_query",
        query_template="批量导入兽药批文 CSV",
        description="兽药批文库：CSV 批量导入",
    ),
    "validate_claim": CopilotCapability(
        action_id="validate_claim",
        mode="orchestrate",
        intent_type="system_query",
        query_template="校验兽药产品宣称是否合规",
        description="兽药批文库：宣称校验",
    ),
    "expiry_warnings": CopilotCapability(
        action_id="expiry_warnings",
        mode="orchestrate",
        intent_type="system_query",
        query_template="查看即将过期的兽药批文",
        description="兽药批文库：到期预警",
    ),
    # Settings
    "save": CopilotCapability(
        action_id="save",
        mode="orchestrate",
        intent_type="system_query",
        query_template="保存系统设置",
        description="系统设置：保存配置",
    ),
    "tab_general": CopilotCapability(
        action_id="tab_general",
        mode="orchestrate",
        intent_type="system_query",
        query_template="切换到通用设置 Tab",
        description="系统设置：通用设置",
    ),
    "tab_api": CopilotCapability(
        action_id="tab_api",
        mode="orchestrate",
        intent_type="system_query",
        query_template="切换到 API 配置 Tab",
        description="系统设置：API 配置",
    ),
    "tab_notifications": CopilotCapability(
        action_id="tab_notifications",
        mode="orchestrate",
        intent_type="system_query",
        query_template="切换到通知设置 Tab",
        description="系统设置：通知设置",
    ),
    "tab_security": CopilotCapability(
        action_id="tab_security",
        mode="orchestrate",
        intent_type="system_query",
        query_template="切换到安全设置 Tab",
        description="系统设置：安全设置",
    ),
    # Lab
    "open_viral_analyzer": CopilotCapability(
        action_id="open_viral_analyzer",
        mode="orchestrate",
        intent_type="content_creation",
        query_template="打开爆款笔记分析工具",
        description="实验室：爆款笔记分析",
    ),
    "open_title_optimizer": CopilotCapability(
        action_id="open_title_optimizer",
        mode="orchestrate",
        intent_type="content_creation",
        query_template="打开标题优化器",
        description="实验室：标题优化器",
    ),
    "open_cover_generator": CopilotCapability(
        action_id="open_cover_generator",
        mode="orchestrate",
        intent_type="content_creation",
        query_template="打开封面生成器",
        description="实验室：封面生成器",
    ),
    "open_ab_test": CopilotCapability(
        action_id="open_ab_test",
        mode="orchestrate",
        intent_type="content_creation",
        query_template="打开 A/B 测试工具",
        description="实验室：A/B 测试",
    ),
}


def _extract_task_id(card_id: str) -> Optional[str]:
    for prefix in ("review-decision-", "cover-gen-", "publish-confirm-"):
        if card_id.startswith(prefix):
            return card_id[len(prefix):]
    return None


# ═══════════════════════════════════════════════════════
# Copilot Action Router
# ═══════════════════════════════════════════════════════

class CopilotActionRouter:
    """Routes Copilot actions to the appropriate execution layer."""

    def __init__(self):
        self._orchestrator = MetaOrchestrator()
        self._handlers: Dict[str, Any] = {
            "_handle_approve": self._handle_approve,
            "_handle_reject": self._handle_reject,
            "_handle_revise": self._handle_revise,
            "_handle_batch_approve": self._handle_batch_approve,
            "_handle_batch_revise": self._handle_batch_revise,
            "_handle_generate_cover": self._handle_generate_cover,
            "_handle_publish": self._handle_publish,
        }

    # ─── Public API ───

    async def route(
        self,
        card_id: str,
        action_id: str,
        inputs: Dict[str, Any],
        payload: Dict[str, Any],
        context: Dict[str, Any],
        db: Any,
        user: Any,
    ) -> Dict[str, Any]:
        """Route a Copilot action to the correct execution path."""

        # 1. Known capability → fast path
        cap = CAPABILITY_REGISTRY.get(action_id)
        if cap:
            return await self._execute_capability(
                cap, card_id, action_id, inputs, payload, context, db, user
            )

        # 2. Unknown action → orchestrate with natural language
        query = f"{card_id}:{action_id}"
        return await self._orchestrate_and_execute(query, context, db, user)

    def list_capabilities(self) -> List[Dict[str, Any]]:
        """Return all registered capabilities (for discovery)."""
        return [
            {
                "action_id": c.action_id,
                "mode": c.mode,
                "description": c.description,
            }
            for c in CAPABILITY_REGISTRY.values()
        ]

    # ─── Execution dispatch ───

    async def _execute_capability(
        self,
        cap: CopilotCapability,
        card_id: str,
        action_id: str,
        inputs: Dict[str, Any],
        payload: Dict[str, Any],
        context: Dict[str, Any],
        db: Any,
        user: Any,
    ) -> Dict[str, Any]:
        if cap.mode == "service":
            handler = self._handlers.get(cap.service_handler)
            if not handler:
                raise HTTPException(
                    status_code=500,
                    detail=f"Service handler '{cap.service_handler}' not found",
                )
            return await handler(card_id, action_id, inputs, payload, context, db, user)

        if cap.mode == "orchestrate":
            query = cap.query_template or f"{card_id}:{action_id}"
            ctx = {**context}
            if cap.intent_type:
                ctx["intent_type"] = cap.intent_type
            return await self._orchestrate_and_execute(query, ctx, db, user)

        if cap.mode == "direct_skill":
            if not cap.skill_id:
                raise HTTPException(status_code=500, detail="Capability missing skill_id")
            result = skill_hub.execute_skill(cap.skill_id, context)
            return {
                "executed": True,
                "mode": "direct_skill",
                "skill_id": cap.skill_id,
                "result": result,
            }

        if cap.mode == "fallback_api":
            raise HTTPException(
                status_code=501, detail="fallback_api mode not yet implemented in Phase 2"
            )

        raise HTTPException(status_code=400, detail=f"Unknown capability mode: {cap.mode}")

    # ─── MetaOrchestrator integration ───

    async def _orchestrate_and_execute(
        self,
        query: str,
        context: Dict[str, Any],
        db: Any,
        user: Any,
    ) -> Dict[str, Any]:
        """Run full orchestration pipeline and execute the resulting plan."""

        # 1. Plan
        plan = self._orchestrator.orchestrate(query=query, context=context)

        # 2. Execute based on routing mode
        mode = plan.route.mode

        if mode.value == "DIRECT" and plan.decomposition.todos:
            todo = plan.decomposition.todos[0]
            skill = skill_hub.get_skill(todo.skill_id)
            if skill is None:
                return {
                    "executed": False,
                    "mode": "DIRECT",
                    "session_id": plan.session_id,
                    "intent": plan.intent.intent.value,
                    "message": f"Skill '{todo.skill_id}' is not yet available. Plan created but not executed.",
                    "todo": {
                        "id": todo.id,
                        "description": todo.description,
                        "skill_id": todo.skill_id,
                    },
                }
            result = skill_hub.execute_skill(
                todo.skill_id,
                {
                    "query": query,
                    "user_id": str(user.id) if user else None,
                    **context,
                },
            )
            return {
                "executed": result.get("success", False),
                "mode": "DIRECT",
                "session_id": plan.session_id,
                "intent": plan.intent.intent.value,
                "result": result,
            }

        if mode.value == "PIPELINE":
            steps = []
            for i, todo in enumerate(plan.decomposition.todos):
                agent_id = self._ensure_agent_for_skill(todo.skill_id)
                steps.append(
                    {
                        "agent_id": agent_id,
                        "name": todo.description,
                        "input_from": "trigger" if i == 0 else f"step_{i - 1}",
                        "output_to": f"step_{i}",
                    }
                )
            workflow = agent_orchestra.create_workflow(
                name=f"copilot-{plan.intent.intent.value}",
                description=query,
                steps=steps,
            )
            pipeline = agent_orchestra.create_pipeline(
                workflow_id=workflow.id,
                context={
                    "query": query,
                    "user_id": str(user.id) if user else None,
                    **context,
                },
            )
            executed = agent_orchestra.execute_pipeline(pipeline.id)
            return {
                "executed": executed.status == "completed",
                "mode": "PIPELINE",
                "session_id": plan.session_id,
                "intent": plan.intent.intent.value,
                "pipeline_id": pipeline.id,
                "workflow_id": workflow.id,
                "pipeline_status": executed.status,
                "results": executed.results,
            }

        # SWARM / DYNAMIC → fallback to plan-only for MVP
        return {
            "executed": False,
            "mode": mode.value,
            "session_id": plan.session_id,
            "intent": plan.intent.intent.value,
            "message": f"Mode {mode.value} is not yet fully implemented. Plan created but not executed.",
            "todos": [
                {"id": t.id, "description": t.description, "skill_id": t.skill_id}
                for t in plan.decomposition.todos
            ],
        }

    def _ensure_agent_for_skill(self, skill_id: str) -> str:
        """Ensure an agent exists that can execute the given skill."""
        for agent in agent_orchestra.list_agents():
            if skill_id in agent.skills:
                return agent.id
        agent = agent_orchestra.create_agent(
            name=f"agent-{skill_id}",
            role="executor",
            description=f"Auto-created agent for skill {skill_id}",
            skills=[skill_id],
        )
        return agent.id

    # ─── Service handlers (extracted from copilot.py) ───

    async def _handle_approve(
        self,
        card_id: str,
        action_id: str,
        inputs: Dict[str, Any],
        payload: Dict[str, Any],
        context: Dict[str, Any],
        db: Any,
        user: Any,
    ) -> Dict[str, Any]:
        task_id = _extract_task_id(card_id)
        if not task_id:
            raise HTTPException(status_code=400, detail="Task ID not found in card_id")

        task = await th_service.get_task(db, task_id)
        if not task or not can_review_task(user, task):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        res = await hil_service.approve_task(
            db,
            task_id,
            user.id,
            publish_mode=payload.get("publish_mode"),
            scheduled_at=payload.get("scheduled_at"),
        )
        result = {
            "executed": True,
            "task_id": task_id,
            "status": res.get("status") if res else None,
        }

        if result.get("status") == "approved_waiting_publish":
            result["copilot_followup"] = {
                "message": "审核已通过！要现在发布还是定时发布？",
                "suggested_cards": [
                    {
                        "type": "decision",
                        "title": "发布确认",
                        "actions": [
                            {
                                "id": "publish_now",
                                "label": "立即发布",
                                "variant": "primary",
                            },
                            {
                                "id": "schedule",
                                "label": "定时发布",
                                "variant": "secondary",
                            },
                        ],
                    }
                ],
            }
        return result

    async def _handle_reject(
        self,
        card_id: str,
        action_id: str,
        inputs: Dict[str, Any],
        payload: Dict[str, Any],
        context: Dict[str, Any],
        db: Any,
        user: Any,
    ) -> Dict[str, Any]:
        task_id = _extract_task_id(card_id)
        if not task_id:
            raise HTTPException(status_code=400, detail="Task ID not found in card_id")

        task = await th_service.get_task(db, task_id)
        if not task or not can_review_task(user, task):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        res = await hil_service.reject_task(db, task_id, user.id, inputs.get("reason", ""))
        return {
            "executed": True,
            "task_id": task_id,
            "status": res.get("status") if res else None,
        }

    async def _handle_revise(
        self,
        card_id: str,
        action_id: str,
        inputs: Dict[str, Any],
        payload: Dict[str, Any],
        context: Dict[str, Any],
        db: Any,
        user: Any,
    ) -> Dict[str, Any]:
        task_id = _extract_task_id(card_id)
        if not task_id:
            raise HTTPException(status_code=400, detail="Task ID not found in card_id")

        task = await th_service.get_task(db, task_id)
        if not task or not can_review_task(user, task):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        res = await hil_service.revise_task(
            db,
            task_id,
            user.id,
            payload.get("target_node_index", 3),
            payload.get("revised_variables", {}),
            inputs.get("reason", ""),
        )
        return {
            "executed": True,
            "task_id": task_id,
            "status": res.get("status") if res else None,
        }

    async def _handle_batch_approve(
        self,
        card_id: str,
        action_id: str,
        inputs: Dict[str, Any],
        payload: Dict[str, Any],
        context: Dict[str, Any],
        db: Any,
        user: Any,
    ) -> Dict[str, Any]:
        task_ids = payload.get("task_ids", [])
        owned_ids = []
        for tid in task_ids:
            t = await th_service.get_task(db, tid)
            if t and can_review_task(user, t):
                owned_ids.append(tid)
        res = await hil_service.batch_approve(db, owned_ids, user.id)
        return {"executed": True, **res}

    async def _handle_batch_revise(
        self,
        card_id: str,
        action_id: str,
        inputs: Dict[str, Any],
        payload: Dict[str, Any],
        context: Dict[str, Any],
        db: Any,
        user: Any,
    ) -> Dict[str, Any]:
        raise HTTPException(status_code=501, detail="Batch revise not yet implemented")

    async def _handle_generate_cover(
        self,
        card_id: str,
        action_id: str,
        inputs: Dict[str, Any],
        payload: Dict[str, Any],
        context: Dict[str, Any],
        db: Any,
        user: Any,
    ) -> Dict[str, Any]:
        task_id = _extract_task_id(card_id)
        if not task_id:
            raise HTTPException(status_code=400, detail="Task ID not found in card_id")

        task = await th_service.get_task(db, task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        # created_by may be username (str) or user_id (UUID)
        if not is_admin(user) and task.created_by not in (str(user.id), user.username):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: not the task owner"
            )

        now = datetime.now(timezone.utc)

        # Rate limit checks
        from sqlalchemy import select, func
        from src.models.copilot_orm import AICoverGenerationJobORM

        user_recent_stmt = (
            select(func.count(AICoverGenerationJobORM.id))
            .where(
                AICoverGenerationJobORM.user_id == user.id,
                AICoverGenerationJobORM.created_at >= now - timedelta(minutes=1),
            )
        )
        user_count = (await db.execute(user_recent_stmt)).scalar_one()
        if user_count >= 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: 3 cover generations per minute",
            )

        task_recent_stmt = (
            select(func.count(AICoverGenerationJobORM.id))
            .where(
                AICoverGenerationJobORM.task_id == task_id,
                AICoverGenerationJobORM.created_at >= now - timedelta(hours=1),
            )
        )
        task_count = (await db.execute(task_recent_stmt)).scalar_one()
        if task_count >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: 5 cover generations per hour for this task",
            )

        job_id = f"cover_gen_{uuid.uuid4().hex[:8]}"

        job = AICoverGenerationJobORM(
            id=job_id,
            task_id=task_id,
            user_id=user.id,
            prompt=inputs.get("prompt"),
            auto_prompt=payload.get("auto_prompt", False),
            style_preset=payload.get("style_preset"),
            count=payload.get("count", 2),
            ratio=payload.get("ratio", "3:4"),
            status="queued",
        )
        db.add(job)
        await db.commit()

        try:
            from src.celery_app import celery_app

            celery_app.send_task(
                "src.services.celery_tasks.generate_cover",
                kwargs={
                    "job_id": job_id,
                    "task_id": task_id,
                    "prompt": inputs.get("prompt"),
                    "auto_prompt": payload.get("auto_prompt", False),
                    "style_preset": payload.get("style_preset"),
                    "count": payload.get("count", 2),
                    "ratio": payload.get("ratio", "3:4"),
                },
            )
        except Exception as exc:
            logger.warning("Failed to enqueue cover generation Celery task: %s", exc)

        return {
            "executed": True,
            "job_id": job_id,
            "status": "queued",
            "estimated_seconds": 8,
        }

    async def _handle_publish(
        self,
        card_id: str,
        action_id: str,
        inputs: Dict[str, Any],
        payload: Dict[str, Any],
        context: Dict[str, Any],
        db: Any,
        user: Any,
    ) -> Dict[str, Any]:
        task_id = _extract_task_id(card_id)
        if not task_id:
            raise HTTPException(status_code=400, detail="Task ID not found in card_id")

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
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Task has no associated draft_id",
            )

        publish_mode = payload.get("publish_mode", "immediate")
        scheduled_at = inputs.get("scheduled_at") if publish_mode == "scheduled" else None

        publish_task_result = await create_publish_task(
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
            "executed": True,
            "task_id": task_id,
            "status": "running",
            "publish_mode": publish_mode,
            "scheduled_at": scheduled_at,
            "publish_task_id": publish_task_result.id,
        }
