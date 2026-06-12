"""
验证工作流真实化改造后的节点输出格式。

不依赖数据库，仅验证数据结构是否符合前端契约。
"""

import sys
from pathlib import Path

backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from src.services.workflow_engine import WorkflowNode, NodeType, FailStrategy
from src.services.task_hub import simulate_node_output
import asyncio


def _make_task(name="测试任务", platform="xhs", account_id="acc_1", persona_id="pers_1"):
    """Build a minimal task object for testing."""
    class FakeTask:
        def __init__(self):
            self.id = "task_test_001"
            self.name = name
            self.platform = platform
            self.account_id = account_id
            self.persona_id = persona_id
            self.persona_story_id = None
            self.node_id = None
            self.current_node_index = 0
            self.prompt_variables = {}
            self.content_format = None
    return FakeTask()


def _make_node(agent_id, template_id=None):
    return WorkflowNode(
        node_index=0,
        node_type=NodeType.AGENT,
        node_name="test",
        agent_id=agent_id,
        prompt_template_id=template_id,
        fail_strategy=FailStrategy.FAIL_FAST,
    )


async def test_trend_scout_output_format():
    """🔴 TrendScout 输出必须包含 topic_report.topics[].tags"""
    node = _make_node("trend-scout")
    task = _make_task(name="猫咪防暑任务")
    result = await simulate_node_output(node, task, db=None)

    tr = result["topic_report"]
    assert "report_id" in tr
    assert "topics" in tr
    assert len(tr["topics"]) > 0
    for t in tr["topics"]:
        assert "id" in t
        assert "title" in t
        assert "tags" in t, f"topic {t['id']} 缺少 tags 字段"
        assert isinstance(t["tags"], list)
        assert "status" in t
        assert "estimated_engagement" in t
        assert "source_report" in t
    assert "5a_stage" in tr
    assert "audience_fit_score" in tr
    print("[OK] trend-scout output format correct")


async def test_marketing_methodology_output_format():
    """🔴 MarketingMethodology 输出必须包含 outline.title 和 outline.sections"""
    node = _make_node("marketing-methodology")
    task = _make_task(name="狗狗驱虫任务")
    result = await simulate_node_output(node, task, db=None)

    outline = result["outline"]
    assert "title" in outline
    assert "sections" in outline
    assert isinstance(outline["sections"], list)
    print("[OK] marketing-methodology output format correct")


async def test_cf_outline_output_format():
    """🔴 cf-outline 输出必须包含 outline.title 和 outline.sections"""
    node = _make_node("content-forge", "cf-outline")
    task = _make_task(name="夏季养猫任务")
    result = await simulate_node_output(node, task, db=None)

    outline = result["outline"]
    assert "title" in outline
    assert "sections" in outline
    assert isinstance(outline["sections"], list)
    print("[OK] cf-outline output format correct")


async def test_pool_predictor_output_format():
    """🔴 PoolPredictor 输出必须包含 engagement_interval.likes.min/max"""
    node = _make_node("pool-predictor")
    task = _make_task(name="新手养狗任务")
    result = await simulate_node_output(node, task, db=None)

    pred = result["prediction_result"]
    assert "engagement_interval" in pred
    ei = pred["engagement_interval"]
    for key in ["likes", "comments", "collects"]:
        assert key in ei, f"缺少 {key}"
        assert "min" in ei[key] or isinstance(ei[key], (list, tuple)), f"{key} 格式错误"
    assert "disclaimer" in pred

    qs = result["quality_score"]
    assert "overall" in qs
    print("[OK] pool-predictor output format correct")


async def main():
    await test_trend_scout_output_format()
    await test_marketing_methodology_output_format()
    await test_cf_outline_output_format()
    await test_pool_predictor_output_format()
    print("\n[SUCCESS] All workflow node output format validations passed")


if __name__ == "__main__":
    asyncio.run(main())
