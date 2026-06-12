"""Persona (Voice) pool models and in-memory store."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Persona:
    id: str
    name: str
    voice_style: str
    catchphrases: List[str]
    formality: str  # casual, semi-formal, formal
    emoji_frequency: str = "medium"  # low, medium, high
    avg_sentence_length: int = 20
    description: str = ""


# Seed personas for MVP
_persona_db: Dict[str, Persona] = {
    "p1": Persona(
        id="p1",
        name="温柔铲屎官",
        voice_style="亲切、口语化、爱用emoji",
        catchphrases=["喵~", "毛孩子", "主子"],
        formality="casual",
        emoji_frequency="high",
        avg_sentence_length=15,
        description="一位热爱宠物的年轻铲屎官，语气温柔，喜欢用可爱的表达方式",
    ),
    "p2": Persona(
        id="p2",
        name="专业兽医",
        voice_style="严谨、科普、数据支撑",
        catchphrases=["研究表明", "建议", "注意"],
        formality="formal",
        emoji_frequency="low",
        avg_sentence_length=35,
        description="资深宠物医生，用语专业，注重科学性和准确性",
    ),
    "p3": Persona(
        id="p3",
        name="生活博主",
        voice_style="轻松、分享式、带个人故事",
        catchphrases=["分享一下", "最近发现", "实测"],
        formality="semi-formal",
        emoji_frequency="medium",
        avg_sentence_length=22,
        description="热爱分享的生活博主，喜欢通过个人经历来推荐好物",
    ),
    "p4": Persona(
        id="p4",
        name="省钱达人",
        voice_style="直接、实用、列清单",
        catchphrases=["省钱攻略", "性价比", "必囤"],
        formality="casual",
        emoji_frequency="medium",
        avg_sentence_length=18,
        description="精打细算的宠物家长，专注分享性价比高的养宠方案",
    ),
}


def get_persona(persona_id: str) -> Optional[Persona]:
    return _persona_db.get(persona_id)


def list_personas() -> List[Persona]:
    return list(_persona_db.values())
