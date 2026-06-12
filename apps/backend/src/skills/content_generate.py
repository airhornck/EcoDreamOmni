"""Content Generate Skill — v4.0 Phase 8 P8-2.

基于 Persona + BrandKnowledge + 结构模板生成正文。
MVP: 模板拼接 + 关键词填充，不调用真实 LLM（预留 LLM Hub 接口）。

架构红线:
- §2.1 Agent 禁 DB: 所有数据通过 context 注入
- §2.5 LLMHub 路由: requires_llm=True，MVP 用模板回退，生产环境接入 LLM Hub
- §3.1 六层 Prompt: 输出包含六层结构标记，便于后续 Prompt 工程优化
"""

import random
from typing import Any, Dict, List

SKILL_ID = "content_generate"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = True
LLM_MODEL_PREFERENCE = "qwen-turbo"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string", "description": "内容主题"},
        "persona_id": {"type": "string", "description": "人设ID"},
        "persona_name": {"type": "string", "description": "人设名称（如 省钱狗爸）"},
        "persona_tone": {"type": "string", "description": "语气风格: casual/professional/humorous/empathetic"},
        "brand_knowledge": {"type": "array", "items": {"type": "string"}, "description": "品牌知识片段列表"},
        "structure_template": {"type": "object", "description": "结构模板: {hook_pattern, body_structure, cta_pattern}"},
        "keywords": {"type": "array", "items": {"type": "string"}, "description": "关键词列表"},
        "platform_id": {"type": "string", "description": "平台标识"},
        "word_count_target": {"type": "integer", "description": "目标字数", "default": 500},
    },
    "required": ["topic", "persona_name"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "word_count": {"type": "integer"},
        "prompt_layers": {"type": "object"},
        "generation_method": {"type": "string"},
    },
}

# MVP templates by platform
_HOOK_TEMPLATES: Dict[str, List[str]] = {
    "xhs": [
        "姐妹们！{topic}这件事我真的踩过太多坑了😭",
        "关于{topic}，养宠3年的人想说几句实话",
        "{persona_name}的{topic}攻略｜新手必看",
        "我家毛孩子{topic}的经历，分享给大家",
    ],
    "douyin": [
        "{topic}到底怎么选？看完这条视频你就懂了",
        "{persona_name}教你{topic}，简单3步搞定",
        "关于{topic}，90%的人都不知道的真相",
    ],
    "bilibili": [
        "【干货】{topic}全攻略｜{persona_name}经验分享",
        "{topic}深度解析：从入门到精通",
    ],
    "wechat_official": [
        "{topic}：一份给养宠人的完整指南",
        "{persona_name}聊{topic}：这些知识你必须知道",
    ],
}

_BODY_TEMPLATES: Dict[str, List[str]] = {
    "casual": [
        "先说说我自己的情况吧。{persona_name}家有一只{pet_type}，之前{topic}的时候真的走了不少弯路。",
        "第一点，{point1}。这个真的是血泪教训，当初我就是没注意，结果{consequence1}。",
        "第二点，{point2}。这里要划重点了！{detail2}",
        "最后总结一下，{topic}最关键的是{key_takeaway}。希望{persona_name}的经验能帮到你！",
    ],
    "professional": [
        "作为{persona_name}，在{topic}方面积累了一些专业知识，今天系统地整理分享给大家。",
        "一、{topic}的核心原理\n{point1}。从专业角度分析，{detail1}",
        "二、实操建议\n{point2}。具体而言，{detail2}",
        "三、常见误区\n{key_takeaway}。很多养宠人容易忽略这一点，{consequence1}",
        "以上就是{persona_name}关于{topic}的专业分享，如有疑问欢迎留言交流。",
    ],
    "humorous": [
        "各位铲屎官好，{persona_name}又来吐槽了！关于{topic}，我家那位主子的故事能说三天三夜。",
        "首先，{point1}。别问我怎么知道的，问就是{consequence1}😂",
        "然后，{point2}。记住这句话：{detail2}",
        "总结：{key_takeaway}。如果这都能翻车，那{persona_name}也救不了你了哈哈",
    ],
    "empathetic": [
        "我知道很多养宠人在{topic}这件事上都很焦虑，{persona_name}完全理解这种心情。",
        "其实{point1}。你不是一个人，{persona_name}当初也{consequence1}。",
        "关于{point2}，想跟你说：{detail2}",
        "最后想告诉你，{key_takeaway}。你已经是一个很好的铲屎官了，相信自己❤️",
    ],
}

_CTA_TEMPLATES: Dict[str, List[str]] = {
    "xhs": [
        "你们家{pet_type}{topic}有什么心得？评论区聊聊👇",
        "觉得有用的话给个❤️和⭐，{persona_name}会持续更新养宠干货",
        "关注{persona_name}，一起科学养宠不踩坑",
    ],
    "douyin": [
        "点赞关注，{persona_name}带你避开养宠所有坑",
        "评论区说出你的{topic}困惑，下期视频安排",
    ],
    "bilibili": [
        "一键三连支持{persona_name}，更多养宠干货持续更新",
        "评论区留下你的{topic}问题，下期详细解答",
    ],
    "wechat_official": [
        "转发给身边的养宠朋友，一起科学养宠",
        "关注{persona_name}，回复「{topic}」获取完整资料包",
    ],
}

_HASHTAG_POOLS: Dict[str, List[str]] = {
    "宠物": ["新手养猫", "养宠攻略", "科学养宠", "铲屎官日常", "萌宠"],
    "驱虫": ["猫咪驱虫", "狗狗驱虫", "体内驱虫", "体外驱虫", "驱虫药推荐"],
    "疫苗": ["猫三联", "狂犬疫苗", "疫苗接种", "养猫必看", "宠物健康"],
    "饮食": ["猫粮推荐", "自制猫饭", "宠物 nutrition", "猫咪饮食", "养猫好物"],
    "护理": ["猫咪洗澡", "毛发护理", "剪指甲", "宠物美容", "养猫经验"],
}


def _generate_title(topic: str, persona_name: str, platform_id: str) -> str:
    templates = _HOOK_TEMPLATES.get(platform_id, _HOOK_TEMPLATES["xhs"])
    template = random.choice(templates)
    return template.format(topic=topic, persona_name=persona_name)


def _generate_body(
    topic: str,
    persona_name: str,
    persona_tone: str,
    brand_knowledge: List[str],
    keywords: List[str],
    platform_id: str,
) -> str:
    templates = _BODY_TEMPLATES.get(persona_tone, _BODY_TEMPLATES["casual"])

    # Build content points from brand knowledge and keywords
    points = brand_knowledge[:2] if brand_knowledge else [f"{topic}的选择很重要", f"{topic}的时机要把握好"]
    detail_points = keywords[:3] if keywords else ["品质", "安全", "性价比"]

    pet_type = "猫咪" if "猫" in topic else "狗狗" if "狗" in topic else "毛孩子"

    paragraphs = []
    for template in templates:
        para = template.format(
            topic=topic,
            persona_name=persona_name,
            pet_type=pet_type,
            point1=points[0] if points else f"{topic}的第一步",
            point2=points[1] if len(points) > 1 else f"{topic}的注意事项",
            detail1=f"建议关注{detail_points[0] if detail_points else '品质'}。",
            detail2=f"重点看{', '.join(detail_points[:2]) if detail_points else '口碑和评价'}。",
            key_takeaway=f"{topic}要综合考虑品质和实际需求",
            consequence1="花了不少冤枉钱" if persona_tone == "casual" else "影响了效果",
        )
        paragraphs.append(para)

    return "\n\n".join(paragraphs)


def _generate_cta(topic: str, persona_name: str, platform_id: str) -> str:
    templates = _CTA_TEMPLATES.get(platform_id, _CTA_TEMPLATES["xhs"])
    pet_type = "猫咪" if "猫" in topic else "狗狗" if "狗" in topic else "毛孩子"
    cta = random.choice(templates)
    return cta.format(topic=topic, persona_name=persona_name, pet_type=pet_type)


def _generate_hashtags(topic: str, keywords: List[str], platform_id: str) -> List[str]:
    tags = []
    # Match topic to hashtag pool
    for key, pool in _HASHTAG_POOLS.items():
        if key in topic:
            tags.extend(pool)
            break
    # Add keyword-based tags
    for kw in keywords[:3]:
        tags.append(kw)
    # Platform-specific limits
    limits = {"xhs": 10, "douyin": 5, "bilibili": 10, "wechat_official": 0}
    max_tags = limits.get(platform_id, 10)
    return list(dict.fromkeys(tags))[:max_tags]  # dedupe and limit


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    topic = context.get("topic", "")
    persona_name = context.get("persona_name", "养宠达人")
    persona_tone = context.get("persona_tone", "casual")
    brand_knowledge = context.get("brand_knowledge", [])
    keywords = context.get("keywords", [])
    platform_id = context.get("platform_id", "xhs")
    # word_count_target reserved for future LLM-based length control

    # Generate components
    title = _generate_title(topic, persona_name, platform_id)
    body = _generate_body(topic, persona_name, persona_tone, brand_knowledge, keywords, platform_id)
    cta = _generate_cta(topic, persona_name, platform_id)
    hashtags = _generate_hashtags(topic, keywords, platform_id)

    # Assemble content
    content_parts = [body]
    if cta:
        content_parts.append(cta)
    content = "\n\n".join(content_parts)

    word_count = len(content)

    # Six-layer prompt structure (for traceability)
    prompt_layers = {
        "layer_1_platform_format": platform_id,
        "layer_2_structure_template": "hook + body + cta",
        "layer_3_brand_knowledge": brand_knowledge[:3],
        "layer_4_keywords": keywords[:5],
        "layer_5_persona": f"{persona_name} ({persona_tone})",
        "layer_6_style_dna": "MVP template generation",
    }

    return {
        "title": title,
        "content": content,
        "hashtags": hashtags,
        "word_count": word_count,
        "prompt_layers": prompt_layers,
        "generation_method": "template_mvp",
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
