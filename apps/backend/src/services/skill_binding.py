"""Agent-Skill binding management."""

import secrets
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AgentSkillBinding:
    id: str
    agent_id: str
    skill_id: str
    priority: int = 0  # Lower = higher priority
    config: Dict = None


_binding_db: Dict[str, AgentSkillBinding] = {}


def bind_skill(agent_id: str, skill_id: str, priority: int = 0, config: Optional[Dict] = None) -> AgentSkillBinding:
    binding_id = secrets.token_urlsafe(16)
    binding = AgentSkillBinding(
        id=binding_id,
        agent_id=agent_id,
        skill_id=skill_id,
        priority=priority,
        config=config or {},
    )
    _binding_db[binding_id] = binding
    return binding


def unbind_skill(binding_id: str) -> bool:
    if binding_id in _binding_db:
        del _binding_db[binding_id]
        return True
    return False


def list_bindings(agent_id: Optional[str] = None, skill_id: Optional[str] = None) -> List[AgentSkillBinding]:
    bindings = list(_binding_db.values())
    if agent_id:
        bindings = [b for b in bindings if b.agent_id == agent_id]
    if skill_id:
        bindings = [b for b in bindings if b.skill_id == skill_id]
    # Sort by priority (ascending)
    bindings.sort(key=lambda b: b.priority)
    return bindings


def get_binding(binding_id: str) -> Optional[AgentSkillBinding]:
    return _binding_db.get(binding_id)


def clear_bindings() -> None:
    _binding_db.clear()
