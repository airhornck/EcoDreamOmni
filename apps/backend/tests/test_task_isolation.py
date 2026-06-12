"""Task data isolation tests — Red-Green TDD.

🔴 Phase: Write failing tests for created_by isolation.
"""

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task_orm import TaskORM
from src.services import task_hub as th
from src.services.task_function import list_tasks_from_db
from src.services import human_in_loop as hil


@pytest_asyncio.fixture(autouse=True)
async def clear_tasks(db: AsyncSession):
    """Clear tasks and caches before/after each test."""
    await db.execute(delete(TaskORM))
    await db.commit()
    th._clear_stores()
    hil._clear_stores()
    yield
    await db.execute(delete(TaskORM))
    await db.commit()
    th._clear_stores()
    hil._clear_stores()


async def test_list_tasks_from_db_filters_by_created_by(db: AsyncSession):
    """🔴 Red: list_tasks_from_db must accept created_by and filter results."""
    await th.create_task(
        db=db,
        name="Alice Task",
        workflow_template_id="wf_001",
        workflow_version=1,
        account_id="acc_001",
        persona_id="pers_001",
        created_by="alice",
    )
    await th.create_task(
        db=db,
        name="Bob Task",
        workflow_template_id="wf_001",
        workflow_version=1,
        account_id="acc_002",
        persona_id="pers_002",
        created_by="bob",
    )

    tasks = await list_tasks_from_db(db, created_by="alice")
    assert len(tasks) == 1
    assert tasks[0].name == "Alice Task"


async def test_list_tasks_filters_by_created_by(db: AsyncSession):
    """🔴 Red: task_hub.list_tasks must accept created_by and filter results."""
    await th.create_task(
        db=db,
        name="Alice Task",
        workflow_template_id="wf_001",
        workflow_version=1,
        account_id="acc_001",
        persona_id="pers_001",
        created_by="alice",
    )
    await th.create_task(
        db=db,
        name="Bob Task",
        workflow_template_id="wf_001",
        workflow_version=1,
        account_id="acc_002",
        persona_id="pers_002",
        created_by="bob",
    )

    tasks = await th.list_tasks(db, created_by="alice")
    assert len(tasks) == 1
    assert tasks[0].name == "Alice Task"


async def test_get_pending_tasks_filters_by_created_by(db: AsyncSession):
    """🔴 Red: human_in_loop.get_pending_tasks must only return tasks created by the given user."""
    t1 = await th.create_task(
        db=db,
        name="Alice Task",
        workflow_template_id="wf_publish_001",
        workflow_version=1,
        account_id="acc_001",
        persona_id="pers_001",
        created_by="alice",
    )
    t2 = await th.create_task(
        db=db,
        name="Bob Task",
        workflow_template_id="wf_publish_001",
        workflow_version=1,
        account_id="acc_002",
        persona_id="pers_002",
        created_by="bob",
    )

    # Transition both to HUMAN_WAIT
    await th.configure(db, t1.id)
    await th.queue(db, t1.id)
    await th.start(db, t1.id)
    await th.wait_human(db, t1.id)

    await th.configure(db, t2.id)
    await th.queue(db, t2.id)
    await th.start(db, t2.id)
    await th.wait_human(db, t2.id)

    pending = await hil.get_pending_tasks(db, created_by="alice")
    assert len(pending) == 1
    assert pending[0].task_name == "Alice Task"
