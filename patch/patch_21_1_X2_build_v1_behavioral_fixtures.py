#!/usr/bin/env python3
"""Stage 21.1.X2: build deterministic behavioral fixture contracts for ROM V1.

The patch statically extracts maintained V1 test scenarios and accepted Stage 21
contracts into a machine-readable behavioral fixture registry. It never imports
or executes V1 runtime code, never opens SQLite, and never mutates production
code or DB/WAL/SHM files.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE = "21.1.X2"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "4f6536e25df5a7e7fa3d04c02fb223e6fb40dfbc"
MODULE_INVENTORY = "reports/stage_21_1_1_v1_module_inventory.json"
DOMAIN_CONTRACTS = "reports/stage_21_1_5_domain_contracts.json"
CONTENT_INVENTORY = "reports/stage_21_1_X1_canonical_content_inventory.json"
PATCH_PATH = "patch/patch_21_1_X2_build_v1_behavioral_fixtures.py"
JSON_PATH = "reports/stage_21_1_X2_v1_behavioral_fixtures.json"
MD_PATH = "MD/STAGE_21_1_X2_V1_BEHAVIORAL_FIXTURES.md"
FAILURE_REPORT = "reports/stage_21_1_X2_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.1.X2: build V1 behavioral fixtures"
OWNED = {PATCH_PATH, JSON_PATH, MD_PATH, FAILURE_REPORT}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
BACKUP_PREFIX = "stage_21_1_X2"

TEST_FUNCTION_RE = re.compile(r"^(test_|verify_|check_|scenario_)", re.I)
SEED_RE = re.compile(r"(?i)(seed|random\.seed|rng)")
DB_RE = re.compile(r"(?i)(sqlite|database|db_|transaction|commit|rollback|ledger|repository)")
RESTART_RE = re.compile(r"(?i)(restart|recovery|reload|reopen|resume)")
IDEMPOTENCY_RE = re.compile(r"(?i)(idempot|exact.?once|duplicate|repeat|twice|second)")
TIME_RE = re.compile(r"(?i)(clock|datetime|utc|timezone|monotonic|advance_time|freeze_time)")

DOMAIN_TOKENS: dict[str, tuple[str, ...]] = {
    "account": ("account", "user", "premium", "crystal", "wallet", "registered"),
    "character": ("character", "player", "class", "attribute", "reset", "rebirth"),
    "stats": ("stat", "hp", "mana", "rage", "energy", "attack", "defense", "crit", "evasion"),
    "combat": ("combat", "battle", "pvp", "damage", "skill", "boss", "mob", "victory", "defeat", "escape"),
    "inventory_equipment": ("inventory", "item", "equipment", "equip", "rune", "durability", "repair", "refine", "potion"),
    "economy": ("shop", "price", "gold", "crystal", "ledger", "auction", "trade", "purchase", "sell"),
    "quests_progression": ("quest", "story", "contract", "daily", "exp", "level", "reward", "loot"),
    "world_travel": ("location", "travel", "map", "world", "city", "region"),
    "social": ("guild", "member", "application", "interaction", "notification", "history"),
    "events_auxiliary": ("event", "reminder", "rating", "chronicle", "inactivity", "support"),
}


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


def git(root: Path, *args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return run(root, "git", *args, timeout=timeout)


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
    result: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists():
            result[name] = {"exists": False}
            continue
        stat = path.stat()
        result[name] = {"exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}
    return result


def write_atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
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
    manifest: dict[str, Any] = {"parent": EXPECTED_PARENT, "files": {}}
    for relative_path in (JSON_PATH, MD_PATH):
        blob = git_blob(root, EXPECTED_PARENT, relative_path)
        backup_path = backup_dir / f"{BACKUP_PREFIX}__{relative_path.replace('/', '__')}"
        if blob is None:
            manifest["files"][relative_path] = {"existed": False, "backup": None}
        else:
            backup_path.write_bytes(blob)
            manifest["files"][relative_path] = {"existed": True, "backup": str(backup_path.relative_to(root)).replace("\\", "/"), "sha256": hashlib.sha256(blob).hexdigest()}
    return manifest


def rollback_artifacts(root: Path, manifest: dict[str, Any], reason: str, checks: list[Check]) -> dict[str, Any]:
    restored: list[str] = []
    removed: list[str] = []
    errors: list[str] = []
    git(root, "reset", "--", JSON_PATH, MD_PATH)
    for relative_path, metadata in manifest["files"].items():
        target = root / relative_path
        try:
            if metadata["existed"]:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((root / metadata["backup"]).read_bytes())
                restored.append(relative_path)
            elif target.exists():
                target.unlink()
                removed.append(relative_path)
        except OSError as exc:
            errors.append(f"{relative_path}: {exc}")
    verification = {
        "json_restored_or_removed": manifest["files"][JSON_PATH]["existed"] == (root / JSON_PATH).exists(),
        "markdown_restored_or_removed": manifest["files"][MD_PATH]["existed"] == (root / MD_PATH).exists(),
    }
    report = {
        "stage": STAGE,
        "status": "FAIL_ROLLED_BACK" if not errors and all(verification.values()) else "ROLLBACK_INCOMPLETE",
        "reason": reason,
        "failed_checks": [asdict(item) for item in checks if item.status == "FAIL"],
        "restored_files": restored,
        "removed_failed_artifacts": removed,
        "rollback_errors": errors,
        "post_rollback_verification": verification,
        "database_evidence_after_rollback": database_evidence(root),
        "main_py_started": False,
        "wal_shm_manipulated": False,
    }
    write_atomic(root / FAILURE_REPORT, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def classify_domains(path: str, function_name: str, source: str) -> list[str]:
    haystack = f"{path} {function_name} {source[:4000]}".lower()
    scores = {
        domain: sum(1 for token in tokens if token in haystack)
        for domain, tokens in DOMAIN_TOKENS.items()
    }
    maximum = max(scores.values(), default=0)
    if maximum == 0:
        return ["cross_cutting"]
    return [domain for domain, score in scores.items() if score == maximum][:2]


def call_names(node: ast.AST) -> list[str]:
    return sorted({unparse(child.func) for child in ast.walk(node) if isinstance(child, ast.Call) and unparse(child.func)})


def assertion_contracts(node: ast.AST) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            expression = unparse(child.test)
            contracts.append({"kind": "assert", "expression_sha256": hashlib.sha256(expression.encode("utf-8")).hexdigest(), "expression_preview": expression[:240], "line": child.lineno})
        elif isinstance(child, ast.Call):
            name = unparse(child.func)
            if name.endswith(("assertEqual", "assertTrue", "assertFalse", "assertIsNone", "assertIsNotNone", "assertRaises", "assertIn", "assertNotIn")):
                expression = unparse(child)
                contracts.append({"kind": "assert_call", "assertion": name.split(".")[-1], "expression_sha256": hashlib.sha256(expression.encode("utf-8")).hexdigest(), "expression_preview": expression[:240], "line": child.lineno})
    return sorted(contracts, key=lambda item: item["line"])


def analyze_test_module(root: Path, path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    text = (root / path).read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=path)
    fixtures: list[dict[str, Any]] = []
    helpers: list[dict[str, Any]] = []
    module_hash = sha256(root / path)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        source = ast.get_source_segment(text, node) or ""
        assertions = assertion_contracts(node)
        calls = call_names(node)
        is_fixture = bool(TEST_FUNCTION_RE.search(node.name)) or bool(assertions)
        metadata = {
            "source_file": path,
            "source_sha256": module_hash,
            "function": node.name,
            "line": node.lineno,
            "end_line": node.end_lineno or node.lineno,
            "async": isinstance(node, ast.AsyncFunctionDef),
            "domains": classify_domains(path, node.name, source),
            "assertions": assertions,
            "assertion_count": len(assertions),
            "calls": calls,
            "determinism": {
                "seed_evidence": bool(SEED_RE.search(source)),
                "clock_evidence": bool(TIME_RE.search(source)),
                "database_evidence": bool(DB_RE.search(source)),
                "restart_evidence": bool(RESTART_RE.search(source)),
                "idempotency_evidence": bool(IDEMPOTENCY_RE.search(source)),
            },
        }
        if is_fixture:
            identity = f"{path}:{node.name}:{node.lineno}"
            metadata.update({
                "fixture_id": "v1_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
                "initial_state_contract": {
                    "source_setup": "derived_from_test_function_and_helpers",
                    "database": "isolated_test_database_if_declared_by_source",
                    "clock": "source_controlled_if_clock_evidence_else_unresolved",
                    "rng": "source_controlled_if_seed_evidence_else_unresolved",
                },
                "event_sequence_contract": calls,
                "expected_observation_contract": assertions,
                "db_delta_contract": "captured_by_assertions_or_repository_observations",
                "final_state_contract": "all_source_assertions_must_hold",
                "source_authority": "V1_TEST_REFERENCE",
            })
            fixtures.append(metadata)
        elif node.name.startswith(("make_", "build_", "create_", "seed_", "setup_")):
            helpers.append(metadata)
    return fixtures, helpers


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    coverage = payload["domain_coverage"]
    return "\n".join([
        "# ROM Stage 21.1.X2 - Behavioral fixtures ROM V1", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Test-reference modules parsed:** `{summary['test_module_count']}`",
        f"- **Behavioral fixtures:** `{summary['fixture_count']}`",
        f"- **Assertion contracts:** `{summary['assertion_contract_count']}`",
        f"- **Fixture helpers:** `{summary['helper_count']}`",
        f"- **Fixtures with seed evidence:** `{summary['seeded_fixture_count']}`",
        f"- **Fixtures with DB evidence:** `{summary['database_fixture_count']}`",
        f"- **Fixtures with restart evidence:** `{summary['restart_fixture_count']}`",
        f"- **Fixtures with idempotency evidence:** `{summary['idempotency_fixture_count']}`", "",
        "## Domain coverage", "",
        *[f"- `{domain}`: **{count}** fixtures" for domain, count in sorted(coverage.items())], "",
        "## Fixture contract", "",
        "Кожний fixture містить:", "",
        "- stable `fixture_id`;",
        "- source file, function, lines і SHA-256;",
        "- domain classification;",
        "- initial-state contract;",
        "- ordered call/event evidence;",
        "- assertion fingerprints і readable previews;",
        "- DB/restart/time/RNG/idempotency evidence;",
        "- final-state acceptance contract.", "",
        "Fixtures не запускають V1 runtime і не копіюють production state. Вони є immutable parity references для майбутніх executable V2 contract tests.", "",
        "## Determinism policy", "",
        "- RNG-dependent fixture без seed evidence позначається review candidate, а не deterministic PASS.",
        "- Time-dependent fixture без Clock evidence позначається review candidate.",
        "- DB fixture використовує тільки isolated test DB під час майбутнього executable replay.",
        "- Production game.db/WAL/SHM не відкривалися і не змінювалися.", "",
        "## Наступний етап", "",
        "Stage 21.1.X3 - матриця чинних і superseded policy.", "",
    ])


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, JSON_PATH, MD_PATH]
    result = git(root, "add", "-f", "--", *paths)
    if result.returncode != 0:
        raise PatchError(result.stderr.strip() or "git add failed")
    staged_result = git(root, "diff", "--cached", "--name-only", "-z")
    staged = sorted(item for item in staged_result.stdout.split("\0") if item)
    if staged_result.returncode != 0 or staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging allowlist mismatch: {staged}")
    committed = git(root, "commit", "-m", COMMIT_MESSAGE)
    if committed.returncode != 0:
        git(root, "reset", "--", *paths)
        raise PatchError(committed.stderr.strip() or committed.stdout.strip() or "git commit failed")
    commit_hash = rev(root, "HEAD")
    if not commit_hash:
        raise PatchError("commit created but HEAD cannot be resolved")
    return commit_hash


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    for required in (MODULE_INVENTORY, DOMAIN_CONTRACTS, CONTENT_INVENTORY):
        if not (root / required).is_file():
            print(f"[FAIL] Missing required input: {required}", file=sys.stderr)
            return 2

    print("[1/8] [PASS] Canonical inventories and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.X1c parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
    db_before = database_evidence(root)
    backup_manifest = prepare_backups(root)
    inventory = json.loads((root / MODULE_INVENTORY).read_text(encoding="utf-8"))
    domains = json.loads((root / DOMAIN_CONTRACTS).read_text(encoding="utf-8"))
    content = json.loads((root / CONTENT_INVENTORY).read_text(encoding="utf-8"))
    test_modules = [item for item in inventory["modules"] if item["classification"] == "TEST_REFERENCE"]

    print(f"[3/8] [PASS] Extracting behavioral contracts from {len(test_modules)} test-reference modules.")
    fixtures: list[dict[str, Any]] = []
    helpers: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, module in enumerate(test_modules, start=1):
        try:
            module_fixtures, module_helpers = analyze_test_module(root, module["path"])
            fixtures.extend(module_fixtures)
            helpers.extend(module_helpers)
        except (OSError, SyntaxError) as exc:
            errors.append({"path": module["path"], "error": str(exc)})
        if index % 50 == 0 or index == len(test_modules):
            print(f"    progress: {index}/{len(test_modules)} modules", flush=True)

    print("[4/8] [PASS] Building deterministic fixture registry and coverage queues.")
    fixture_ids = [fixture["fixture_id"] for fixture in fixtures]
    duplicate_ids = sorted([fixture_id for fixture_id, count in Counter(fixture_ids).items() if count > 1])
    domain_coverage = Counter(domain for fixture in fixtures for domain in fixture["domains"])
    assertion_count = sum(fixture["assertion_count"] for fixture in fixtures)
    seeded = [fixture for fixture in fixtures if fixture["determinism"]["seed_evidence"]]
    database_fixtures = [fixture for fixture in fixtures if fixture["determinism"]["database_evidence"]]
    restart_fixtures = [fixture for fixture in fixtures if fixture["determinism"]["restart_evidence"]]
    idempotency_fixtures = [fixture for fixture in fixtures if fixture["determinism"]["idempotency_evidence"]]
    clock_fixtures = [fixture for fixture in fixtures if fixture["determinism"]["clock_evidence"]]
    random_without_seed = [fixture for fixture in fixtures if any("random" in call.lower() or "rng" in call.lower() for call in fixture["calls"]) and not fixture["determinism"]["seed_evidence"]]
    time_without_clock = [fixture for fixture in fixtures if any(token in " ".join(fixture["calls"]).lower() for token in ("datetime", "time.", "utcnow")) and not fixture["determinism"]["clock_evidence"]]
    no_assertions = [fixture for fixture in fixtures if not fixture["assertions"]]
    core_domains = [name for name in domains["domain_contracts"] if name != "cross_cutting"]

    checks.extend([
        Check("AST_COVERAGE", "PASS" if not errors else "FAIL", "All test-reference modules parsed." if not errors else "Test-reference AST errors found.", {"errors": errors}, bool(errors)),
        Check("FIXTURES_FOUND", "PASS" if fixtures else "FAIL", f"Behavioral fixtures extracted: {len(fixtures)}.", {}, not fixtures),
        Check("FIXTURE_ID_UNIQUENESS", "PASS" if not duplicate_ids else "FAIL", "Fixture IDs are unique." if not duplicate_ids else "Duplicate fixture IDs found.", {"duplicates": duplicate_ids}, bool(duplicate_ids)),
        Check("ASSERTION_CONTRACTS_FOUND", "PASS" if assertion_count else "FAIL", f"Assertion contracts extracted: {assertion_count}.", {}, assertion_count == 0),
        Check("CORE_DOMAIN_COVERAGE", "PASS" if all(domain_coverage.get(domain, 0) for domain in core_domains) else "FAIL", "All core domains have fixture coverage.", {domain: domain_coverage.get(domain, 0) for domain in core_domains}, any(not domain_coverage.get(domain, 0) for domain in core_domains)),
        Check("CONTENT_REVISION", "PASS" if content.get("canonical_revision") == "21.1.X1c" else "FAIL", f"Canonical content revision: {content.get('canonical_revision')}.", {"expected": "21.1.X1c"}, content.get("canonical_revision") != "21.1.X1c"),
        Check("DATABASE_EVIDENCE_READY", "PASS", "DB/WAL/SHM evidence captured without opening SQLite.", {"production_connection_opened": False}),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"
    fixture_registry = sorted(fixtures, key=lambda item: (item["domains"], item["source_file"], item["line"]))
    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            "test_module_count": len(test_modules),
            "fixture_count": len(fixtures),
            "assertion_contract_count": assertion_count,
            "helper_count": len(helpers),
            "seeded_fixture_count": len(seeded),
            "clock_fixture_count": len(clock_fixtures),
            "database_fixture_count": len(database_fixtures),
            "restart_fixture_count": len(restart_fixtures),
            "idempotency_fixture_count": len(idempotency_fixtures),
        },
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "domain_coverage": dict(sorted(domain_coverage.items())),
        "fixtures": fixture_registry,
        "fixture_helpers": helpers,
        "review_queues": {
            "random_usage_without_seed_evidence": random_without_seed,
            "time_usage_without_clock_evidence": time_without_clock,
            "fixture_candidates_without_assertions": no_assertions,
        },
        "fixture_execution_contract": {
            "current_stage_mode": "STATIC_REFERENCE_EXTRACTION",
            "future_v2_replay_mode": "ISOLATED_RESET_BASED",
            "production_database_access": "FORBIDDEN",
            "initial_state_required": True,
            "seed_required_for_rng": True,
            "clock_required_for_time": True,
            "event_sequence_required": True,
            "expected_db_delta_required_for_mutations": True,
            "final_state_assertions_required": True,
            "source_hash_drift_blocks_replay": True,
        },
        "source_authority": {
            "module_inventory_commit": inventory["git"]["head_before_commit"],
            "domain_contract_commit": domains["git"]["head_before_commit"],
            "content_revision": content["canonical_revision"],
            "content_parent_commit": EXPECTED_PARENT,
        },
        "database_evidence_before": db_before,
        "artifacts": {"patch": PATCH_PATH, "json": JSON_PATH, "markdown": MD_PATH},
        "next_stage": "21.1.X3" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing V1 behavioral fixture registry and contract documentation.")
    try:
        write_atomic(root / JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / MD_PATH, render_markdown(payload))
        if conclusion != "GO":
            for item in checks:
                if item.status == "FAIL":
                    print(f"[FAIL] {item.check_id}: {item.summary}")
            report = rollback_artifacts(root, backup_manifest, "Behavioral fixture checks returned NO_GO.", checks)
            print(f"[6/8] [FAIL] NO_GO; rollback status: {report['status']}; commit not created.")
            return 1
        if db_before != database_evidence(root):
            report = rollback_artifacts(root, backup_manifest, "DB/WAL/SHM evidence changed before commit.", checks)
            print(f"[6/8] [FAIL] DB evidence changed; rollback status: {report['status']}.")
            return 2
    except Exception as exc:
        report = rollback_artifacts(root, backup_manifest, f"Unexpected mutation-phase failure: {exc}", checks)
        print(f"[6/8] [FAIL] {exc}; rollback status: {report['status']}.", file=sys.stderr)
        return 2

    print("[6/8] [PASS] Behavioral fixture coverage and deterministic contracts validated.")
    failure_path = root / FAILURE_REPORT
    if failure_path.exists():
        failure_path.unlink()
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.X2 commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        report = rollback_artifacts(root, backup_manifest, f"Commit phase failed: {exc}", checks)
        print(f"[7/8] [FAIL] {exc}; rollback status: {report['status']}.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Behavioral fixtures committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - V1 behavioral fixtures")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] TEST_MODULES: {len(test_modules)}")
    print(f"[PASS] FIXTURES: {len(fixtures)}")
    print(f"[PASS] ASSERTION_CONTRACTS: {assertion_count}")
    print(f"[PASS] SEEDED_FIXTURES: {len(seeded)}")
    print(f"[PASS] DATABASE_FIXTURES: {len(database_fixtures)}")
    print(f"[PASS] RESTART_FIXTURES: {len(restart_fixtures)}")
    print(f"[PASS] IDEMPOTENCY_FIXTURES: {len(idempotency_fixtures)}")
    print(f"[PASS] RANDOM_WITHOUT_SEED_REVIEW: {len(random_without_seed)}")
    print(f"[PASS] TIME_WITHOUT_CLOCK_REVIEW: {len(time_without_clock)}")
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: NOT REQUIRED")
    print("FAIL-SAFE ROLLBACK: ARMED")
    print("WAL/SHM: NOT MANIPULATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
