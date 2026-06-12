"""Tests for Workflow Engine DAG compilation + keyword_inject (Phase 4 P4-1 / P4-2).

Red-Green TDD for:
  - DAG cycle detection
  - Topological sort correctness
  - SKILL node execution (keyword_inject / brand_knowledge_inject)
  - DAG-aware next-node scheduling
  - Backward compatibility with serial templates
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import workflow_engine as we
from src.services.workflow_engine import (
    WorkflowStatus,
    NodeType,
    compile_dag,
    _find_next_executable_node,
)


@pytest.fixture(autouse=True)
def clear_db():
    we._clear_stores()
    we.load_presets()
    yield


# ─── 1. DAG Compilation ───


def test_compile_dag_serial_template():
    """串行模板编译后拓扑序等于 node_index 顺序."""
    tmpl = we.get_template("content_creation_standard")
    dag = compile_dag(tmpl.nodes)
    assert dag.topological_order == list(range(len(tmpl.nodes)))
    # 每个层级只有一个节点（串行）
    assert all(len(level) == 1 for level in dag.levels)


def test_compile_dag_with_explicit_deps():
    """显式 depends_on 编译正确."""
    nodes = [
        we.WorkflowNode(0, NodeType.AGENT, "A"),
        we.WorkflowNode(1, NodeType.AGENT, "B", depends_on=[0]),
        we.WorkflowNode(2, NodeType.AGENT, "C", depends_on=[0]),
        we.WorkflowNode(3, NodeType.AGENT, "D", depends_on=[1, 2]),
    ]
    dag = compile_dag(nodes)
    assert dag.topological_order[0] == 0
    assert dag.topological_order[-1] == 3
    # 层级：0 | 1,2 | 3
    assert dag.levels[0] == [0]
    assert set(dag.levels[1]) == {1, 2}
    assert dag.levels[2] == [3]


def test_compile_dag_detects_cycle():
    """环检测必须抛出 ValueError."""
    nodes = [
        we.WorkflowNode(0, NodeType.AGENT, "A", depends_on=[1]),
        we.WorkflowNode(1, NodeType.AGENT, "B", depends_on=[0]),
    ]
    with pytest.raises(ValueError, match="cycle"):
        compile_dag(nodes)


def test_compile_dag_missing_dependency():
    """依赖不存在的节点必须抛出 ValueError."""
    nodes = [
        we.WorkflowNode(0, NodeType.AGENT, "A"),
        we.WorkflowNode(1, NodeType.AGENT, "B", depends_on=[99]),
    ]
    with pytest.raises(ValueError, match="not found"):
        compile_dag(nodes)


# ─── 2. DAG Execution Scheduling ───


def test_find_next_executable_node():
    """_find_next_executable_node 找到依赖全部完成的节点."""
    tmpl = we.create_template(
        name="DAG",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
            {"node_type": "AGENT", "node_name": "B", "agent_id": "a2"},
            {"node_type": "AGENT", "node_name": "C", "agent_id": "a3"},
        ],
    )
    exec = we.start_execution("task_dag", tmpl.id)
    dag = compile_dag(tmpl.nodes)

    # 初始：节点 0 可执行
    assert _find_next_executable_node(dag, exec) == 0

    # 完成 0 后：节点 1 可执行
    we.execute_next_node(exec.id, node_output={"step0": "ok"})
    exec = we.get_execution(exec.id)
    assert _find_next_executable_node(dag, exec) == 1

    # 完成 1 后：节点 2 可执行
    we.execute_next_node(exec.id, node_output={"step1": "ok"})
    exec = we.get_execution(exec.id)
    assert _find_next_executable_node(dag, exec) == 2


# ─── 3. SKILL Node Execution ───


def test_keyword_inject_skill_node():
    """SKILL 类型 keyword_inject 节点自动执行并写入 context."""
    tmpl = we.create_template(
        name="SkillTest",
        nodes=[
            {"node_type": "AGENT", "node_name": "Setup", "agent_id": "a1"},
            {
                "node_type": "SKILL",
                "node_name": "关键词注入",
                "skill_id": "keyword_inject",
            },
        ],
    )
    exec = we.start_execution("task_skill", tmpl.id)
    # 第一步：Setup
    r1 = we.execute_next_node(exec.id, node_output={"topic": "宠物", "content": "test"})
    assert r1["done"] is False

    # 第二步：keyword_inject（自动执行，无需外部输入）
    r2 = we.execute_next_node(exec.id)
    assert r2["done"] is True

    exec = we.get_execution(exec.id)
    assert "injected_keywords" in exec.context
    assert exec.context["injected_count"] == 3


def test_brand_knowledge_inject_skill_node():
    """SKILL 类型 brand_knowledge_inject 节点执行."""
    tmpl = we.create_template(
        name="BrandTest",
        nodes=[
            {
                "node_type": "SKILL",
                "node_name": "品牌知识注入",
                "skill_id": "brand_knowledge_inject",
            },
        ],
    )
    exec = we.start_execution("task_brand", tmpl.id)
    r = we.execute_next_node(exec.id)
    assert r["done"] is True
    exec = we.get_execution(exec.id)
    assert exec.context.get("brand_knowledge_injected") is True


# ─── 4. Preset Templates with keyword_inject ───


def test_standard_template_has_keyword_inject():
    """标准模板必须包含 keyword_inject 节点."""
    preset = we.get_template("content_creation_standard")
    skill_nodes = [n for n in preset.nodes if n.node_type == NodeType.SKILL]
    assert any(n.skill_id == "keyword_inject" for n in skill_nodes)


def test_standard_template_has_brand_knowledge_inject():
    """标准模板必须包含 brand_knowledge_inject 节点."""
    preset = we.get_template("content_creation_standard")
    skill_nodes = [n for n in preset.nodes if n.node_type == NodeType.SKILL]
    assert any(n.skill_id == "brand_knowledge_inject" for n in skill_nodes)


# ─── 5. Backward Compatibility ───


def test_execute_next_node_still_advances_linearly():
    """execute_next_node 对串行模板仍按顺序推进."""
    tmpl = we.create_template(
        name="Linear",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
            {"node_type": "AGENT", "node_name": "B", "agent_id": "a2"},
        ],
    )
    exec = we.start_execution("task_linear", tmpl.id)
    r1 = we.execute_next_node(exec.id, node_output={"s1": "ok"})
    assert r1["done"] is False
    assert r1["next_node"] == 1
    r2 = we.execute_next_node(exec.id, node_output={"s2": "ok"})
    assert r2["done"] is True


# ─── 6. React Flow DAG Edges ───


def test_react_flow_dag_edges():
    """to_react_flow 对 DAG 模板生成正确边."""
    tmpl = we.create_template(name="DAGFlow", nodes=[
        {"node_type": "AGENT", "node_name": "A", "node_index": 0},
        {"node_type": "AGENT", "node_name": "B", "node_index": 1, "depends_on": [0]},
        {"node_type": "AGENT", "node_name": "C", "node_index": 2, "depends_on": [0]},
        {"node_type": "AGENT", "node_name": "D", "node_index": 3, "depends_on": [1, 2]},
    ])
    flow = we.to_react_flow(tmpl.id)
    edges = flow["edges"]
    # 4 条边：0->1, 0->2, 1->3, 2->3
    assert len(edges) == 4
    sources = {e["source"] for e in edges}
    assert sources == {"node-0", "node-1", "node-2"}


# ─── 7. Resume from checkpoint ───


def test_resume_rebuilds_completed_nodes():
    """resume_execution 能从 checkpoint 重建 completed_nodes."""
    from src.core.checkpoint import CheckpointManager

    mgr = CheckpointManager()
    we.set_checkpoint_manager(mgr)

    tmpl = we.create_template(
        name="ResumeTest",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
            {"node_type": "AGENT", "node_name": "B", "agent_id": "a2"},
            {"node_type": "AGENT", "node_name": "C", "agent_id": "a3"},
        ],
    )
    exec = we.start_execution("task_resume", tmpl.id)
    # 完成前两步
    we.execute_next_node(exec.id, node_output={"step": 0})
    we.execute_next_node(exec.id, node_output={"step": 1})
    exec = we.get_execution(exec.id)
    assert exec.completed_nodes == [0, 1]

    # 暂停
    we.pause_execution(exec.id)
    # 恢复（从 checkpoint 重建）
    we.resume_execution(exec.id)
    exec = we.get_execution(exec.id)
    assert exec.status == WorkflowStatus.RUNNING
    assert exec.resumed_count == 1
    assert exec.current_node_index == 2  # 下一步是 C
    assert "_audit_log" in exec.context

    we.set_checkpoint_manager(None)
