"""Prompt Composition Engine — v4.0 Strategy Element Architecture.

将 ContentStrategy（策略元素组合）渲染为完整的六层 Prompt。

设计灵感：
- Unreal Engine AI Toolkit 2026: Composable Prompt Architecture
- Claude Code: 六层 Context Injection
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.services.element_renderers import get_renderer

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """估算文本 Token 数（简单启发式，适合中文和英文混合）.
    
    生产环境建议替换为 tiktoken 精确计算。
    """
    if not text:
        return 0
    # 中文字符 ≈ 1.5 tokens，英文单词 ≈ 1.3 tokens
    import re
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_tokens = len(re.findall(r'[a-zA-Z]+', text))
    other_tokens = len(text) - chinese_chars - english_tokens
    return int(chinese_chars * 1.5 + english_tokens * 1.3 + other_tokens * 0.5)


@dataclass
class PromptElement:
    """渲染后的 Prompt 元素（含元数据）."""

    element_id: str
    element_type: str
    fragment: str
    priority: int
    token_count: int
    target_layer: str


@dataclass
class ComposedPrompt:
    """组装后的完整 Prompt."""

    six_layers: Dict[str, str]
    full_prompt: str
    used_elements: List[str]
    pruned_elements: List[str]
    total_tokens: int


@dataclass
class ContentStrategy:
    """内容策略配置（Pydantic-less dataclass for internal use）."""

    strategy_id: Optional[str] = None
    name: Optional[str] = None
    elements: List[Dict[str, Any]] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    custom_fragments: List[str] = field(default_factory=list)
    persona_id: Optional[str] = None
    persona_story_id: Optional[str] = None
    node_id: Optional[str] = None
    content_series_id: Optional[str] = None
    timeline_event_id: Optional[str] = None
    methodology_stage_id: Optional[str] = None


class PromptCompositionEngine:
    """Prompt 组装引擎 —— 将 ContentStrategy 渲染为完整 Prompt."""

    # 平台格式规则（Layer 1）
    PLATFORM_RULES = {
        "xhs": "平台：小红书\n- 风格：活泼亲切，多用emoji，段落简短\n- 结构：标题吸睛 + 正文分段（带emoji小标题）+ 结尾互动 + 话题标签\n- 字数：500-800字\n- 禁止：医疗诊断承诺、处方药推荐、绝对化功效宣称\n- 必须：宠物零食/用品标注'本品不能替代药品'",
        "xiaohongshu": "平台：小红书\n- 风格：活泼亲切，多用emoji，段落简短\n- 结构：标题吸睛 + 正文分段（带emoji小标题）+ 结尾互动 + 话题标签\n- 字数：500-800字\n- 禁止：医疗诊断承诺、处方药推荐、绝对化功效宣称\n- 必须：宠物零食/用品标注'本品不能替代药品'",
        "douyin": "平台：抖音\n- 风格：口语化、节奏快、有hook\n- 结构：黄金3秒hook + 核心要点 + 结尾互动\n- 字数：300-500字\n- 禁止：医疗诊断承诺、处方药推荐",
    }

    # 默认输出格式规则（Layer 2 兜底）
    DEFAULT_STRUCTURE_TEMPLATE = """输出格式要求（JSON）：
- title: 标题（吸睛，带emoji，符合平台调性）
- body: 正文（Markdown格式）
  · 分3-4个部分，每部分有小标题和emoji
  · 提供具体可操作的建议（不少于5条）
  · 加入一个简短的"我家毛孩子"真实案例
  · 结尾引导用户评论互动
- tags: 标签数组（5-8个相关话题标签）"""

    # 默认风格层（Layer 6 兜底）
    DEFAULT_STYLE_LAYER = """语气风格：casual — 轻松随意，像跟朋友聊天
叙事视角：第一人称"我"
情感温度：温暖、真实、有共鸣
互动策略：结尾引导评论，中间适当提问"""

    def compose(
        self,
        content_strategy: ContentStrategy,
        topic: str,
        platform: str,
        token_budget: int = 6000,
    ) -> ComposedPrompt:
        """将内容策略组合渲染为完整 Prompt.

        Args:
            content_strategy: 用户配置的内容策略
            topic: 内容主题
            platform: 目标平台
            token_budget: Token 预算上限

        Returns:
            ComposedPrompt: 包含六层分解和完整 Prompt
        """
        # Step 1: 渲染所有策略元素
        prompt_elements = self._render_elements(content_strategy, topic, platform)

        # Step 2: 按优先级排序，Token 预算内贪心选择
        selected, pruned = self._select_elements(prompt_elements, token_budget)

        # Step 3: 按六层 Prompt 组织
        six_layers = self._build_six_layers(
            content_strategy=content_strategy,
            selected_elements=selected,
            topic=topic,
            platform=platform,
        )

        # Step 4: 追加自定义片段
        for fragment in content_strategy.custom_fragments:
            six_layers["style_layer"] += f"\n\n[自定义约束]\n{fragment}"

        # Step 5: 组装完整 Prompt
        full_prompt = self._assemble_full_prompt(six_layers)
        total_tokens = estimate_tokens(full_prompt)

        return ComposedPrompt(
            six_layers=six_layers,
            full_prompt=full_prompt,
            used_elements=[e.element_id for e in selected],
            pruned_elements=[e.element_id for e in pruned],
            total_tokens=total_tokens,
        )

    def _render_elements(
        self,
        content_strategy: ContentStrategy,
        topic: str,
        platform: str,
    ) -> List[PromptElement]:
        """将 ContentStrategy.elements 渲染为 PromptElement 列表."""
        prompt_elements: List[PromptElement] = []

        for ref in content_strategy.elements:
            element_id = ref.get("element_id")
            element_type = ref.get("element_type")
            priority = ref.get("priority", 50)
            override_variables = ref.get("override_variables", {}) or {}

            if not element_id or not element_type:
                logger.warning("Skipping invalid element ref: %s", ref)
                continue

            # 创建轻量化的 element-like 对象
            element_data = ref.get("_resolved_element")
            if element_data is None:
                element_data = {
                    "element_id": element_id,
                    "element_type": element_type,
                    "content": ref.get("override_content", {}),
                    "render_template": ref.get("_render_template", ""),
                }

            from types import SimpleNamespace
            element_obj = SimpleNamespace(**element_data)

            renderer = get_renderer(element_type)
            merged_variables = {**content_strategy.variables, **override_variables}

            try:
                fragment = renderer.render(
                    element=element_obj,
                    variables=merged_variables,
                    topic=topic,
                    platform=platform,
                )
            except Exception as e:
                logger.warning("Failed to render element %s: %s", element_id, e)
                fragment = f"<!-- 渲染失败: {element_id} -->"

            prompt_elements.append(
                PromptElement(
                    element_id=element_id,
                    element_type=element_type,
                    fragment=fragment,
                    priority=priority,
                    token_count=estimate_tokens(fragment),
                    target_layer=renderer.target_layer,
                )
            )

        return prompt_elements

    def _select_elements(
        self,
        elements: List[PromptElement],
        token_budget: int,
    ) -> tuple[List[PromptElement], List[PromptElement]]:
        """按优先级排序并在 Token 预算内贪心选择.
        
        策略：
        1. 按优先级降序、Token 数升序排序
        2. 普通元素必须在预算内才选择
        3. 对于当前最高优先级的元素（priority >= 80），允许 10% 预算弹性
           确保核心策略元素不会被裁剪
        """
        sorted_elements = sorted(elements, key=lambda e: (-e.priority, e.token_count))

        selected: List[PromptElement] = []
        total_tokens = 0

        for idx, pe in enumerate(sorted_elements):
            is_top_priority = pe.priority >= 80 and idx == 0
            effective_budget = int(token_budget * 1.1) if is_top_priority else token_budget

            if total_tokens + pe.token_count <= effective_budget:
                selected.append(pe)
                total_tokens += pe.token_count
            else:
                logger.warning(
                    "Token budget exhausted, skipping element %s (%d tokens)",
                    pe.element_id,
                    pe.token_count,
                )

        pruned = [e for e in sorted_elements if e not in selected]
        return selected, pruned

    def _build_six_layers(
        self,
        content_strategy: ContentStrategy,
        selected_elements: List[PromptElement],
        topic: str,
        platform: str,
    ) -> Dict[str, str]:
        """构建六层 Prompt."""
        platform_format = self.PLATFORM_RULES.get(platform, self.PLATFORM_RULES["xhs"])

        structure_fragments = [
            e.fragment for e in selected_elements if e.target_layer == "structure_template"
        ]
        structure_template = self.DEFAULT_STRUCTURE_TEMPLATE
        if structure_fragments:
            structure_template = (
                "=== 内容结构策略 ===\n"
                + "\n\n".join(structure_fragments)
                + "\n\n=== 输出格式要求 ===\n"
                + self.DEFAULT_STRUCTURE_TEMPLATE
            )

        brand_knowledge = self._build_knowledge_layer(content_strategy)

        keyword_fragments = [
            e.fragment for e in selected_elements if e.target_layer == "keyword_injection"
        ]
        keyword_injection = f"核心话题：{topic}\n"
        keyword_injection += "创作要求：\n"
        keyword_injection += "1. 内容必须有真实价值，不能是空洞的套话\n"
        keyword_injection += "2. 分享具体可操作的建议\n"
        keyword_injection += "3. 用第一人称'我'来写，增加真实感\n"
        keyword_injection += "4. 适当加入个人经历或案例\n"
        keyword_injection += "5. 结尾引导评论互动\n"
        keyword_injection += "6. 严格遵守知识库参考中的禁止宣称和必须声明"
        if keyword_fragments:
            keyword_injection += "\n\n" + "\n\n".join(keyword_fragments)

        persona_layer = self._build_persona_layer(content_strategy)

        style_fragments = [
            e.fragment for e in selected_elements if e.target_layer == "style_layer"
        ]
        style_layer = self.DEFAULT_STYLE_LAYER
        if style_fragments:
            style_layer = "=== 风格策略 ===\n" + "\n\n".join(style_fragments) + "\n\n=== 基础风格 ===\n" + style_layer

        return {
            "platform_format": platform_format,
            "structure_template": structure_template,
            "brand_knowledge": brand_knowledge,
            "keyword_injection": keyword_injection,
            "persona_layer": persona_layer,
            "style_layer": style_layer,
        }

    def _build_knowledge_layer(self, content_strategy: ContentStrategy) -> str:
        """构建知识注入层（故事线、系列、时间线、场景切入）."""
        lines = []

        if content_strategy.methodology_stage_id:
            lines.append(f"方法论阶段：{content_strategy.methodology_stage_id}")
        if content_strategy.timeline_event_id:
            lines.append(f"时间线事件：{content_strategy.timeline_event_id}")
        if content_strategy.content_series_id:
            lines.append(f"内容系列：{content_strategy.content_series_id}")
        if content_strategy.persona_story_id:
            lines.append(f"故事线：{content_strategy.persona_story_id}")
            if content_strategy.node_id:
                lines.append(f"当前节点：{content_strategy.node_id}")

        if lines:
            return "=== 策略上下文 ===\n" + "\n".join(lines)
        return "（当前未配置额外策略上下文）"

    def _build_persona_layer(self, content_strategy: ContentStrategy) -> str:
        """构建人设层."""
        if content_strategy.persona_id:
            return f"人设：{content_strategy.persona_id}\n请使用该人设的口吻、口头禅和价值观进行创作。"
        return "人设：默认创作者\n请用亲切、真实、有共鸣的第一人称进行创作。"

    def _assemble_full_prompt(self, six_layers: Dict[str, str]) -> str:
        """将六层 Prompt 组装为完整字符串."""
        return f"""{six_layers['platform_format']}

{six_layers['structure_template']}

{six_layers['brand_knowledge']}

{six_layers['keyword_injection']}

{six_layers['persona_layer']}

{six_layers['style_layer']}
"""


# ═══════════════════════════════════════════════════════════════════
# Singleton instance
# ═══════════════════════════════════════════════════════════════════

_default_engine: Optional[PromptCompositionEngine] = None


def get_prompt_composition_engine() -> PromptCompositionEngine:
    """获取默认的 PromptCompositionEngine 单例."""
    global _default_engine
    if _default_engine is None:
        _default_engine = PromptCompositionEngine()
    return _default_engine
