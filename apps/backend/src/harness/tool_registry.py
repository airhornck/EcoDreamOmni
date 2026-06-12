"""Tool Registry — unified tool invocation interface for Harness.

Wraps SkillHub skills as Tools with standardized schema.
Each Tool = Skill + unified invoke() interface.

Aligned with dev-plan H1: "Tool Registry (SkillHub has雏形 → no unified schema/sandbox)".
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.services import skill_hub


@dataclass
class Tool:
    """Unified Tool definition for Harness consumption."""
    tool_id: str
    name: str
    description: str
    skill_id: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    requires_tools: List[str] = field(default_factory=list)
    requires_toolsets: List[str] = field(default_factory=list)
    timeout_ms: int = 30000


def _tool_from_skill(skill: skill_hub.Skill) -> Tool:
    meta = skill.metadata or {}
    ts = meta.get("tool_schema", {})
    return Tool(
        tool_id=skill.id,
        name=skill.name,
        description=skill.description,
        skill_id=skill.id,
        input_schema=ts.get("input", {}),
        output_schema=ts.get("output", {}),
        requires_tools=meta.get("requires_tools", []),
        requires_toolsets=meta.get("requires_toolsets", []),
    )


def list_tools(layer: Optional[str] = None) -> List[Tool]:
    """List all available tools (active skills)."""
    skills = skill_hub.list_skills(level=layer)
    return [_tool_from_skill(s) for s in skills if s.status == "active"]


def get_tool(tool_id: str) -> Optional[Tool]:
    """Get a tool by ID."""
    skill = skill_hub.get_skill(tool_id)
    if skill is None or skill.status != "active":
        return None
    return _tool_from_skill(skill)


def invoke_tool(tool_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke a tool with given context.

    Returns standardized result:
      {
        "success": bool,
        "tool_id": str,
        "result": Any,
        "error": str | None,
        "elapsed_ms": int,
      }
    """
    import time

    tool = get_tool(tool_id)
    if tool is None:
        return {
            "success": False,
            "tool_id": tool_id,
            "result": None,
            "error": f"Tool '{tool_id}' not found or inactive",
            "elapsed_ms": 0,
        }

    # Dependency check
    deps = skill_hub.check_dependencies(tool_id)
    if deps["missing_tools"] or deps["missing_toolsets"]:
        return {
            "success": False,
            "tool_id": tool_id,
            "result": None,
            "error": f"Missing dependencies: tools={deps['missing_tools']}, toolsets={deps['missing_toolsets']}",
            "elapsed_ms": 0,
        }

    start = time.time()
    try:
        raw = skill_hub.execute_skill(tool_id, context)
        elapsed = int((time.time() - start) * 1000)
        return {
            "success": raw.get("success", False),
            "tool_id": tool_id,
            "result": raw.get("result"),
            "error": raw.get("error"),
            "elapsed_ms": elapsed,
        }
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return {
            "success": False,
            "tool_id": tool_id,
            "result": None,
            "error": str(e),
            "elapsed_ms": elapsed,
        }


def resolve_tools_for_agent(agent_id: str) -> List[Tool]:
    """Resolve effective tools for an agent (bindings + L1 builtins)."""
    skills = skill_hub.resolve_skills_for_agent(agent_id)
    return [_tool_from_skill(s) for s in skills]
