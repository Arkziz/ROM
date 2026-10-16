#!/usr/bin/env python3
"""Verify the ROM V2 Result/error contract and detect competing implementations."""
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path
from typing import Any

REQUIRED_STATUS_KEYS = {
    "success", "business_rejection", "validation_error", "stale_state",
    "idempotent_repeat", "retryable_error", "consistency_error",
}
FORBIDDEN_PUBLIC_RESULT_PATTERNS = ("dict", "None", "str", "bool")
RESULT_CLASS_RE = re.compile(r"(?i)^(result|operationresult|commandresult|serviceresult)$")


def verify(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    status_rows = contract.get("statuses", [])
    keys = [row.get("key") for row in status_rows]
    if set(keys) != REQUIRED_STATUS_KEYS or len(keys) != len(set(keys)):
        violations.append({"rule": "STATUS_SET", "expected": sorted(REQUIRED_STATUS_KEYS), "actual": sorted(keys)})
    if contract.get("canonical_owner") != "rom_v2.application.result":
        violations.append({"rule": "CANONICAL_OWNER"})
    if not contract.get("mutation_contract", {}).get("unit_of_work_required"):
        violations.append({"rule": "UNIT_OF_WORK_REQUIRED"})
    if not contract.get("mutation_contract", {}).get("preconditions_before_first_mutation"):
        violations.append({"rule": "PRECONDITIONS_BEFORE_MUTATION"})
    if not contract.get("presentation_contract", {}).get("telegram_types_forbidden"):
        violations.append({"rule": "PRESENTATION_SEPARATION"})
    retryable = {row["key"] for row in status_rows if row.get("retryable")}
    if retryable != {"stale_state", "retryable_error"}:
        violations.append({"rule": "RETRYABILITY_SET", "actual": sorted(retryable)})
    mutating = {row["key"] for row in status_rows if row.get("mutation_allowed")}
    if mutating != {"success"}:
        violations.append({"rule": "MUTATION_ALLOWED_SET", "actual": sorted(mutating)})

    result_owners: list[dict[str, Any]] = []
    implicit_results: list[dict[str, Any]] = []
    rom_v2 = root / "rom_v2"
    if rom_v2.is_dir():
        for path in sorted(rom_v2.rglob("*.py")):
            text = path.read_text(encoding="utf-8", errors="replace")
            try:
                tree = ast.parse(text, filename=str(path))
            except SyntaxError as exc:
                violations.append({"rule": "PARSE_ERROR", "file": path.relative_to(root).as_posix(), "error": str(exc)})
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and RESULT_CLASS_RE.fullmatch(node.name):
                    result_owners.append({"file": path.relative_to(root).as_posix(), "class": node.name, "line": node.lineno})
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns:
                    annotation = ast.unparse(node.returns)
                    if annotation in FORBIDDEN_PUBLIC_RESULT_PATTERNS and not node.name.startswith("_"):
                        implicit_results.append({"file": path.relative_to(root).as_posix(), "function": node.name, "line": node.lineno, "annotation": annotation})
    if len(result_owners) > 1:
        violations.append({"rule": "MULTIPLE_RESULT_OWNERS", "owners": result_owners})
    if result_owners and result_owners[0]["file"] != "rom_v2/application/result.py":
        violations.append({"rule": "WRONG_RESULT_OWNER", "owners": result_owners})
    if implicit_results:
        violations.append({"rule": "IMPLICIT_PUBLIC_RESULTS", "functions": implicit_results})

    return {
        "schema_version": 1,
        "summary": {
            "status": "PASS" if not violations else "FAIL",
            "status_count": len(status_rows),
            "result_owner_count": len(result_owners),
            "implicit_public_result_count": len(implicit_results),
            "violation_count": len(violations),
            "physical_result_model_exists": bool(result_owners),
        },
        "result_owners": result_owners,
        "implicit_public_results": implicit_results,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    result = verify(Path(args.project_root).resolve(), contract)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8", newline="\n")
    print(f"V2 result/error verifier: {result['summary']['status']}")
    print(f"Statuses: {result['summary']['status_count']}")
    print(f"Physical Result owners: {result['summary']['result_owner_count']}")
    print(f"Implicit public results: {result['summary']['implicit_public_result_count']}")
    print(f"Violations: {result['summary']['violation_count']}")
    return 0 if result["summary"]["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
