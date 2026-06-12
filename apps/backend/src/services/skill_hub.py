"""SkillHub: four-layer skill loading engine + built-in skills + Tool Registry.

Layers (detailed design §5.3, dev-plan W15):
  L1 (Built-in):   System-provided skills, always available
  L2 (Configured): Team/tenant scoped skills (Marketplace / hermes-agent)
  L3 (User):       User-created skills
  L4 (Evolved):    Runtime evolved skills (SkillSmith output)

Loading order: L1 → L2 → L3 → L4.
Higher layers override lower layers for the same skill name.

Tool Registry:
  Each skill can be registered as a Tool with a unified schema.
  Schema is inferred from skill metadata / run() signature (MVP static).
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from src.models.skill_definition import SkillDefinitionORM


@dataclass
class Skill:
    id: str
    name: str
    description: str
    level: str  # L1, L2, L3, L4
    code: str
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    status: str = "active"  # active, deprecated, draft
    metadata: Dict = field(default_factory=dict)
    # v4.0 Phase 1 P1-5: 模态支持字段
    modality_support: Dict = field(default_factory=lambda: {"text": True})
    created_at: str = ""
    updated_at: str = ""


@dataclass
class ToolSchema:
    """Unified tool schema for Tool Registry (Harness H1)."""
    skill_id: str
    name: str
    description: str
    input_schema: Dict
    output_schema: Dict
    requires_tools: List[str] = field(default_factory=list)
    requires_toolsets: List[str] = field(default_factory=list)


# In-memory stores
_skill_db: Dict[str, Skill] = {}
_tool_registry: Dict[str, ToolSchema] = {}
_builtin_skills_loaded: bool = False


# Layer loading order (lowest → highest)
_LAYER_ORDER = ["L1", "L2", "L3", "L4"]
_LAYER_RANK = {layer: idx for idx, layer in enumerate(_LAYER_ORDER)}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_builtin_skills() -> None:
    """Seed L1 built-in skills on first access."""
    global _builtin_skills_loaded
    if _builtin_skills_loaded:
        return

    builtins = [
        Skill(
            id="L1-content-generate",
            name="content_generate",
            description="基于话题和平台生成社交媒体内容",
            level="L1",
            code="# Built-in: delegates to ContentForge",
            tags=["内容生成", "built-in"],
            version="1.0.0",
            status="active",
            metadata={
                "tool_schema": {
                    "input": {"topic": "str", "platform": "str", "persona_id": "str"},
                    "output": {"title": "str", "body": "str", "tags": "list"},
                },
                "requires_tools": [],
                "requires_toolsets": [],
            },
            created_at=_now(),
            updated_at=_now(),
        ),
        Skill(
            id="L1-compliance-check",
            name="compliance_check",
            description="检测内容是否符合平台合规要求",
            level="L1",
            code="# Built-in: delegates to ComplianceGuard",
            tags=["合规", "built-in"],
            version="1.0.0",
            status="active",
            metadata={
                "tool_schema": {
                    "input": {"text": "str", "content_id": "str"},
                    "output": {"level": "str", "violations": "list", "warnings": "list"},
                },
                "requires_tools": [],
                "requires_toolsets": [],
            },
            created_at=_now(),
            updated_at=_now(),
        ),
        Skill(
            id="L1-fingerprint-gen",
            name="fingerprint_generate",
            description="为账号生成差异化浏览器指纹",
            level="L1",
            code="# Built-in: delegates to fingerprint_engine",
            tags=["指纹", "built-in"],
            version="1.0.0",
            status="active",
            metadata={
                "tool_schema": {
                    "input": {"account_id": "str"},
                    "output": {"fingerprint": "dict"},
                },
                "requires_tools": [],
                "requires_toolsets": [],
            },
            created_at=_now(),
            updated_at=_now(),
        ),
        Skill(
            id="L1-health-score",
            name="health_score",
            description="计算账号健康度评分",
            level="L1",
            code="# Built-in: delegates to account_health",
            tags=["健康", "built-in"],
            version="1.0.0",
            status="active",
            metadata={
                "tool_schema": {
                    "input": {"account_id": "str"},
                    "output": {"score": "float", "status": "str"},
                },
                "requires_tools": [],
                "requires_toolsets": [],
            },
            created_at=_now(),
            updated_at=_now(),
        ),
        Skill(
            id="L1-engagement-predict",
            name="engagement_predict",
            description="预测内容发布后的互动量区间",
            level="L1",
            code="# Built-in: delegates to prediction_engine",
            tags=["预测", "built-in"],
            version="1.0.0",
            status="active",
            metadata={
                "tool_schema": {
                    "input": {"account_id": "str", "content_type": "str", "topic": "str"},
                    "output": {
                        "likes": "dict", "comments": "dict", "saves": "dict",
                        "interval_mode": "str", "confidence": "float",
                    },
                },
                "requires_tools": [],
                "requires_toolsets": [],
            },
            created_at=_now(),
            updated_at=_now(),
        ),
        Skill(
            id="L1-publish-schedule",
            name="publish_schedule",
            description="错峰调度发布任务",
            level="L1",
            code="# Built-in: delegates to publish_scheduler",
            tags=["发布", "built-in"],
            version="1.0.0",
            status="active",
            metadata={
                "tool_schema": {
                    "input": {"draft_id": "str", "account_id": "str", "platform": "str"},
                    "output": {"task_id": "str", "status": "str", "scheduled_at": "str"},
                },
                "requires_tools": [],
                "requires_toolsets": [],
            },
            created_at=_now(),
            updated_at=_now(),
        ),
        Skill(
            id="L1-qr-login",
            name="qr_login",
            description="启动和轮询平台二维码登录",
            level="L1",
            code="# Built-in: delegates to platform_account_service",
            tags=["登录", "built-in"],
            version="1.0.0",
            status="active",
            metadata={
                "tool_schema": {
                    "input": {"platform": "str", "account_id": "str"},
                    "output": {"qr_url": "str", "status": "str"},
                },
                "requires_tools": [],
                "requires_toolsets": [],
            },
            created_at=_now(),
            updated_at=_now(),
        ),
        Skill(
            id="L1-session-check",
            name="session_check",
            description="检测平台账号会话是否有效",
            level="L1",
            code="# Built-in: delegates to platform_account_service",
            tags=["会话", "built-in"],
            version="1.0.0",
            status="active",
            metadata={
                "tool_schema": {
                    "input": {"account_id": "str"},
                    "output": {"valid": "bool", "expires_at": "str"},
                },
                "requires_tools": [],
                "requires_toolsets": [],
            },
            created_at=_now(),
            updated_at=_now(),
        ),
        Skill(
            id="L1-xhs-note-data-extraction",
            name="xhs_note_data_extraction",
            description="发布后24h自动抓取小红书笔记互动数据（点赞/评论/收藏/分享）",
            level="L1",
            code='''def run(ctx):
    from src.services.xhs_note_data_extraction import fetch_note_engagement
    return fetch_note_engagement(ctx)
''',
            tags=["数据回收", "小红书", "built-in"],
            version="1.0.0",
            status="active",
            metadata={
                "tool_schema": {
                    "input": {"account_id": "str", "platform_post_id": "str"},
                    "output": {
                        "success": "bool",
                        "metrics": {
                            "likes": "int|None",
                            "comments": "int|None",
                            "saves": "int|None",
                            "shares": "int|None",
                            "views": "int|None",
                        },
                        "error": "str|None",
                    },
                },
                "requires_tools": [],
                "requires_toolsets": [],
            },
            created_at=_now(),
            updated_at=_now(),
        ),
    ]
    for skill in builtins:
        _skill_db[skill.id] = skill
        _register_tool(skill)
    _builtin_skills_loaded = True


def _register_tool(skill: Skill) -> None:
    """Register a skill in the Tool Registry."""
    meta = skill.metadata or {}
    tool_schema = meta.get("tool_schema", {})
    _tool_registry[skill.id] = ToolSchema(
        skill_id=skill.id,
        name=skill.name,
        description=skill.description,
        input_schema=tool_schema.get("input", {}),
        output_schema=tool_schema.get("output", {}),
        requires_tools=meta.get("requires_tools", []),
        requires_toolsets=meta.get("requires_toolsets", []),
    )


def _unregister_tool(skill_id: str) -> None:
    _tool_registry.pop(skill_id, None)


def create_skill(
    name: str,
    description: str,
    level: str,
    code: str,
    tags: Optional[List[str]] = None,
    version: str = "1.0.0",
    metadata: Optional[Dict] = None,
    modality_support: Optional[Dict] = None,
) -> Skill:
    _load_builtin_skills()
    skill_id = secrets.token_urlsafe(16)
    now = _now()
    skill = Skill(
        id=skill_id,
        name=name,
        description=description,
        level=level,
        code=code,
        tags=tags or [],
        version=version,
        status="active",
        metadata=metadata or {},
        modality_support=modality_support or {"text": True},
        created_at=now,
        updated_at=now,
    )
    _skill_db[skill_id] = skill
    _register_tool(skill)
    return skill


def get_skill(skill_id: str) -> Optional[Skill]:
    _load_builtin_skills()
    return _skill_db.get(skill_id)


def load_skill(name: str, level: Optional[str] = None) -> Optional[Skill]:
    """Load a skill by name, optionally filtering by level.

    If no level is specified, returns the highest-layer match
    (L4 > L3 > L2 > L1).
    """
    _load_builtin_skills()
    candidates = [s for s in _skill_db.values() if s.name == name]
    if level:
        candidates = [s for s in candidates if s.level == level]
    if not candidates:
        return None
    # Return highest layer match
    candidates.sort(key=lambda s: _LAYER_RANK.get(s.level, 0), reverse=True)
    return candidates[0]


def list_skills(level: Optional[str] = None) -> List[Skill]:
    _load_builtin_skills()
    skills = list(_skill_db.values())
    if level:
        skills = [s for s in skills if s.level == level]
    return skills


def list_builtin_skills() -> List[Skill]:
    return list_skills(level="L1")


def update_skill(skill_id: str, **kwargs) -> Optional[Skill]:
    _load_builtin_skills()
    skill = _skill_db.get(skill_id)
    if skill is None:
        return None
    for key, value in kwargs.items():
        if hasattr(skill, key):
            setattr(skill, key, value)
    skill.updated_at = _now()
    # Re-register tool if metadata changed
    if "metadata" in kwargs:
        _register_tool(skill)
    return skill


def delete_skill(skill_id: str) -> bool:
    _load_builtin_skills()
    if skill_id in _skill_db:
        del _skill_db[skill_id]
        _unregister_tool(skill_id)
        return True
    return False


def clear_skills() -> None:
    _skill_db.clear()
    _tool_registry.clear()
    global _builtin_skills_loaded
    _builtin_skills_loaded = False


# ─── Four-Layer Resolution ───

def resolve_skills(agent_id: Optional[str] = None) -> List[Skill]:
    """Resolve the effective skill set for an agent.

    Loading order: L1 → L2 → L3 → L4.
    Higher layers override lower layers for the same skill name.
    Returns the deduplicated list in name-sorted order.
    """
    _load_builtin_skills()
    effective: Dict[str, Skill] = {}
    for layer in _LAYER_ORDER:
        for skill in _skill_db.values():
            if skill.status != "active":
                continue
            if skill.level == layer:
                effective[skill.name] = skill  # override
    return sorted(effective.values(), key=lambda s: s.name)


def resolve_skills_for_agent(agent_id: str) -> List[Skill]:
    """Resolve skills considering agent-specific bindings.

    L1 → L2 → L3 → L4, then apply agent bindings (priority ordering).
    """
    from src.services.skill_binding import list_bindings

    base = resolve_skills()
    bindings = list_bindings(agent_id=agent_id)
    bound_skill_ids = {b.skill_id for b in bindings}
    # Filter to only bound skills + L1 builtins
    result = [s for s in base if s.id in bound_skill_ids or s.level == "L1"]
    return sorted(result, key=lambda s: s.name)


def check_dependencies(skill_id: str) -> Dict[str, List[str]]:
    """Check whether all required tools / toolsets are available.

    Returns {"missing_tools": [...], "missing_toolsets": [...]}.
    """
    _load_builtin_skills()
    skill = _skill_db.get(skill_id)
    if skill is None:
        return {"missing_tools": [], "missing_toolsets": []}

    meta = skill.metadata or {}
    required_tools = set(meta.get("requires_tools", []))
    required_toolsets = set(meta.get("requires_toolsets", []))

    available_tools = {s.name for s in _skill_db.values() if s.status == "active"}
    available_toolsets: Set[str] = set()
    for s in _skill_db.values():
        for tag in s.tags:
            available_toolsets.add(tag)

    return {
        "missing_tools": sorted(required_tools - available_tools),
        "missing_toolsets": sorted(required_toolsets - available_toolsets),
    }


# ─── Tool Registry ───

def get_tool_schema(skill_id: str) -> Optional[ToolSchema]:
    _load_builtin_skills()
    return _tool_registry.get(skill_id)


def list_tools() -> List[ToolSchema]:
    _load_builtin_skills()
    return list(_tool_registry.values())


def list_tools_by_layer(layer: Optional[str] = None) -> List[ToolSchema]:
    _load_builtin_skills()
    schemas = list(_tool_registry.values())
    if layer:
        schemas = [t for t in schemas if _skill_db.get(t.skill_id, Skill("", "", "", "", "")).level == layer]
    return schemas


# ─── Hermes-Agent Import ───

def import_hermes_skill(skill_md_content: str) -> Optional[Skill]:
    """Import a hermes-agent SKILL.md as an L2 Configured skill."""
    from src.services.hermes_skill_adapter import adapt_hermes_skill

    adapted = adapt_hermes_skill(skill_md_content)
    if adapted is None:
        return None
    adapted["level"] = "L2"
    return create_skill(**adapted)


def discover_and_import_hermes_skills(directory: str) -> List[Skill]:
    """Discover and import all hermes-agent skills from a directory."""
    from src.services.hermes_skill_adapter import discover_hermes_skills as _discover

    adapted_list = _discover(directory)
    results: List[Skill] = []
    for adapted in adapted_list:
        adapted["level"] = "L2"
        skill = create_skill(**adapted)
        results.append(skill)
    return results


# ─── Skill Execution ───

def execute_skill(skill_id: str, context: Dict) -> Dict:
    """Execute a skill with given context.

    MVP: Extracts a `run(ctx)` function from skill code and calls it.
    Production: Use isolated sandbox / WASM / restricted Python.
    """
    skill = get_skill(skill_id)
    if skill is None:
        return {"success": False, "error": "Skill not found", "result": None}

    # Dependency check
    deps = check_dependencies(skill_id)
    if deps["missing_tools"] or deps["missing_toolsets"]:
        return {
            "success": False,
            "error": f"Missing dependencies: tools={deps['missing_tools']}, toolsets={deps['missing_toolsets']}",
            "result": None,
        }

    # Simple safe execution pattern for MVP
    # L1 built-in skills are trusted system code → full builtins
    # L2-L4 are external/user code → restricted sandbox
    safe_globals = {"__builtins__": __builtins__} if skill.level == "L1" else {"__builtins__": {}}
    safe_locals = {}

    try:
        exec(skill.code, safe_globals, safe_locals)
        run_fn = safe_locals.get("run")
        if run_fn and callable(run_fn):
            result = run_fn(context)
            return {"success": True, "result": result, "error": None}
        # If no run() function, return the code as-is (for delegation skills)
        return {"success": True, "result": skill.code, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e), "result": None}


# ═══════════════════════════════════════════════════════
# P3-1: Skill Hub Registration & Validation v4.0
# ═══════════════════════════════════════════════════════

from packaging.version import Version, InvalidVersion

# ─── Skill Definition (JSON Schema) ───

@dataclass
class SkillDefinition:
    """Formal skill definition with JSON Schema validation."""
    skill_id: str
    name: str
    description: str
    version: str = "1.0.0"
    level: str = "L2"  # L1, L2, L3, L4
    input_schema: Dict = field(default_factory=dict)
    output_schema: Dict = field(default_factory=dict)
    modality_support: Dict = field(default_factory=lambda: {"text": True})
    requires_llm: bool = False
    llm_model_preference: str = ""
    required_functions: List[str] = field(default_factory=list)
    permissions: Dict = field(default_factory=dict)
    code: str = ""
    metadata: Dict = field(default_factory=dict)
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""


# ─── Agent-Skill Binding ───

@dataclass
class AgentSkillBinding:
    agent_id: str
    skill_id: str
    priority: int = 0
    config: Dict = field(default_factory=dict)
    granted_at: str = ""
    granted_by: str = ""


_agent_skill_bindings: List[AgentSkillBinding] = []
_skill_versions: Dict[str, List[SkillDefinition]] = {}  # skill_id -> versions


def _validate_json_schema(schema: Dict, label: str = "schema") -> List[str]:
    """Validate a JSON Schema is structurally valid. MVP: basic checks."""
    errors = []
    if not isinstance(schema, dict):
        errors.append(f"{label} must be a dict")
        return errors
    # Empty dict is allowed (no schema constraint)
    if not schema:
        return errors
    if "type" not in schema and "properties" not in schema and "items" not in schema:
        errors.append(f"{label} should have 'type', 'properties', or 'items'")
    return errors


def register(definition: SkillDefinition) -> SkillDefinition:
    """Register a new Skill with JSON Schema validation.

    Validates:
    - skill_id uniqueness (if same skill_id, create new version)
    - input_schema / output_schema are valid JSON Schema
    - version is valid semantic version
    """
    # Schema validation
    schema_errors = _validate_json_schema(definition.input_schema, "input_schema")
    schema_errors += _validate_json_schema(definition.output_schema, "output_schema")
    if schema_errors:
        raise ValueError(f"Schema validation failed: {'; '.join(schema_errors)}")

    # Semantic version validation
    try:
        Version(definition.version)
    except InvalidVersion:
        raise ValueError(f"Invalid semantic version: {definition.version}")

    now = _now()
    definition.created_at = now
    definition.updated_at = now

    # Store in version history
    versions = _skill_versions.setdefault(definition.skill_id, [])
    versions.append(definition)
    versions.sort(key=lambda d: Version(d.version), reverse=True)

    # Also register as Skill for backward compatibility
    skill = Skill(
        id=definition.skill_id,
        name=definition.name,
        description=definition.description,
        level=definition.level,
        code=definition.code,
        version=definition.version,
        status=definition.status,
        metadata=definition.metadata,
        modality_support=definition.modality_support,
        created_at=now,
        updated_at=now,
    )
    _skill_db[definition.skill_id] = skill
    _register_tool(skill)

    return definition


def bind_to_agent(
    skill_id: str,
    agent_id: str,
    priority: int = 0,
    config: Optional[Dict] = None,
    granted_by: str = "",
) -> AgentSkillBinding:
    """Bind a Skill to an Agent with optional config."""
    binding = AgentSkillBinding(
        agent_id=agent_id,
        skill_id=skill_id,
        priority=priority,
        config=config or {},
        granted_at=_now(),
        granted_by=granted_by,
    )
    _agent_skill_bindings.append(binding)
    return binding


def get_agent_skills(agent_id: str) -> List[SkillDefinition]:
    """Get all skills bound to an agent (highest version per skill)."""
    bound_skill_ids = {b.skill_id for b in _agent_skill_bindings if b.agent_id == agent_id}
    # Also include L1 builtins
    _load_builtin_skills()
    for sid, skill in _skill_db.items():
        if skill.level == "L1":
            bound_skill_ids.add(sid)

    results = []
    for sid in bound_skill_ids:
        versions = _skill_versions.get(sid)
        if versions:
            results.append(versions[0])  # latest version
        else:
            skill = _skill_db.get(sid)
            if skill:
                results.append(SkillDefinition(
                    skill_id=skill.id,
                    name=skill.name,
                    description=skill.description,
                    version=skill.version,
                    level=skill.level,
                    code=skill.code,
                    modality_support=skill.modality_support,
                    metadata=skill.metadata,
                ))
    return results


def validate_invocation(
    skill_id: str,
    agent_id: str,
    inputs: Dict,
) -> Dict:
    """Validate that an agent can invoke a skill and inputs match schema.

    Returns {"valid": bool, "errors": List[str]}
    """
    errors = []

    # 1. Check agent has permission (binding exists or skill is L1)
    has_permission = False
    for b in _agent_skill_bindings:
        if b.agent_id == agent_id and b.skill_id == skill_id:
            has_permission = True
            break
    # L1 skills are public
    skill = get_skill(skill_id)
    if skill and skill.level == "L1":
        has_permission = True
    if not has_permission:
        errors.append(f"Agent '{agent_id}' is not bound to skill '{skill_id}'")

    # 2. Check input schema
    versions = _skill_versions.get(skill_id, [])
    definition = versions[0] if versions else None
    if definition and definition.input_schema:
        input_errors = _validate_inputs_against_schema(inputs, definition.input_schema)
        errors.extend(input_errors)

    return {"valid": len(errors) == 0, "errors": errors}


def _validate_inputs_against_schema(inputs: Dict, schema: Dict) -> List[str]:
    """MVP input validation: check required properties exist and types match."""
    errors = []
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    for prop in required:
        if prop not in inputs:
            errors.append(f"Missing required input: '{prop}'")

    for key, value in inputs.items():
        prop_schema = properties.get(key)
        if prop_schema:
            expected_type = prop_schema.get("type")
            if expected_type and not _type_matches(value, expected_type):
                errors.append(
                    f"Input '{key}' has wrong type: expected {expected_type}, got {type(value).__name__}"
                )

    return errors


def _type_matches(value: Any, expected: str) -> bool:
    """Check if a Python value matches a JSON Schema type."""
    mapping = {
        "string": (str,),
        "integer": (int,),
        "number": (int, float),
        "boolean": (bool,),
        "array": (list, tuple),
        "object": (dict,),
        "null": (type(None),),
    }
    return isinstance(value, mapping.get(expected, (object,)))


def get_skill_versions(skill_id: str) -> List[SkillDefinition]:
    """Get all versions of a skill, sorted by version descending."""
    return list(_skill_versions.get(skill_id, []))


def get_latest_version(skill_id: str) -> Optional[SkillDefinition]:
    """Get the latest version of a skill."""
    versions = _skill_versions.get(skill_id)
    return versions[0] if versions else None


# ─── P8-5: ORM Integration ───


def _orm_to_dataclass(orm: SkillDefinitionORM) -> SkillDefinition:
    """Convert ORM instance to in-memory dataclass."""
    from typing import cast
    return SkillDefinition(
        skill_id=cast(str, orm.skill_id),
        name=cast(str, orm.name),
        version=cast(str, orm.version),
        description=cast(str, orm.description) or "",
        level=cast(str, orm.level),
        input_schema=cast(Dict, orm.input_schema) or {},
        output_schema=cast(Dict, orm.output_schema) or {},
        modality_support=cast(Dict, orm.modality_support) or {"text": True},
        requires_llm=cast(bool, orm.requires_llm),
        llm_model_preference=cast(str, orm.llm_model_preference) or "",
        required_functions=cast(List[str], orm.required_functions) or [],
        permissions=cast(Dict, orm.permissions) or {},
        code=cast(str, orm.code_path) or "",
        status=cast(str, orm.status),
        meta=cast(Dict, orm.meta) or {},
    )


async def load_skills_from_orm(db_session) -> int:
    """Load all active skills from DB into in-memory registry.

    Called during startup or admin-triggered refresh.
    Returns count of loaded skills.
    """
    from sqlalchemy import select
    result = await db_session.execute(
        select(SkillDefinitionORM).where(SkillDefinitionORM.status == "active")
    )
    orm_skills = result.scalars().all()
    count = 0
    for orm in orm_skills:
        sd = _orm_to_dataclass(orm)
        register(sd)
        count += 1
    return count


async def save_skill_to_orm(db_session, skill_def: SkillDefinition) -> SkillDefinitionORM:
    """Persist a SkillDefinition to DB (upsert)."""
    from sqlalchemy import select
    result = await db_session.execute(
        select(SkillDefinitionORM).where(
            SkillDefinitionORM.skill_id == skill_def.skill_id,
            SkillDefinitionORM.version == skill_def.version,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.name = skill_def.name
        existing.description = skill_def.description
        existing.level = skill_def.level
        existing.input_schema = skill_def.input_schema
        existing.output_schema = skill_def.output_schema
        existing.modality_support = skill_def.modality_support
        existing.requires_llm = skill_def.requires_llm
        existing.llm_model_preference = skill_def.llm_model_preference
        existing.required_functions = skill_def.required_functions
        existing.permissions = skill_def.permissions
        existing.code_path = skill_def.code
        existing.status = skill_def.status
        existing.meta = skill_def.metadata
        existing.updated_at = datetime.now(timezone.utc)
        await db_session.flush()
        return existing
    else:
        orm = SkillDefinitionORM(
            skill_id=skill_def.skill_id,
            name=skill_def.name,
            description=skill_def.description,
            version=skill_def.version,
            level=skill_def.level,
            input_schema=skill_def.input_schema,
            output_schema=skill_def.output_schema,
            modality_support=skill_def.modality_support,
            requires_llm=skill_def.requires_llm,
            llm_model_preference=skill_def.llm_model_preference,
            required_functions=skill_def.required_functions,
            permissions=skill_def.permissions,
            code_path=skill_def.code,
            status=skill_def.status,
            meta=skill_def.metadata,
        )
        db_session.add(orm)
        await db_session.flush()
        return orm
