"""Migration verification script — v4.0 Agent-First.

Run after deploying Phase 1~5 to verify:
  1. agents table seeded correctly (10 agents + 1 generic)
  2. tasks.agent_id backfilled for legacy tasks
  3. No tasks left with null agent_id (when workflow_template_id is present)
  4. Agent-platform-format mappings are correct

Usage:
    cd apps/backend
    .venv/Scripts/python.exe scripts/verify_agent_migration.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.models.agent_orm import AgentORM
from src.models.task_orm import TaskORM


EXPECTED_AGENTS = {
    "content_forge_xhs_image", "content_forge_xhs_video", "content_forge_xhs_text",
    "content_forge_douyin_video", "content_forge_douyin_clone",
    "content_forge_wx_text", "content_forge_wx_video",
    "content_forge_bili_video", "content_forge_bili_clone",
    "content_forge_generic",
}


async def verify():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("Agent-First v4.0 Migration Verification")
        print("=" * 60)

        # 1. Check agents table
        result = await db.execute(select(AgentORM))
        agents = result.scalars().all()
        agent_ids = {a.id for a in agents}
        missing = EXPECTED_AGENTS - agent_ids
        extra = agent_ids - EXPECTED_AGENTS

        print(f"\n[1] Agents table: {len(agents)} rows")
        if missing:
            print(f"    FAIL: Missing agents: {missing}")
        else:
            print(f"    PASS: All {len(EXPECTED_AGENTS)} expected agents present")
        if extra:
            print(f"    WARN: Extra agents: {extra}")

        # 2. Check tasks with agent_id
        result = await db.execute(select(func.count()).select_from(TaskORM))
        total_tasks = result.scalar() or 0

        result = await db.execute(
            select(func.count()).select_from(TaskORM).where(TaskORM.agent_id.isnot(None))
        )
        tasks_with_agent = result.scalar() or 0

        result = await db.execute(
            select(func.count()).select_from(TaskORM)
            .where(TaskORM.agent_id.is_(None))
            .where(TaskORM.workflow_template_id.isnot(None))
        )
        orphan_tasks = result.scalar() or 0

        print(f"\n[2] Tasks migration:")
        print(f"    Total tasks: {total_tasks}")
        print(f"    Tasks with agent_id: {tasks_with_agent}")
        print(f"    Tasks missing agent_id (but have workflow_template_id): {orphan_tasks}")
        if orphan_tasks == 0:
            print(f"    PASS: All legacy tasks backfilled")
        else:
            print(f"    FAIL: {orphan_tasks} tasks still need backfill")

        # 3. Show agent distribution
        result = await db.execute(
            select(TaskORM.agent_id, func.count())
            .where(TaskORM.agent_id.isnot(None))
            .group_by(TaskORM.agent_id)
        )
        distribution = result.all()
        print(f"\n[3] Task distribution by agent:")
        for agent_id, count in sorted(distribution, key=lambda x: -x[1]):
            print(f"    {agent_id}: {count}")

        # 4. Check agent configs have workflow mapping
        bad_configs = []
        for a in agents:
            if not a.config or not a.config.get("default_workflow_template_id"):
                bad_configs.append(a.id)
        print(f"\n[4] Agent config integrity:")
        if bad_configs:
            print(f"    FAIL: Agents missing workflow mapping: {bad_configs}")
        else:
            print(f"    PASS: All agents have default_workflow_template_id")

        print("\n" + "=" * 60)
        if missing or orphan_tasks > 0 or bad_configs:
            print("RESULT: FAIL — please fix issues above")
            return 1
        else:
            print("RESULT: PASS — migration verified")
            return 0


if __name__ == "__main__":
    exit_code = asyncio.run(verify())
    sys.exit(exit_code)
