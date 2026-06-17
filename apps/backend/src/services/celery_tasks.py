"""Celery tasks — Production async execution layer.

Tasks:
  - run_pipeline_task: Execute pipeline tasks (publish, data_analysis, etc.)
  - execute_workflow: Drive workflow execution for a TaskHub task
  - scheduled_publish: Execute a publish task at scheduled time
  - heartbeat: Health check / keepalive
  - fetch_note_engagement: 24h post-publish XHS data recovery
  - generate_cover: AI cover image generation (v4.0 Copilot-Driven)
"""

import asyncio
import logging
import random
import secrets
from datetime import datetime, timezone

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_pipeline_task(self, task_id: str):
    """Execute a pipeline task synchronously (called from Celery worker)."""
    from src.services import pipeline_service

    try:
        pipeline_service._run_task_sync(task_id)
    except SoftTimeLimitExceeded:
        pipeline_task = pipeline_service.get_task(task_id)
        if pipeline_task:
            pipeline_task.status = "failed"
            pipeline_task.error_message = "Task timed out (soft limit)"
        raise self.retry(exc=Exception("Soft time limit exceeded"), countdown=60)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def execute_workflow(self, task_hub_task_id: str):
    """Drive a TaskHub workflow execution to completion or next human gate.

    This task is called when a workflow needs to be driven asynchronously,
    e.g. after human approval resumes execution.
    """
    import asyncio
    from src.services.celery_tasks_function import drive_workflow

    return asyncio.run(drive_workflow(task_hub_task_id))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scheduled_publish(self, publish_task_id: str):
    """Execute a scheduled publish task."""
    from src.services.publisher_service import execute_publish
    from src.services.publish_task import get_task as get_publish_task

    task = get_publish_task(publish_task_id)
    if not task:
        raise ValueError(f"Publish task not found: {publish_task_id}")

    try:
        result = execute_publish(publish_task_id, {})
        return {
            "publish_task_id": publish_task_id,
            "status": result.status,
            "published_url": result.published_url,
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task
def heartbeat():
    """Celery worker heartbeat — ensures worker is alive."""
    return {"status": "ok", "time": __import__("datetime").datetime.utcnow().isoformat()}


@shared_task
def check_and_execute_cron_jobs():
    """Check all active cron jobs and execute those whose schedule matches current time."""
    from src.services import cron_hub
    from datetime import datetime, timezone, timedelta

    logger = logging.getLogger(__name__)
    now = datetime.now(timezone.utc)
    triggered = 0

    for job in cron_hub.list_jobs(status="ACTIVE"):
        try:
            if cron_hub.croniter is None:
                logger.warning("croniter not available, skipping cron job check")
                break
            # Check if this job should run at the current minute
            base = now.replace(second=0, microsecond=0)
            itr = cron_hub.croniter(job.schedule, base - timedelta(minutes=1))
            nxt = itr.get_next(datetime)
            if base <= nxt <= base + timedelta(minutes=1):
                cron_hub.execute_job(job.id, "SCHEDULED")
                triggered += 1
                logger.info("Triggered cron job %s (%s) at %s", job.id, job.name, now.isoformat())
        except Exception:
            logger.exception("Failed to check job %s", job.id)

    return {"checked_at": now.isoformat(), "triggered": triggered}


# ─── Note Engagement Data Recovery ───

async def _save_engagement_record(
    publish_task_id: str,
    account_id: str,
    platform_post_id: str,
    metrics: dict,
    fetch_status: str,
    fetch_error: str = "",
):
    """Async helper to write NoteEngagementORM."""
    from src.core.database import AsyncSessionLocal
    from src.models.note_engagement_orm import NoteEngagementORM

    async with AsyncSessionLocal() as session:
        record = NoteEngagementORM(
            id=secrets.token_urlsafe(16),
            publish_task_id=publish_task_id,
            account_id=account_id,
            platform_post_id=platform_post_id,
            likes=metrics.get("likes"),
            comments=metrics.get("comments"),
            saves=metrics.get("saves"),
            shares=metrics.get("shares"),
            views=metrics.get("views"),
            fetch_status=fetch_status,
            fetch_error=fetch_error or None,
            fetched_at=datetime.now(timezone.utc) if fetch_status == "success" else None,
            raw_response={"metrics": metrics, "error": fetch_error} if metrics else None,
        )
        session.add(record)
        await session.commit()
        return record.id


@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def fetch_note_engagement(self, publish_task_id: str, account_id: str, platform_post_id: str):
    """Fetch XHS note engagement data ~24h after publish.

    Workflow:
      1. Check account auto_engagement_fetch toggle (default off).
      2. Execute L1 xhs_note_data_extraction Skill.
      3. On success: write NoteEngagementORM (status=success).
      4. On failure: retry up to 3 times, then write NoteEngagementORM (status=failed)
         and leave manual import as fallback.
    """
    from src.models.account_pool import get_pool_entry
    from src.services.skill_hub import execute_skill

    account = get_pool_entry(account_id)
    if not account:
        logger.error("Account %s not found for engagement fetch", account_id)
        asyncio.run(
            _save_engagement_record(
                publish_task_id, account_id, platform_post_id,
                {}, "failed", "Account not found",
            )
        )
        return {"success": False, "error": "Account not found"}

    # PRD: default off; skip silently if disabled
    if not getattr(account, "auto_engagement_fetch", False):
        logger.info("Auto engagement fetch disabled for account %s; skipping", account_id)
        asyncio.run(
            _save_engagement_record(
                publish_task_id, account_id, platform_post_id,
                {}, "manual", "Auto fetch disabled",
            )
        )
        return {"success": False, "error": "Auto engagement fetch disabled"}

    # Frequency limit: max 3 fetches per account per day
    from src.models.account_pool import _today_iso

    today = _today_iso()
    if getattr(account, "last_engagement_fetch_reset", "") != today:
        account.engagement_fetches_today = 0
        account.last_engagement_fetch_reset = today

    if account.engagement_fetches_today >= 3:
        logger.warning("Account %s daily engagement fetch limit reached (3)", account_id)
        asyncio.run(
            _save_engagement_record(
                publish_task_id, account_id, platform_post_id,
                {}, "failed", "Daily fetch limit exceeded (max 3/day)",
            )
        )
        return {"success": False, "error": "Daily fetch limit exceeded"}

    # Execute Skill
    # Increment daily counter before attempting fetch
    account.engagement_fetches_today += 1

    skill_result = execute_skill("L1-xhs-note-data-extraction", {
        "account_id": account_id,
        "platform_post_id": platform_post_id,
    })

    if not skill_result.get("success"):
        err = f"Skill execution failed: {skill_result.get('error')}"
        logger.error(err)
        raise self.retry(exc=Exception(err), countdown=600)

    result = skill_result.get("result", {})
    if result.get("success"):
        metrics = result.get("metrics", {})
        record_id = asyncio.run(
            _save_engagement_record(
                publish_task_id, account_id, platform_post_id,
                metrics, "success",
            )
        )
        logger.info(
            "Engagement saved for note %s: likes=%s comments=%s saves=%s record=%s",
            platform_post_id,
            metrics.get("likes"),
            metrics.get("comments"),
            metrics.get("saves"),
            record_id,
        )
        return {"success": True, "record_id": record_id, "metrics": metrics}

    # Skill returned structured failure → retry
    error_msg = result.get("error", "Unknown skill error")
    logger.warning("Engagement fetch failed (attempt %s): %s", self.request.retries, error_msg)

    if self.request.retries < 3:
        raise self.retry(exc=Exception(error_msg), countdown=600)

    # Max retries exhausted → mark as failed, prompt manual import
    record_id = asyncio.run(
        _save_engagement_record(
            publish_task_id, account_id, platform_post_id,
            {}, "failed", error_msg,
        )
    )
    logger.error("Max retries exhausted for note %s; marked as failed", platform_post_id)
    return {"success": False, "record_id": record_id, "error": error_msg}


# ───────────────────────────────────────────────
# AI Content Regeneration — v4.0 Copilot-Driven
# ───────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def regenerate_content(
    self,
    job_id: str,
    task_id: str,
    user_id: str,
    style_option: str = "casual",
    length_option: str = "medium",
    tone_option: str = "friendly",
    prompt_variables: dict | None = None,
):
    """Regenerate content asynchronously with progress WebSocket events.

    Steps:
      1. Push content.generation.started event
      2. Call LLM / ContentForge Agent (mock for dev)
      3. Push progress events at 30%, 60%, 90%
      4. Push content.generation.completed with generated content
    """
    import asyncio
    from src.api.copilot import push_copilot_event

    async def _run():
        pv = prompt_variables or {}
        topic = pv.get("title", "未命名主题")
        platform = pv.get("platform", "xhs")

        # Step 1: started
        await push_copilot_event(
            user_id,
            "content.generation.started",
            {
                "job_id": job_id,
                "task_id": task_id,
                "status": "generating",
                "progress": 0,
                "step": "analyzing_requirements",
                "meta": {"style": style_option, "length": length_option, "tone": tone_option},
            },
        )

        await asyncio.sleep(1)

        # Step 2: progress 30% — outline
        await push_copilot_event(
            user_id,
            "content.generation.progress",
            {
                "job_id": job_id,
                "task_id": task_id,
                "status": "generating",
                "progress": 30,
                "step": "generating_outline",
            },
        )

        await asyncio.sleep(2)

        # Step 3: progress 60% — drafting
        await push_copilot_event(
            user_id,
            "content.generation.progress",
            {
                "job_id": job_id,
                "task_id": task_id,
                "status": "generating",
                "progress": 60,
                "step": "drafting_content",
            },
        )

        await asyncio.sleep(2)

        # Step 4: progress 90% — polishing
        await push_copilot_event(
            user_id,
            "content.generation.progress",
            {
                "job_id": job_id,
                "task_id": task_id,
                "status": "generating",
                "progress": 90,
                "step": "polishing_and_compliance_check",
            },
        )

        await asyncio.sleep(1)

        # Step 5: generate mock content based on style/tone
        style_map = {
            "casual": "轻松随性",
            "professional": "专业严谨",
            "humorous": "幽默风趣",
        }
        tone_map = {
            "friendly": "亲切友好",
            "serious": "严肃认真",
            "playful": "活泼俏皮",
        }
        length_map = {
            "short": (80, 120),
            "medium": (150, 250),
            "long": (300, 500),
        }

        style_label = style_map.get(style_option, "轻松随性")
        tone_label = tone_map.get(tone_option, "亲切友好")
        min_len, max_len = length_map.get(length_option, (150, 250))

        generated_body = (
            f"✨ 这是一篇{style_label}、{tone_label}的{platform}内容。\n\n"
            f"主题：{topic}\n\n"
            f"【正文】\n"
            f"在这里，我们用最真诚的态度分享每一个瞬间。"
            f"{' '.join(['生活不止眼前的苟且，还有诗和远方。'] * ((min_len // 20) + 1))}\n\n"
            f"#{' #'.join(pv.get('hashtags', ['生活方式', '分享']))}\n\n"
            f"—— 由 ContentForge Agent 生成 ({style_option}/{tone_option}/{length_option})"
        )[:max_len]

        generated_title = f"【{style_label}】{topic}"[:60]

        # Step 6: completed
        await push_copilot_event(
            user_id,
            "content.generation.completed",
            {
                "job_id": job_id,
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "generated_content": {
                    "title": generated_title,
                    "body": generated_body,
                    "hashtags": pv.get("hashtags", ["生活方式", "分享"]),
                },
                "compliance_score": random.randint(85, 98),
            },
        )

        logger.info("Content regeneration completed for job %s, task %s", job_id, task_id)
        return {
            "success": True,
            "job_id": job_id,
            "task_id": task_id,
            "title": generated_title,
            "body_preview": generated_body[:100],
        }

    async def _on_error(exc):
        await push_copilot_event(
            user_id,
            "content.generation.failed",
            {
                "job_id": job_id,
                "task_id": task_id,
                "status": "failed",
                "error": str(exc),
            },
        )

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("Content regeneration failed for job %s", job_id)
        asyncio.run(_on_error(exc))
        raise self.retry(exc=exc, countdown=30)


# ───────────────────────────────────────────────
# AI Cover Generation — v4.0 Copilot-Driven
# ───────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_cover(self, job_id: str, task_id: str, prompt: str, style_preset: str | None, ratio: str, count: int, auto_prompt: bool = False):
    """Generate AI cover images asynchronously.

    Steps:
      1. Update job status to 'generating'
      2. Call external image generation service (or mock for dev)
      3. Update job status to 'completed' with results
      4. Push WebSocket event to client
    """
    import asyncio
    from datetime import datetime, timezone
    from src.core.database import AsyncSessionLocal
    from src.models.copilot_orm import AICoverGenerationJobORM
    from src.api.copilot import push_copilot_event

    async def _run():
        async with AsyncSessionLocal() as db:
            # Fetch job
            from sqlalchemy import select
            result = await db.execute(select(AICoverGenerationJobORM).where(AICoverGenerationJobORM.id == job_id))
            job = result.scalar_one_or_none()
            if not job:
                logger.error("Cover generation job %s not found", job_id)
                return {"success": False, "error": "Job not found"}

            # Update status to generating
            job.status = "generating"
            await db.commit()

            # Push progress event
            await push_copilot_event(
                job.user_id,
                "cover.generation.progress",
                {"job_id": job_id, "task_id": task_id, "status": "generating", "progress": 10, "step": "prompt_encoding"},
            )

            # TODO Sprint 2: replace with real image generation service
            # Mock generation delay
            await asyncio.sleep(2)

            # Generate mock results
            import uuid as uuid_module
            mock_urls = [
                f"https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&r={uuid_module.uuid4().hex[:6]}",
                f"https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=600&r={uuid_module.uuid4().hex[:6]}",
            ]
            results = []
            for i, url in enumerate(mock_urls[:count]):
                results.append({
                    "url": url,
                    "thumbnail_url": url.replace("w=600", "w=200"),
                    "ratio": ratio,
                    "prompt_used": prompt or f"AI generated cover for {task_id}",
                    "seed": 42 + i,
                })

            # Update job to completed
            job.status = "completed"
            job.results = results
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

            # Push completed event
            await push_copilot_event(
                job.user_id,
                "cover.generation.completed",
                {
                    "job_id": job_id,
                    "task_id": task_id,
                    "results": results,
                },
            )

            logger.info("Cover generation completed for job %s: %s images", job_id, len(results))
            return {"success": True, "job_id": job_id, "results_count": len(results)}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("Cover generation failed for job %s", job_id)
        # Update job to failed
        _exc = exc
        async def _mark_failed():
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                result = await db.execute(select(AICoverGenerationJobORM).where(AICoverGenerationJobORM.id == job_id))
                job = result.scalar_one_or_none()
                if job:
                    job.status = "failed"
                    job.error_message = str(_exc)
                    await db.commit()
        asyncio.run(_mark_failed())
        raise self.retry(exc=exc, countdown=30)
