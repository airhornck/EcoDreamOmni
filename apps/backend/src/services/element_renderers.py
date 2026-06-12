"""Element Renderers — v4.0 Strategy Element Architecture.

每个 Renderer 负责将特定类型的 StrategyElement 渲染为 Prompt 片段。
渲染后的片段会被 PromptCompositionEngine 组织到六层 Prompt 的对应层中。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from jinja2 import Template


class ElementRenderer(ABC):
    """策略元素渲染器基类."""

    target_layer: str = "style_layer"  # 默认目标层

    @abstractmethod
    def render(
        self,
        element: Any,
        variables: Dict[str, str],
        topic: str,
        platform: str,
    ) -> str:
        """Render the element into a prompt fragment."""
        ...

    def _render_template(self, template_str: str, context: Dict[str, Any]) -> str:
        return Template(template_str).render(**context)


class HookPatternRenderer(ElementRenderer):
    """Hook 模式渲染器 → Layer 2: Structure Template."""

    target_layer = "structure_template"

    def render(self, element, variables, topic, platform) -> str:
        content = element.content or {}
        ctx = {
            "pattern": content.get("pattern", ""),
            "examples": content.get("examples", []),
            "rationale": content.get("rationale", ""),
            **variables,
            "topic": topic,
            "platform": platform,
        }
        return self._render_template(element.render_template or "", ctx)


class StructureFrameworkRenderer(ElementRenderer):
    """结构框架渲染器 → Layer 2: Structure Template."""

    target_layer = "structure_template"

    def render(self, element, variables, topic, platform) -> str:
        content = element.content or {}
        ctx = {
            "structure_type": content.get("structure_type", ""),
            "sections": content.get("sections", []),
            "rationale": content.get("rationale", ""),
            **variables,
            "topic": topic,
            "platform": platform,
        }
        return self._render_template(element.render_template or "", ctx)


class KeywordStrategyRenderer(ElementRenderer):
    """关键词策略渲染器 → Layer 4: Keyword Injection."""

    target_layer = "keyword_injection"

    def render(self, element, variables, topic, platform) -> str:
        content = element.content or {}
        ctx = {
            "primary_keywords": content.get("primary_keywords", []),
            "secondary_keywords": content.get("secondary_keywords", []),
            "long_tail_keywords": content.get("long_tail_keywords", []),
            "density_target": content.get("density_target", 0.03),
            "placement_rules": content.get("placement_rules", []),
            **variables,
            "topic": topic,
            "platform": platform,
        }
        return self._render_template(element.render_template or "", ctx)


class EmotionCurveRenderer(ElementRenderer):
    """情感曲线渲染器 → Layer 6: Style Layer."""

    target_layer = "style_layer"

    def render(self, element, variables, topic, platform) -> str:
        content = element.content or {}
        ctx = {
            "curve": content.get("curve", []),
            "rationale": content.get("rationale", ""),
            **variables,
            "topic": topic,
            "platform": platform,
        }
        return self._render_template(element.render_template or "", ctx)


class EngagementFormulaRenderer(ElementRenderer):
    """互动公式渲染器 → Layer 6: Style Layer."""

    target_layer = "style_layer"

    def render(self, element, variables, topic, platform) -> str:
        content = element.content or {}
        ctx = {
            "emoji_density": content.get("emoji_density", ""),
            "sentence_rhythm": content.get("sentence_rhythm", ""),
            "interaction_hooks": content.get("interaction_hooks", []),
            "visual_cues": content.get("visual_cues", []),
            **variables,
            "topic": topic,
            "platform": platform,
        }
        return self._render_template(element.render_template or "", ctx)


class CTAPatternRenderer(ElementRenderer):
    """CTA 模式渲染器 → Layer 2: Structure Template."""

    target_layer = "structure_template"

    def render(self, element, variables, topic, platform) -> str:
        content = element.content or {}
        ctx = {
            "pattern": content.get("pattern", ""),
            "examples": content.get("examples", []),
            **variables,
            "topic": topic,
            "platform": platform,
        }
        return self._render_template(element.render_template or "", ctx)


class BodyStructureRenderer(ElementRenderer):
    """正文结构渲染器 → Layer 2: Structure Template."""

    target_layer = "structure_template"

    def render(self, element, variables, topic, platform) -> str:
        content = element.content or {}
        ctx = {
            "sections": content.get("sections", []),
            **variables,
            "topic": topic,
            "platform": platform,
        }
        return self._render_template(element.render_template or "", ctx)


class MethodologyStageRenderer(ElementRenderer):
    """方法论阶段渲染器 → Layer 2: Structure Template."""

    target_layer = "structure_template"

    def render(self, element, variables, topic, platform) -> str:
        content = element.content or {}
        ctx = {
            "stage_id": content.get("stage_id", ""),
            "stage_name": content.get("stage_name", ""),
            "stage_description": content.get("stage_description", ""),
            "content_template": content.get("content_template", {}),
            **variables,
            "topic": topic,
            "platform": platform,
        }
        return self._render_template(element.render_template or "", ctx)


class SceneAnchorRenderer(ElementRenderer):
    """场景切入渲染器 → Layer 3: Knowledge Injection."""

    target_layer = "knowledge"

    def render(self, element, variables, topic, platform) -> str:
        content = element.content or {}
        ctx = {
            "scene": content.get("scene", ""),
            "pain_point": content.get("pain_point", ""),
            "trend": content.get("trend", ""),
            **variables,
            "topic": topic,
            "platform": platform,
        }
        return self._render_template(element.render_template or "", ctx)


class CustomFragmentRenderer(ElementRenderer):
    """自定义片段渲染器 → 追加到 Style Layer."""

    target_layer = "style_layer"

    def render(self, element, variables, topic, platform) -> str:
        content = element.content or {}
        ctx = {
            "fragment": content.get("fragment", ""),
            **variables,
            "topic": topic,
            "platform": platform,
        }
        return self._render_template(element.render_template or "", ctx)


# ═══════════════════════════════════════════════════════════════════
# Renderer Registry
# ═══════════════════════════════════════════════════════════════════

_RENDERER_MAP: Dict[str, ElementRenderer] = {
    "hook_pattern": HookPatternRenderer(),
    "structure_framework": StructureFrameworkRenderer(),
    "keyword_strategy": KeywordStrategyRenderer(),
    "emotion_curve": EmotionCurveRenderer(),
    "engagement_formula": EngagementFormulaRenderer(),
    "cta_pattern": CTAPatternRenderer(),
    "body_structure": BodyStructureRenderer(),
    "methodology_stage": MethodologyStageRenderer(),
    "scene_anchor": SceneAnchorRenderer(),
    "custom_fragment": CustomFragmentRenderer(),
}


def get_renderer(element_type: str) -> ElementRenderer:
    """Get renderer by element type. Falls back to CustomFragmentRenderer."""
    return _RENDERER_MAP.get(element_type, CustomFragmentRenderer())


def register_renderer(element_type: str, renderer: ElementRenderer) -> None:
    """Register a custom renderer (plugin extension point)."""
    _RENDERER_MAP[element_type] = renderer
