#!/usr/bin/env python3
"""Generate backend API route documentation from source code.

Scans apps/backend/src/api/*.py for APIRouter definitions and route decorators,
then generates a markdown table for docs/数据词典/02-后端API路由层.md.
"""

import re
import sys
from pathlib import Path

API_DIR = Path(__file__).parent.parent / "apps" / "backend" / "src" / "api"
OUTPUT_FILE = (
    Path(__file__).parent.parent
    / "docs"
    / "数据词典"
    / "02-后端API路由层.md"
)


def extract_router_prefix(source: str) -> str:
    """Extract APIRouter prefix from source code."""
    match = re.search(
        r'router\s*=\s*APIRouter\(\s*[^)]*prefix\s*=\s*["\']([^"\']+)["\']',
        source,
    )
    if match:
        return match.group(1)
    # Fallback: look for prefix= on a separate line
    match = re.search(
        r'prefix\s*=\s*["\']([^"\']+)["\']',
        source,
    )
    return match.group(1) if match else ""


def extract_routes(source: str) -> list[dict]:
    """Extract all @router.<method>("/path") decorators and their function names."""
    routes = []

    # Pattern for decorators like @router.get("/path", ...) or @router.post(...)
    # We need to match the decorator and the following function definition
    pattern = re.compile(
        r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']*)["\'][^)]*\)\s*\n\s*async\s+def\s+(\w+)',
        re.IGNORECASE,
    )

    for match in pattern.finditer(source):
        method = match.group(1).upper()
        path = match.group(2)
        handler = match.group(3)
        routes.append(
            {
                "method": method,
                "path": path,
                "handler": handler,
            }
        )

    # Also match decorators without quotes (using variables) — less common
    pattern2 = re.compile(
        r'@router\.(get|post|put|patch|delete)\(([^)]+)\)\s*\n\s*async\s+def\s+(\w+)',
        re.IGNORECASE,
    )
    for match in pattern2.finditer(source):
        method = match.group(1).upper()
        path_arg = match.group(2).strip()
        handler = match.group(3)
        # Skip if already captured by first pattern
        if any(r["handler"] == handler and r["method"] == method for r in routes):
            continue
        # Extract string literal from path_arg
        str_match = re.search(r'["\']([^"\']+)["\']', path_arg)
        path = str_match.group(1) if str_match else path_arg
        routes.append(
            {
                "method": method,
                "path": path,
                "handler": handler,
            }
        )

    return routes


def generate_markdown(api_files: list[Path]) -> str:
    """Generate markdown documentation from API files."""
    lines = ["# 后端 API 路由总览\n", "> **自动生成于** 2026-05-28\n", ""]

    total_endpoints = 0

    for api_file in sorted(api_files):
        if api_file.name.startswith("__"):
            continue

        source = api_file.read_text(encoding="utf-8")
        prefix = extract_router_prefix(source)
        routes = extract_routes(source)

        if not routes:
            continue

        total_endpoints += len(routes)

        module_name = api_file.stem
        lines.append(f"## {module_name}.py\n")
        lines.append(f"- **Router Prefix**: `{prefix}`\n")
        lines.append("")
        lines.append("| 方法 | 路径 | Handler |")
        lines.append("|------|------|---------|")

        for route in routes:
            full_path = f"{prefix}{route['path']}"
            lines.append(
                f"| {route['method']} | `{full_path}` | `{route['handler']}()` |"
            )

        lines.append("")

    # Prepend summary
    lines.insert(
        3, f"> **统计**: {len([f for f in api_files if not f.name.startswith('__')])} 个路由文件，{total_endpoints} 个端点\n"
    )

    return "\n".join(lines)


def main() -> int:
    api_files = list(API_DIR.glob("*.py"))
    markdown = generate_markdown(api_files)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(markdown, encoding="utf-8")

    print(f"Generated {OUTPUT_FILE}")
    print(f"Scanned {len(api_files)} files, wrote API documentation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
