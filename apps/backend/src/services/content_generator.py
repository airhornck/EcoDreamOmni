"""Content generator with Voice/Persona injection — DeepSeek edition.

Production (W11+): Integrate with LLM Gateway via LiteLLM.
"""

import httpx
from typing import Dict, List, Optional

from src.core.config import settings
from src.models.persona import Persona, get_persona


def _build_system_prompt(
    persona: Persona, platform: str, topic: str,
    brand_knowledge_entries: Optional[List[Dict]] = None,
    story_context: Optional[Dict] = None,
    keywords: Optional[List[str]] = None,
    template: Optional[Dict] = None,
) -> str:
    """Build system prompt with persona voice and platform constraints."""
    voice_desc = persona.voice_style or "亲切专业"
    formality = persona.formality or "casual"
    catchphrases = ", ".join(persona.catchphrases[:3]) if persona.catchphrases else "喵~"

    platform_rules = {
        "xhs": """
- 平台：小红书
- 风格：活泼亲切，多用emoji，段落简短
- 结构：标题吸睛 + 正文分段（带emoji小标题）+ 结尾互动 + 话题标签
- 字数：500-800字
- 禁止：医疗诊断承诺、处方药推荐、绝对化功效宣称
- 必须：宠物零食/用品标注"本品不能替代药品"
""",
        "douyin": """
- 平台：抖音
- 风格：口语化、节奏快、有hook
- 结构：黄金3秒hook + 核心要点 + 结尾互动
- 字数：300-500字
- 禁止：医疗诊断承诺、处方药推荐
""",
    }

    # RAG injection: brand knowledge context
    knowledge_section = ""
    if brand_knowledge_entries:
        knowledge_lines = []
        for entry in brand_knowledge_entries:
            name = entry.get("name", "")
            content = entry.get("content", "")
            prohibited = entry.get("prohibited_claims", [])
            disclaimers = entry.get("required_disclaimers", [])
            if name or content:
                knowledge_lines.append(f"【{name}】\n{content}")
            if prohibited:
                knowledge_lines.append(f"  ⚠️ 禁止宣称：{', '.join(prohibited)}")
            if disclaimers:
                knowledge_lines.append(f"  📌 必须声明：{', '.join(disclaimers)}")
        if knowledge_lines:
            knowledge_section = "\n\n=== 品牌知识库参考（创作时必须遵守）===\n" + "\n\n".join(knowledge_lines) + "\n=== 知识库参考结束 ===\n"

    # PersonaStory injection
    story_section = ""
    if story_context:
        series_theme = story_context.get("series_theme", "")
        emotional_arc = story_context.get("emotional_arc", "")
        current_node = story_context.get("current_node", {})
        prev_recap = story_context.get("prev_recap", "")
        next_teaser = story_context.get("next_teaser", "")
        node_theme = current_node.get("theme", "")
        key_event = current_node.get("key_event", "")
        emotion_tone = current_node.get("emotion_tone", "medium")

        story_lines = []
        if series_theme:
            story_lines.append(f"系列主题：{series_theme}")
        if emotional_arc:
            story_lines.append(f"情感曲线：{emotional_arc}")
        if node_theme:
            story_lines.append(f"本节点主题：{node_theme}")
        if key_event:
            story_lines.append(f"关键事件：{key_event}")
        if emotion_tone:
            story_lines.append(f"情感基调：{emotion_tone}")
        if prev_recap:
            story_lines.append(f"前文回顾：{prev_recap}")
        if next_teaser:
            story_lines.append(f"下集预告：{next_teaser}")
        if story_lines:
            story_section = "\n\n=== 故事线上下文（创作时必须融入）===\n" + "\n".join(story_lines) + "\n=== 故事线上下文结束 ===\n"

    # Template injection
    template_section = ""
    if template:
        prompt_tmpl = template.get("prompt_template", "")
        variables = template.get("variables", [])
        var_lines = []
        if variables:
            for v in variables:
                var_name = v.get("name", "")
                var_label = v.get("label", "")
                var_type = v.get("type", "text")
                var_default = v.get("default_value", "无")
                var_lines.append(f"- {var_name}（{var_label}）: 类型={var_type}, 默认值={var_default}")
        var_desc = "\n".join(var_lines) if var_lines else "（无变量定义）"
        template_section = f"\n\n=== 内容模板结构（创作时必须遵循）===\n模板Prompt:\n{prompt_tmpl}\n\n变量说明:\n{var_desc}\n=== 模板结构结束 ===\n"

    # Keywords injection
    keywords_section = ""
    if keywords:
        keywords_section = f"\n\n=== 关键词注入（创作时必须自然融入以下关键词）===\n{', '.join(keywords)}\n=== 关键词注入结束 ===\n"

    return f"""你是一位{voice_desc}的宠物内容创作者，人设：{persona.name}。
语气风格：{formality}，口头禅：{catchphrases}。

任务：围绕「{topic}」创作一篇平台原生内容。

{platform_rules.get(platform, platform_rules["xhs"])}
{knowledge_section}{story_section}{template_section}{keywords_section}
额外要求：
1. 内容必须有真实价值，不能是空洞的套话
2. 分享具体可操作的建议
3. 用第一人称"我"来写，增加真实感
4. 适当加入个人经历或案例
5. 结尾引导评论互动
6. 严格遵守知识库参考中的禁止宣称和必须声明
7. 紧扣故事线上下文中的系列主题和情感基调
"""


def _build_user_prompt(topic: str, platform: str, content_type: str) -> str:
    return f"""请围绕「{topic}」创作一篇{platform}平台的{content_type}。

要求：
1. 标题要吸睛，带emoji，符合平台调性
2. 正文分3-4个部分，每部分有小标题和emoji
3. 提供具体、可操作的建议（不少于5条）
4. 加入一个简短的"我家毛孩子"真实案例
5. 结尾引导用户评论互动
6. 附上5-8个相关话题标签

请以JSON格式输出，包含以下字段：
- title: 标题
- body: 正文（Markdown格式）
- tags: 标签数组（字符串数组）
"""


def call_llm(
    system_prompt: str,
    user_prompt: str,
    llm_config: Optional[dict] = None,
    max_tokens: int = 2000,
) -> str:
    """Call LLM API synchronously. Supports any provider via llm_config."""
    if llm_config:
        api_key = llm_config["api_key"]
        model = llm_config["model_name"]
        url = llm_config["endpoint_url"]
        temperature = llm_config.get("temperature", 0.8)
    else:
        # Fallback to legacy DeepSeek env config
        api_key = settings.DEEPSEEK_API_KEY
        model = settings.DEFAULT_LLM_MODEL or "deepseek-chat"
        url = "https://api.deepseek.com/chat/completions"
        temperature = 0.8
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not configured and no LLM Hub config available")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }

    import logging
    logger = logging.getLogger(__name__)
    logger.info("[LLM_CALL] provider=%s model=%s endpoint=%s", llm_config.get("provider") if llm_config else "deepseek", model, url)
    with httpx.Client(timeout=60) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        logger.info("[LLM_CALL_OK] model=%s tokens_used=%s", model, data.get("usage", {}).get("total_tokens", "unknown"))
        return data["choices"][0]["message"]["content"]


def generate_content(
    topic: str,
    platform: str = "xhs",
    content_type: str = "note",
    persona: Optional[dict] = None,
    template_version: Optional[str] = None,
    llm_config: Optional[dict] = None,
    brand_knowledge_entries: Optional[List[Dict]] = None,
    story_context: Optional[Dict] = None,
    keywords: Optional[List[str]] = None,
    template: Optional[Dict] = None,
    composed_prompt: Optional[str] = None,
) -> Dict:
    """Generate content with Voice injection using LLM Hub or fallback DeepSeek.

    ★ v4.0 Strategy Element Architecture:
      如果传入 composed_prompt，则直接使用该 Prompt 替代默认的 _build_system_prompt。
    """
    # Resolve persona
    persona_obj = None
    if persona:
        if isinstance(persona, dict):
            persona_obj = Persona(
                id="custom",
                name=persona.get("name", "默认"),
                voice_style=persona.get("voice_style", ""),
                catchphrases=persona.get("catchphrases", []),
                formality=persona.get("formality", "casual"),
            )
        else:
            persona_obj = get_persona(str(persona))

    if persona_obj is None:
        persona_obj = get_persona("p1")

    # Build prompts
    if composed_prompt:
        system_prompt = composed_prompt
    else:
        system_prompt = _build_system_prompt(
            persona_obj, platform, topic,
            brand_knowledge_entries, story_context,
            keywords=keywords, template=template,
        )
    user_prompt = _build_user_prompt(topic, platform, content_type)

    # Call LLM
    import logging
    logger = logging.getLogger(__name__)
    logger.info("[GENERATE_CONTENT] topic=%s platform=%s persona=%s", topic, platform, persona_obj.name)
    try:
        raw_response = call_llm(system_prompt, user_prompt, llm_config=llm_config)
        import json
        llm_result = json.loads(raw_response)

        result = {
            "title": llm_result.get("title", f"{topic}攻略").strip(),
            "body": llm_result.get("body", "").strip(),
            "tags": llm_result.get("tags", [topic, "宠物健康", "养宠日常"])[:8],
            "platform": platform,
            "content_type": content_type,
            "persona_id": persona_obj.id,
            "_persona_used": persona_obj.name,
        }
    except Exception as e:
        # Fallback to template-based generation if LLM fails
        result = _fallback_generate(persona_obj, topic, platform, content_type)
        result["_llm_error"] = str(e)

    if template_version:
        result["template_version"] = template_version
    if template:
        result["template_id"] = template.get("template_id")

    return result


def generate_outline(
    topic: str,
    platform: str = "xhs",
    persona: Optional[dict] = None,
    llm_config: Optional[dict] = None,
) -> Dict:
    """Generate detailed content outline using LLM."""
    persona_obj = None
    if persona:
        if isinstance(persona, dict):
            persona_obj = Persona(
                id="custom",
                name=persona.get("name", "默认"),
                voice_style=persona.get("voice_style", ""),
                catchphrases=persona.get("catchphrases", []),
                formality=persona.get("formality", "casual"),
            )
        else:
            persona_obj = get_persona(str(persona))

    if persona_obj is None:
        persona_obj = get_persona("p1")

    voice_desc = persona_obj.voice_style or "亲切专业"
    platform_rules = {
        "xhs": "小红书：活泼亲切，多用emoji，段落简短，标题吸睛",
        "douyin": "抖音：口语化、节奏快、黄金3秒hook",
    }

    system_prompt = f"""你是一位{voice_desc}的宠物内容创作者。
平台：{platform_rules.get(platform, platform_rules['xhs'])}

基于选题生成详细的内容框架大纲。
要求：
1. 标题有吸引力，带emoji
2. 3-5个部分，每部分有小标题和核心要点（2-3条）
3. 标注每部分的预计字数
4. 输出 JSON：{{"title": "", "sections": [{{"heading": "", "points": [""], "word_count": 0}}]}}"""

    user_prompt = f"请为「{topic}」生成详细的内容框架大纲"

    try:
        raw_response = call_llm(system_prompt, user_prompt, llm_config=llm_config)
        import json
        outline = json.loads(raw_response)
        return {
            "title": outline.get("title", f"{topic}攻略").strip(),
            "sections": outline.get("sections", []),
            "persona_id": persona_obj.id,
        }
    except Exception as e:
        return {
            "title": f"{topic}攻略",
            "sections": [
                {"heading": "✨ 为什么重要", "points": ["解释背景"], "word_count": 100},
                {"heading": "📝 核心经验", "points": ["分享经验"], "word_count": 200},
                {"heading": "💡 实用建议", "points": ["给出建议"], "word_count": 150},
                {"heading": "❓ 常见误区", "points": ["指出误区"], "word_count": 100},
            ],
            "_llm_error": str(e),
        }


def decompose_six_layer_prompt(
    topic: str,
    platform: str = "xhs",
    persona: Optional[dict] = None,
    brand_knowledge_entries: Optional[List[Dict]] = None,
    story_context: Optional[Dict] = None,
) -> Dict[str, str]:
    """Decompose the full prompt into six visualizable layers.

    Returns a dict with keys:
        platform_format, structure_template, brand_knowledge,
        keyword_injection, persona_layer, style_layer
    """
    # Resolve persona
    persona_obj = None
    if persona:
        if isinstance(persona, dict):
            persona_obj = Persona(
                id="custom",
                name=persona.get("name", "默认"),
                voice_style=persona.get("voice_style", ""),
                catchphrases=persona.get("catchphrases", []),
                formality=persona.get("formality", "casual"),
            )
        else:
            persona_obj = get_persona(str(persona))
    if persona_obj is None:
        persona_obj = get_persona("p1")

    # ─── Layer 1: Platform Format ───
    platform_rules = {
        "xhs": """平台：小红书
- 风格：活泼亲切，多用emoji，段落简短
- 结构：标题吸睛 + 正文分段（带emoji小标题）+ 结尾互动 + 话题标签
- 字数：500-800字
- 禁止：医疗诊断承诺、处方药推荐、绝对化功效宣称
- 必须：宠物零食/用品标注'本品不能替代药品'""",
        "douyin": """平台：抖音
- 风格：口语化、节奏快、有hook
- 结构：黄金3秒hook + 核心要点 + 结尾互动
- 字数：300-500字
- 禁止：医疗诊断承诺、处方药推荐""",
    }
    platform_format = platform_rules.get(platform, platform_rules["xhs"])

    # ─── Layer 2: Structure Template ───
    structure_template = """输出格式要求（JSON）：
- title: 标题（吸睛，带emoji，符合平台调性）
- body: 正文（Markdown格式）
  · 分3-4个部分，每部分有小标题和emoji
  · 提供具体可操作的建议（不少于5条）
  · 加入一个简短的"我家毛孩子"真实案例
  · 结尾引导用户评论互动
- tags: 标签数组（5-8个相关话题标签）"""

    # ─── Layer 3: Brand Knowledge ───
    brand_knowledge = ""
    if brand_knowledge_entries:
        knowledge_lines = []
        for entry in brand_knowledge_entries:
            name = entry.get("name", "")
            content = entry.get("content", "")
            prohibited = entry.get("prohibited_claims", [])
            disclaimers = entry.get("required_disclaimers", [])
            if name or content:
                knowledge_lines.append(f"【{name}】\n{content}")
            if prohibited:
                knowledge_lines.append(f"  ⚠️ 禁止宣称：{', '.join(prohibited)}")
            if disclaimers:
                knowledge_lines.append(f"  📌 必须声明：{', '.join(disclaimers)}")
        if knowledge_lines:
            brand_knowledge = "\n".join(knowledge_lines)
    if not brand_knowledge:
        brand_knowledge = "（当前未匹配到品牌知识库条目，创作时以通用合规要求为准）"

    # ─── Layer 4: Keyword Injection ───
    keyword_injection = f"""核心话题：{topic}
创作要求：
1. 内容必须有真实价值，不能是空洞的套话
2. 分享具体可操作的建议
3. 用第一人称"我"来写，增加真实感
4. 适当加入个人经历或案例
5. 结尾引导评论互动
6. 严格遵守知识库参考中的禁止宣称和必须声明"""

    if story_context:
        story_lines = []
        series_theme = story_context.get("series_theme", "")
        emotional_arc = story_context.get("emotional_arc", "")
        current_node = story_context.get("current_node", {})
        prev_recap = story_context.get("prev_recap", "")
        next_teaser = story_context.get("next_teaser", "")
        if series_theme:
            story_lines.append(f"系列主题：{series_theme}")
        if emotional_arc:
            story_lines.append(f"情感曲线：{emotional_arc}")
        if current_node.get("theme"):
            story_lines.append(f"本节点主题：{current_node['theme']}")
        if current_node.get("key_event"):
            story_lines.append(f"关键事件：{current_node['key_event']}")
        if current_node.get("emotion_tone"):
            story_lines.append(f"情感基调：{current_node['emotion_tone']}")
        if prev_recap:
            story_lines.append(f"前文回顾：{prev_recap}")
        if next_teaser:
            story_lines.append(f"下集预告：{next_teaser}")
        if story_lines:
            keyword_injection += "\n\n故事线上下文（创作时必须融入）：\n" + "\n".join(story_lines)

    # ─── Layer 5: Persona Layer ───
    persona_layer = f"""人设：{persona_obj.name}
身份定位：{persona_obj.voice_style or '亲切专业的宠物内容创作者'}
口头禅：{', '.join(persona_obj.catchphrases[:3]) if persona_obj.catchphrases else '喵~'}"""

    # ─── Layer 6: Style Layer ───
    formality_desc = {
        "casual": "轻松随意，像跟朋友聊天",
        "formal": "正式专业，像专家讲座",
        "mixed": "张弛有度，专业中带亲切",
    }
    style_layer = f"""语气风格：{persona_obj.formality or 'casual'} — {formality_desc.get(persona_obj.formality, '轻松随意')}
叙事视角：第一人称"我"
情感温度：温暖、真实、有共鸣
互动策略：结尾引导评论，中间适当提问"""

    return {
        "platform_format": platform_format,
        "structure_template": structure_template,
        "brand_knowledge": brand_knowledge,
        "keyword_injection": keyword_injection,
        "persona_layer": persona_layer,
        "style_layer": style_layer,
    }


async def recommend_templates(topic: str, platform: str, db) -> List[Dict]:
    """Recommend top-3 content templates based on text similarity to topic.

    Queries ContentTemplateORM for active templates, scores them by keyword
    overlap between the topic and template_id / prompt_template, and returns
    the best matches.
    """
    from sqlalchemy import select
    from src.models.content_template import ContentTemplateORM

    # Prefer platform-specific templates
    result = await db.execute(
        select(ContentTemplateORM).where(
            ContentTemplateORM.status == "active",
            ContentTemplateORM.source_platform_id == platform,
        )
    )
    templates = result.scalars().all()

    # Fallback to all active templates if no platform-specific results
    if not templates:
        result = await db.execute(
            select(ContentTemplateORM).where(ContentTemplateORM.status == "active")
        )
        templates = result.scalars().all()

    topic_lower = topic.lower()
    topic_words = set(w for w in topic_lower.split() if len(w) > 1)

    scored = []
    for t in templates:
        text = f"{t.template_id} {t.prompt_template or ''}".lower()
        matches = sum(1 for word in topic_words if word in text)
        match_score = min(matches / max(len(topic_words), 1), 1.0)

        name = t.template_id
        if t.extracted_structure and isinstance(t.extracted_structure, dict):
            name = t.extracted_structure.get("name", t.template_id)

        scored.append({
            "template_id": t.template_id,
            "name": name,
            "prompt_template": t.prompt_template,
            "variables": t.variables or [],
            "match_score": round(match_score, 2),
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:3]


def _fallback_generate(persona: Persona, topic: str, platform: str, content_type: str) -> Dict:
    """Template-based fallback when LLM is unavailable."""
    greeting = "嗨！喵~ " if persona.formality == "casual" else "大家好，"
    closing = "好啦，今天就分享到这里，有问题评论区见~ 喵~" if persona.formality == "casual" else "希望对你有帮助。"
    hashtags = f"#{topic} #宠物健康 #养宠日常"

    body = f"""{greeting}今天想跟大家分享一下关于{topic}的心得~

✨ 为什么{topic}很重要？
{topic}是每位宠物家长都需要关注的话题，关系到毛孩子的健康和幸福。

📝 我的经验
我家宠物在{topic}方面积累了一些经验，跟大家分享一下。定期关注、选择正规渠道、记录宠物反应是关键。

💡 小贴士
1. 定期关注{topic}
2. 选择正规渠道和产品
3. 记录宠物反应，及时调整
4. 有问题及时咨询专业人士

{closing}

{hashtags}"""

    title = f"{topic}攻略，快码住！" if persona.formality == "casual" else f"关于{topic}的专业建议"
    tags = [topic, "宠物健康", "养宠日常", "攻略", "省钱"]

    return {
        "title": title.strip(),
        "body": body.strip(),
        "tags": tags[:5],
        "platform": platform,
        "content_type": content_type,
        "persona_id": persona.id,
        "_persona_used": persona.name,
    }
