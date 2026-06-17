"""MarketingMethodology 5A — 5A methodology engine with AIPL migration support.

Manages 5A stage templates (Aware, Appeal, Ask, Act, Advocate),
AIPL→5A mapping, and audience segment recommendations.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class MethodologyStage5A:
    id: str
    framework: str
    stage: str
    stage_name: str
    stage_order: int
    content_template: Dict
    kpi_targets: Dict
    compliance_tags: List[str]
    forbidden_elements: List[str]
    stage_transition_criteria: Dict
    recommended_persona_types: List[str]
    audience_segments: List[Dict]


# In-memory store for 5A stages
_5a_stage_db: Dict[str, MethodologyStage5A] = {}
_initialized_5a: bool = False

# AIPL to 5A mapping
AIPL_TO_5A = {
    "AWARENESS": "AWARE",
    "INTEREST": "APPEAL",
    "PURCHASE": "ACT",
    "LOYALTY": "ADVOCATE",
}

# 5A to AIPL mapping (ASK maps to INTEREST)
FIVE_A_TO_AIPL = {
    "AWARE": "AWARENESS",
    "APPEAL": "INTEREST",
    "ASK": "INTEREST",
    "ACT": "PURCHASE",
    "ADVOCATE": "LOYALTY",
}


def _initialize_5a_stages() -> None:
    global _initialized_5a
    if _initialized_5a:
        return

    stages = [
        MethodologyStage5A(
            id="mm_5a_aware",
            framework="5A",
            stage="AWARE",
            stage_name="认知期",
            stage_order=1,
            content_template={
                "hook": {"type": "attention_grab", "formula": "痛点共鸣+场景代入"},
                "body": {
                    "section_1": {"type": "problem_identification", "content": "问题识别与描述"},
                    "section_2": {"type": "scenario_building", "content": "场景构建引发共鸣"},
                },
                "cta": {"type": "engagement_question", "formula": "互动提问引导参与"},
                "disclaimer": {"required": False},
            },
            kpi_targets={"impression": 1000, "ctr": 0.03, "engagement_rate": 0.02},
            compliance_tags=["知识科普", "经验分享"],
            forbidden_elements=["治愈", "根治", "特效药", "立即见效"],
            stage_transition_criteria={"to_next_stage": "APPEAL", "condition": "点击率≥3%且互动率≥2%"},
            recommended_persona_types=["新手铲屎官", "焦虑型家长"],
            audience_segments=[
                {"segment_id": "seg_new_pet_owner", "name": "新手养宠人群", "characteristics": ["首次养宠", "经验不足", "容易焦虑"]},
                {"segment_id": "seg_problem_seeker", "name": "问题求解者", "characteristics": ["主动搜索", "痛点明确", "高意向"]},
            ],
        ),
        MethodologyStage5A(
            id="mm_5a_appeal",
            framework="5A",
            stage="APPEAL",
            stage_name="吸引期",
            stage_order=2,
            content_template={
                "hook": {"type": "curiosity_gap", "formula": "悬念设置+价值承诺"},
                "body": {
                    "section_1": {"type": "journey_narrative", "content": "养宠历程叙述"},
                    "section_2": {"type": "struggle_sharing", "content": "困难与尝试分享"},
                    "section_3": {"type": "insight_reveal", "content": "关键发现/转折点"},
                },
                "cta": {"type": "soft_guidance", "formula": "引导关注/收藏"},
                "disclaimer": {"required": True, "template": "以上仅为个人养宠经验分享，不构成专业医疗建议。"},
            },
            kpi_targets={"impression": 5000, "ctr": 0.05, "save_rate": 0.03, "follow_rate": 0.02},
            compliance_tags=["经验分享", "个人感受"],
            forbidden_elements=["治愈", "根治", "医生推荐", "临床验证"],
            stage_transition_criteria={"to_next_stage": "ASK", "condition": "收藏率≥3%或关注率≥2%"},
            recommended_persona_types=["经验分享者", "真实用户"],
            audience_segments=[
                {"segment_id": "seg_engaged_viewer", "name": "高互动观众", "characteristics": ["喜欢互动", "愿意收藏", "信任建立中"]},
                {"segment_id": "seg_solution_explorer", "name": "方案探索者", "characteristics": ["对比多个方案", "理性决策", "高留存"]},
            ],
        ),
        MethodologyStage5A(
            id="mm_5a_ask",
            framework="5A",
            stage="ASK",
            stage_name="问询期",
            stage_order=3,
            content_template={
                "hook": {"type": "question_driven", "formula": "问题引导+互动邀请"},
                "body": {
                    "section_1": {"type": "experience_detail", "content": "详细经验描述"},
                    "section_2": {"type": "comparison_analysis", "content": "多方案对比分析"},
                    "section_3": {"type": "consideration_factors", "content": "选择考量因素"},
                },
                "cta": {"type": "consultation_invite", "formula": "邀请私信咨询"},
                "disclaimer": {"required": True, "template": "以上仅为个人养宠经验分享，不构成医疗建议。如有严重症状请及时就医。"},
            },
            kpi_targets={"impression": 8000, "comment_rate": 0.04, "private_msg_rate": 0.02, "response_time_hours": 4},
            compliance_tags=["经验分享", "问答互动"],
            forbidden_elements=["处方", "具体用量", "替代就医", "包治百病"],
            stage_transition_criteria={"to_next_stage": "ACT", "condition": "私信咨询率≥2%且回复及时"},
            recommended_persona_types=["资深铲屎官", "经验分享者"],
            audience_segments=[
                {"segment_id": "seg_question_asker", "name": "主动提问者", "characteristics": ["信任度提升", "有具体问题", "咨询意向强"]},
                {"segment_id": "seg_comparison_shopper", "name": "比价选购者", "characteristics": ["多方案对比", "价格敏感", "决策犹豫"]},
            ],
        ),
        MethodologyStage5A(
            id="mm_5a_act",
            framework="5A",
            stage="ACT",
            stage_name="行动期",
            stage_order=4,
            content_template={
                "hook": {"type": "result_showcase", "formula": "成果展示+效果验证"},
                "body": {
                    "section_1": {"type": "decision_process", "content": "决策过程回顾"},
                    "section_2": {"type": "implementation_detail", "content": "实施细节分享"},
                    "section_3": {"type": "outcome_demonstration", "content": "效果展示与数据"},
                },
                "cta": {"type": "purchase_guidance", "formula": "温和购买引导"},
                "disclaimer": {"required": True, "template": "以上仅为个人养宠经验分享，不构成医疗建议。购买前请咨询专业人士。"},
            },
            kpi_targets={"impression": 10000, "conversion_rate": 0.03, "purchase_intent": 0.05},
            compliance_tags=["经验分享", "购买决策"],
            forbidden_elements=["疗效保证", "100%有效", "医生同款", "医院专用"],
            stage_transition_criteria={"to_next_stage": "ADVOCATE", "condition": "转化率≥3%且满意度≥4.5"},
            recommended_persona_types=["医院常客", "多宠家庭"],
            audience_segments=[
                {"segment_id": "seg_purchase_ready", "name": "购买准备者", "characteristics": ["决策成熟", "价格接受度高", "立即购买意向"]},
                {"segment_id": "seg_repeat_buyer", "name": "复购用户", "characteristics": ["品牌忠诚", "长期需求", "口碑传播潜力"]},
            ],
        ),
        MethodologyStage5A(
            id="mm_5a_advocate",
            framework="5A",
            stage="ADVOCATE",
            stage_name="拥护期",
            stage_order=5,
            content_template={
                "hook": {"type": "advocacy_story", "formula": "长期陪伴故事"},
                "body": {
                    "section_1": {"type": "long_term_followup", "content": "长期跟踪记录"},
                    "section_2": {"type": "community_value", "content": "社群价值分享"},
                    "section_3": {"type": "knowledge_contribution", "content": "知识经验沉淀"},
                },
                "cta": {"type": "community_engagement", "formula": "社群互动邀请"},
                "disclaimer": {"required": False},
            },
            kpi_targets={"impression": 8000, "referral_rate": 0.05, "ugc_generation": 0.03, "community_activity": 0.08},
            compliance_tags=["知识科普", "社群共建"],
            forbidden_elements=[],
            stage_transition_criteria={},
            recommended_persona_types=["专家型人设", "KOC型用户"],
            audience_segments=[
                {"segment_id": "seg_brand_advocate", "name": "品牌拥护者", "characteristics": ["高度信任", "主动推荐", "口碑传播"]},
                {"segment_id": "seg_community_leader", "name": "社群领袖", "characteristics": ["影响力强", "内容创作", "带动力高"]},
            ],
        ),
    ]

    for s in stages:
        _5a_stage_db[s.id] = s
    _initialized_5a = True


def list_5a_stages() -> List[MethodologyStage5A]:
    _initialize_5a_stages()
    return list(_5a_stage_db.values())


def get_5a_stage(stage_id: str) -> Optional[MethodologyStage5A]:
    _initialize_5a_stages()
    return _5a_stage_db.get(stage_id)


def get_5a_stage_template(stage_id: str) -> Optional[Dict]:
    _initialize_5a_stages()
    stage = _5a_stage_db.get(stage_id)
    if not stage:
        return None
    return stage.content_template


def get_stage_audience_segments(stage_id: str) -> Optional[List[Dict]]:
    _initialize_5a_stages()
    stage = _5a_stage_db.get(stage_id)
    if not stage:
        return None
    return stage.audience_segments


def get_stage_persona_recommendations(stage_id: str) -> Optional[List[str]]:
    _initialize_5a_stages()
    stage = _5a_stage_db.get(stage_id)
    if not stage:
        return None
    return stage.recommended_persona_types


def map_aipl_to_5a(aipl_stage: str) -> Optional[Tuple[str, str]]:
    """Map AIPL stage to 5A stage."""
    aipl_upper = aipl_stage.upper()
    five_a = AIPL_TO_5A.get(aipl_upper)
    if not five_a:
        return None
    return five_a, f"{aipl_stage} -> {five_a}"


def map_5a_to_aipl(five_a_stage: str) -> Optional[Tuple[str, str]]:
    """Map 5A stage to AIPL stage."""
    five_a_upper = five_a_stage.upper()
    aipl = FIVE_A_TO_AIPL.get(five_a_upper)
    if not aipl:
        return None
    return aipl, f"{five_a_stage} -> {aipl}"


def evaluate_5a_content(stage_id: str, body: str) -> Dict:
    """Evaluate if content matches 5A stage requirements."""
    _initialize_5a_stages()
    stage = _5a_stage_db.get(stage_id)
    if not stage:
        return {"score": 0, "stage_match": None, "missing_elements": ["stage_not_found"]}

    score = 100
    missing = []
    forbidden_found = []

    text = body.strip()

    # Check hook quality
    if len(text) < 20:
        missing.append("hook_insufficient")
        score -= 15

    # Check body depth
    if len(text) < 80:
        missing.append("body_insufficient")
        score -= 20

    # Check CTA presence
    cta_keywords = ["评论", "私信", "点赞", "关注", "收藏", "互动", "留言", "告诉我", "码住", "行动起来", "试试", "分享", "咨询", "了解"]
    if not any(kw in text for kw in cta_keywords):
        missing.append("cta_missing")
        score -= 10

    # Check disclaimer if required
    disclaimer_cfg = stage.content_template.get("disclaimer", {})
    if disclaimer_cfg.get("required", False):
        disclaimer_template = disclaimer_cfg.get("template", "")
        if disclaimer_template and disclaimer_template[:10] not in text:
            missing.append("disclaimer_missing")
            score -= 10

    # Check forbidden elements
    for elem in stage.forbidden_elements:
        if elem in text:
            forbidden_found.append(elem)
            score -= 25

    return {
        "score": max(0, score),
        "stage_match": stage.stage,
        "missing_elements": missing,
        "forbidden_found": forbidden_found,
    }


def clear_5a_methodologies() -> None:
    _5a_stage_db.clear()
    global _initialized_5a
    _initialized_5a = False
