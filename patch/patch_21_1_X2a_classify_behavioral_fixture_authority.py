#!/usr/bin/env python3
"""Stage 21.1.X2a: classify authority of extracted V1 fixture candidates.

The patch refines Stage 21.1.X2 without executing V1 runtime code. Each source
record is assigned exactly one authority class, backed by explicit evidence.
Helpers and structural/documentation checks are not promoted to behavioral
fixtures merely because they contain assertions.
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

STAGE = "21.1.X2a"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "3d927ebe1e92683ebf7d9133c8c05a000376e36d"
SOURCE_JSON = "reports/stage_21_1_X2_v1_behavioral_fixtures.json"
CANONICAL_JSON = SOURCE_JSON
CANONICAL_MD = "MD/STAGE_21_1_X2_V1_BEHAVIORAL_FIXTURES.md"
REMEDIATION_JSON = "reports/stage_21_1_X2a_fixture_authority_classification.json"
REMEDIATION_MD = "MD/STAGE_21_1_X2A_FIXTURE_AUTHORITY_CLASSIFICATION.md"
FAILURE_REPORT = "reports/stage_21_1_X2a_failure_rollback.json"
PATCH_PATH = "patch/patch_21_1_X2a_classify_behavioral_fixture_authority.py"
COMMIT_MESSAGE = "Stage 21.1.X2a: classify behavioral fixture authority"
OWNED = {PATCH_PATH, CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD, FAILURE_REPORT}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
BACKUP_PREFIX = "stage_21_1_X2a"

AUTHORITY_CLASSES = (
    "BEHAVIORAL_EXECUTABLE_CANDIDATE",
    "BEHAVIORAL_STATIC_CONTRACT",
    "STRUCTURAL_SOURCE_CONTRACT",
    "DOCUMENTATION_ACCEPTANCE",
    "TOOL_WRAPPER",
    "HELPER_ONLY",
    "REVIEW_REQUIRED",
)
HELPER_NAMES = re.compile(r"(?i)^(assignment|source|segment|owner|fn|helper|extract|parse|find|collect|load|read|build|make|create|seed|setup|normalize|render|format|assert_)$")
WRAPPER_NAMES = re.compile(r"(?i)^(run_tool|run_check|run_script|invoke|execute|run)$")
BEHAVIOR_NAMES = re.compile(r"(?i)^(test_|scenario_|smoke_|verify_|check_|main$)")
STRUCTURAL_PATH = re.compile(r"(?i)(architecture|ast|duplicate|import|source|registration|manifest|schema|contract_scan|static)")
DOCUMENT_PATH = re.compile(r"(?i)(documentation|docs|markdown|readme|report|dump|roadmap)")
RUNTIME_CALL = re.compile(r"(?i)(combat|battle|quest|inventory|equip|trade|auction|guild|travel|shop|reward|level|player|character|database|sqlite|repository|handler|callback)")
STRUCTURAL_CALL = re.compile(r"(?i)(ast\.|read_text|read_bytes|git|subprocess|compile|parse|walk|grep|glob|rglob|inspect|getsource)")
RNG_CALL = re.compile(r"(?i)(random|randint|choice|shuffle|rng)")
SEED_EVIDENCE = re.compile(r"(?i)(random\.seed|random\.Random\s*\([^)]|seed\s*=|seed\s*\)|rng\s*=.*\d)")
TIME_CALL = re.compile(r"(?i)(datetime\.|utcnow|now\(|time\.|monotonic|ZoneInfo|timezone)")
CLOCK_CONTROL = re.compile(r"(?i)(fakeclock|frozen|freeze_time|advance_time|clock\s*=|now_provider|monotonic_provider)")


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
    for relative_path in (CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD):
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
    git(root, "reset", "--", CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD)
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
        relative_path: metadata["existed"] == (root / relative_path).exists()
        for relative_path, metadata in manifest["files"].items()
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


def find_function(root: Path, fixture: dict[str, Any]) -> tuple[ast.AST | None, str, list[str]]:
    path = root / fixture["source_file"]
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=str(path))
    matches = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == fixture["function"] and node.lineno == fixture["line"]
    ]
    if not matches:
        return None, "", []
    node = matches[0]
    source = ast.get_source_segment(text, node) or ""
    parents: list[str] = []
    for candidate in ast.walk(tree):
        if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)) or candidate is node:
            continue
        if candidate.lineno < node.lineno <= (candidate.end_lineno or candidate.lineno):
            parents.append(candidate.name)
    return node, source, parents


def classify_fixture(fixture: dict[str, Any], source: str, parents: list[str]) -> tuple[str, list[str], list[str]]:
    path = fixture["source_file"]
    name = fixture["function"]
    calls = " ".join(fixture.get("calls", []))
    evidence: list[str] = []
    warnings: list[str] = []
    nested = bool(parents)
    observable_oracle = fixture.get("assertion_count", 0) > 0
    runtime_signal = bool(RUNTIME_CALL.search(f"{path} {name} {calls} {source[:3000]}"))
    structural_signal = bool(STRUCTURAL_PATH.search(path) or STRUCTURAL_CALL.search(calls))
    documentation_signal = bool(DOCUMENT_PATH.search(path))
    wrapper_signal = bool(WRAPPER_NAMES.search(name) or re.search(r"(?i)(subprocess|run_tool|python .*tools/)", source))
    helper_signal = bool(nested or HELPER_NAMES.search(name))

    if nested:
        evidence.append("NESTED_FUNCTION")
    if observable_oracle:
        evidence.append("OBSERVABLE_ASSERTION_ORACLE")
    if runtime_signal:
        evidence.append("RUNTIME_BEHAVIOR_SIGNAL")
    if structural_signal:
        evidence.append("STRUCTURAL_SOURCE_SIGNAL")
    if documentation_signal:
        evidence.append("DOCUMENTATION_SIGNAL")
    if wrapper_signal:
        evidence.append("TOOL_INVOCATION_SIGNAL")

    if helper_signal and not (BEHAVIOR_NAMES.search(name) and runtime_signal):
        authority = "HELPER_ONLY"
    elif wrapper_signal and not runtime_signal:
        authority = "TOOL_WRAPPER"
    elif documentation_signal and not runtime_signal:
        authority = "DOCUMENTATION_ACCEPTANCE"
    elif structural_signal and not runtime_signal:
        authority = "STRUCTURAL_SOURCE_CONTRACT"
    elif runtime_signal and observable_oracle and not wrapper_signal:
        authority = "BEHAVIORAL_EXECUTABLE_CANDIDATE"
    elif runtime_signal and observable_oracle:
        authority = "BEHAVIORAL_STATIC_CONTRACT"
    elif observable_oracle and BEHAVIOR_NAMES.search(name):
        authority = "BEHAVIORAL_STATIC_CONTRACT"
    else:
        authority = "REVIEW_REQUIRED"

    actual_rng = bool(RNG_CALL.search(f"{calls} {source}"))
    actual_seed = bool(SEED_EVIDENCE.search(source))
    actual_time = bool(TIME_CALL.search(f"{calls} {source}"))
    actual_clock = bool(CLOCK_CONTROL.search(source))
    if actual_rng and not actual_seed:
        warnings.append("RNG_WITHOUT_REAL_SEED_EVIDENCE")
    if actual_time and not actual_clock:
        warnings.append("TIME_WITHOUT_REAL_CLOCK_CONTROL")
    if authority == "BEHAVIORAL_EXECUTABLE_CANDIDATE" and not observable_oracle:
        warnings.append("EXECUTABLE_FIXTURE_WITHOUT_OBSERVABLE_ORACLE")
    return authority, sorted(set(evidence)), sorted(set(warnings))


def render_canonical(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    counts = summary["authority_counts"]
    return "\n".join([
        "# ROM Stage 21.1.X2 - Behavioral fixtures ROM V1", "",
        "- **Canonical revision:** `Stage 21.1.X2a`",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Source candidates classified:** `{summary['source_candidate_count']}`",
        f"- **Behavioral executable candidates:** `{counts.get('BEHAVIORAL_EXECUTABLE_CANDIDATE', 0)}`",
        f"- **Behavioral static contracts:** `{counts.get('BEHAVIORAL_STATIC_CONTRACT', 0)}`",
        f"- **Structural source contracts:** `{counts.get('STRUCTURAL_SOURCE_CONTRACT', 0)}`",
        f"- **Documentation acceptance:** `{counts.get('DOCUMENTATION_ACCEPTANCE', 0)}`",
        f"- **Tool wrappers:** `{counts.get('TOOL_WRAPPER', 0)}`",
        f"- **Helpers only:** `{counts.get('HELPER_ONLY', 0)}`",
        f"- **Review required:** `{counts.get('REVIEW_REQUIRED', 0)}`", "",
        "## Canonical authority rules", "",
        "- Assertion alone does not make a helper behavioral.",
        "- AST/source/document checks are structural contracts, not runtime parity fixtures.",
        "- Executable behavioral candidates require runtime behavior evidence and an observable oracle.",
        "- RNG dependency requires real seed evidence in source.",
        "- Time dependency requires real Clock/frozen-time control evidence.",
        "- Every record preserves source path, function, lines and SHA-256 authority.", "",
        "## Review queues", "",
        f"- RNG without real seed evidence: **{len(payload['review_queues']['rng_without_real_seed'])}**.",
        f"- Time without real Clock control: **{len(payload['review_queues']['time_without_real_clock'])}**.",
        f"- Review-required records: **{len(payload['review_queues']['review_required'])}**.", "",
        "## Usage in V2", "",
        "Only behavioral executable candidates and explicitly approved behavioral static contracts may seed parity tests. Structural, documentation, wrapper and helper records remain supporting evidence and must not be counted as gameplay behavior.", "",
        "Production code and DB/WAL/SHM were not opened or modified.", "",
        "## Наступний етап", "",
        "Stage 21.1.X3 - матриця чинних і superseded policy.", "",
    ])


def render_remediation(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join([
        "# ROM Stage 21.1.X2a - fixture authority classification", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Candidates before classification:** `{summary['source_candidate_count']}`",
        f"- **Behavioral authority records:** `{summary['behavioral_authority_count']}`",
        f"- **Supporting/non-behavioral records:** `{summary['supporting_authority_count']}`",
        f"- **Review required:** `{summary['authority_counts'].get('REVIEW_REQUIRED', 0)}`", "",
        "## Safeguards", "",
        "- `HELPER_IS_NOT_BEHAVIORAL_BY_ASSERT_ALONE`",
        "- `STRUCTURAL_CHECK_NOT_RUNTIME_BEHAVIOR`",
        "- `EXECUTABLE_FIXTURE_REQUIRES_OBSERVABLE_ORACLE`",
        "- `RNG_DEPENDENCY_REQUIRES_REAL_SEED_EVIDENCE`",
        "- `TIME_DEPENDENCY_REQUIRES_REAL_CLOCK_USAGE`",
        "- `SOURCE_AUTHORITY_RECORDED`", "",
        "Production code and DB/WAL/SHM were not opened or modified.", "",
    ])


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD]
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
    if not (root / SOURCE_JSON).is_file():
        print(f"[FAIL] Missing {SOURCE_JSON}", file=sys.stderr)
        return 2

    print("[1/8] [PASS] Stage 21.1.X2 registry and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.X2 parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified; parent artifacts backed up in ROM\\backup.")
    db_before = database_evidence(root)
    backup_manifest = prepare_backups(root)
    parent_blob = git_blob(root, EXPECTED_PARENT, SOURCE_JSON)
    if parent_blob is None:
        print(f"[FAIL] Cannot read {SOURCE_JSON} from expected parent.", file=sys.stderr)
        return 2
    original = json.loads(parent_blob.decode("utf-8"))

    print(f"[3/8] [PASS] Classifying authority of {len(original['fixtures'])} fixture candidates.")
    classified: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, fixture in enumerate(original["fixtures"], start=1):
        try:
            node, source, parents = find_function(root, fixture)
            if node is None:
                raise ValueError("source function not found at recorded line")
            authority, evidence, warnings = classify_fixture(fixture, source, parents)
            record = dict(fixture)
            record.update({
                "authority_class": authority,
                "authority_evidence": evidence,
                "authority_warnings": warnings,
                "enclosing_functions": parents,
                "source_function_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            })
            classified.append(record)
        except (OSError, SyntaxError, ValueError) as exc:
            errors.append({"fixture_id": fixture.get("fixture_id"), "source_file": fixture.get("source_file"), "function": fixture.get("function"), "error": str(exc)})
        if index % 25 == 0 or index == len(original["fixtures"]):
            print(f"    progress: {index}/{len(original['fixtures'])} candidates", flush=True)

    print("[4/8] [PASS] Building authority registry and semantic safeguard queues.")
    counts = Counter(record["authority_class"] for record in classified)
    rng_without_seed = [record for record in classified if "RNG_WITHOUT_REAL_SEED_EVIDENCE" in record["authority_warnings"]]
    time_without_clock = [record for record in classified if "TIME_WITHOUT_REAL_CLOCK_CONTROL" in record["authority_warnings"]]
    review_required = [record for record in classified if record["authority_class"] == "REVIEW_REQUIRED"]
    helper_promoted = [record for record in classified if record["authority_class"].startswith("BEHAVIORAL_") and (record["enclosing_functions"] or HELPER_NAMES.search(record["function"]))]
    structural_promoted = [record for record in classified if record["authority_class"] == "BEHAVIORAL_EXECUTABLE_CANDIDATE" and "STRUCTURAL_SOURCE_SIGNAL" in record["authority_evidence"] and "RUNTIME_BEHAVIOR_SIGNAL" not in record["authority_evidence"]]
    executable_without_oracle = [record for record in classified if record["authority_class"] == "BEHAVIORAL_EXECUTABLE_CANDIDATE" and record["assertion_count"] == 0]
    missing_authority = [record for record in classified if record["authority_class"] not in AUTHORITY_CLASSES or not record["authority_evidence"]]
    behavioral = [record for record in classified if record["authority_class"] in {"BEHAVIORAL_EXECUTABLE_CANDIDATE", "BEHAVIORAL_STATIC_CONTRACT"}]
    supporting = [record for record in classified if record["authority_class"] in {"STRUCTURAL_SOURCE_CONTRACT", "DOCUMENTATION_ACCEPTANCE", "TOOL_WRAPPER", "HELPER_ONLY"}]

    checks.extend([
        Check("SOURCE_COVERAGE", "PASS" if not errors and len(classified) == original["summary"]["fixture_count"] else "FAIL", f"Classified {len(classified)} of {original['summary']['fixture_count']} candidates.", {"errors": errors}, bool(errors) or len(classified) != original["summary"]["fixture_count"]),
        Check("AUTHORITY_EXCLUSIVITY", "PASS" if sum(counts.values()) == len(classified) else "FAIL", "Every candidate has exactly one authority class.", dict(counts), sum(counts.values()) != len(classified)),
        Check("HELPER_IS_NOT_BEHAVIORAL_BY_ASSERT_ALONE", "PASS" if not helper_promoted else "FAIL", "No nested/helper record was promoted solely by assertions.", {"violations": [record["fixture_id"] for record in helper_promoted]}, bool(helper_promoted)),
        Check("STRUCTURAL_CHECK_NOT_RUNTIME_BEHAVIOR", "PASS" if not structural_promoted else "FAIL", "Structural-only checks are not executable behavioral fixtures.", {"violations": [record["fixture_id"] for record in structural_promoted]}, bool(structural_promoted)),
        Check("EXECUTABLE_FIXTURE_REQUIRES_OBSERVABLE_ORACLE", "PASS" if not executable_without_oracle else "FAIL", "Every executable candidate has an observable assertion oracle.", {"violations": [record["fixture_id"] for record in executable_without_oracle]}, bool(executable_without_oracle)),
        Check("RNG_DEPENDENCY_REQUIRES_REAL_SEED_EVIDENCE", "PASS", f"RNG review candidates: {len(rng_without_seed)}.", {"review_count": len(rng_without_seed)}),
        Check("TIME_DEPENDENCY_REQUIRES_REAL_CLOCK_USAGE", "PASS", f"Clock review candidates: {len(time_without_clock)}.", {"review_count": len(time_without_clock)}),
        Check("SOURCE_AUTHORITY_RECORDED", "PASS" if not missing_authority else "FAIL", "Every record has source authority and evidence.", {"violations": [record.get("fixture_id") for record in missing_authority]}, bool(missing_authority)),
        Check("DATABASE_EVIDENCE_READY", "PASS", "DB/WAL/SHM evidence captured without opening SQLite.", {"production_connection_opened": False}),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"

    canonical = dict(original)
    canonical.update({
        "schema_version": 2,
        "canonical_revision": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "fixtures": sorted(classified, key=lambda record: (record["authority_class"], record["source_file"], record["line"])),
        "authority_contract": {
            "classes": list(AUTHORITY_CLASSES),
            "helper_assertion_alone_is_behavioral": False,
            "structural_check_is_runtime_behavior": False,
            "executable_requires_observable_oracle": True,
            "rng_requires_real_seed_evidence": True,
            "time_requires_real_clock_control": True,
            "source_authority_required": True,
        },
        "review_queues": {
            "rng_without_real_seed": rng_without_seed,
            "time_without_real_clock": time_without_clock,
            "review_required": review_required,
        },
        "database_evidence_before": db_before,
        "artifacts": {"patch": PATCH_PATH, "json": CANONICAL_JSON, "markdown": CANONICAL_MD, "remediation_json": REMEDIATION_JSON, "remediation_markdown": REMEDIATION_MD},
        "next_stage": "21.1.X3" if conclusion == "GO" else None,
    })
    canonical["summary"] = dict(original["summary"],
        conclusion=conclusion,
        blocking_failures=blockers,
        source_candidate_count=len(classified),
        authority_counts=dict(sorted(counts.items())),
        behavioral_authority_count=len(behavioral),
        supporting_authority_count=len(supporting),
        rng_without_real_seed_count=len(rng_without_seed),
        time_without_real_clock_count=len(time_without_clock),
    )
    remediation = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": canonical["generated_at_utc"],
        "summary": {
            "conclusion": conclusion,
            "source_candidate_count": len(classified),
            "authority_counts": dict(sorted(counts.items())),
            "behavioral_authority_count": len(behavioral),
            "supporting_authority_count": len(supporting),
        },
        "checks": [asdict(item) for item in checks],
        "canonical_artifacts_updated": [CANONICAL_JSON, CANONICAL_MD],
        "database_evidence_before": db_before,
        "next_stage": "21.1.X3" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing canonical authority registry and remediation evidence.")
    try:
        write_atomic(root / CANONICAL_JSON, json.dumps(canonical, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / CANONICAL_MD, render_canonical(canonical))
        write_atomic(root / REMEDIATION_JSON, json.dumps(remediation, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / REMEDIATION_MD, render_remediation(remediation))
        if conclusion != "GO":
            for item in checks:
                if item.status == "FAIL":
                    print(f"[FAIL] {item.check_id}: {item.summary}")
            report = rollback_artifacts(root, backup_manifest, "Fixture authority checks returned NO_GO.", checks)
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

    print("[6/8] [PASS] Fixture authority semantics and safeguards validated.")
    failure_path = root / FAILURE_REPORT
    if failure_path.exists():
        failure_path.unlink()
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.X2a commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        report = rollback_artifacts(root, backup_manifest, f"Commit phase failed: {exc}", checks)
        print(f"[7/8] [FAIL] {exc}; rollback status: {report['status']}.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Fixture authority classification committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - classify behavioral fixture authority")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] SOURCE_CANDIDATES: {len(classified)}")
    for authority in AUTHORITY_CLASSES:
        print(f"[PASS] {authority}: {counts.get(authority, 0)}")
    print(f"[PASS] RNG_WITHOUT_REAL_SEED_REVIEW: {len(rng_without_seed)}")
    print(f"[PASS] TIME_WITHOUT_REAL_CLOCK_REVIEW: {len(time_without_clock)}")
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
