#!/usr/bin/env python3
"""Verify ROM V2 Clock/RNG contract without importing runtime modules."""
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path
from typing import Any

EXPECTED_OWNERS = {
    "clock_port": "rom_v2.application.ports.clock",
    "rng_port": "rom_v2.application.ports.random_source",
    "system_clock_adapter": "rom_v2.infrastructure.time.system_clock",
    "system_rng_adapter": "rom_v2.infrastructure.random.system_random_source",
    "fake_clock": "tests_v2.fakes.clock",
    "seeded_rng": "tests_v2.fakes.random_source",
}
CLOCK_CLASS = re.compile(r"(?i)^(clock|systemclock|fakeclock)$")
RNG_CLASS = re.compile(r"(?i)^(randomsource|systemrandomsource|seededrandomsource|fakerandomsource)$")


def call_name(node: ast.Call) -> str:
    try: return ast.unparse(node.func)
    except Exception: return ""


def verify(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    if contract.get("canonical_owners") != EXPECTED_OWNERS:
        violations.append({"rule": "CANONICAL_OWNERS"})
    clock = contract.get("clock", {})
    rng = contract.get("rng", {})
    deterministic = contract.get("determinism", {})
    layering = contract.get("layering", {})
    if set(clock.get("operations", {})) != {"now_utc", "monotonic_seconds"}:
        violations.append({"rule": "CLOCK_OPERATION_SET"})
    for key in ("wall_clock_utc_only", "naive_datetime_forbidden", "local_timezone_in_domain_forbidden", "datetime_now_direct_use_forbidden", "utcnow_direct_use_forbidden", "time_time_for_elapsed_forbidden", "elapsed_time_uses_monotonic", "event_occurred_at_uses_clock", "scheduling_deadlines_use_clock", "persistence_normalizes_utc"):
        if not clock.get(key): violations.append({"rule": "CLOCK_INVARIANT", "key": key})
    if set(rng.get("operations", {})) != {"random", "randint", "choice", "shuffle"}:
        violations.append({"rule": "RNG_OPERATION_SET"})
    for key in ("single_injected_source_per_operation", "module_random_direct_use_forbidden", "secrets_for_gameplay_forbidden", "seed_owned_by_composition_or_test", "seed_not_generated_inside_domain", "empty_choice_is_validation_error", "invalid_range_is_validation_error", "draw_order_is_explicit_contract"):
        if not rng.get(key): violations.append({"rule": "RNG_INVARIANT", "key": key})
    for key in ("same_initial_state_same_seed_same_clock_same_commands_same_result", "tests_use_fake_clock", "tests_use_seeded_rng", "fixtures_record_seed_and_clock", "idempotent_repeat_performs_no_new_rng_draw", "failed_operation_does_not_persist_rng_dependent_events", "restart_test_reconstructs_clock_and_rng_inputs"):
        if not deterministic.get(key): violations.append({"rule": "DETERMINISM_INVARIANT", "key": key})
    for key in ("domain_imports_clock_port_only", "domain_imports_rng_port_only", "application_injects_ports", "infrastructure_implements_adapters", "app_composition_wires_exactly_one_clock_and_rng", "global_singletons_forbidden"):
        if not layering.get(key): violations.append({"rule": "LAYERING_INVARIANT", "key": key})

    direct_time_calls: list[dict[str, Any]] = []
    direct_rng_calls: list[dict[str, Any]] = []
    clock_owners: list[dict[str, Any]] = []
    rng_owners: list[dict[str, Any]] = []
    runtime = root / "rom_v2"
    if runtime.is_dir():
        for path in sorted(runtime.rglob("*.py")):
            rel = path.relative_to(root).as_posix()
            try: tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=rel)
            except SyntaxError as exc:
                violations.append({"rule": "PARSE_ERROR", "file": rel, "error": str(exc)}); continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if CLOCK_CLASS.fullmatch(node.name): clock_owners.append({"file": rel, "class": node.name, "line": node.lineno})
                    if RNG_CLASS.fullmatch(node.name): rng_owners.append({"file": rel, "class": node.name, "line": node.lineno})
                if isinstance(node, ast.Call) and rel.startswith(("rom_v2/domain/", "rom_v2/application/")):
                    name = call_name(node)
                    if name in {"datetime.now", "datetime.utcnow", "time.time", "date.today"}:
                        direct_time_calls.append({"file": rel, "line": node.lineno, "call": name})
                    if name.startswith("random.") or name.startswith("secrets."):
                        direct_rng_calls.append({"file": rel, "line": node.lineno, "call": name})
    if direct_time_calls: violations.append({"rule": "DIRECT_TIME_CALL", "calls": direct_time_calls})
    if direct_rng_calls: violations.append({"rule": "DIRECT_RNG_CALL", "calls": direct_rng_calls})
    if runtime.is_dir():
        ports_clock = [x for x in clock_owners if x["file"] == "rom_v2/application/ports/clock.py" and x["class"] == "Clock"]
        ports_rng = [x for x in rng_owners if x["file"] == "rom_v2/application/ports/random_source.py" and x["class"] == "RandomSource"]
        if len(ports_clock) != 1: violations.append({"rule": "CLOCK_PORT_COUNT", "owners": ports_clock})
        if len(ports_rng) != 1: violations.append({"rule": "RNG_PORT_COUNT", "owners": ports_rng})
    return {
        "schema_version": 1,
        "summary": {
            "status": "PASS" if not violations else "FAIL",
            "physical_v2_exists": runtime.is_dir(),
            "clock_owner_count": len(clock_owners),
            "rng_owner_count": len(rng_owners),
            "direct_time_call_count": len(direct_time_calls),
            "direct_rng_call_count": len(direct_rng_calls),
            "violation_count": len(violations),
        },
        "clock_owners": clock_owners,
        "rng_owners": rng_owners,
        "direct_time_calls": direct_time_calls,
        "direct_rng_calls": direct_rng_calls,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    result = verify(Path(args.project_root).resolve(), json.loads(Path(args.contract).read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out: Path(args.json_out).write_text(text, encoding="utf-8", newline="\n")
    print(f"V2 Clock/RNG verifier: {result['summary']['status']}")
    print(f"Clock owners: {result['summary']['clock_owner_count']}")
    print(f"RNG owners: {result['summary']['rng_owner_count']}")
    print(f"Direct time calls: {result['summary']['direct_time_call_count']}")
    print(f"Direct RNG calls: {result['summary']['direct_rng_call_count']}")
    print(f"Violations: {result['summary']['violation_count']}")
    return 0 if result["summary"]["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
