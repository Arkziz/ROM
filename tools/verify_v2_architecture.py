#!/usr/bin/env python3
"""Enforce the complete ROM V2 architecture without importing runtime modules."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

LAYER_ORDER = {
    "domain": 0,
    "application": 1,
    "infrastructure": 2,
    "app": 3,
    "content": 0,
}
FORBIDDEN_EXTERNAL_ROOTS = {"telegram", "aiogram", "sqlite3", "sqlalchemy", "aiosqlite"}
FORBIDDEN_CATCH_ALL_MODULES = {
    "common.py", "helper.py", "helpers.py", "utils.py", "utility.py",
    "misc.py", "manager.py", "service.py", "services.py", "shared.py",
}
REQUIRED_FILES = {
    "rom_v2/__init__.py",
    "rom_v2/main.py",
    "rom_v2/bootstrap.py",
    "rom_v2/config.py",
    "rom_v2/container.py",
    "rom_v2/lifecycle.py",
    "rom_v2/runtime_paths.py",
    "rom_v2/settings.py",
    "rom_v2/structured_logging.py",
    "rom_v2/domain/__init__.py",
    "rom_v2/application/__init__.py",
    "rom_v2/application/ports/repositories.py",
    "rom_v2/application/ports/unit_of_work.py",
    "rom_v2/application/ports/clock.py",
    "rom_v2/application/ports/random_source.py",
    "rom_v2/infrastructure/__init__.py",
    "rom_v2/app/__init__.py",
    "rom_v2/content/__init__.py",
}


def _layer(relative_path: str) -> str | None:
    """Return the first V2 package layer for a source path."""
    parts = Path(relative_path).parts
    return parts[1] if len(parts) > 2 and parts[0] == "rom_v2" else None


def _imports(tree: ast.AST) -> list[tuple[int, str]]:
    """Return imported module names with source line numbers."""
    result: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            result.append((node.lineno, node.module or ""))
    return result


def verify(root: Path) -> dict[str, Any]:
    """Inspect the physical V2 tree and return machine-readable findings."""
    violations: list[dict[str, Any]] = []
    parsed_files: list[str] = []
    import_edges: list[dict[str, Any]] = []
    runtime = root / "rom_v2"
    if not runtime.is_dir():
        violations.append({"rule": "MISSING_V2_ROOT", "file": "rom_v2"})
    physical_files = {
        path.relative_to(root).as_posix()
        for path in runtime.rglob("*.py")
    } if runtime.is_dir() else set()
    for required in sorted(REQUIRED_FILES - physical_files):
        violations.append({"rule": "MISSING_REQUIRED_FILE", "file": required})

    for relative in sorted(physical_files):
        path = root / relative
        if path.name in FORBIDDEN_CATCH_ALL_MODULES:
            violations.append({"rule": "CATCH_ALL_MODULE", "file": relative, "line": 1})
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=relative)
        except SyntaxError as exc:
            violations.append({"rule": "PARSE_ERROR", "file": relative, "line": exc.lineno, "detail": str(exc)})
            continue
        parsed_files.append(relative)
        source_layer = _layer(relative)
        for line, module in _imports(tree):
            root_name = module.split(".")[0]
            edge = {"file": relative, "line": line, "import": module}
            import_edges.append(edge)
            if root_name in {"data", "handlers", "systems", "services", "database", "legacy_v1"}:
                violations.append({"rule": "V1_RUNTIME_IMPORT", **edge})
            if source_layer in {"domain", "application"} and root_name in FORBIDDEN_EXTERNAL_ROOTS:
                violations.append({"rule": "FORBIDDEN_EXTERNAL_IMPORT", **edge})
            if module.startswith("rom_v2."):
                target_parts = module.split(".")
                target_layer = target_parts[1] if len(target_parts) > 1 else None
                if source_layer in LAYER_ORDER and target_layer in LAYER_ORDER:
                    if LAYER_ORDER[target_layer] > LAYER_ORDER[source_layer]:
                        violations.append({"rule": "OUTWARD_LAYER_IMPORT", "source_layer": source_layer, "target_layer": target_layer, **edge})

    result_owners: list[dict[str, Any]] = []
    event_owners: list[dict[str, Any]] = []
    uow_owners: list[dict[str, Any]] = []
    clock_owners: list[dict[str, Any]] = []
    rng_owners: list[dict[str, Any]] = []
    for relative in parsed_files:
        tree = ast.parse((root / relative).read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            row = {"file": relative, "class": node.name, "line": node.lineno}
            if node.name in {"Result", "OperationResult", "CommandResult", "ServiceResult"}: result_owners.append(row)
            if node.name in {"DomainEvent", "EventEnvelope"}: event_owners.append(row)
            if node.name == "UnitOfWork": uow_owners.append(row)
            if node.name == "Clock": clock_owners.append(row)
            if node.name == "RandomSource": rng_owners.append(row)
    owner_rules = (
        ("MULTIPLE_RESULT_OWNERS", result_owners, 1),
        ("MULTIPLE_EVENT_OWNERS", event_owners, 1),
        ("UNIT_OF_WORK_OWNER_COUNT", uow_owners, 1),
        ("CLOCK_OWNER_COUNT", clock_owners, 1),
        ("RNG_OWNER_COUNT", rng_owners, 1),
    )
    for rule, owners, maximum in owner_rules:
        if len(owners) > maximum or (rule in {"UNIT_OF_WORK_OWNER_COUNT", "CLOCK_OWNER_COUNT", "RNG_OWNER_COUNT"} and len(owners) != 1):
            violations.append({"rule": rule, "owners": owners})

    return {
        "schema_version": 1,
        "summary": {
            "status": "PASS" if not violations else "FAIL",
            "physical_file_count": len(physical_files),
            "parsed_file_count": len(parsed_files),
            "import_edge_count": len(import_edges),
            "violation_count": len(violations),
        },
        "owners": {
            "result": result_owners,
            "events": event_owners,
            "unit_of_work": uow_owners,
            "clock": clock_owners,
            "random_source": rng_owners,
        },
        "import_edges": import_edges,
        "violations": violations,
    }


def main() -> int:
    """Run architecture enforcement and optionally write JSON evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    result = verify(Path(args.project_root).resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8", newline="\n")
    summary = result["summary"]
    print(f"V2 architecture enforcement: {summary['status']}")
    print(f"Physical files: {summary['physical_file_count']}")
    print(f"Import edges: {summary['import_edge_count']}")
    print(f"Violations: {summary['violation_count']}")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
