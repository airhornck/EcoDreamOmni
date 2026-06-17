"""
审核发布中心 API 测试。

Red-Green TDD for:
  - GET /review-publish-center/conclusions 审核结论列表聚合
  - GET /review-publish-center/conclusions/{task_id} 详情查询
  - POST /review-publish-center/conclusions/{task_id}/confirm-publish 确认发布（立即/定时/Cron）
  - 状态校验与错误处理
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.task_orm import TaskORM
from src.services import task_hub as th
from src.services import human_in_loop as hil
from src.api.review_publish import _get_draft_id

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest.fixture(autouse=True)
async def clear_db(db: AsyncSession):
    await db.execute(delete(TaskORM))
    await db.commit()
    hil._review_db.clear()
    hil._task_risk_db.clear()
    th._clear_stores()
    yield


def get_auth_token(client):
    import uuid
    from src.models.user import clear_users
    clear_users()
    email = f"rpc_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"rpcuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]


async def _create_approved_task(db: AsyncSession, workflow_template_id: str = "content_creation_standard", **variables):
    """Helper: 创建并推进到 APPROVED_WAITING_PUBLISH 状态的任务。"""
    t = await th.create_task(db, "Review Publish Task", workflow_template_id, 1, "acc_1", "pers_1", created_by="alice")
    if variables:
        await th.update_task(db, t.id, prompt_variables=variables)
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    # 处理双人复核：wf_publish 需要两次 approve
    r1 = await hil.approve_task(db, t.id, "reviewer_1")
    if r1["status"] == "human_wait":
        await hil.approve_task(db, t.id, "reviewer_2")
    return await th.get_task(db, t.id)


# ─── 1. 审核结论列表聚合 ───


async def test_get_review_conclusions_empty(client, db: AsyncSession):
    """🔴 无审核记录时返回空列表。"""
    token = get_auth_token(client)
    response = client.get(
        "/review-publish-center/conclusions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_get_review_conclusions_approved_waiting_publish(client, db: AsyncSession):
    """🔴 APPROVED_WAITING_PUBLISH 任务出现在已通过列表中。"""
    token = get_auth_token(client)
    t = await _create_approved_task(db, content_preview="测试内容预览", draft_id="draft_001")

    response = client.get(
        "/review-publish-center/conclusions?status_filter=approved",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["task_id"] == t.id
    assert item["task_name"] == "Review Publish Task"
    assert item["status"] == "approved_waiting_publish"
    assert item["review_decision"] == "APPROVE"
    assert item["can_publish_now"] is True
    assert item["has_cron_job"] is False
    assert item["content_preview"].startswith("测试内容")


async def test_get_review_conclusions_filter_by_status(client, db: AsyncSession):
    """🔴 按状态过滤结论列表。"""
    token = get_auth_token(client)
    # 创建已通过任务
    t1 = await _create_approved_task(db, content_preview="已通过内容")
    # 创建已驳回任务
    t2 = await th.create_task(db, "Rejected Task", "wf_publish", 1, "acc_1", "pers_1", created_by="alice")
    await th.configure(db, t2.id)
    await th.queue(db, t2.id)
    await th.start(db, t2.id)
    await th.wait_human(db, t2.id)
    await hil.reject_task(db, t2.id, "reviewer_1", "违规内容")

    # 过滤已通过
    resp_approved = client.get(
        "/review-publish-center/conclusions?status_filter=approved",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_approved.json()["total"] == 1
    assert resp_approved.json()["items"][0]["task_id"] == t1.id

    # 过滤已驳回
    resp_rejected = client.get(
        "/review-publish-center/conclusions?status_filter=rejected",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_rejected.json()["total"] == 1
    assert resp_rejected.json()["items"][0]["task_id"] == t2.id


# ─── 2. 审核结论详情 ───


async def test_get_review_conclusion_detail(client, db: AsyncSession):
    """🔴 详情接口返回完整审核信息。"""
    token = get_auth_token(client)
    t = await _create_approved_task(
        db,
        content_preview="正文内容",
        draft_id="draft_001",
        agent_summary="Agent 摘要",
        compliance_result={"l1": "pass"},
    )

    response = client.get(
        f"/review-publish-center/conclusions/{t.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == t.id
    assert data["status"] == "approved_waiting_publish"
    assert data["content_preview"] == "正文内容"
    assert data["agent_summary"] == "Agent 摘要"
    assert data["compliance_result"]["l1"] == "pass"
    assert data["can_publish"] is True
    assert data["draft_id"] == "draft_001"


async def test_get_review_conclusion_detail_structured_content(client, db: AsyncSession):
    """🔴 详情接口返回结构化内容、选题报告、互动预演等新字段。"""
    token = get_auth_token(client)
    t = await _create_approved_task(
        db,
        content_preview="正文内容",
        draft_id="draft_002",
        generated_content={
            "title": "🔥猫咪防暑攻略",
            "body": "喵~各位铲屎官们！今天必须跟你们唠唠猫咪防暑那些事儿！",
            "tags": ["猫咪防暑", "夏季养猫"],
            "platform": "xhs",
            "content_type": "note",
            "cover_image_url": "https://example.com/cover.jpg",
        },
        topic_report={
            "report_id": "report_001",
            "selected_topic": "猫咪防暑",
            "topics": [
                {"id": "topic-001", "title": "猫咪防暑", "source_report": "report-001", "estimated_engagement": 350, "tags": ["猫咪"], "status": "adopted"},
            ],
            "5a_stage": "AWARENESS",
            "audience_fit_score": 82,
        },
        prediction_result={
            "engagement_interval": {
                "likes": {"min": 25, "max": 60, "confidence": "medium"},
                "comments": {"min": 5, "max": 15, "confidence": "medium"},
                "collects": {"min": 8, "max": 20, "confidence": "medium"},
            },
            "viral_probability": 0.35,
            "best_publish_time": "09:00-11:00",
        },
        quality_score={"overall": 92, "title_attractiveness": 88, "body_completeness": 95},
        compliance_result={"level": "pass", "violations": [], "suggestions": []},
    )

    response = client.get(
        f"/review-publish-center/conclusions/{t.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    # Structured content
    assert data["generated_content"] is not None
    assert data["generated_content"]["title"] == "🔥猫咪防暑攻略"
    assert data["generated_content"]["body"].startswith("喵~")
    assert data["generated_content"]["tags"] == ["猫咪防暑", "夏季养猫"]
    assert data["generated_content"]["cover_image_url"] == "https://example.com/cover.jpg"

    # Topic report
    assert data["topic_report"] is not None
    assert data["topic_report"]["selected_topic"] == "猫咪防暑"
    assert data["topic_report"]["5a_stage"] == "AWARENESS"
    assert data["topic_report"]["audience_fit_score"] == 82
    assert len(data["topic_report"]["topics"]) == 1

    # Prediction result
    assert data["prediction_result"] is not None
    assert data["prediction_result"]["engagement_interval"]["likes"]["min"] == 25
    assert data["prediction_result"]["viral_probability"] == 0.35

    # Quality score
    assert data["quality_score"]["overall"] == 92

    # Compliance
    assert data["compliance_result"]["level"] == "pass"


async def test_get_review_conclusion_detail_not_found(client, db: AsyncSession):
    """🔴 不存在的任务返回 404。"""
    token = get_auth_token(client)
    response = client.get(
        "/review-publish-center/conclusions/non_existent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


# ─── 3. 确认发布 ───


async def test_confirm_publish_immediate(client, db: AsyncSession):
    """🔴 立即发布确认后任务进入 RUNNING。"""
    token = get_auth_token(client)
    t = await _create_approved_task(db, content_preview="立即发布", draft_id="draft_002")

    response = client.post(
        f"/review-publish-center/conclusions/{t.id}/confirm-publish",
        json={
            "operator": "operator_1",
            "publish_mode": "immediate",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["task_id"] == t.id
    assert data["status"] == "running"
    assert data["publish_mode"] == "immediate"
    assert data["publish_task_id"] is not None


async def test_confirm_publish_scheduled(client, db: AsyncSession):
    """🔴 定时发布确认包含 scheduled_at。"""
    token = get_auth_token(client)
    t = await _create_approved_task(db, content_preview="定时发布", draft_id="draft_003")

    response = client.post(
        f"/review-publish-center/conclusions/{t.id}/confirm-publish",
        json={
            "operator": "operator_1",
            "publish_mode": "scheduled",
            "scheduled_at": "2026-05-25T09:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["publish_mode"] == "scheduled"
    assert data["scheduled_at"] == "2026-05-25T09:00:00"


async def test_confirm_publish_with_cron(client, db: AsyncSession):
    """🔴 循环执行确认后创建 CronJob。"""
    token = get_auth_token(client)
    t = await _create_approved_task(db, content_preview="循环发布", draft_id="draft_004")

    response = client.post(
        f"/review-publish-center/conclusions/{t.id}/confirm-publish",
        json={
            "operator": "operator_1",
            "publish_mode": "immediate",
            "cron_schedule": "0 9 * * *",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["cron_job_id"] is not None


async def test_confirm_publish_not_in_approved_waiting_publish(client, db: AsyncSession):
    """🔴 非 APPROVED_WAITING_PUBLISH 状态的任务不能确认发布。"""
    token = get_auth_token(client)
    t = await th.create_task(db, "Not Ready", "wf_publish", 1, "acc_1", "pers_1", created_by="alice")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    # 任务在 RUNNING 状态，不是 APPROVED_WAITING_PUBLISH

    response = client.post(
        f"/review-publish-center/conclusions/{t.id}/confirm-publish",
        json={"operator": "operator_1", "publish_mode": "immediate"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


async def test_confirm_publish_no_draft_id(client, db: AsyncSession):
    """🔴 没有 draft_id 的任务不能确认发布。"""
    token = get_auth_token(client)
    t = await th.create_task(db, "No Draft", "wf_001", 1, "acc_1", "pers_1", created_by="alice")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    await hil.approve_task(db, t.id, "reviewer_1")

    response = client.post(
        f"/review-publish-center/conclusions/{t.id}/confirm-publish",
        json={"operator": "operator_1", "publish_mode": "immediate"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


# ─── 4. 内容更新 ───


async def test_update_content_title_body_tags_cover(client, db: AsyncSession):
    """🔴 更新标题、正文、标签、封面，并记录修改元数据。"""
    token = get_auth_token(client)
    t = await _create_approved_task(
        db,
        content_preview="旧正文",
        draft_id="draft_005",
        generated_content={
            "title": "旧标题",
            "body": "旧正文",
            "tags": ["旧标签"],
            "cover_image_url": "https://old.com/cover.jpg",
        },
    )

    response = client.put(
        f"/review-publish-center/conclusions/{t.id}/content",
        json={
            "title": "新标题",
            "body": "新正文内容",
            "tags": ["新标签A", "新标签B"],
            "cover_image_url": "https://new.com/cover.jpg",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert "updated_at" in data

    # Verify persisted changes
    t_refreshed = await th.get_task(db, t.id)
    generated = t_refreshed.prompt_variables["generated_content"]
    assert generated["title"] == "新标题"
    assert generated["body"] == "新正文内容"
    assert generated["tags"] == ["新标签A", "新标签B"]
    assert generated["cover_image_url"] == "https://new.com/cover.jpg"
    assert t_refreshed.prompt_variables["content_preview"] == "新正文内容"
    assert "content_modified_at" in t_refreshed.prompt_variables
    assert t_refreshed.prompt_variables["content_modified_by"] == "operator"
    # Compliance marked stale
    assert t_refreshed.prompt_variables["compliance_result"]["level"] == "stale"


async def test_update_content_partial(client, db: AsyncSession):
    """🔴 部分字段更新不影响其他字段。"""
    token = get_auth_token(client)
    t = await _create_approved_task(
        db,
        content_preview="正文",
        draft_id="draft_006",
        generated_content={"title": "原标题", "body": "正文", "tags": ["标签"]},
    )

    response = client.put(
        f"/review-publish-center/conclusions/{t.id}/content",
        json={"title": "仅改标题"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    t_refreshed = await th.get_task(db, t.id)
    generated = t_refreshed.prompt_variables["generated_content"]
    assert generated["title"] == "仅改标题"
    assert generated["body"] == "正文"  # unchanged
    assert generated["tags"] == ["标签"]  # unchanged


async def test_update_content_not_found(client, db: AsyncSession):
    """🔴 不存在的任务返回 404。"""
    token = get_auth_token(client)
    response = client.put(
        "/review-publish-center/conclusions/non_existent/content",
        json={"title": "x"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


# ─── 5. 内容重新生成 ───


async def test_regenerate_content(client, db: AsyncSession):
    """🔴 重新生成应重新执行完整工作流，驱动到 HUMAN_WAIT 并生成新内容+封面。"""
    token = get_auth_token(client)
    t = await _create_approved_task(
        db,
        content_preview="旧正文",
        draft_id="draft_007",
        generated_content={
            "title": "旧标题",
            "body": "旧正文",
            "tags": ["旧标签"],
            "platform": "xhs",
            "content_type": "note",
            "cover_image_url": "https://example.com/old.jpg",
        },
        topic_report={
            "report_id": "r1",
            "selected_topic": "猫咪防暑",
            "topics": [],
            "5a_stage": "AWARENESS",
            "audience_fit_score": 80,
        },
    )
    old_execution_id = t.execution_id

    response = client.post(
        f"/review-publish-center/conclusions/{t.id}/regenerate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "human_wait"
    assert "工作流已重新执行" in data["message"]

    t_refreshed = await th.get_task(db, t.id)
    assert t_refreshed.status.value == "human_wait"
    assert t_refreshed.execution_id is not None
    assert t_refreshed.execution_id != old_execution_id  # new execution
    assert t_refreshed.review_decision is None  # cleared for re-review
    assert "regenerate_requested_at" in t_refreshed.prompt_variables
    assert t_refreshed.prompt_variables["regenerate_requested_by"] == "operator"
    # Content should be updated by workflow (either LLM or fallback)
    generated = t_refreshed.prompt_variables.get("generated_content")
    assert generated is not None
    assert generated["body"] != "旧正文"
    # Cover image should be preset (unsplash) or preserved
    assert generated.get("cover_image_url") is not None
    # Compliance should be real result from check_compliance
    compliance = t_refreshed.prompt_variables.get("compliance_result")
    assert compliance is not None
    assert "level" in compliance


async def test_regenerate_content_still_visible_in_list(client, db: AsyncSession):
    """🔴 重新生成后任务仍应在审核发布中心可见（human_wait 状态）。"""
    token = get_auth_token(client)
    t = await _create_approved_task(db, content_preview="正文", draft_id="draft_008")

    # Before regenerate: visible in approved filter
    resp_before = client.get(
        "/review-publish-center/conclusions?status_filter=approved",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_before.json()["total"] == 1

    # Regenerate — drives workflow to HUMAN_WAIT
    client.post(
        f"/review-publish-center/conclusions/{t.id}/regenerate",
        headers={"Authorization": f"Bearer {token}"},
    )

    # After regenerate: visible in pending filter (human_wait)
    resp_after = client.get(
        "/review-publish-center/conclusions?status_filter=pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp_after.json()
    assert data["total"] == 1, f"Task disappeared after regenerate: {data}"
    assert data["items"][0]["status"] == "human_wait"


async def test_regenerate_content_not_found(client, db: AsyncSession):
    """🔴 不存在的任务返回 404。"""
    token = get_auth_token(client)
    response = client.post(
        "/review-publish-center/conclusions/non_existent/regenerate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


# ─── 6. Helper 测试 ───


async def test_get_draft_id_helper(db: AsyncSession):
    """🔴 _get_draft_id 从 prompt_variables 中提取 draft_id。"""
    assert _get_draft_id({"draft_id": "d001"}) == "d001"
    assert _get_draft_id({"draftId": "d002"}) == "d002"
    assert _get_draft_id({"other": "value"}) is None
