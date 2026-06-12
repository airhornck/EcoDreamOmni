"""Export OpenAPI spec to JSON/YAML — W29 documentation automation.

Usage:
  python scripts/export_openapi.py --format json --output docs/openapi.json
  python scripts/export_openapi.py --format yaml --output docs/openapi.yaml
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app


def export_spec(fmt: str, output_path: str):
    spec = app.openapi()

    if fmt == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
    else:
        try:
            import yaml
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(spec, f, allow_unicode=True, sort_keys=False)
        except ImportError:
            print("PyYAML not installed. Install with: pip install pyyaml")
            sys.exit(1)

    print(f"OpenAPI spec exported to {output_path} ({fmt})")
    print(f"  Title: {spec['info']['title']}")
    print(f"  Version: {spec['info']['version']}")
    print(f"  Routes: {len(spec['paths'])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export EcoDreamOmni OpenAPI spec")
    parser.add_argument("--format", choices=["json", "yaml"], default="json")
    parser.add_argument("--output", default="docs/openapi.json")
    args = parser.parse_args()
    export_spec(args.format, args.output)
