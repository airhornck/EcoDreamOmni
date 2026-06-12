"""
W17 HITL-2 弹性单人审核 Red-Green 测试。

核心要求:
- 弹性审核策略（标准内容单人 / 高风险双人）
- 高风险标签自动检测（调用 BrandKnowledge / VetDrugDB）
- batch-approve 批量操作管控（含高风险强制逐篇审核）
"""

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.task_orm import TaskORM
from src.models.user import clear_users
from src.services.auth_service import register_user
from src.services import human_in_loop as hil
from src.services import task_hub

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest.fixture(autouse=True)
async def clear_db(db: AsyncSession):
    await db.execute(delete(TaskORM))
    await db.commit()
    hil._review_db.clear()
    hil._task_risk_db.clear()
    task_hub._clear_stores()
    yield


def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    email = f"hitlv2_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"hitlv2user_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]


async def _create_task_in_human_wait(db: AsyncSession, workflow_template_id: str = "wf_001", **variables) -> task_hub.Task:
    t = await task_hub.create_task(db, "Review Me", workflow_template_id, 1, "acc_1", "pers_1", created_by="alice")
    if variables:
        await task_hub.update_task(db, t.id, prompt_variables=variables)
    await task_hub.configure(db, t.id)
    await task_hub.queue(db, t.id)
    await task_hub.start(db, t.id)
    await task_hub.wait_human(db, t.id)
    return await task_hub.get_task(db, t.id)


# =============================================================================
# HITL-1: 弹性审核策略 — 风险等级检测
# =============================================================================


async def test_detect_risk_level_for_safe_content(client, db: AsyncSession):
    """🔴 安全内容风险等级为 LOW."""
    token = get_auth_token(client)
    response = client.post(
        "/human-in-the-loop/detect-risk",
        json={
            "title": "春天给猫咪梳毛的小技巧",
            "body": "春天到了，记得给猫咪勤梳毛，保持环境清洁",
            "tags": ["养宠日常"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["risk_level"] == "LOW"
    assert data["review_strategy"] == "single"


async def test_detect_risk_level_for_medium_risk(client, db: AsyncSession):
    """🔴 含商业推广但未标注的内容风险等级为 MEDIUM."""
    token = get_auth_token(client)
    response = client.post(
        "/human-in-the-loop/detect-risk",
        json={
            "title": "驱虫药推荐",
            "body": "这款驱虫药效果很好，大家快去购买链接在评论区",
            "tags": ["驱虫", "推荐"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "MEDIUM"
    assert data["review_strategy"] in ["single", "dual"]


async def test_detect_risk_level_for_high_risk(client, db: AsyncSession):
    """🔴 含处方药或诊疗承诺的内容风险等级为 HIGH."""
    token = get_auth_token(client)
    response = client.post(
        "/human-in-the-loop/detect-risk",
        json={
            "title": "三天治愈猫癣",
            "body": "用阿莫西林三天治愈猫癣，保证有效，无效退款",
            "tags": ["治疗", "保证"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "HIGH"
    assert data["review_strategy"] == "dual"
    assert data["requires_forced_individual_review"] is True


# =============================================================================
# HITL-2: 高风险内容 PENDING_REVIEW 状态
# =============================================================================


async def test_high_risk_task_marked_pending_review(client, db: AsyncSession):
    """🔴 高风险内容在审核台显示为 PENDING_REVIEW."""
    token = get_auth_token(client)
    t = await _create_task_in_human_wait(
        db,
        workflow_template_id="wf_publish",
        content_preview="用阿莫西林三天治愈",
    )

    # 标记为高风险
    response = client.post(
        f"/human-in-the-loop/tasks/{t.id}/mark-risk",
        json={"risk_level": "HIGH", "reason": "含处方药关键词"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "HIGH"

    # 获取待审核列表
    pending_resp = client.get(
        "/human-in-the-loop/pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    pending_data = pending_resp.json()
    high_risk_items = [item for item in pending_data["items"] if item.get("risk_level") == "HIGH"]
    assert len(high_risk_items) >= 1


# =============================================================================
# HITL-3: batch-approve 批量操作管控
# =============================================================================


async def test_batch_approve_standard_content(client, db: AsyncSession):
    """🔴 标准内容（LOW风险）支持批量审核通过."""
    token = get_auth_token(client)
    # 创建3个低风险任务
    task_ids = []
    for i in range(3):
        t = await _create_task_in_human_wait(
            db,
            workflow_template_id="wf_001",
            content_preview=f"安全内容 {i}",
        )
        task_ids.append(t.id)
        # 标记为低风险
        client.post(
            f"/human-in-the-loop/tasks/{t.id}/mark-risk",
            json={"risk_level": "LOW"},
            headers={"Authorization": f"Bearer {token}"},
        )

    response = client.post(
        "/human-in-the-loop/batch-approve",
        json={"task_ids": task_ids, "reviewer_id": "reviewer_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["approved_count"] == 3
    assert data["rejected_count"] == 0


async def test_batch_approve_blocks_high_risk(client, db: AsyncSession):
    """🔴 批量审核中包含高风险内容时，强制逐篇审核."""
    token = get_auth_token(client)
    low_task = await _create_task_in_human_wait(db, workflow_template_id="wf_001", content_preview="安全内容")
    high_task = await _create_task_in_human_wait(db, workflow_template_id="wf_001", content_preview="用阿莫西林治疗")

    client.post(
        f"/human-in-the-loop/tasks/{low_task.id}/mark-risk",
        json={"risk_level": "LOW"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        f"/human-in-the-loop/tasks/{high_task.id}/mark-risk",
        json={"risk_level": "HIGH"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.post(
        "/human-in-the-loop/batch-approve",
        json={"task_ids": [low_task.id, high_task.id], "reviewer_id": "reviewer_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    # 低风险内容通过，高风险内容被拒绝批量操作
    assert data["approved_count"] == 1
    assert data["forced_individual_review_count"] == 1
    assert high_task.id in data["forced_individual_review_ids"]


async def test_batch_approve_single_reviewer_for_low_risk(client, db: AsyncSession):
    """🔴 LOW风险内容单人审核即可."""
    token = get_auth_token(client)
    t = await _create_task_in_human_wait(db, workflow_template_id="wf_001", content_preview="普通内容")
    client.post(
        f"/human-in-the-loop/tasks/{t.id}/mark-risk",
        json={"risk_level": "LOW"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.post(
        "/human-in-the-loop/batch-approve",
        json={"task_ids": [t.id], "reviewer_id": "reviewer_single"},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    assert data["approved_count"] == 1
    # 验证只需要一个审批人
    record = await hil.get_review_history(db, t.id)
    assert len(record) == 1


async def test_high_risk_requires_dual_approval(client, db: AsyncSession):
    """🔴 HIGH风险内容需要双人审核."""
    token = get_auth_token(client)
    t = await _create_task_in_human_wait(db, workflow_template_id="wf_publish", content_preview="高风险内容")
    client.post(
        f"/human-in-the-loop/tasks/{t.id}/mark-risk",
        json={"risk_level": "HIGH"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 单人审核不能完成
    r1 = await hil.approve_task(db, t.id, "reviewer_a")
    assert r1["status"] == "human_wait"

    # 第二人审核才能完成（v2: 进入 APPROVED_WAITING_PUBLISH 而非直接 RUNNING）
    r2 = await hil.approve_task(db, t.id, "reviewer_b")
    assert r2["status"] == "approved_waiting_publish"
