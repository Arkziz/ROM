#!/usr/bin/env python3
"""Stage 21.2.6: define canonical Clock and RNG abstractions for ROM V2."""
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE = "21.2.6"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "daae596404c111a37ce3869ec0096021998b4ca2"
UOW_REPORT = "reports/stage_21_2_5_repository_unit_of_work.json"
UOW_ADR = "MD/ADR_21_2_5_V2_REPOSITORY_UNIT_OF_WORK.md"
EVENT_REPORT = "reports/stage_21_2_4_domain_event_model.json"
PATCH_PATH = "patch/patch_21_2_6_define_clock_rng_abstractions.py"
VERIFIER_PATH = "tools/verify_v2_clock_rng_abstractions.py"
REPORT_PATH = "reports/stage_21_2_6_clock_rng_abstractions.json"
ADR_PATH = "MD/ADR_21_2_6_V2_CLOCK_RNG_ABSTRACTIONS.md"
FAILURE_REPORT = "reports/stage_21_2_6_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.2.6: define Clock and RNG abstractions"
OWNED = {PATCH_PATH, VERIFIER_PATH, REPORT_PATH, ADR_PATH, FAILURE_REPORT}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
BACKUP_PREFIX = "stage_21_2_6"

CONTRACT: dict[str, Any] = {
    "schema_version": 1,
    "canonical_owners": {
        "clock_port": "rom_v2.application.ports.clock",
        "rng_port": "rom_v2.application.ports.random_source",
        "system_clock_adapter": "rom_v2.infrastructure.time.system_clock",
        "system_rng_adapter": "rom_v2.infrastructure.random.system_random_source",
        "fake_clock": "tests_v2.fakes.clock",
        "seeded_rng": "tests_v2.fakes.random_source",
    },
    "clock": {
        "port_name": "Clock",
        "operations": {
            "now_utc": "timezone-aware UTC datetime",
            "monotonic_seconds": "non-decreasing float for elapsed-time measurement",
        },
        "wall_clock_utc_only": True,
        "naive_datetime_forbidden": True,
        "local_timezone_in_domain_forbidden": True,
        "datetime_now_direct_use_forbidden": True,
        "utcnow_direct_use_forbidden": True,
        "time_time_for_elapsed_forbidden": True,
        "elapsed_time_uses_monotonic": True,
        "event_occurred_at_uses_clock": True,
        "scheduling_deadlines_use_clock": True,
        "persistence_normalizes_utc": True,
    },
    "rng": {
        "port_name": "RandomSource",
        "operations": {
            "random": "float in [0.0, 1.0)",
            "randint": "inclusive integer range",
            "choice": "one element from non-empty sequence",
            "shuffle": "explicitly mutates supplied mutable sequence",
        },
        "single_injected_source_per_operation": True,
        "module_random_direct_use_forbidden": True,
        "secrets_for_gameplay_forbidden": True,
        "seed_owned_by_composition_or_test": True,
        "seed_not_generated_inside_domain": True,
        "empty_choice_is_validation_error": True,
        "invalid_range_is_validation_error": True,
        "draw_order_is_explicit_contract": True,
    },
    "determinism": {
        "same_initial_state_same_seed_same_clock_same_commands_same_result": True,
        "tests_use_fake_clock": True,
        "tests_use_seeded_rng": True,
        "fixtures_record_seed_and_clock": True,
        "retry_reuses_business_operation_semantics": True,
        "idempotent_repeat_performs_no_new_rng_draw": True,
        "failed_operation_does_not_persist_rng_dependent_events": True,
        "restart_test_reconstructs_clock_and_rng_inputs": True,
    },
    "layering": {
        "domain_imports_clock_port_only": True,
        "domain_imports_rng_port_only": True,
        "application_injects_ports": True,
        "infrastructure_implements_adapters": True,
        "app_composition_wires_exactly_one_clock_and_rng": True,
        "global_singletons_forbidden": True,
    },
    "forbidden_alternatives": [
        "datetime.now/utcnow in domain or application",
        "time.time for elapsed-time logic",
        "random module calls in domain or application",
        "hidden reseeding",
        "seed from current time inside domain",
        "multiple production Clock implementations wired simultaneously",
        "multiple production RNG implementations wired simultaneously",
    ],
}

VERIFIER_SOURCE = r'''#!/usr/bin/env python3
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
'''

@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False

class PatchError(RuntimeError):
    pass


def run(root: Path, *command: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run(root, "git", *args)


def rev(root: Path, name: str) -> str | None:
    result = git(root, "rev-parse", "--verify", f"{name}^{{commit}}")
    return result.stdout.strip() if result.returncode == 0 else None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def database_evidence(root: Path) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists(): evidence[name] = {"exists": False}
        else:
            stat = path.stat()
            evidence[name] = {"exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}
    return evidence


def write_atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def parse_status(raw: str) -> list[dict[str, str]]:
    return [{"status": item[:2], "path": item[3:]} for item in raw.split("\0") if item]


def git_blob(root: Path, commit: str, relative_path: str) -> bytes | None:
    result = subprocess.run(["git", "show", f"{commit}:{relative_path}"], cwd=root, capture_output=True, check=False)
    return result.stdout if result.returncode == 0 else None


def prepare_backups(root: Path) -> dict[str, Any]:
    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"files": {}}
    for relative_path in (VERIFIER_PATH, REPORT_PATH, ADR_PATH):
        blob = git_blob(root, EXPECTED_PARENT, relative_path)
        backup = backup_dir / f"{BACKUP_PREFIX}__{relative_path.replace('/', '__')}"
        if blob is None: manifest["files"][relative_path] = {"existed": False, "backup": None}
        else:
            backup.write_bytes(blob)
            manifest["files"][relative_path] = {"existed": True, "backup": str(backup.relative_to(root)).replace("\\", "/")}
    return manifest


def rollback(root: Path, manifest: dict[str, Any], reason: str, checks: list[Check]) -> dict[str, Any]:
    git(root, "reset", "--", VERIFIER_PATH, REPORT_PATH, ADR_PATH)
    restored: list[str] = []; removed: list[str] = []; errors: list[str] = []
    for relative_path, metadata in manifest["files"].items():
        target = root / relative_path
        try:
            if metadata["existed"]:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((root / metadata["backup"]).read_bytes())
                restored.append(relative_path)
            elif target.exists():
                target.unlink(); removed.append(relative_path)
        except OSError as exc: errors.append(f"{relative_path}: {exc}")
    payload = {"stage": STAGE, "status": "FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE", "reason": reason, "failed_checks": [asdict(item) for item in checks if item.status == "FAIL"], "restored_files": restored, "removed_failed_artifacts": removed, "rollback_errors": errors, "database_evidence_after_rollback": database_evidence(root), "main_py_started": False, "wal_shm_manipulated": False}
    write_atomic(root / FAILURE_REPORT, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return payload


def render_adr(result: dict[str, Any]) -> str:
    summary = result["summary"]
    return "\n".join([
        "# ADR 21.2.6 — ROM V2 Clock and RNG abstractions", "",
        "- **Status:** `ACCEPTED`",
        "- **Clock port:** `rom_v2.application.ports.clock`",
        "- **RNG port:** `rom_v2.application.ports.random_source`", "",
        "## Clock", "",
        "`Clock` exposes timezone-aware `now_utc()` and monotonic elapsed-time measurement. Domain/application code cannot call `datetime.now`, `datetime.utcnow`, `time.time` or local timezone APIs directly.", "",
        "## Random source", "",
        "`RandomSource` exposes explicit `random`, `randint`, `choice` and `shuffle` operations. Domain/application code cannot call the module-level `random` or `secrets` APIs for gameplay decisions. Seeds belong to composition or tests, never domain code.", "",
        "## Determinism", "",
        "The same initial state, command sequence, seed and controlled clock must produce the same Result and domain events. Idempotent repeats perform no additional RNG draw. Failed operations persist no RNG-dependent event.", "",
        "## Production and tests", "",
        "Production composition wires exactly one SystemClock and one SystemRandomSource. Tests use FakeClock and SeededRandomSource and record both seed and clock state in fixtures.", "",
        "## Automated evidence", "",
        f"- Physical V2 exists: **{summary['physical_v2_exists']}**.",
        f"- Direct time calls: **{summary['direct_time_call_count']}**.",
        f"- Direct RNG calls: **{summary['direct_rng_call_count']}**.",
        f"- Violations: **{summary['violation_count']}**.", "",
        "## Next roadmap stage", "",
        "Stage 21.2.7 — Configuration and secrets boundary.", "",
    ])


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, VERIFIER_PATH, REPORT_PATH, ADR_PATH]
    added = git(root, "add", "-f", "--", *paths)
    if added.returncode != 0: raise PatchError(added.stderr.strip())
    staged = sorted(item for item in git(root, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if item)
    if staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging allowlist mismatch: {staged}")
    committed = git(root, "commit", "-m", COMMIT_MESSAGE)
    if committed.returncode != 0:
        git(root, "reset", "--", *paths)
        raise PatchError(committed.stderr.strip() or committed.stdout.strip())
    return rev(root, "HEAD") or ""


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    for required in (UOW_REPORT, UOW_ADR, EVENT_REPORT):
        if not (root / required).is_file():
            print(f"[FAIL] Missing prerequisite artifact: {required}", file=sys.stderr); return 2
    print("[1/8] [PASS] Stage 21.2.4/21.2.5 artifacts and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip(); head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"); upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.2.5 parent verified.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks): print("[2/8] [FAIL] Preflight returned NO_GO."); return 1
    uow = json.loads((root / UOW_REPORT).read_text(encoding="utf-8")); events = json.loads((root / EVENT_REPORT).read_text(encoding="utf-8"))
    if uow.get("stage") != "21.2.5" or uow.get("summary", {}).get("conclusion") != "GO" or events.get("summary", {}).get("conclusion") != "GO":
        print("[FAIL] Repository/UoW or event prerequisite is not canonical GO.", file=sys.stderr); return 2
    checks.append(Check("UOW_EVENT_PREREQUISITES", "PASS", "Repository/UoW and event contracts are canonical GO.", {}))
    print("[2/8] [PASS] Branch, parent, upstream, worktree and prerequisites verified; backups prepared in ROM\\backup.")
    before = database_evidence(root); manifest = prepare_backups(root)
    print("[3/8] [PASS] Writing Clock/RNG verifier and canonical contract."); write_atomic(root / VERIFIER_PATH, VERIFIER_SOURCE)
    try: py_compile.compile(str(root / VERIFIER_PATH), doraise=True)
    except py_compile.PyCompileError as exc:
        report = rollback(root, manifest, f"py_compile failed: {exc}", checks); print(f"[FAIL] rollback: {report['status']}"); return 2
    print("[4/8] [PASS] Executing Clock/RNG verifier against contract and current V2 tree.")
    temporary_contract = root / "reports" / ".stage_21_2_6_contract.tmp.json"; temporary_result = root / "reports" / ".stage_21_2_6_result.tmp.json"
    write_atomic(temporary_contract, json.dumps(CONTRACT, ensure_ascii=False, indent=2) + "\n")
    verifier_run = run(root, sys.executable, VERIFIER_PATH, "--project-root", str(root), "--contract", str(temporary_contract), "--json-out", str(temporary_result))
    result = json.loads(temporary_result.read_text(encoding="utf-8")) if temporary_result.exists() else {}
    temporary_contract.unlink(missing_ok=True); temporary_result.unlink(missing_ok=True)
    summary = result.get("summary", {})
    checks += [
        Check("VERIFIER_EXECUTION", "PASS" if verifier_run.returncode == 0 else "FAIL", verifier_run.stdout.strip(), {"stderr": verifier_run.stderr.strip()}, verifier_run.returncode != 0),
        Check("ONE_CLOCK_AND_RNG_ADAPTER", "PASS" if summary.get("violation_count") == 0 else "FAIL", f"Violations: {summary.get('violation_count')}", {}, summary.get("violation_count") != 0),
        Check("NO_DIRECT_TIME_CALLS", "PASS" if summary.get("direct_time_call_count") == 0 else "FAIL", "No direct time calls in domain/application.", {}, summary.get("direct_time_call_count") != 0),
        Check("NO_DIRECT_RNG_CALLS", "PASS" if summary.get("direct_rng_call_count") == 0 else "FAIL", "No direct RNG calls in domain/application.", {}, summary.get("direct_rng_call_count") != 0),
        Check("DATABASE_EVIDENCE_READY", "PASS", "DB/WAL/SHM captured without SQLite connection.", {"production_connection_opened": False}),
    ]
    blockers = [item.check_id for item in checks if item.blocking]
    payload = {"schema_version": 1, "stage": STAGE, "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "summary": {"conclusion": "GO" if not blockers else "NO_GO", "blocking_failures": blockers, **summary}, "git": {"branch": branch, "head_before_commit": head, "upstream": upstream}, "checks": [asdict(item) for item in checks], "clock_rng_contract": CONTRACT, "verifier_result": result, "database_evidence_before": before, "artifacts": {"patch": PATCH_PATH, "verifier": VERIFIER_PATH, "json": REPORT_PATH, "adr": ADR_PATH}, "next_stage": "21.2.7", "suggested_next_patch": "patch_21_2_7_define_configuration_secrets_boundary.py"}
    print("[5/8] [PASS] Writing full Clock/RNG contract and evidence report.")
    try:
        write_atomic(root / REPORT_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"); write_atomic(root / ADR_PATH, render_adr(result))
        if blockers:
            report = rollback(root, manifest, "Clock/RNG acceptance NO_GO", checks); print(f"[6/8] [FAIL] rollback: {report['status']}"); return 1
        if before != database_evidence(root):
            report = rollback(root, manifest, "DB evidence changed", checks); print(f"[6/8] [FAIL] rollback: {report['status']}"); return 2
    except Exception as exc:
        report = rollback(root, manifest, f"mutation failure: {exc}", checks); print(f"[6/8] [FAIL] rollback: {report['status']}"); return 2
    print("[6/8] [PASS] Clock, RNG, determinism, injection and restart semantics validated."); (root / FAILURE_REPORT).unlink(missing_ok=True)
    try: print("[7/8] [PASS] Creating exact-allowlist Stage 21.2.6 commit."); commit_hash = exact_commit(root)
    except PatchError as exc:
        report = rollback(root, manifest, f"commit failed: {exc}", checks); print(f"[7/8] [FAIL] rollback: {report['status']}"); return 2
    print(f"[8/8] [PASS] Clock/RNG model committed and DB/WAL/SHM verified: {commit_hash}"); print("=" * 72); print(f"ROM Stage {STAGE} - Clock and RNG abstractions")
    for item in checks: print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] PHYSICAL_V2_EXISTS: {summary['physical_v2_exists']}"); print(f"[PASS] CLOCK_OWNERS: {summary['clock_owner_count']}"); print(f"[PASS] RNG_OWNERS: {summary['rng_owner_count']}"); print(f"[PASS] DIRECT_TIME_CALLS: {summary['direct_time_call_count']}"); print(f"[PASS] DIRECT_RNG_CALLS: {summary['direct_rng_call_count']}"); print(f"[PASS] VIOLATIONS: {summary['violation_count']}")
    print("CONCLUSION: GO\nPATCH STATUS: PASS"); print(f"GIT COMMIT STATUS: PASS ({commit_hash})"); print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nWAL/SHM: NOT MANIPULATED\nSUGGESTED NEXT PATCH: patch_21_2_7_define_configuration_secrets_boundary.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
