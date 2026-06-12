"""PersonaPool — 人设资产全生命周期管理.

MVP: In-memory persona storage with full schema (identity/pet/owner/voice/scenes/success_patterns).
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Persona:
    id: str
    name: str
    status: str  # active, draft, archived
    identity_core: Dict  # nickname_pattern, bio, gender, age_range, location
    pet_profile: Dict  # pet_type, breed, age, health_conditions, personality
    owner_profile: Dict  # owner_type, housing, income_level, lifestyle
    content_voice: Dict  # tone, formality_level, emoji_frequency, emoji_style, catchphrases, sentence_length_preference
    life_scenes: List[Dict]  # scene_name, description, frequency, photo_style
    success_patterns: List[Dict]  # pattern_name, trigger_condition, content_formula, avg_ces
    usage_stats: Dict  # use_count, avg_ces, last_used
    created_at: str = ""
    updated_at: str = ""


_persona_db: Dict[str, Persona] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_personas():
    """Seed default personas for MVP."""
    if _persona_db:
        return
    defaults = [
        {
            "id": "p1",
            "name": "温柔铲屎官",
            "status": "active",
            "identity_core": {"nickname_pattern": "XX的喵", "bio": "家有毛孩，分享日常", "gender": "female", "age_range": "25-30", "location": "上海"},
            "pet_profile": {"pet_type": "cat", "breed": "英短", "age": 2, "health_conditions": [], "personality": "粘人、胆小"},
            "owner_profile": {"owner_type": "独居青年", "housing": "租房", "income_level": "中等", "lifestyle": "上班族"},
            "content_voice": {"tone": "亲切、口语化、爱用emoji", "formality_level": "casual", "emoji_frequency": "high", "emoji_style": "可爱", "catchphrases": ["喵~", "毛孩子", "主子"], "sentence_length_preference": "短句"},
            "life_scenes": [{"scene_name": "日常撸猫", "description": "下班回家和猫咪互动", "frequency": "daily", "photo_style": "居家暖色调"}],
            "success_patterns": [],
            "usage_stats": {"use_count": 0, "avg_ces": 0.0, "last_used": ""},
        },
        {
            "id": "p2",
            "name": "专业兽医",
            "status": "active",
            "identity_core": {"nickname_pattern": "Dr.XX", "bio": "10年临床兽医，科学养宠", "gender": "male", "age_range": "35-45", "location": "北京"},
            "pet_profile": {"pet_type": "dog", "breed": "金毛", "age": 5, "health_conditions": [], "personality": "活泼、友善"},
            "owner_profile": {"owner_type": "专业人士", "housing": "自有房", "income_level": "高", "lifestyle": "工作狂"},
            "content_voice": {"tone": "严谨、科普、数据支撑", "formality_level": "formal", "emoji_frequency": "low", "emoji_style": "简洁", "catchphrases": ["研究表明", "建议", "注意"], "sentence_length_preference": "长句"},
            "life_scenes": [{"scene_name": "诊所日常", "description": "分享病例和养宠知识", "frequency": "weekly", "photo_style": "专业白底"}],
            "success_patterns": [],
            "usage_stats": {"use_count": 0, "avg_ces": 0.0, "last_used": ""},
        },
        {
            "id": "p3",
            "name": "生活博主",
            "status": "active",
            "identity_core": {"nickname_pattern": "XX和毛孩子", "bio": "记录和毛孩子的每一天", "gender": "female", "age_range": "28-35", "location": "杭州"},
            "pet_profile": {"pet_type": "cat", "breed": "布偶", "age": 1, "health_conditions": [], "personality": "高冷、优雅"},
            "owner_profile": {"owner_type": "小家庭", "housing": "自有房", "income_level": "中高", "lifestyle": "精致生活"},
            "content_voice": {"tone": "轻松、分享式、带个人故事", "formality_level": "semi-formal", "emoji_frequency": "medium", "emoji_style": "生活化", "catchphrases": ["分享一下", "最近发现", "实测"], "sentence_length_preference": "中等"},
            "life_scenes": [{"scene_name": "周末探店", "description": "带宠物去宠物友好店", "frequency": "weekly", "photo_style": "ins风"}],
            "success_patterns": [],
            "usage_stats": {"use_count": 0, "avg_ces": 0.0, "last_used": ""},
        },
        {
            "id": "p4",
            "name": "省钱达人",
            "status": "active",
            "identity_core": {"nickname_pattern": "会省钱的XX", "bio": "精打细算养宠不花冤枉钱", "gender": "female", "age_range": "22-28", "location": "成都"},
            "pet_profile": {"pet_type": "dog", "breed": "泰迪", "age": 3, "health_conditions": [], "personality": "聪明、活泼"},
            "owner_profile": {"owner_type": "学生/初入职场", "housing": "租房", "income_level": "中等偏下", "lifestyle": "节俭"},
            "content_voice": {"tone": "直接、实用、列清单", "formality_level": "casual", "emoji_frequency": "medium", "emoji_style": "实用", "catchphrases": ["省钱攻略", "性价比", "必囤"], "sentence_length_preference": "短句"},
            "life_scenes": [{"scene_name": "好物测评", "description": "测评平价宠物用品", "frequency": "weekly", "photo_style": "对比图"}],
            "success_patterns": [],
            "usage_stats": {"use_count": 0, "avg_ces": 0.0, "last_used": ""},
        },
    ]
    for data in defaults:
        _persona_db[data["id"]] = Persona(
            id=data["id"],
            name=data["name"],
            status=data["status"],
            identity_core=data["identity_core"],
            pet_profile=data["pet_profile"],
            owner_profile=data["owner_profile"],
            content_voice=data["content_voice"],
            life_scenes=data["life_scenes"],
            success_patterns=data["success_patterns"],
            usage_stats=data["usage_stats"],
            created_at=_now(),
            updated_at=_now(),
        )


_seed_personas()


def create_persona(data: Dict) -> Persona:
    persona_id = data.get("id") or secrets.token_urlsafe(12)
    persona = Persona(
        id=persona_id,
        name=data.get("name", "未命名人设"),
        status=data.get("status", "draft"),
        identity_core=data.get("identity_core", {}),
        pet_profile=data.get("pet_profile", {}),
        owner_profile=data.get("owner_profile", {}),
        content_voice=data.get("content_voice", {}),
        life_scenes=data.get("life_scenes", []),
        success_patterns=data.get("success_patterns", []),
        usage_stats=data.get("usage_stats", {"use_count": 0, "avg_ces": 0.0, "last_used": ""}),
        created_at=_now(),
        updated_at=_now(),
    )
    _persona_db[persona_id] = persona
    return persona


def get_persona(persona_id: str) -> Optional[Persona]:
    return _persona_db.get(persona_id)


def list_personas(status: Optional[str] = None) -> List[Persona]:
    personas = list(_persona_db.values())
    if status:
        personas = [p for p in personas if p.status == status]
    return sorted(personas, key=lambda p: p.created_at, reverse=True)


def update_persona(persona_id: str, data: Dict) -> Optional[Persona]:
    persona = _persona_db.get(persona_id)
    if not persona:
        return None
    for key, value in data.items():
        if hasattr(persona, key) and key not in ("id", "created_at"):
            setattr(persona, key, value)
    persona.updated_at = _now()
    return persona


def clone_persona(source_id: str, overrides: Optional[Dict] = None) -> Optional[Persona]:
    source = _persona_db.get(source_id)
    if not source:
        return None
    overrides = overrides or {}
    new_data = {
        "name": overrides.get("name", f"{source.name} (克隆)"),
        "status": "draft",
        "identity_core": {**source.identity_core, **overrides.get("identity_core", {})},
        "pet_profile": {**source.pet_profile, **overrides.get("pet_profile", {})},
        "owner_profile": {**source.owner_profile, **overrides.get("owner_profile", {})},
        "content_voice": {**source.content_voice, **overrides.get("content_voice", {})},
        "life_scenes": overrides.get("life_scenes", source.life_scenes.copy()),
        "success_patterns": overrides.get("success_patterns", source.success_patterns.copy()),
        "usage_stats": {"use_count": 0, "avg_ces": 0.0, "last_used": ""},
    }
    return create_persona(new_data)


def delete_persona(persona_id: str) -> bool:
    if persona_id in _persona_db:
        del _persona_db[persona_id]
        return True
    return False


class PersonaMatcher:
    """Match target audience to recommended persona profiles."""

    @staticmethod
    def recommend(target_audience: Dict) -> List[Dict]:
        """Recommend personas based on target audience attributes."""
        recommendations = []
        pet_type = target_audience.get("pet_type", "")
        owner_type = target_audience.get("owner_type", "")
        budget_level = target_audience.get("budget_level", "")

        for persona in _persona_db.values():
            score = 0
            if pet_type and persona.pet_profile.get("pet_type") == pet_type:
                score += 40
            if owner_type and persona.owner_profile.get("owner_type") == owner_type:
                score += 30
            if budget_level and persona.owner_profile.get("income_level") == budget_level:
                score += 20
            if persona.usage_stats.get("avg_ces", 0) > 35:
                score += 10
            if score > 0:
                recommendations.append({
                    "persona_id": persona.id,
                    "name": persona.name,
                    "match_score": min(score, 100),
                    "reason": f"匹配度 {score}%",
                })

        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        return recommendations


def clear_persona_pool() -> None:
    _persona_db.clear()
