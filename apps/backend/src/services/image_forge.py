"""ImageForge — W16 图片配置引擎。

核心能力:
- 图片-内容匹配（调用 AssetPool 推荐接口）
- 排版配置（封面+正文配图）
- 人工干预闭环
- T2 预检（含产品信息禁止路由境外模型）
- 强制人工审核
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ImageConfig:
    id: str
    content_draft_id: str
    account_id: str
    layout_type: str  # cover_3_body | cover_1_body | no_cover
    topic: str = ""
    has_product_info: bool = False
    cover_image: Optional[Dict] = None
    body_images: List[Dict] = field(default_factory=list)
    status: str = "draft"  # draft | PENDING_REVIEW | APPROVED | REJECTED
    t2_check_result: Optional[Dict] = None
    reviewer_id: Optional[str] = None
    reject_reason: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


_image_config_db: Dict[str, ImageConfig] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_image_config(
    content_draft_id: str,
    account_id: str,
    layout_type: str,
    topic: str = "",
    has_product_info: bool = False,
) -> ImageConfig:
    config = ImageConfig(
        id=secrets.token_urlsafe(12),
        content_draft_id=content_draft_id,
        account_id=account_id,
        layout_type=layout_type,
        topic=topic,
        has_product_info=has_product_info,
        created_at=_now(),
        updated_at=_now(),
    )
    _image_config_db[config.id] = config
    return config


def get_image_config(config_id: str) -> Optional[ImageConfig]:
    return _image_config_db.get(config_id)


def list_image_configs(account_id: Optional[str] = None) -> List[ImageConfig]:
    configs = list(_image_config_db.values())
    if account_id:
        configs = [c for c in configs if c.account_id == account_id]
    return configs


def set_layout(
    config_id: str,
    cover_image: Optional[Dict],
    body_images: List[Dict],
) -> Optional[ImageConfig]:
    config = _image_config_db.get(config_id)
    if not config:
        return None
    config.cover_image = cover_image
    config.body_images = list(body_images)
    config.updated_at = _now()
    return config


def recommend_images(topic: str) -> List[Dict]:
    """MVP: Mock image recommendations based on topic."""
    # In production: call AssetPool function to get recommended assets
    recommendations = []
    for i in range(3):
        recommendations.append({
            "asset_id": f"asset_{topic}_{i}",
            "filename": f"{topic}_recommendation_{i+1}.jpg",
            "file_url": f"https://cdn.example.com/{topic}_rec_{i+1}.jpg",
            "source_type": "OPERATOR_UPLOAD",
            "score": 90 - i * 10,
        })
    return recommendations


def t2_check(config_id: str) -> Optional[Dict]:
    """T2 pre-check: block foreign model routing if product info detected."""
    config = _image_config_db.get(config_id)
    if not config:
        return None

    if config.has_product_info:
        result = {
            "allow_t2": False,
            "product_info_detected": True,
            "reason": "含产品信息禁止路由T2境外模型",
        }
    else:
        result = {
            "allow_t2": True,
            "product_info_detected": False,
            "reason": "",
        }
    config.t2_check_result = result
    return result


def submit_for_review(config_id: str) -> Optional[ImageConfig]:
    """Submit image config for human review."""
    config = _image_config_db.get(config_id)
    if not config:
        return None
    if config.status != "draft":
        return config
    config.status = "PENDING_REVIEW"
    config.updated_at = _now()
    return config


def approve_config(config_id: str, reviewer_id: str) -> Optional[ImageConfig]:
    """Approve image config after human review."""
    config = _image_config_db.get(config_id)
    if not config:
        return None
    if config.status != "PENDING_REVIEW":
        return config
    config.status = "APPROVED"
    config.reviewer_id = reviewer_id
    config.updated_at = _now()
    return config


def reject_config(config_id: str, reviewer_id: str, reason: str) -> Optional[ImageConfig]:
    """Reject image config after human review."""
    config = _image_config_db.get(config_id)
    if not config:
        return None
    config.status = "REJECTED"
    config.reviewer_id = reviewer_id
    config.reject_reason = reason
    config.updated_at = _now()
    return config


def clear_image_forge() -> None:
    _image_config_db.clear()
