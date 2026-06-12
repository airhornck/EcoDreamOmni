"""Publisher service: task CRUD + scheduling + execution orchestration.

Aligned with detailed design §5.7 — L3 evaluation before scheduling.
"""

import logging
from typing import Dict, List, Optional

from asgiref.sync import async_to_sync

from src.core.database import AsyncSessionLocal
from src.models.publish_task import (
    PublishTask,
    clear_tasks,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)
from src.services import platform_rule_service
from src.services import platform_schema_service as pss
from src.services.playwright_publisher import publish_content
from src.services.publish_scheduler import schedule_publish

logger = logging.getLogger(__name__)


async def create_publish_task(
    draft_id: str,
    account_id: str,
    platform: str,
    scheduled_at: Optional[str] = None,
    task_hub_task_id: Optional[str] = None,
    created_by: Optional[str] = None,
) -> PublishTask:
    """Create a publish task with L3 evaluation + scheduler integration."""
    # Evaluate L3 before scheduling
    l3_result = await platform_rule_service.evaluate_l3(account_id, scheduled_at)
    if not l3_result["allowed"]:
        task = create_task(
            draft_id=draft_id,
            account_id=account_id,
            platform=platform,
            scheduled_at=scheduled_at,
            task_hub_task_id=task_hub_task_id,
            created_by=created_by,
        )
        update_task(
            task.id,
            status="skipped",
            publish_skipped_reason=l3_result["reason"],
        )
        return get_task(task.id)

    schedule_result = schedule_publish(
        draft_id=draft_id,
        account_id=account_id,
        platform=platform,
        preferred_time=scheduled_at,
    )

    if not schedule_result["success"]:
        # Create task but mark as failed due to scheduling conflict
        task = create_task(
            draft_id=draft_id,
            account_id=account_id,
            platform=platform,
            scheduled_at=scheduled_at,
            task_hub_task_id=task_hub_task_id,
            created_by=created_by,
        )
        update_task(task.id, status="failed", error_reason=schedule_result["reason"])
        return get_task(task.id)

    task = create_task(
        draft_id=draft_id,
        account_id=account_id,
        platform=platform,
        scheduled_at=schedule_result["scheduled_at"],
        task_hub_task_id=task_hub_task_id,
        created_by=created_by,
    )
    update_task(task.id, status="scheduled")
    return get_task(task.id)


def list_publish_tasks(created_by: Optional[str] = None) -> List[PublishTask]:
    return list_tasks(created_by=created_by)


def get_publish_task(task_id: str) -> Optional[PublishTask]:
    return get_task(task_id)


def update_publish_task(task_id: str, **kwargs) -> Optional[PublishTask]:
    return update_task(task_id, **kwargs)


def remove_publish_task(task_id: str) -> bool:
    return delete_task(task_id)


def _infer_format_name(content: dict, platform: str) -> Optional[str]:
    """根据内容推断平台格式名称."""
    if content.get("video") or content.get("videos"):
        return "视频"
    if content.get("images") or content.get("pics"):
        return "图文"
    # 小红书默认图文；微信公众号默认文章
    if platform in ("xhs", "xiaohongshu"):
        return "图文"
    if platform == "wechat_official":
        return "文章"
    return None


def _validate_content_schema(
    platform: str, format_name: Optional[str], content: dict, strict: bool = True
) -> tuple[bool, list]:
    """同步包装：查询 PlatformSchema 并验证内容格式.

    Returns:
        (passed, errors)
    """

    async def _do_validate():
        async with AsyncSessionLocal() as db:
            fmt = await pss.get_content_format(db, platform, format_name or "")
            if fmt is None:
                # 尝试推断格式
                inferred = _infer_format_name(content, platform)
                if inferred:
                    fmt = await pss.get_content_format(db, platform, inferred)
                if fmt is None:
                    logger.warning(
                        "PlatformSchema not found for %s/%s, skipping validation",
                        platform,
                        format_name or inferred,
                    )
                    return True, []
            passed, errors = pss.validate_content_against_schema(
                content, fmt.fields or [], strict=strict
            )
            return passed, errors

    return async_to_sync(_do_validate)()


def execute_publish(
    task_id: str, content: dict, format_name: Optional[str] = None
) -> PublishTask:
    """Execute a publish task using Playwright (MVP: mock).

    在调用真实发布前，先通过 PlatformSchema 验证内容格式。
    """
    task = get_task(task_id)
    if task is None:
        raise ValueError(f"Task {task_id} not found")

    update_task(task_id, status="publishing")

    # ── PlatformSchema 格式校验 ──
    schema_passed, schema_errors = _validate_content_schema(
        platform=task.platform,
        format_name=format_name,
        content=content,
        strict=True,
    )
    if not schema_passed:
        error_msg = "; ".join(f"{e.field}: {e.message}" for e in schema_errors)
        logger.error("PlatformSchema validation failed for task %s: %s", task_id, error_msg)
        update_task(
            task_id,
            status="failed",
            error_reason=f"格式校验失败: {error_msg}",
            retry_count=task.retry_count + 1,
        )
        return get_task(task_id)

    result = publish_content(
        draft_id=task.draft_id,
        account_id=task.account_id,
        platform=task.platform,
        content=content,
    )

    if result["success"]:
        from datetime import datetime, timezone

        update_task(
            task_id,
            status="published",
            published_url=result.get("published_url"),
            platform_post_id=result.get("platform_post_id"),
            published_at=datetime.now(timezone.utc).isoformat(),
        )
        # Consume account daily quota
        from src.models.account_pool import _ensure_daily_reset, get_pool_entry

        account = get_pool_entry(task.account_id)
        if account:
            _ensure_daily_reset(account)
            account.posts_today += 1
            account.updated_at = datetime.now(timezone.utc).isoformat()

        # ── 24h engagement data recovery (Celery delayed task) ──
        # Only for XHS platform and when platform_post_id is available
        platform_post_id = result.get("platform_post_id")
        if task.platform == "xhs" and platform_post_id:
            import random
            from src.celery_app import celery_app

            jitter = random.randint(0, 300)  # 0-5 min jitter to avoid burst
            celery_app.send_task(
                "src.services.celery_tasks.fetch_note_engagement",
                kwargs={
                    "publish_task_id": task_id,
                    "account_id": task.account_id,
                    "platform_post_id": platform_post_id,
                },
                countdown=86400 + jitter,  # 24h + jitter
            )
    else:
        update_task(
            task_id,
            status="failed",
            error_reason=result.get("error", "Unknown error"),
            retry_count=task.retry_count + 1,
        )

    return get_task(task_id)
