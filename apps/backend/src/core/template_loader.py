"""Workflow Template Loader — v4.0 Phase 8 P8-4.

从 `src/data/workflows/*.yaml` 加载 Pipeline 模板，支持热加载。
MVP: 启动时加载所有 YAML，运行时可通过 `reload()` 刷新。
"""

import glob
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.services.workflow_engine import (
    WorkflowNode,
    WorkflowTemplate,
    NodeType,
    FailStrategy,
)

_WORKFLOW_DIR = Path(__file__).resolve().parent.parent / "data" / "workflows"


def _parse_node(raw: Dict[str, Any]) -> WorkflowNode:
    """Parse a raw dict into WorkflowNode."""
    return WorkflowNode(
        node_index=raw["node_index"],
        node_type=NodeType(raw["node_type"]),
        node_name=raw["node_name"],
        agent_id=raw.get("agent_id"),
        prompt_template_id=raw.get("prompt_template_id"),
        fail_strategy=FailStrategy(raw.get("fail_strategy", "FAIL_FAST")),
        human_config=raw.get("human_config"),
        timer_seconds=raw.get("timer_seconds"),
        skill_id=raw.get("skill_id"),
        depends_on=raw.get("depends_on", []),
    )


def _load_yaml(path: Path) -> Optional[WorkflowTemplate]:
    """Load a single YAML template file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not raw:
            return None

        nodes = [_parse_node(n) for n in raw.get("nodes", [])]

        # Red line: any workflow containing Publisher must have human_approval
        has_publisher = any(
            n.agent_id == "publisher" for n in nodes if n.node_type == NodeType.AGENT
        )
        has_human = any(n.node_type == NodeType.HUMAN_APPROVAL for n in nodes)
        if has_publisher and not has_human:
            raise ValueError(f"模板 {raw['id']} 含 Publisher 节点但缺少 human_approval")

        return WorkflowTemplate(
            id=raw["id"],
            name=raw["name"],
            description=raw.get("description", ""),
            source_preset=raw.get("source_preset", raw["id"]),
            version=raw.get("version", 1),
            status=raw.get("status", "DRAFT"),
            owner=raw.get("owner", ""),
            nodes=nodes,
            created_at=raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=raw.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )
    except Exception as exc:
        # Log and skip corrupted files
        print(f"[template_loader] Failed to load {path}: {exc}")
        return None


def load_all_templates() -> Dict[str, WorkflowTemplate]:
    """Load all YAML templates from the workflows directory."""
    templates: Dict[str, WorkflowTemplate] = {}
    pattern = str(_WORKFLOW_DIR / "*.yaml")
    for path in glob.glob(pattern):
        tmpl = _load_yaml(Path(path))
        if tmpl:
            templates[tmpl.id] = tmpl
    return templates


def load_template(template_id: str) -> Optional[WorkflowTemplate]:
    """Load a single template by ID."""
    path = _WORKFLOW_DIR / f"{template_id}.yaml"
    if not path.exists():
        return None
    return _load_yaml(path)


def reload_template(template_id: str) -> Optional[WorkflowTemplate]:
    """Reload a single template from disk (hot-reload)."""
    return load_template(template_id)


def list_template_ids() -> List[str]:
    """List all available template IDs on disk."""
    pattern = str(_WORKFLOW_DIR / "*.yaml")
    return [Path(p).stem for p in glob.glob(pattern)]
