#!/usr/bin/env python3
"""Verify the ROM V2 package-layout contract without importing runtime code."""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any

EXPECTED_RUNTIME_PACKAGES = {"domain", "application", "infrastructure", "app", "content"}
EXPECTED_SUPPORT_ROOTS = {"tests_v2", "tools", "reports", "MD"}
FORBIDDEN_CATCH_ALL = {
    "common.py", "helpers.py", "helper.py", "utils.py", "utility.py", "misc.py",
    "manager.py", "service.py", "services.py", "base.py", "core.py", "shared.py",
}
VALID_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def verify(project_root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    runtime_root = project_root / contract["runtime_root"]
    physical_runtime_exists = runtime_root.is_dir()

    declared_runtime = {Path(path).name for path in contract["runtime_packages"]}
    declared_support = set(contract["support_roots"])
    if declared_runtime != EXPECTED_RUNTIME_PACKAGES:
        violations.append({"rule": "RUNTIME_PACKAGE_SET", "expected": sorted(EXPECTED_RUNTIME_PACKAGES), "actual": sorted(declared_runtime)})
    if not EXPECTED_SUPPORT_ROOTS.issubset(declared_support):
        violations.append({"rule": "SUPPORT_ROOT_SET", "missing": sorted(EXPECTED_SUPPORT_ROOTS - declared_support)})

    duplicate_owners: dict[str, list[str]] = {}
    owners: dict[str, list[str]] = {}
    for path, metadata in contract["runtime_packages"].items():
        owners.setdefault(metadata["owner"], []).append(path)
        name = Path(path).name
        if not VALID_NAME.fullmatch(name):
            violations.append({"rule": "PACKAGE_NAMING", "path": path})
        if Path(path).name + ".py" in FORBIDDEN_CATCH_ALL:
            violations.append({"rule": "CATCH_ALL_PACKAGE_NAME", "path": path})
    duplicate_owners = {owner: paths for owner, paths in owners.items() if len(paths) > 1}
    if duplicate_owners:
        violations.append({"rule": "DUPLICATE_OWNER", "owners": duplicate_owners})

    files: list[Path] = []
    if physical_runtime_exists:
        files = sorted(runtime_root.rglob("*.py"))
        for path in files:
            relative = path.relative_to(project_root).as_posix()
            if path.name in FORBIDDEN_CATCH_ALL:
                violations.append({"rule": "FORBIDDEN_CATCH_ALL_MODULE", "file": relative})
            if path.name != "__init__.py" and not VALID_NAME.fullmatch(path.stem):
                violations.append({"rule": "MODULE_NAMING", "file": relative})
            try:
                ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=relative)
            except SyntaxError as exc:
                violations.append({"rule": "PYTHON_PARSE_ERROR", "file": relative, "error": str(exc)})
        physical_packages = {path.name for path in runtime_root.iterdir() if path.is_dir()}
        unknown = sorted(physical_packages - EXPECTED_RUNTIME_PACKAGES)
        missing = sorted(EXPECTED_RUNTIME_PACKAGES - physical_packages)
        if unknown:
            violations.append({"rule": "UNDECLARED_RUNTIME_PACKAGE", "packages": unknown})
        if missing:
            violations.append({"rule": "MISSING_RUNTIME_PACKAGE_AFTER_SCAFFOLD", "packages": missing})
    else:
        observations.append({"kind": "STAGE_BOUNDARY", "message": "Physical rom_v2 skeleton is intentionally reserved for Stage 21.3.1."})

    return {
        "schema_version": 1,
        "summary": {
            "status": "PASS" if not violations else "FAIL",
            "physical_runtime_exists": physical_runtime_exists,
            "physical_python_file_count": len(files),
            "declared_runtime_package_count": len(declared_runtime),
            "declared_support_root_count": len(declared_support),
            "violation_count": len(violations),
        },
        "declared_runtime_packages": sorted(declared_runtime),
        "declared_support_roots": sorted(declared_support),
        "observations": observations,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    result = verify(root, contract)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8", newline="\n")
    print(f"V2 package structure verifier: {result['summary']['status']}")
    print(f"Declared runtime packages: {result['summary']['declared_runtime_package_count']}")
    print(f"Declared support roots: {result['summary']['declared_support_root_count']}")
    print(f"Physical V2 tree exists: {result['summary']['physical_runtime_exists']}")
    print(f"Violations: {result['summary']['violation_count']}")
    return 0 if result["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
