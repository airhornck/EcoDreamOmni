"""Prompt Registry — Prompt versioning, variable whitelist, secure rendering.

Aligned with detailed design §9 / PRD V2.6 §10.5.
Open-source: Jinja2 SandboxedEnvironment.
"""

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from jinja2.sandbox import SandboxedEnvironment
    from jinja2.meta import find_undeclared_variables
except ImportError:  # pragma: no cover
    SandboxedEnvironment = None  # type: ignore
    find_undeclared_variables = None  # type: ignore


class PromptStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class VariableType(str, Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    ENUM = "ENUM"
    JSON = "JSON"


# ─── Dataclasses ───

@dataclass
class PromptTemplate:
    id: str
    name: str
    agent_id: str
    version: int
    env: str
    template_content: str
    variables: List[str]
    system_fingerprint: str
    status: PromptStatus
    approval_status: ApprovalStatus
    performance_score: Optional[float]
    langfuse_prompt_id: Optional[str]
    created_by: str
    created_at: str
    updated_at: str


@dataclass
class PromptVariable:
    name: str
    description: str
    type: VariableType
    allowed_values: Optional[List[str]]
    max_length: int
    required: bool
    default_value: Optional[str]
    validation_regex: Optional[str]
    created_at: str


@dataclass
class PromptPerformance:
    id: str
    template_id: str
    version: int
    date: str
    invocations: int
    avg_quality_score: Optional[float]
    avg_token_cost: Optional[float]
    human_intervention_rate: Optional[float]
    task_completion_rate: Optional[float]
    fail_rate: Optional[float]


# ─── In-memory stores ───
# template_id -> list of versions (ordered by version number)
_template_versions_db: Dict[str, List[PromptTemplate]] = {}
_variable_db: Dict[str, PromptVariable] = {}
_performance_db: List[PromptPerformance] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(8)}"


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _get_latest_version(template_id: str) -> Optional[PromptTemplate]:
    versions = _template_versions_db.get(template_id, [])
    return versions[-1] if versions else None


def _get_all_versions(template_id: str) -> List[PromptTemplate]:
    return _template_versions_db.get(template_id, [])[:]


# ─── Secure Prompt Renderer ───

class SecurePromptRenderer:
    """Jinja2 sandbox + variable whitelist + injection detection."""

    INJECTION_BLACKLIST = [
        r"ignore\s+previous\s+instructions",
        r"system\s+override",
        r"ignore\s+above",
        r"disregard\s+.*prompt",
        r"__\w+__",
        r"\{\{.*\{\{.*\}\}.*\}\}",  # nested braces (SSTI-like)
    ]
    MAX_VARIABLE_LENGTH = 1000

    def __init__(self, registered_variables: set[str]):
        self.registered_variables = registered_variables
        self.env = SandboxedEnvironment() if SandboxedEnvironment else None

    def validate_template(self, template_content: str) -> tuple[bool, str]:
        if self.env is None:
            # Fallback: basic regex check
            unknown = set()
            for match in re.finditer(r"\{\{\s*(\w+)\s*\}\}", template_content):
                var = match.group(1)
                if var not in self.registered_variables:
                    unknown.add(var)
            if unknown:
                return False, f"未注册变量: {', '.join(unknown)}"
            return True, "OK"

        try:
            ast = self.env.parse(template_content)
            undeclared = find_undeclared_variables(ast)
        except Exception as e:
            return False, f"Template parse error: {e}"

        unknown = undeclared - self.registered_variables
        if unknown:
            return False, f"未注册变量: {', '.join(unknown)}"

        for pattern in self.INJECTION_BLACKLIST:
            if re.search(pattern, template_content, re.IGNORECASE):
                return False, f"检测到潜在 Prompt 注入模式: {pattern}"

        return True, "OK"

    def render(self, template_content: str, variables: Dict[str, Any]) -> str:
        if self.env is None:
            # Fallback: simple string replacement
            result = template_content
            for name, value in variables.items():
                if name not in self.registered_variables:
                    raise ValueError(f"未注册变量: {name}")
                val = str(value)
                if len(val) > self.MAX_VARIABLE_LENGTH:
                    val = val[:self.MAX_VARIABLE_LENGTH]
                result = result.replace(f"{{{{ {name} }}}}", val)
                result = result.replace(f"{{{{{name}}}}}", val)
            return result

        for name, value in variables.items():
            if name not in self.registered_variables:
                raise ValueError(f"未注册变量: {name}")
            if isinstance(value, str) and len(value) > self.MAX_VARIABLE_LENGTH:
                variables[name] = value[:self.MAX_VARIABLE_LENGTH]

        template = self.env.from_string(template_content)
        return template.render(**variables)


# ─── Prompt Variable Registry ───

def register_variable(
    name: str,
    description: str,
    type: str = "STRING",
    allowed_values: Optional[List[str]] = None,
    max_length: int = 100,
    required: bool = True,
    default_value: Optional[str] = None,
    validation_regex: Optional[str] = None,
) -> PromptVariable:
    var = PromptVariable(
        name=name,
        description=description,
        type=VariableType(type),
        allowed_values=allowed_values,
        max_length=max_length,
        required=required,
        default_value=default_value,
        validation_regex=validation_regex,
        created_at=_now(),
    )
    _variable_db[name] = var
    return var


def get_variable(name: str) -> Optional[PromptVariable]:
    return _variable_db.get(name)


def list_variables() -> List[PromptVariable]:
    return list(_variable_db.values())


def delete_variable(name: str) -> bool:
    return _variable_db.pop(name, None) is not None


# ─── Prompt Template Management ───

def create_template(
    name: str,
    agent_id: str,
    template_content: str,
    variables: List[str],
    created_by: str,
    env: str = "prod",
) -> PromptTemplate:
    # Validate all variables are registered
    renderer = SecurePromptRenderer(set(_variable_db.keys()))
    ok, msg = renderer.validate_template(template_content)
    if not ok:
        raise ValueError(msg)

    # Check all declared variables are registered
    unknown = set(variables) - set(_variable_db.keys())
    if unknown:
        raise ValueError(f"未注册变量: {', '.join(unknown)}")

    tmpl_id = _new_id("tmpl")
    now = _now()
    tmpl = PromptTemplate(
        id=tmpl_id,
        name=name,
        agent_id=agent_id,
        version=1,
        env=env,
        template_content=template_content,
        variables=variables,
        system_fingerprint=_sha256(template_content),
        status=PromptStatus.DRAFT,
        approval_status=ApprovalStatus.PENDING,
        performance_score=None,
        langfuse_prompt_id=None,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    _template_versions_db[tmpl_id] = [tmpl]
    return tmpl


def create_template_version(
    template_id: str,
    template_content: str,
    variables: List[str],
    created_by: str,
) -> PromptTemplate:
    versions = _template_versions_db.get(template_id)
    if not versions:
        raise ValueError(f"Template not found: {template_id}")
    existing = versions[-1]

    renderer = SecurePromptRenderer(set(_variable_db.keys()))
    ok, msg = renderer.validate_template(template_content)
    if not ok:
        raise ValueError(msg)

    unknown = set(variables) - set(_variable_db.keys())
    if unknown:
        raise ValueError(f"未注册变量: {', '.join(unknown)}")

    new_version = existing.version + 1
    now = _now()
    tmpl = PromptTemplate(
        id=template_id,
        name=existing.name,
        agent_id=existing.agent_id,
        version=new_version,
        env=existing.env,
        template_content=template_content,
        variables=variables,
        system_fingerprint=_sha256(template_content),
        status=PromptStatus.DRAFT,
        approval_status=ApprovalStatus.PENDING,
        performance_score=None,
        langfuse_prompt_id=None,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    # Archive previous version
    existing.status = PromptStatus.ARCHIVED
    versions.append(tmpl)
    return tmpl


def get_template(template_id: str, version: Optional[int] = None) -> Optional[PromptTemplate]:
    versions = _template_versions_db.get(template_id, [])
    if version is None:
        return versions[-1] if versions else None
    for v in versions:
        if v.version == version:
            return v
    return None


def list_templates(
    agent_id: Optional[str] = None,
    env: Optional[str] = None,
    status: Optional[str] = None,
) -> List[PromptTemplate]:
    results = []
    for versions in _template_versions_db.values():
        results.extend(versions)
    if agent_id:
        results = [t for t in results if t.agent_id == agent_id]
    if env:
        results = [t for t in results if t.env == env]
    if status:
        results = [t for t in results if t.status.value == status]
    return results


def activate_template(template_id: str) -> Optional[PromptTemplate]:
    tmpl = _get_latest_version(template_id)
    if not tmpl:
        return None
    # Archive any other ACTIVE version for same agent+env+name
    for versions in _template_versions_db.values():
        for t in versions:
            if (
                t.id == template_id
                and t.version != tmpl.version
                and t.agent_id == tmpl.agent_id
                and t.env == tmpl.env
                and t.name == tmpl.name
                and t.status == PromptStatus.ACTIVE
            ):
                t.status = PromptStatus.ARCHIVED
    tmpl.status = PromptStatus.ACTIVE
    tmpl.updated_at = _now()
    return tmpl


def archive_template(template_id: str) -> Optional[PromptTemplate]:
    tmpl = _get_latest_version(template_id)
    if not tmpl:
        return None
    tmpl.status = PromptStatus.ARCHIVED
    tmpl.updated_at = _now()
    return tmpl


def delete_template(template_id: str) -> bool:
    return _template_versions_db.pop(template_id, None) is not None


# ─── Rendering ───

def render_template(
    template_id: str,
    variables: Dict[str, Any],
    dry_run: bool = False,
) -> Dict[str, Any]:
    tmpl = _get_latest_version(template_id)
    if not tmpl:
        raise ValueError(f"Template not found: {template_id}")

    renderer = SecurePromptRenderer(set(_variable_db.keys()))
    try:
        rendered = renderer.render(tmpl.template_content, variables)
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "template_id": template_id,
            "version": tmpl.version,
        }

    if not dry_run:
        # Record performance placeholder
        _record_invocation(template_id, tmpl.version)

    return {
        "ok": True,
        "rendered": rendered,
        "template_id": template_id,
        "version": tmpl.version,
        "dry_run": dry_run,
    }


def _record_invocation(template_id: str, version: int):
    today = datetime.now(timezone.utc).date().isoformat()
    for p in _performance_db:
        if p.template_id == template_id and p.version == version and p.date == today:
            p.invocations += 1
            return
    _performance_db.append(
        PromptPerformance(
            id=_new_id("perf"),
            template_id=template_id,
            version=version,
            date=today,
            invocations=1,
            avg_quality_score=None,
            avg_token_cost=None,
            human_intervention_rate=None,
            task_completion_rate=None,
            fail_rate=None,
        )
    )


def get_performance(template_id: str, version: int) -> Optional[PromptPerformance]:
    today = datetime.now(timezone.utc).date().isoformat()
    for p in _performance_db:
        if p.template_id == template_id and p.version == version and p.date == today:
            return p
    return None


# ─── Clear stores (for testing) ───

def _clear_stores():
    _template_versions_db.clear()
    _variable_db.clear()
    _performance_db.clear()
