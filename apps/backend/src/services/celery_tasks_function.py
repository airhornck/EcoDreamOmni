"""Celery tasks Function layer — DB context + workflow driving."""

from typing import Any, Dict

from src.core.database import AsyncSessionLocal
from src.services import task_hub as th
from src.services import workflow_engine as we


async def drive_workflow(task_hub_task_id: str) -> Dict[str, Any]:
    """Drive a TaskHub workflow execution to completion or next human gate."""
    async with AsyncSessionLocal() as db:
        task = await th.get_task(db, task_hub_task_id)
        if not task or not task.execution_id:
            return {"status": "not_found", "task_id": task_hub_task_id}

        execution = we.get_execution(task.execution_id)
        if not execution:
            return {"status": "no_execution", "task_id": task_hub_task_id}

        # If paused (after human approval), resume via task_hub
        if execution.status == we.WorkflowStatus.PAUSED:
            task = await th.resume_workflow_execution(db, task)
            execution = we.get_execution(task.execution_id)
            return {
                "status": execution.status.value if execution else "unknown",
                "task_id": task_hub_task_id,
                "current_node": execution.current_node_index if execution else 0,
            }

        # For RUNNING state, drive remaining nodes with real node outputs
        while True:
            execution = we.get_execution(task.execution_id)
            if execution.status in (
                we.WorkflowStatus.COMPLETED,
                we.WorkflowStatus.FAILED,
                we.WorkflowStatus.CANCELLED,
            ):
                break
            if execution.status == we.WorkflowStatus.PAUSED:
                break

            tmpl = we.get_template(execution.template_id)
            if not tmpl or execution.current_node_index >= len(tmpl.nodes):
                break

            node = tmpl.nodes[execution.current_node_index]
            if node.node_type == we.NodeType.HUMAN_APPROVAL:
                we.pause_execution(execution.id)
                await th.transition_task(db, task_hub_task_id, "human_wait")
                break

            # Generate real node output before advancing
            node_output = await th.simulate_node_output(
                node, task, execution_context=execution.context, db=db
            )
            result = we.execute_next_node(execution.id, node_output=node_output)
            await th.update_task(
                db, task_hub_task_id, current_node_index=execution.current_node_index
            )

            if result.get("done"):
                if result.get("status") == "COMPLETED":
                    await th.transition_task(db, task_hub_task_id, "completed")
                elif result.get("status") == "FAILED":
                    await th.transition_task(db, task_hub_task_id, "failed")
                break

        return {
            "status": execution.status.value if execution else "unknown",
            "task_id": task_hub_task_id,
            "current_node": execution.current_node_index if execution else 0,
        }
