"""Image Generate Skill — v4.0 Phase 8 P8-2.

文生图/图生图，支持平台封面规格。
MVP: 返回占位图片参数和规格信息，不调用真实图像模型（预留 LLM Hub image 路由）。

架构红线:
- §2.1 Agent 禁 DB: 纯计算，无 DB 访问
- §2.5 LLMHub 路由: requires_llm=True，MVP 返回占位，生产接入 LLM Hub image 路由
"""

from typing import Any, Dict
from src.core.config import settings

SKILL_ID = "image_generate"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"image": True}
REQUIRES_LLM = True
LLM_MODEL_PREFERENCE = settings.QWEN_IMAGE_MODEL or "qwen-image-2.0-pro"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {"type": "string", "description": "图像生成提示词"},
        "platform_id": {"type": "string", "description": "平台标识: xhs / douyin / bilibili / wechat_official"},
        "image_style": {"type": "string", "description": "图像风格: realistic/illustration/minimal/cartoon", "default": "realistic"},
        "reference_image_url": {"type": "string", "description": "参考图 URL（图生图模式）"},
        "aspect_ratio": {"type": "string", "description": "宽高比: 1:1 / 3:4 / 9:16 / 16:9", "default": "1:1"},
    },
    "required": ["prompt", "platform_id"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "image_url": {"type": "string"},
        "image_dimensions": {"type": "object"},
        "format": {"type": "string"},
        "file_size_estimate_kb": {"type": "integer"},
        "generation_params": {"type": "object"},
        "status": {"type": "string"},
        "placeholder": {"type": "boolean"},
    },
}

# Platform cover image specs
_PLATFORM_SPECS: Dict[str, Dict[str, Any]] = {
    "xhs": {
        "note_image": {"width": 1080, "height": 1440, "aspect": "3:4", "format": "jpg", "max_size_kb": 20480},
        "note_video": {"width": 1080, "height": 1920, "aspect": "9:16", "format": "jpg", "max_size_kb": 20480},
    },
    "douyin": {
        "video_cover": {"width": 1080, "height": 1920, "aspect": "9:16", "format": "jpg", "max_size_kb": 5120},
    },
    "bilibili": {
        "video_cover": {"width": 1146, "height": 717, "aspect": "16:10", "format": "jpg", "max_size_kb": 5120},
    },
    "wechat_official": {
        "article_cover": {"width": 900, "height": 383, "aspect": "2.35:1", "format": "jpg", "max_size_kb": 2048},
        "article_inline": {"width": 640, "height": 427, "aspect": "3:2", "format": "jpg", "max_size_kb": 2048},
    },
}

_ASPECT_RATIO_MAP: Dict[str, tuple] = {
    "1:1": (1024, 1024),
    "3:4": (768, 1024),
    "4:3": (1024, 768),
    "9:16": (576, 1024),
    "16:9": (1024, 576),
    "2.35:1": (1024, 435),
    "16:10": (1024, 640),
    "3:2": (1024, 683),
}

_STYLE_PROMPT_PREFIXES: Dict[str, str] = {
    "realistic": "超写实风格，细节丰富，光影自然，",
    "illustration": "手绘插画风格，温暖柔和，",
    "minimal": "极简风格，干净背景，突出主体，",
    "cartoon": "卡通风格，色彩明亮，可爱生动，",
}


def _resolve_dimensions(platform_id: str, aspect_ratio: str) -> Dict[str, Any]:
    specs = _PLATFORM_SPECS.get(platform_id, _PLATFORM_SPECS["xhs"])
    # Use first available spec for the platform as default
    default_spec = list(specs.values())[0]

    if aspect_ratio in _ASPECT_RATIO_MAP:
        width, height = _ASPECT_RATIO_MAP[aspect_ratio]
    else:
        width, height = default_spec["width"], default_spec["height"]

    return {
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "format": default_spec["format"],
        "max_size_kb": default_spec["max_size_kb"],
    }


def _enhance_prompt(prompt: str, image_style: str, platform_id: str) -> str:
    prefix = _STYLE_PROMPT_PREFIXES.get(image_style, "")
    platform_hint = {
        "xhs": "适合社交媒体封面，吸睛",
        "douyin": "适合短视频封面，动感",
        "bilibili": "适合视频封面，信息丰富",
        "wechat_official": "适合公众号封面，专业",
    }.get(platform_id, "")

    enhanced = f"{prefix}{prompt}，{platform_hint}".strip("，")
    return enhanced


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    prompt = context.get("prompt", "")
    platform_id = context.get("platform_id", "xhs")
    image_style = context.get("image_style", "realistic")
    reference_image_url = context.get("reference_image_url", "")
    aspect_ratio = context.get("aspect_ratio", "1:1")

    # Resolve dimensions
    dims = _resolve_dimensions(platform_id, aspect_ratio)

    # Enhance prompt
    enhanced_prompt = _enhance_prompt(prompt, image_style, platform_id)

    # MVP: placeholder image URL
    mode = "img2img" if reference_image_url else "txt2img"
    placeholder_url = (
        f"/api/v1/placeholder/image?"
        f"w={dims['width']}&h={dims['height']}&"
        f"text={prompt[:20].replace(' ', '+')}&"
        f"style={image_style}"
    )

    generation_params = {
        "original_prompt": prompt,
        "enhanced_prompt": enhanced_prompt,
        "image_style": image_style,
        "platform_id": platform_id,
        "aspect_ratio": aspect_ratio,
        "mode": mode,
        "model": LLM_MODEL_PREFERENCE,
        "dimensions": dims,
    }

    return {
        "image_url": placeholder_url,
        "image_dimensions": {
            "width": dims["width"],
            "height": dims["height"],
            "aspect_ratio": aspect_ratio,
        },
        "format": dims["format"],
        "file_size_estimate_kb": min(dims["max_size_kb"] // 4, 2048),
        "generation_params": generation_params,
        "status": "placeholder",
        "placeholder": True,
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
