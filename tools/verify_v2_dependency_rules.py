#!/usr/bin/env python3
"""Verify ROM V2 dependency directions without importing application code."""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

LAYERS = ("domain", "application", "infrastructure", "app")
LAYER_RANK = {name: index for index, name in enumerate(LAYERS)}
FORBIDDEN_DOMAIN_ROOTS = {
    "aiogram", "telebot", "telegram", "sqlite3", "sqlalchemy", "aiosqlite",
    "requests", "httpx", "aiohttp", "dotenv", "os", "subprocess",
}
FORBIDDEN_APPLICATION_ROOTS = {
    "aiogram", "telebot", "telegram", "sqlite3", "sqlalchemy", "aiosqlite",
}
ALLOWED_CROSS_LAYER = {
    "application": {"domain"},
    "infrastructure": {"domain", "application"},
    "app": {"domain", "application", "infrastructure"},
    "domain": set(),
}


def module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root.parent).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def layer_for(root: Path, path: Path) -> str | None:
    relative = path.relative_to(root)
    return relative.parts[0] if relative.parts and relative.parts[0] in LAYERS else None


def imported_modules(tree: ast.AST) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                records.append({"module": alias.name, "line": node.lineno, "kind": "import"})
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level
            records.append({"module": prefix + (node.module or ""), "line": node.lineno, "kind": "from"})
    return records


def resolve_internal_layer(module: str) -> str | None:
    normalized = module.lstrip(".")
    parts = normalized.split(".")
    if not parts:
        return None
    if parts[0] == "rom_v2" and len(parts) > 1 and parts[1] in LAYERS:
        return parts[1]
    if parts[0] in LAYERS:
        return parts[0]
    return None


def verify(project_root: Path) -> dict[str, Any]:
    root = project_root / "rom_v2"
    files = sorted(root.rglob("*.py")) if root.is_dir() else []
    modules: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []

    for path in files:
        layer = layer_for(root, path)
        if layer is None:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            parse_errors.append({"file": str(path.relative_to(project_root)), "error": str(exc)})
            continue
        imports = imported_modules(tree)
        module = module_name(root, path)
        modules.append({"file": str(path.relative_to(project_root)).replace("\\", "/"), "module": module, "layer": layer, "imports": imports})
        for item in imports:
            imported = item["module"]
            external_root = imported.lstrip(".").split(".")[0]
            target_layer = resolve_internal_layer(imported)
            if target_layer:
                edges.append({"source_layer": layer, "target_layer": target_layer, "file": str(path.relative_to(project_root)).replace("\\", "/"), "line": item["line"], "import": imported})
                if target_layer != layer and target_layer not in ALLOWED_CROSS_LAYER[layer]:
                    violations.append({"rule": "FORBIDDEN_LAYER_DIRECTION", "source_layer": layer, "target_layer": target_layer, "file": str(path.relative_to(project_root)).replace("\\", "/"), "line": item["line"], "import": imported})
            if layer == "domain" and external_root in FORBIDDEN_DOMAIN_ROOTS:
                violations.append({"rule": "FORBIDDEN_DOMAIN_DEPENDENCY", "file": str(path.relative_to(project_root)).replace("\\", "/"), "line": item["line"], "import": imported})
            if layer == "application" and external_root in FORBIDDEN_APPLICATION_ROOTS:
                violations.append({"rule": "FORBIDDEN_APPLICATION_ADAPTER_DEPENDENCY", "file": str(path.relative_to(project_root)).replace("\\", "/"), "line": item["line"], "import": imported})

    return {
        "schema_version": 1,
        "root": "rom_v2",
        "contract": {
            "layers_inner_to_outer": list(LAYERS),
            "allowed_cross_layer_dependencies": {key: sorted(value) for key, value in ALLOWED_CROSS_LAYER.items()},
            "domain_forbidden_roots": sorted(FORBIDDEN_DOMAIN_ROOTS),
            "application_forbidden_roots": sorted(FORBIDDEN_APPLICATION_ROOTS),
        },
        "summary": {
            "status": "PASS" if not violations and not parse_errors else "FAIL",
            "module_count": len(modules),
            "edge_count": len(edges),
            "violation_count": len(violations),
            "parse_error_count": len(parse_errors),
            "layer_counts": dict(sorted(Counter(item["layer"] for item in modules).items())),
            "empty_v2_tree": not files,
        },
        "modules": modules,
        "edges": edges,
        "violations": violations,
        "parse_errors": parse_errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    result = verify(Path(args.project_root).resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8", newline="\n")
    print(f"V2 dependency verifier: {result['summary']['status']}")
    print(f"Modules: {result['summary']['module_count']}")
    print(f"Edges: {result['summary']['edge_count']}")
    print(f"Violations: {result['summary']['violation_count']}")
    print(f"Parse errors: {result['summary']['parse_error_count']}")
    if result['summary']['empty_v2_tree']:
        print("V2 tree is not created yet; contract validation itself passed.")
    return 0 if result["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
