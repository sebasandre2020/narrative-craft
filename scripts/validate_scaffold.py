#!/usr/bin/env python3
"""
Scaffold and Contract Validator for Narrative-Craft.
Ensures repository structure, OpenAPI 3.1 contract, JSON Schemas, SQL schemas,
and example payloads conform to architectural standards.
"""

import json
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    print(f"[+] Validating Narrative-Craft scaffold at: {repo_root}")

    errors = []

    # 1. Required Core Files
    required_files = [
        "README.md",
        "Architecture.md",
        "Class.md",
        "Index.md",
        "Operations.md",
        "PROJECT_BRIEF.md",
        "compose.yaml",
        "pyproject.toml",
        "requirements-dev.txt",
        ".env.example",
        ".gitignore",
        ".github/workflows/scaffold.yml",
        "contracts/openapi.json",
        "contracts/schemas.json",
        "infra/postgres/001_init_schema.sql",
        "infra/docker/Dockerfile.blueprint",
        "infra/terraform/main.tf",
        "infra/terraform/variables.tf",
        "infra/terraform/outputs.tf",
        "examples/create_world.json",
        "examples/narrative_turn_request.json",
        "examples/narrative_turn_response.json",
        "examples/graph_delta_sample.json",
        "examples/branch_timeline.json"
    ]

    for rel_path in required_files:
        p = repo_root / rel_path
        if not p.is_file():
            errors.append(f"Missing required file: {rel_path}")
        elif p.stat().st_size == 0:
            errors.append(f"File is empty: {rel_path}")

    # 2. JSON Syntax & Contract Validation
    json_targets = list((repo_root / "contracts").glob("*.json")) + list((repo_root / "examples").glob("*.json"))
    for json_file in json_targets:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, (dict, list)):
                errors.append(f"JSON root in {json_file.name} is not object or array")
        except Exception as e:
            errors.append(f"Invalid JSON in {json_file.name}: {e}")

    # 3. OpenAPI 3.1 Basic Sanity
    openapi_path = repo_root / "contracts" / "openapi.json"
    if openapi_path.is_file():
        try:
            with open(openapi_path, "r", encoding="utf-8") as f:
                spec = json.load(f)
            assert spec.get("openapi", "").startswith("3.1"), "OpenAPI spec must be 3.1.x"
            assert "paths" in spec, "OpenAPI spec missing 'paths'"
            assert "/v1/timelines/{timeline_id}/turns" in spec["paths"], "Missing turns endpoint"
        except Exception as e:
            errors.append(f"OpenAPI validation failed: {e}")

    # 4. SQL Schema Sanity
    sql_path = repo_root / "infra" / "postgres" / "001_init_schema.sql"
    if sql_path.is_file():
        sql_text = sql_path.read_text(encoding="utf-8")
        expected_tables = ["worlds", "timelines", "narrative_events", "graph_nodes", "graph_edges"]
        for table in expected_tables:
            if f"CREATE TABLE IF NOT EXISTS {table}" not in sql_text:
                errors.append(f"SQL missing table definition: {table}")

    if errors:
        print("\n[!] Scaffold Validation Failed with errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("\n[OK] Scaffold Validation Succeeded! All contracts, schemas, files, and fixtures verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
