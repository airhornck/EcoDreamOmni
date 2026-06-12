"""Tests for PromptCompositionEngine."""

import pytest

from src.services.prompt_composition_engine import (
    ContentStrategy,
    PromptCompositionEngine,
    estimate_tokens,
)


def test_estimate_tokens_basic():
    assert estimate_tokens("") == 0
    assert estimate_tokens("hello world") > 0
    assert estimate_tokens("你好世界") > 0


def test_compose_empty_strategy():
    engine = PromptCompositionEngine()
    strategy = ContentStrategy()

    result = engine.compose(strategy, topic="养猫驱虫", platform="xhs")

    assert "小红书" in result.full_prompt
    assert "养猫驱虫" in result.full_prompt
    assert result.used_elements == []
    assert result.total_tokens > 0


def test_compose_with_structure_framework():
    engine = PromptCompositionEngine()
    strategy = ContentStrategy(
        elements=[
            {
                "element_id": "elem_test_001",
                "element_type": "structure_framework",
                "priority": 80,
                "_resolved_element": {
                    "element_id": "elem_test_001",
                    "element_type": "structure_framework",
                    "content": {
                        "structure_type": "避坑排雷型",
                        "sections": [
                            {"type": "hook", "description": "痛点引入"},
                            {"type": "body", "description": "避坑清单"},
                            {"type": "cta", "description": "互动引导"},
                        ],
                    },
                    "render_template": """结构类型：{{ structure_type }}
段落安排：
{% for section in sections %}- {{ section.type }}: {{ section.description }}
{% endfor %}""",
                },
            }
        ],
        variables={"痛点词": "驱虫药"},
    )

    result = engine.compose(strategy, topic="养猫驱虫", platform="xhs")

    assert "elem_test_001" in result.used_elements
    assert "避坑排雷型" in result.full_prompt
    assert "痛点引入" in result.full_prompt
    assert "小红书" in result.full_prompt


def test_compose_with_keyword_strategy():
    engine = PromptCompositionEngine()
    strategy = ContentStrategy(
        elements=[
            {
                "element_id": "elem_test_002",
                "element_type": "keyword_strategy",
                "priority": 70,
                "_resolved_element": {
                    "element_id": "elem_test_002",
                    "element_type": "keyword_strategy",
                    "content": {
                        "primary_keywords": ["新手养猫", "驱虫攻略"],
                        "secondary_keywords": ["性价比"],
                    },
                    "render_template": """核心关键词：{{ primary_keywords | join(', ') }}
辅助关键词：{{ secondary_keywords | join(', ') }}""",
                },
            }
        ],
    )

    result = engine.compose(strategy, topic="养猫驱虫", platform="xhs")

    assert "elem_test_002" in result.used_elements
    assert "新手养猫" in result.full_prompt
    assert "驱虫攻略" in result.full_prompt


def test_token_budget_prunes_low_priority():
    engine = PromptCompositionEngine()

    # 高优先级元素约 500 tokens，低优先级元素约 500 tokens
    # 预算 800：高优先级先被选中，低优先级因超出剩余预算被裁剪
    big_element = {
        "element_id": "elem_big",
        "element_type": "custom_fragment",
        "priority": 100,
        "_resolved_element": {
            "element_id": "elem_big",
            "element_type": "custom_fragment",
            "content": {"fragment": "x" * 1000},
            "render_template": "{{ fragment }}",
        },
    }
    small_element = {
        "element_id": "elem_small",
        "element_type": "custom_fragment",
        "priority": 10,
        "_resolved_element": {
            "element_id": "elem_small",
            "element_type": "custom_fragment",
            "content": {"fragment": "y" * 1000},
            "render_template": "{{ fragment }}",
        },
    }

    strategy = ContentStrategy(elements=[big_element, small_element])
    result = engine.compose(strategy, topic="test", platform="xhs", token_budget=800)

    # 高优先级元素（priority=100 >= 80）允许 10% 弹性，应被选中
    assert "elem_big" in result.used_elements
    # 低优先级元素因预算不足被裁剪
    assert "elem_small" in result.pruned_elements
