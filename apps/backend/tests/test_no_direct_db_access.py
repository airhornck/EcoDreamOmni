"""FUNC-ARCH: Architecture red-line — Agent禁止直接操作数据库.

Static scan ensures zero direct database access outside Function layer.
Aligned with PRD V3.1 architecture / TASK_V2.7.1 FUNC-ARCH.
"""

import ast
import pathlib
from typing import List, Set

import pytest

PROJECT_ROOT = pathlib.Path(__file__).parent.parent / "src"

# Direct DB access patterns that are forbidden outside Function layer
FORBIDDEN_PATTERNS = [
    "session.execute",
    "session.query",
    "db.query",
    "AsyncSessionLocal",
    "get_db()",
]

# Import patterns indicating DB layer usage
FORBIDDEN_IMPORTS = [
    "from src.core.database import",
    "from sqlalchemy.ext.asyncio import AsyncSession",
]

# Paths allowed to use DB directly (Function layer + infrastructure + API routes)
ALLOWED_PATHS = [
    "src/models/",
    "src/core/database.py",
    "src/core/config.py",
    "src/core/dependencies.py",
    "src/api/",
    "src/main.py",
]

# Services that ARE Function layer and allowed DB access
FUNCTION_LAYER_SERVICES = [
    "asset_pool_function.py",
    "auth_function.py",
    "brand_knowledge_function.py",
    "vetdrug_db_function.py",
    "timeline_library_function.py",
    "platform_rule_function.py",
    "prohibited_word_function.py",
    "task_function.py",
    "celery_tasks_function.py",
]


def _collect_py_files(base: pathlib.Path) -> List[pathlib.Path]:
    """Collect all .py files under base, excluding __pycache__."""
    files = []
    for f in base.rglob("*.py"):
        if "__pycache__" in str(f):
            continue
        files.append(f)
    return files


def _is_allowed(path: pathlib.Path) -> bool:
    """Check if a file is in the allowed DB-access list."""
    rel = path.relative_to(PROJECT_ROOT.parent)
    rel_str = str(rel).replace("\\", "/")

    for allowed in ALLOWED_PATHS:
        if rel_str.startswith(allowed) or rel_str == allowed:
            return True

    if "services/" in rel_str:
        for func_file in FUNCTION_LAYER_SERVICES:
            if rel_str.endswith(f"services/{func_file}"):
                return True

    return False


def _scan_file_for_forbidden(path: pathlib.Path) -> List[str]:
    """Scan a single file for forbidden DB access patterns."""
    violations = []
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    lines = source.splitlines()
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith("#"):
            continue

        for pattern in FORBIDDEN_IMPORTS:
            if pattern in stripped:
                violations.append(f"{path}:{lineno} forbidden import: {pattern}")

        # Heuristic: direct session usage (not perfect but catches obvious cases)
        # We parse AST for more accuracy below

    # AST-based check for AsyncSession import and usage
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return violations

    has_async_session_import = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if "asyncio" in module or "database" in module:
                for alias in node.names:
                    if alias.name == "AsyncSession":
                        has_async_session_import = True
        if isinstance(node, (ast.Call, ast.Attribute)):
            # Check for session.execute / session.query patterns
            name = ast.unparse(node) if hasattr(ast, "unparse") else ""
            if name and ("session.execute" in name or "session.query" in name):
                violations.append(f"{path}: AST-detected direct DB call: {name}")

    return violations


@pytest.fixture(scope="session")
def scan_violations() -> List[str]:
    """Run static scan once per session."""
    all_violations: List[str] = []
    files = _collect_py_files(PROJECT_ROOT)
    for f in files:
        if _is_allowed(f):
            continue
        all_violations.extend(_scan_file_for_forbidden(f))
    return all_violations


def test_no_direct_db_access_in_agent_layer(scan_violations):
    """🔴 静态扫描: Agent层禁止直接数据库访问 — 目标0处违规."""
    if scan_violations:
        pytest.fail(
            f"Direct DB access violations found ({len(scan_violations)}):\n"
            + "\n".join(scan_violations)
        )


def test_function_layer_files_exist():
    """🟢 Function层ORM Service文件存在."""
    services_dir = PROJECT_ROOT / "services"
    for fname in FUNCTION_LAYER_SERVICES:
        assert (services_dir / fname).exists(), f"Missing Function layer: {fname}"


def test_alembic_migration_exists():
    """🟢 Alembic迁移脚本存在."""
    migrations = list((PROJECT_ROOT.parent / "alembic" / "versions").glob("*.py"))
    # Exclude __pycache__
    migrations = [m for m in migrations if "__pycache__" not in str(m)]
    assert len(migrations) >= 2, "Expected at least 2 migrations (initial + W14)"
