"""ContentForge service: draft CRUD, generation, persona lookup."""

from typing import Dict, List, Optional

from src.models.content_draft import (
    ContentDraft,
    clear_drafts,
    create_draft,
    delete_draft,
    get_draft,
    list_drafts,
    update_draft,
)
from src.models.persona import Persona, get_persona, list_personas
from src.services.content_generator import generate_content
from src.services import methodology_service


def create_content_draft(
    title: str,
    content_type: str,
    platform: str,
    account_id: str = "",
    body: str = "",
    tags: Optional[List[str]] = None,
    status: str = "draft",
    cover_image_url: Optional[str] = None,
) -> ContentDraft:
    return create_draft(
        title=title,
        content_type=content_type,
        platform=platform,
        account_id=account_id,
        body=body,
        tags=tags,
        status=status,
        cover_image_url=cover_image_url,
    )


def list_content_drafts() -> List[ContentDraft]:
    return list_drafts()


def get_content_draft(draft_id: str) -> Optional[ContentDraft]:
    return get_draft(draft_id)


def update_content_draft(draft_id: str, **kwargs) -> Optional[ContentDraft]:
    return update_draft(draft_id, **kwargs)


def remove_content_draft(draft_id: str) -> bool:
    return delete_draft(draft_id)


def generate_with_persona(
    topic: str,
    platform: str,
    persona_id: Optional[str] = None,
    stage_id: Optional[str] = None,
    llm_config: Optional[dict] = None,
    brand_knowledge_entries: Optional[List[dict]] = None,
    story_context: Optional[Dict] = None,
    keywords: Optional[List[str]] = None,
    composed_prompt: Optional[str] = None,
) -> dict:
    """Generate content using a persona from the pool.

    ★ v4.0 Strategy Element Architecture:
      如果传入 composed_prompt，则直接使用该 Prompt 替代默认的系统 Prompt 构建。
    """
    persona = get_persona(persona_id) if persona_id else None
    persona_dict = None
    if persona:
        persona_dict = {
            "name": persona.name,
            "voice_style": persona.voice_style,
            "catchphrases": persona.catchphrases,
            "formality": persona.formality,
        }

    template_version = None
    if stage_id and not composed_prompt:
        stage = methodology_service.get_stage(stage_id)
        if stage:
            template_version = stage.id

    return generate_content(
        topic=topic,
        platform=platform,
        llm_config=llm_config,
        persona=persona_dict,
        template_version=template_version,
        brand_knowledge_entries=brand_knowledge_entries,
        story_context=story_context,
        keywords=keywords,
        composed_prompt=composed_prompt,
    )


def list_persona_pool() -> List[Persona]:
    return list_personas()


def get_persona_detail(persona_id: str) -> Optional[Persona]:
    return get_persona(persona_id)
