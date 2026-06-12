"""Content draft models and in-memory store."""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ContentDraft:
    id: str
    title: str
    content_type: str  # note, video, carousel
    platform: str
    account_id: str
    body: str
    tags: List[str] = field(default_factory=list)
    status: str = "draft"  # draft, reviewing, approved, published, rejected
    cover_image_url: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    published_at: Optional[str] = None
    engagement_estimate: Optional[float] = None


_draft_db: Dict[str, ContentDraft] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_draft(
    title: str,
    content_type: str,
    platform: str,
    account_id: str = "",
    body: str = "",
    tags: Optional[List[str]] = None,
    status: str = "draft",
    cover_image_url: Optional[str] = None,
) -> ContentDraft:
    draft_id = secrets.token_urlsafe(16)
    now = _now()
    draft = ContentDraft(
        id=draft_id,
        title=title,
        content_type=content_type,
        platform=platform,
        account_id=account_id,
        body=body,
        tags=tags or [],
        status=status,
        cover_image_url=cover_image_url,
        created_at=now,
        updated_at=now,
    )
    _draft_db[draft_id] = draft
    return draft


def get_draft(draft_id: str) -> Optional[ContentDraft]:
    return _draft_db.get(draft_id)


def list_drafts() -> List[ContentDraft]:
    return list(_draft_db.values())


def update_draft(draft_id: str, **kwargs) -> Optional[ContentDraft]:
    draft = _draft_db.get(draft_id)
    if draft is None:
        return None
    for key, value in kwargs.items():
        if hasattr(draft, key):
            setattr(draft, key, value)
    draft.updated_at = _now()
    return draft


def delete_draft(draft_id: str) -> bool:
    if draft_id in _draft_db:
        del _draft_db[draft_id]
        return True
    return False


def clear_drafts() -> None:
    _draft_db.clear()
