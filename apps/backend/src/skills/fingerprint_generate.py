"""Fingerprint Generate Skill — v4.0 Phase 9.

生成内容指纹（语义哈希），用于查重。
MVP: 基于文本特征的简化哈希，无 LLM 调用。
"""

import hashlib
from typing import Any, Dict

SKILL_ID = "fingerprint_generate"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string"},
        "title": {"type": "string"},
        "algorithm": {"type": "string", "default": "simhash_mvp"},
    },
    "required": ["content"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "fingerprint": {"type": "string"},
        "algorithm": {"type": "string"},
        "content_hash": {"type": "string"},
        "feature_vector": {"type": "array", "items": {"type": "integer"}},
    },
}


def _extract_features(text: str) -> list:
    """Extract simple n-gram features for MVP fingerprinting."""
    # Normalize
    cleaned = "".join(c for c in text.lower() if c.isalnum() or c.isspace())
    words = cleaned.split()
    # Bigram features
    features = []
    for i in range(len(words) - 1):
        bigram = f"{words[i]}_{words[i + 1]}"
        features.append(hash(bigram) & 0xFFFF)
    # If too few words, add unigrams
    if len(features) < 8:
        for w in words[:16]:
            features.append(hash(w) & 0xFFFF)
    return features[:32]  # cap at 32 features


def _simhash_mvp(features: list) -> str:
    """Simplified simhash: XOR-based 64-bit fingerprint."""
    vec = [0] * 64
    for f in features:
        for i in range(64):
            bit = (f >> i) & 1
            vec[i] += 1 if bit else -1
    fingerprint = 0
    for i, v in enumerate(vec):
        if v > 0:
            fingerprint |= (1 << i)
    return format(fingerprint, "016x")


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    content = context.get("content", "")
    title = context.get("title", "")
    algorithm = context.get("algorithm", "simhash_mvp")

    full_text = f"{title}\n{content}".strip()
    features = _extract_features(full_text)

    if algorithm == "simhash_mvp":
        fingerprint = _simhash_mvp(features)
    else:
        fingerprint = _content_hash(full_text)

    return {
        "fingerprint": fingerprint,
        "algorithm": algorithm,
        "content_hash": _content_hash(full_text),
        "feature_vector": features[:16],
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
