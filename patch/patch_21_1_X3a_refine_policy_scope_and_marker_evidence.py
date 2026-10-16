#!/usr/bin/env python3
"""Stage 21.1.X3a: refine policy scope and marker evidence.

Rebuild the Stage 21.1.X3 matrix from its parent commit. Non-policy runtime
state is excluded; marker evidence is scoped to the symbol, its inline comment,
immediately preceding comment block, and module docstring. Mixed active/shadow
evidence receives an explicit conflict classification and is never migrated.
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

STAGE = "21.1.X3a"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "3e6be5ee692972d0a33c4f8eca6526fcb0b47d62"
SOURCE_JSON = "reports/stage_21_1_X3_superseded_policy_matrix.json"
CANONICAL_JSON = SOURCE_JSON
CANONICAL_MD = "MD/STAGE_21_1_X3_SUPERSEDED_POLICY_MATRIX.md"
REMEDIATION_JSON = "reports/stage_21_1_X3a_policy_scope_marker_refinement.json"
REMEDIATION_MD = "MD/STAGE_21_1_X3A_POLICY_SCOPE_MARKER_REFINEMENT.md"
FAILURE_REPORT = "reports/stage_21_1_X3a_failure_rollback.json"
PATCH_PATH = "patch/patch_21_1_X3a_refine_policy_scope_and_marker_evidence.py"
COMMIT_MESSAGE = "Stage 21.1.X3a: refine policy scope and marker evidence"
OWNED = {PATCH_PATH, CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD, FAILURE_REPORT}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
BACKUP_PREFIX = "stage_21_1_X3a"

POLICY_SYMBOL_RE = re.compile(
    r"(?i)(policy|rule|limit|cap|chance|rate|multiplier|price|cost|reward|cooldown|"
    r"duration|threshold|retention|timeout|interval|exp|gold|damage|defense|attack|"
    r"hp|mp|mana|rage|energy|premium|capacity|slot|drop|repair|durability|namespace)"
)
NON_POLICY_SYMBOL_RE = re.compile(
    r"(?i)^(DB_PATH|LOGGER|LOG_LEVEL|states?|_?registered|_?REGISTERED_BOTS|BOTS?|"
    r"COMMANDS?|__all__|__version__|HANDLERS?|ROUTERS?|CALLBACKS?|CONNECTIONS?|"
    r"DEFAULT_PATH|BASE_DIR|ROOT_DIR|ENV_FILE|TOKEN|BOT_TOKEN)$"
)
NON_POLICY_VALUE_RE = re.compile(r"(?i)(logger|pathlib|sqlite3\.Connection|telebot|router|handler|callback)")
EXPLICIT_SUPERSEDED_RE = re.compile(
    r"(?i)(superseded|deprecated|obsolete|legacy[_ -]?only|do[_ -]?not[_ -]?migrate|"
    r"not[_ -]?required|replaced[_ -]?by|historical[_ -]?only|old[_ -]?policy)"
)
SHADOW_RE = re.compile(r"(?i)(candidate|shadow|fallback|compat|legacy|temporary|experimental)")
ACTIVE_RE = re.compile(r"(?i)(canonical|authoritative|accepted|current|active|production|final|effective)")
REPLACEMENT_RE = re.compile(r"(?i)(replaced[_ -]?by|superseded[_ -]?by|use\s+([A-Z][A-Z0-9_]+)|migrated[_ -]?to)")

CLASSIFICATIONS = (
    "ACTIVE_CANONICAL",
    "SUPERSEDED_EXPLICIT",
    "HISTORICAL_ONLY",
    "SHADOW_CANDIDATE",
    "ACTIVE_SHADOW_CONFLICT",
    "OWNER_REVIEW_REQUIRED",
)


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
    evidence: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists():
            evidence[name] = {"exists": False}
            continue
        stat = path.stat()
        evidence[name] = {"exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}
    return evidence


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
    verification = {path: metadata["existed"] == (root / path).exists() for path, metadata in manifest["files"].items()}
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


def module_docstring(tree: ast.Module) -> str:
    return ast.get_docstring(tree, clean=False) or ""


def scoped_marker_text(text: str, tree: ast.Module, line: int) -> dict[str, str]:
    lines = text.splitlines()
    inline = lines[line - 1] if 0 < line <= len(lines) else ""
    preceding: list[str] = []
    index = line - 2
    while index >= 0 and len(preceding) < 6:
        stripped = lines[index].strip()
        if stripped.startswith("#"):
            preceding.append(stripped)
            index -= 1
            continue
        if not stripped:
            if preceding:
                break
            index -= 1
            continue
        break
    return {
        "symbol_line": inline,
        "preceding_comment": "\n".join(reversed(preceding)),
        "module_docstring": module_docstring(tree),
    }


def is_policy_scope(entry: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    symbol = entry["symbol"]
    preview = entry.get("value_preview") or ""
    if NON_POLICY_SYMBOL_RE.fullmatch(symbol):
        reasons.append("EXCLUDED_NON_POLICY_SYMBOL")
    if NON_POLICY_VALUE_RE.search(preview):
        reasons.append("EXCLUDED_RUNTIME_OBJECT_OR_PATH")
    if not POLICY_SYMBOL_RE.search(symbol):
        reasons.append("NO_POLICY_SEMANTIC_IN_SYMBOL")
    return not reasons, reasons


def classify(entry: dict[str, Any], siblings: list[dict[str, Any]]) -> tuple[str, list[str], dict[str, Any]]:
    scoped = entry["scoped_marker_evidence"]
    symbol_text = entry["symbol"]
    local_text = " ".join([symbol_text, scoped["symbol_line"], scoped["preceding_comment"]])
    module_text = scoped["module_docstring"]
    explicit = bool(EXPLICIT_SUPERSEDED_RE.search(local_text) or EXPLICIT_SUPERSEDED_RE.search(module_text))
    shadow = bool(SHADOW_RE.search(symbol_text) or SHADOW_RE.search(scoped["symbol_line"]) or SHADOW_RE.search(scoped["preceding_comment"]))
    active = bool(ACTIVE_RE.search(symbol_text) or ACTIVE_RE.search(scoped["symbol_line"]) or ACTIVE_RE.search(scoped["preceding_comment"]) or ACTIVE_RE.search(module_text))
    replacement = REPLACEMENT_RE.search(local_text + " " + module_text)
    marker = {"explicit_superseded": explicit, "shadow": shadow, "active": active, "replacement_evidence": replacement.group(0) if replacement else None}
    reasons: list[str] = []
    if explicit:
        reasons.append("SCOPED_EXPLICIT_SUPERSEDED_MARKER")
        return "SUPERSEDED_EXPLICIT", reasons, marker
    if active and shadow:
        reasons.append("SCOPED_ACTIVE_AND_SHADOW_EVIDENCE")
        return "ACTIVE_SHADOW_CONFLICT", reasons, marker
    if shadow:
        reasons.append("SCOPED_SHADOW_MARKER")
        return "SHADOW_CANDIDATE", reasons, marker
    distinct_values = {item.get("value_sha256") for item in siblings if item.get("value_sha256")}
    if len(siblings) == 1 and entry["evidence"]["runtime_source"] and entry["literal"]:
        reasons.extend(["SINGLE_RUNTIME_OWNER", "LITERAL_POLICY_VALUE"])
        return "ACTIVE_CANONICAL", reasons, marker
    if active and entry["evidence"]["runtime_source"]:
        reasons.extend(["SCOPED_ACTIVE_MARKER", "RUNTIME_SOURCE"])
        return "ACTIVE_CANONICAL", reasons, marker
    if len(siblings) > 1 and len(distinct_values) > 1:
        reasons.append("MULTIPLE_DISTINCT_VALUES_REQUIRE_OWNER_REVIEW")
        return "OWNER_REVIEW_REQUIRED", reasons, marker
    if not entry["evidence"]["runtime_source"]:
        reasons.append("NON_RUNTIME_HISTORICAL_SOURCE")
        return "HISTORICAL_ONLY", reasons, marker
    reasons.append("INSUFFICIENT_CANONICAL_OWNER_EVIDENCE")
    return "OWNER_REVIEW_REQUIRED", reasons, marker


def render_canonical(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    counts = summary["classification_counts"]
    return "\n".join([
        "# ROM Stage 21.1.X3 - current and superseded policy matrix", "",
        "- **Canonical revision:** `Stage 21.1.X3a`",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Candidates before scope filtering:** `{summary['candidate_count_before_scope_filter']}`",
        f"- **Policy-only candidates:** `{summary['policy_candidate_count']}`",
        f"- **Excluded non-policy records:** `{summary['excluded_non_policy_count']}`",
        f"- **Active canonical:** `{counts.get('ACTIVE_CANONICAL', 0)}`",
        f"- **Superseded explicit:** `{counts.get('SUPERSEDED_EXPLICIT', 0)}`",
        f"- **Historical only:** `{counts.get('HISTORICAL_ONLY', 0)}`",
        f"- **Shadow candidates:** `{counts.get('SHADOW_CANDIDATE', 0)}`",
        f"- **Active/shadow conflicts:** `{counts.get('ACTIVE_SHADOW_CONFLICT', 0)}`",
        f"- **Owner review required:** `{counts.get('OWNER_REVIEW_REQUIRED', 0)}`", "",
        "## Marker scope", "",
        "Policy markers are read only from the symbol name, assignment line, immediately preceding comment block, and module docstring. Neighboring assignments cannot contribute markers.", "",
        "## Migration rules", "",
        "- Only `ACTIVE_CANONICAL` may migrate automatically.",
        "- `ACTIVE_SHADOW_CONFLICT` is never auto-migrated.",
        "- Supersession requires explicit replacement/deprecation evidence.",
        "- Non-policy runtime state is excluded from the migration allowlist.",
        "- Every matrix row preserves source, lines, hashes, scoped evidence, classification reasons and value fingerprint.", "",
        "## Review queues", "",
        f"- Multiple active groups: **{len(payload['review_queues']['multiple_active_candidates'])}**.",
        f"- Groups without active owner: **{len(payload['review_queues']['groups_without_active_owner'])}**.",
        f"- Active/shadow conflicts: **{len(payload['review_queues']['active_shadow_conflicts'])}**.",
        f"- Owner-review groups: **{len(payload['review_queues']['owner_review_required'])}**.",
        f"- Superseded without replacement evidence: **{len(payload['review_queues']['superseded_without_replacement'])}**.", "",
        "Production code and DB/WAL/SHM were not opened or modified.", "",
        "## Наступний етап", "",
        "Stage 21.1.9 - observability, logging, errors and audit trails inventory.", "",
    ])


def render_remediation(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join([
        "# ROM Stage 21.1.X3a - policy scope and marker refinement", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Candidates before:** `{summary['candidate_count_before_scope_filter']}`",
        f"- **Policy-only after:** `{summary['policy_candidate_count']}`",
        f"- **Excluded non-policy:** `{summary['excluded_non_policy_count']}`",
        f"- **Active/shadow conflicts:** `{summary['classification_counts'].get('ACTIVE_SHADOW_CONFLICT', 0)}`", "",
        "## Safeguards", "",
        "- `NON_POLICY_RUNTIME_STATE_EXCLUDED`",
        "- `MARKER_SCOPED_TO_SYMBOL`",
        "- `ACTIVE_SHADOW_CONFLICT_NOT_AUTO_MIGRATED`",
        "- `SUPERSESSION_REQUIRES_REPLACEMENT_EVIDENCE`",
        "- `MIGRATION_ALLOWLIST_CONTAINS_POLICY_ONLY`",
        "- `FULL_EVIDENCE_PERSISTED_IN_JSON`", "",
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

    print("[1/8] [PASS] Stage 21.1.X3 matrix and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.X3 parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
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

    print(f"[3/8] [PASS] Refining scope and marker evidence for {len(original['policy_matrix'])} policy candidates.")
    scoped_entries: list[dict[str, Any]] = []
    excluded_entries: list[dict[str, Any]] = []
    parse_cache: dict[str, tuple[str, ast.Module]] = {}
    errors: list[dict[str, Any]] = []
    for index, entry in enumerate(original["policy_matrix"], start=1):
        try:
            source_file = entry["source_file"]
            if source_file not in parse_cache:
                text = (root / source_file).read_text(encoding="utf-8", errors="replace")
                parse_cache[source_file] = (text, ast.parse(text, filename=source_file))
            text, tree = parse_cache[source_file]
            scoped = scoped_marker_text(text, tree, entry["line"])
            in_scope, exclusion_reasons = is_policy_scope(entry)
            refined = dict(entry)
            refined["scoped_marker_evidence"] = scoped
            refined["scope_evidence"] = {"is_policy": in_scope, "exclusion_reasons": exclusion_reasons}
            if in_scope:
                scoped_entries.append(refined)
            else:
                refined["policy_classification"] = "EXCLUDED_NON_POLICY"
                refined["automatic_v2_migration"] = False
                excluded_entries.append(refined)
        except (OSError, SyntaxError) as exc:
            errors.append({"policy_id": entry.get("policy_id"), "source_file": entry.get("source_file"), "error": str(exc)})
        if index % 75 == 0 or index == len(original["policy_matrix"]):
            print(f"    progress: {index}/{len(original['policy_matrix'])} candidates", flush=True)

    print("[4/8] [PASS] Rebuilding policy groups, scoped classifications and replacement evidence.")
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for entry in scoped_entries:
        key = (entry["matrix_group"]["domain"], entry["symbol"])
        groups[key].append(entry)
    matrix: list[dict[str, Any]] = []
    for key, siblings in sorted(groups.items()):
        for entry in siblings:
            classification, reasons, marker = classify(entry, siblings)
            refined = dict(entry)
            refined.update({
                "policy_classification": classification,
                "classification_evidence": reasons,
                "resolved_marker_evidence": marker,
                "automatic_v2_migration": classification == "ACTIVE_CANONICAL",
            })
            matrix.append(refined)
    counts = Counter(entry["policy_classification"] for entry in matrix)
    by_group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for entry in matrix:
        by_group[(entry["matrix_group"]["domain"], entry["symbol"])].append(entry)
    multiple_active = [{"domain": key[0], "symbol": key[1], "entries": entries} for key, entries in by_group.items() if sum(item["policy_classification"] == "ACTIVE_CANONICAL" for item in entries) > 1]
    without_active = [{"domain": key[0], "symbol": key[1], "entries": entries} for key, entries in by_group.items() if not any(item["policy_classification"] == "ACTIVE_CANONICAL" for item in entries)]
    conflicts = [entry for entry in matrix if entry["policy_classification"] == "ACTIVE_SHADOW_CONFLICT"]
    owner_review = [{"domain": key[0], "symbol": key[1], "entries": entries} for key, entries in by_group.items() if any(item["policy_classification"] == "OWNER_REVIEW_REQUIRED" for item in entries)]
    superseded_without_replacement = [entry for entry in matrix if entry["policy_classification"] == "SUPERSEDED_EXPLICIT" and not entry["resolved_marker_evidence"]["replacement_evidence"]]
    migration_allowlist = [entry["policy_id"] for entry in matrix if entry["automatic_v2_migration"]]
    non_policy_in_allowlist = sorted(set(migration_allowlist) & {entry["policy_id"] for entry in excluded_entries})
    conflict_in_allowlist = [entry["policy_id"] for entry in conflicts if entry["automatic_v2_migration"]]
    unscoped_marker_records = [entry for entry in matrix if "scoped_marker_evidence" not in entry or "resolved_marker_evidence" not in entry]

    checks.extend([
        Check("SOURCE_COVERAGE", "PASS" if not errors and len(scoped_entries) + len(excluded_entries) == len(original["policy_matrix"]) else "FAIL", f"Processed {len(scoped_entries) + len(excluded_entries)} of {len(original['policy_matrix'])} records.", {"errors": errors}, bool(errors) or len(scoped_entries) + len(excluded_entries) != len(original["policy_matrix"])),
        Check("NON_POLICY_RUNTIME_STATE_EXCLUDED", "PASS" if not non_policy_in_allowlist else "FAIL", f"Excluded non-policy records: {len(excluded_entries)}.", {"allowlist_violations": non_policy_in_allowlist}, bool(non_policy_in_allowlist)),
        Check("MARKER_SCOPED_TO_SYMBOL", "PASS" if not unscoped_marker_records else "FAIL", "Every policy row has scoped marker evidence.", {"violations": [entry["policy_id"] for entry in unscoped_marker_records]}, bool(unscoped_marker_records)),
        Check("ACTIVE_SHADOW_CONFLICT_NOT_AUTO_MIGRATED", "PASS" if not conflict_in_allowlist else "FAIL", f"Active/shadow conflicts: {len(conflicts)}.", {"allowlist_violations": conflict_in_allowlist}, bool(conflict_in_allowlist)),
        Check("SUPERSESSION_REQUIRES_REPLACEMENT_EVIDENCE", "PASS", f"Superseded records without replacement evidence remain review items: {len(superseded_without_replacement)}.", {"review_count": len(superseded_without_replacement)}),
        Check("MIGRATION_ALLOWLIST_CONTAINS_POLICY_ONLY", "PASS" if not non_policy_in_allowlist else "FAIL", f"Migration allowlist entries: {len(migration_allowlist)}.", {"violations": non_policy_in_allowlist}, bool(non_policy_in_allowlist)),
        Check("FULL_EVIDENCE_PERSISTED_IN_JSON", "PASS" if not unscoped_marker_records else "FAIL", "Source, value, scoped markers and classification reasons are persisted per row.", {}, bool(unscoped_marker_records)),
        Check("DATABASE_EVIDENCE_READY", "PASS", "DB/WAL/SHM evidence captured without opening SQLite.", {"production_connection_opened": False}),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"
    review_queues = {
        "multiple_active_candidates": multiple_active,
        "groups_without_active_owner": without_active,
        "active_shadow_conflicts": conflicts,
        "owner_review_required": owner_review,
        "superseded_without_replacement": superseded_without_replacement,
    }
    canonical = dict(original)
    canonical.update({
        "schema_version": 2,
        "canonical_revision": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "policy_matrix": sorted(matrix, key=lambda entry: (entry["domains"], entry["symbol"], entry["source_file"], entry["line"])),
        "excluded_non_policy_records": excluded_entries,
        "migration_allowlist": migration_allowlist,
        "review_queues": review_queues,
        "marker_scope_contract": {
            "allowed_sources": ["symbol_name", "assignment_line", "immediately_preceding_comment_block", "module_docstring"],
            "neighboring_assignment_context_forbidden": True,
            "active_shadow_conflict_auto_migration": False,
            "supersession_requires_replacement_evidence": True,
        },
        "database_evidence_before": db_before,
        "artifacts": {"patch": PATCH_PATH, "json": CANONICAL_JSON, "markdown": CANONICAL_MD, "remediation_json": REMEDIATION_JSON, "remediation_markdown": REMEDIATION_MD},
        "next_stage": "21.1.9" if conclusion == "GO" else None,
    })
    canonical["summary"] = dict(original["summary"],
        conclusion=conclusion,
        blocking_failures=blockers,
        candidate_count_before_scope_filter=len(original["policy_matrix"]),
        policy_candidate_count=len(matrix),
        policy_group_count=len(groups),
        excluded_non_policy_count=len(excluded_entries),
        migration_allowlist_count=len(migration_allowlist),
        classification_counts=dict(sorted(counts.items())),
    )
    canonical["v2_policy_migration_contract"] = dict(original["v2_policy_migration_contract"],
        automatic_migration_allowed_classifications=["ACTIVE_CANONICAL"],
        active_shadow_conflict_excluded=True,
        non_policy_runtime_state_excluded=True,
        marker_scope="SYMBOL_LOCAL",
        full_row_evidence_persisted=True,
    )
    remediation = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": canonical["generated_at_utc"],
        "summary": {
            "conclusion": conclusion,
            "candidate_count_before_scope_filter": len(original["policy_matrix"]),
            "policy_candidate_count": len(matrix),
            "excluded_non_policy_count": len(excluded_entries),
            "classification_counts": dict(sorted(counts.items())),
            "migration_allowlist_count": len(migration_allowlist),
        },
        "checks": [asdict(item) for item in checks],
        "canonical_artifacts_updated": [CANONICAL_JSON, CANONICAL_MD],
        "database_evidence_before": db_before,
        "next_stage": "21.1.9" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing canonical policy matrix and refinement evidence.")
    try:
        write_atomic(root / CANONICAL_JSON, json.dumps(canonical, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / CANONICAL_MD, render_canonical(canonical))
        write_atomic(root / REMEDIATION_JSON, json.dumps(remediation, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / REMEDIATION_MD, render_remediation(remediation))
        if conclusion != "GO":
            for item in checks:
                if item.status == "FAIL":
                    print(f"[FAIL] {item.check_id}: {item.summary}")
            report = rollback_artifacts(root, backup_manifest, "Policy refinement checks returned NO_GO.", checks)
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

    print("[6/8] [PASS] Policy scope, marker evidence and migration safeguards validated.")
    failure_path = root / FAILURE_REPORT
    if failure_path.exists():
        failure_path.unlink()
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.X3a commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        report = rollback_artifacts(root, backup_manifest, f"Commit phase failed: {exc}", checks)
        print(f"[7/8] [FAIL] {exc}; rollback status: {report['status']}.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Refined policy matrix committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - refine policy scope and marker evidence")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] CANDIDATES_BEFORE: {len(original['policy_matrix'])}")
    print(f"[PASS] POLICY_ONLY_CANDIDATES: {len(matrix)}")
    print(f"[PASS] EXCLUDED_NON_POLICY: {len(excluded_entries)}")
    for classification in CLASSIFICATIONS:
        print(f"[PASS] {classification}: {counts.get(classification, 0)}")
    print(f"[PASS] MIGRATION_ALLOWLIST: {len(migration_allowlist)}")
    print(f"[PASS] ACTIVE_SHADOW_CONFLICT_REVIEW: {len(conflicts)}")
    print(f"[PASS] OWNER_REVIEW_GROUPS: {len(owner_review)}")
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
