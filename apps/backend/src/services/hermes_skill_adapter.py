"""Hermes-agent skill format compatibility layer.

Parses SKILL.md frontmatter (YAML between --- fences) and maps hermes
metadata fields to our Skill model.

References:
- vendor/ai-frameworks/hermes-agent/agent/skill_utils.py::parse_frontmatter
"""

import re
from typing import Any, Dict, List, Optional, Tuple


# YAML parsing with lazy import (same pattern as hermes-agent)
_yaml_load_fn = None


def _yaml_load(content: str):
    global _yaml_load_fn
    if _yaml_load_fn is None:
        try:
            import yaml
            loader = getattr(yaml, "CSafeLoader", None) or yaml.SafeLoader
            def _yaml_load_fn(value):
                return yaml.load(value, Loader=loader)
        except ImportError:
            # Fallback to simple key:value parsing
            def _simple_parse(value: str) -> Dict[str, Any]:
                result: Dict[str, Any] = {}
                for line in value.strip().split("\n"):
                    if ":" not in line:
                        continue
                    key, val = line.split(":", 1)
                    k = key.strip()
                    v = val.strip().strip('"').strip("'")
                    # Simple list parsing
                    if v.startswith("[") and v.endswith("]"):
                        v = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",")]
                    result[k] = v
                return result
            _yaml_load_fn = _simple_parse
    return _yaml_load_fn(content)


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from a markdown string.

    Returns (frontmatter_dict, remaining_body).
    """
    frontmatter: Dict[str, Any] = {}
    body = content

    if not content.startswith("---"):
        return frontmatter, body

    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return frontmatter, body

    yaml_content = content[3 : end_match.start() + 3]
    body = content[end_match.end() + 3 :]

    try:
        parsed = _yaml_load(yaml_content)
        if isinstance(parsed, dict):
            frontmatter = parsed
    except Exception:
        # Fallback handled inside _yaml_load
        pass

    return frontmatter, body


def extract_hermes_conditions(frontmatter: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract conditional activation fields from hermes metadata.

    Returns keys:
        - fallback_for_toolsets
        - requires_toolsets
        - fallback_for_tools
        - requires_tools
    """
    metadata = frontmatter.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    hermes = metadata.get("hermes", {})
    if not isinstance(hermes, dict):
        hermes = {}
    return {
        "fallback_for_toolsets": hermes.get("fallback_for_toolsets", []),
        "requires_toolsets": hermes.get("requires_toolsets", []),
        "fallback_for_tools": hermes.get("fallback_for_tools", []),
        "requires_tools": hermes.get("requires_tools", []),
    }


def adapt_hermes_skill(skill_md_content: str) -> Optional[Dict[str, Any]]:
    """Convert a hermes-agent SKILL.md into our Skill constructor kwargs.

    Returns None if the content cannot be parsed.
    """
    frontmatter, body = parse_frontmatter(skill_md_content)
    if not frontmatter:
        return None

    name = frontmatter.get("name", "")
    if not name:
        return None

    description = frontmatter.get("description", "")
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    conditions = extract_hermes_conditions(frontmatter)
    requires_tools = conditions.get("requires_tools", [])
    requires_toolsets = conditions.get("requires_toolsets", [])

    return {
        "name": name,
        "description": description,
        "level": "L2",  # Hermes skills map to Configured/Marketplace layer
        "code": body,
        "tags": tags,
        "version": str(frontmatter.get("version", "1.0.0")),
        "metadata": {
            "requires_tools": requires_tools,
            "requires_toolsets": requires_toolsets,
            "source": "hermes",
        },
    }


def discover_hermes_skills(directory: str) -> List[Dict[str, Any]]:
    """Walk a directory and discover all SKILL.md files.

    Returns a list of adapted skill kwargs.
    """
    import os

    results: List[Dict[str, Any]] = []
    for root, _dirs, files in os.walk(directory):
        if "SKILL.md" in files:
            path = os.path.join(root, "SKILL.md")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                adapted = adapt_hermes_skill(content)
                if adapted:
                    adapted["metadata"]["file_path"] = path
                    results.append(adapted)
            except Exception:
                continue
    return results
