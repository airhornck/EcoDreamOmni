"""MarketingMethodology — AIPL methodology engine.

Manages stage templates, KPI targets, and content evaluation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class MethodologyStage:
    id: str
    framework: str
    stage: str
    stage_name: str
    content_template: Dict
    kpi_targets: Dict
    compliance_tags: List[str]
    forbidden_elements: List[str]
    stage_transition_criteria: Dict
    recommended_persona_types: List[str]


_stage_db: Dict[str, MethodologyStage] = {}
_initialized: bool = False


def _initialize_default_stages() -> None:
    global _initialized
    if _initialized:
        return
    stages = [
        MethodologyStage(
            id="mm_aip_awareness",
            framework="AIPL",
            stage="AWARENESS",
            stage_name="认知期",
            content_template={
                "hook": {"type": "pain_point_resonance", "formula": "亲身经历+具体场景+情绪共鸣"},
                "body": {"section_1": {"type": "phenomenon_description", "content": "描述观察到的现象"}},
                "cta": {"type": "engagement_question", "formula": "互动提问"},
                "disclaimer": {"required": False},
            },
            kpi_targets={"ces": 15, "exposure": 500, "like_rate": 0.02, "comment_rate": 0.03},
            compliance_tags=["经验分享"],
            forbidden_elements=["治愈", "根治", "推荐", "用法用量"],
            stage_transition_criteria={"to_next_stage": "INTEREST", "condition": "平均CES≥15且评论率≥3%"},
            recommended_persona_types=["新手猫妈", "多宠家庭"],
        ),
        MethodologyStage(
            id="mm_aip_interest",
            framework="AIPL",
            stage="INTEREST",
            stage_name="兴趣期",
            content_template={
                "hook": {"type": "pain_point_resonance", "formula": "亲身经历+具体场景+情绪共鸣"},
                "body": {
                    "section_1": {"type": "mistake_process", "content": "描述2-3个错误尝试"},
                    "section_2": {"type": "turning_point", "content": "转折点发现"},
                    "section_3": {"type": "solution_sharing", "content": "非诊断性经验分享"},
                },
                "cta": {"type": "soft_guidance", "formula": "引导私信"},
                "disclaimer": {"required": True, "template": "以上仅为个人养宠经验分享，不构成医疗建议。"},
            },
            kpi_targets={"ces": 40, "exposure": 5000, "like_rate": 0.03, "comment_rate": 0.05},
            compliance_tags=["经验分享", "个人感受"],
            forbidden_elements=["治愈", "根治", "推荐", "用法用量", "医生证明"],
            stage_transition_criteria={"to_next_stage": "PURCHASE", "condition": "平均CES≥40且私信咨询≥20条/周"},
            recommended_persona_types=["资深铲屎官", "多宠家庭", "医院常客"],
        ),
        MethodologyStage(
            id="mm_aip_purchase",
            framework="AIPL",
            stage="PURCHASE",
            stage_name="购买期",
            content_template={
                "hook": {"type": "result_oriented", "formula": "结果导向"},
                "body": {
                    "section_1": {"type": "problem_review", "content": "问题回顾"},
                    "section_2": {"type": "solution_sharing", "content": "经验分享"},
                    "section_3": {"type": "effect_display", "content": "效果展示"},
                },
                "cta": {"type": "soft_guidance", "formula": "温和CTA"},
                "disclaimer": {"required": True, "template": "以上仅为个人养宠经验分享，不构成医疗建议。如有严重症状请及时就医。"},
            },
            kpi_targets={"ces": 80, "exposure": 10000, "like_rate": 0.04, "comment_rate": 0.06},
            compliance_tags=["经验分享", "个人感受", "非广告"],
            forbidden_elements=["治愈", "根治", "推荐", "用法用量"],
            stage_transition_criteria={"to_next_stage": "LOYALTY", "condition": "私信转化率≥10%"},
            recommended_persona_types=["医院常客", "多宠家庭"],
        ),
        MethodologyStage(
            id="mm_aip_loyalty",
            framework="AIPL",
            stage="LOYALTY",
            stage_name="忠诚期",
            content_template={
                "hook": {"type": "daily_sharing", "formula": "日常分享"},
                "body": {"section_1": {"type": "long_term_tracking", "content": "长期跟踪"}},
                "cta": {"type": "community_interaction", "formula": "社群互动"},
                "disclaimer": {"required": False},
            },
            kpi_targets={"ces": 100, "exposure": 8000, "like_rate": 0.05, "comment_rate": 0.08},
            compliance_tags=["知识科普", "日常分享"],
            forbidden_elements=[],
            stage_transition_criteria={},
            recommended_persona_types=["专家型人设"],
        ),
    ]
    for s in stages:
        _stage_db[s.id] = s
    _initialized = True


def list_methodologies() -> List[Dict]:
    _initialize_default_stages()
    from src.services.methodology_5a_service import _initialize_5a_stages, _5a_stage_db
    _initialize_5a_stages()
    
    frameworks = {}
    # Add AIPL stages
    for s in _stage_db.values():
        frameworks.setdefault(s.framework, []).append(s.stage)
    # Add 5A stages
    for s in _5a_stage_db.values():
        frameworks.setdefault(s.framework, []).append(s.stage)
    return [{"framework": k, "stages": v} for k, v in frameworks.items()]


def list_stages(framework: Optional[str] = None) -> List[MethodologyStage]:
    _initialize_default_stages()
    from src.services.methodology_5a_service import _initialize_5a_stages, _5a_stage_db
    _initialize_5a_stages()
    
    stages = list(_stage_db.values())
    
    # Add 5A stages by converting to compatible format
    if not framework or framework == "5A":
        for s5a in _5a_stage_db.values():
            # Create a compatible MethodologyStage from 5A stage
            compatible_stage = MethodologyStage(
                id=s5a.id,
                framework=s5a.framework,
                stage=s5a.stage,
                stage_name=s5a.stage_name,
                content_template=s5a.content_template,
                kpi_targets=s5a.kpi_targets,
                compliance_tags=s5a.compliance_tags,
                forbidden_elements=s5a.forbidden_elements,
                stage_transition_criteria=s5a.stage_transition_criteria,
                recommended_persona_types=s5a.recommended_persona_types,
            )
            stages.append(compatible_stage)
    
    if framework:
        stages = [s for s in stages if s.framework == framework]
    return stages


def list_stages_by_framework(framework_id: str) -> List[MethodologyStage]:
    _initialize_default_stages()
    from src.services.methodology_5a_service import _initialize_5a_stages, _5a_stage_db
    _initialize_5a_stages()
    
    aipl_stages = [s for s in _stage_db.values() if s.framework == framework_id]
    
    if framework_id == "5A":
        # Convert 5A stages to compatible format
        for s5a in _5a_stage_db.values():
            compatible_stage = MethodologyStage(
                id=s5a.id,
                framework=s5a.framework,
                stage=s5a.stage,
                stage_name=s5a.stage_name,
                content_template=s5a.content_template,
                kpi_targets=s5a.kpi_targets,
                compliance_tags=s5a.compliance_tags,
                forbidden_elements=s5a.forbidden_elements,
                stage_transition_criteria=s5a.stage_transition_criteria,
                recommended_persona_types=s5a.recommended_persona_types,
            )
            aipl_stages.append(compatible_stage)
    
    return aipl_stages


def get_stage(stage_id: str) -> Optional[MethodologyStage]:
    _initialize_default_stages()
    stage = _stage_db.get(stage_id)
    if stage:
        return stage
    
    # Try 5A stages
    from src.services.methodology_5a_service import _initialize_5a_stages, _5a_stage_db
    _initialize_5a_stages()
    s5a = _5a_stage_db.get(stage_id)
    if s5a:
        return MethodologyStage(
            id=s5a.id,
            framework=s5a.framework,
            stage=s5a.stage,
            stage_name=s5a.stage_name,
            content_template=s5a.content_template,
            kpi_targets=s5a.kpi_targets,
            compliance_tags=s5a.compliance_tags,
            forbidden_elements=s5a.forbidden_elements,
            stage_transition_criteria=s5a.stage_transition_criteria,
            recommended_persona_types=s5a.recommended_persona_types,
        )
    return None


def get_stage_template(stage_id: str) -> Optional[dict]:
    _initialize_default_stages()
    stage = _stage_db.get(stage_id)
    if stage:
        return stage.content_template
    
    # Try 5A stages
    from src.services.methodology_5a_service import _initialize_5a_stages, _5a_stage_db
    _initialize_5a_stages()
    s5a = _5a_stage_db.get(stage_id)
    if s5a:
        return s5a.content_template
    return None


def evaluate_content(stage_id: str, body: str) -> Dict:
    """Evaluate if content body matches stage template requirements."""
    _initialize_default_stages()
    stage = _stage_db.get(stage_id)
    if not stage:
        return {"missing_fields": ["stage_not_found"], "score": 0}

    missing_fields = []
    score = 100
    text = body.strip()

    # Check hook: body should have an opening hook (sufficient length)
    if len(text) < 10:
        missing_fields.append("hook")
        score -= 15

    # Check body: should have meaningful content beyond a minimal hook
    if len(text) < 50:
        missing_fields.append("body")
        score -= 20

    # Check CTA: body should contain call-to-action indicators
    cta_keywords = ["评论", "私信", "点赞", "关注", "收藏", "互动", "留言", "告诉我", "码住", "行动起来", "试试", "分享"]
    if not any(kw in text for kw in cta_keywords):
        missing_fields.append("cta")
        score -= 10

    # Check disclaimer if required
    disclaimer_cfg = stage.content_template.get("disclaimer", {})
    if disclaimer_cfg.get("required", False):
        disclaimer_template = disclaimer_cfg.get("template", "")
        if disclaimer_template and disclaimer_template[:10] not in text:
            missing_fields.append("disclaimer")
            score -= 10

    # Check forbidden elements
    for elem in stage.forbidden_elements:
        if elem in text:
            score -= 20

    return {
        "missing_fields": missing_fields,
        "score": max(0, score),
    }


def clear_methodologies() -> None:
    _stage_db.clear()
    global _initialized
    _initialized = False
