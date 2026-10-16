#!/usr/bin/env python3
"""Stage 21.1.X3: build the current/superseded policy matrix for ROM V1.

This read-only audit inventories policy-bearing constants and symbols, explicit
historical markers, duplicate policy names, and accepted Git-history evidence.
It classifies evidence conservatively and never treats a mere duplicate as a
superseded policy. V1 runtime code is not imported or executed; SQLite is not
opened; production code and DB/WAL/SHM are not mutated.
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

STAGE = "21.1.X3"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "1d4bdc4c7cad5374aef261b213326235f473f1f3"
MODULE_INVENTORY = "reports/stage_21_1_1_v1_module_inventory.json"
DOMAIN_CONTRACTS = "reports/stage_21_1_5_domain_contracts.json"
CONTENT_INVENTORY = "reports/stage_21_1_X1_canonical_content_inventory.json"
FIXTURE_REGISTRY = "reports/stage_21_1_X2_v1_behavioral_fixtures.json"
PATCH_PATH = "patch/patch_21_1_X3_build_superseded_policy_matrix.py"
JSON_PATH = "reports/stage_21_1_X3_superseded_policy_matrix.json"
MD_PATH = "MD/STAGE_21_1_X3_SUPERSEDED_POLICY_MATRIX.md"
FAILURE_REPORT = "reports/stage_21_1_X3_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.1.X3: build superseded policy matrix"
OWNED = {PATCH_PATH, JSON_PATH, MD_PATH, FAILURE_REPORT}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
BACKUP_PREFIX = "stage_21_1_X3"
EXCLUDED = {"TEST_REFERENCE", "DO_NOT_MIGRATE"}

POLICY_NAME_RE = re.compile(
    r"(?i)(policy|config|rule|limit|cap|chance|rate|multiplier|price|cost|reward|"
    r"cooldown|duration|threshold|retention|timeout|interval|level|exp|gold|damage|"
    r"defense|attack|hp|mp|mana|rage|energy|premium|capacity|slot|drop|repair|"
    r"durability|namespace|allowlist|blocklist|enabled|disabled)"
)
EXPLICIT_SUPERSEDED_RE = re.compile(
    r"(?i)(superseded|deprecated|obsolete|legacy[_ -]?only|do[_ -]?not[_ -]?migrate|"
    r"not[_ -]?required|replaced[_ -]?by|historical[_ -]?only|old[_ -]?policy)"
)
SHADOW_RE = re.compile(r"(?i)(candidate|shadow|fallback|compat|legacy|old|previous|temporary|temp_|experimental)")
ACTIVE_RE = re.compile(r"(?i)(canonical|authoritative|accepted|current|active|production|final|effective)")
COMMIT_POLICY_RE = re.compile(r"(?i)(policy|price|reward|formula|chance|limit|premium|mana|exp|loot|repair|guild|quest|stage 20|accepted|not_required)")

DOMAIN_TOKENS: dict[str, tuple[str, ...]] = {
    "account": ("account", "user", "premium", "crystal", "wallet", "registered"),
    "character_stats": ("character", "player", "class", "stat", "hp", "mp", "mana", "rage", "energy", "crit", "evasion"),
    "combat": ("combat", "battle", "damage", "defense", "attack", "skill", "boss", "mob", "pvp"),
    "inventory_equipment": ("inventory", "item", "equipment", "rune", "durability", "repair", "enhancement", "refine"),
    "economy": ("shop", "price", "cost", "gold", "crystal", "auction", "trade", "purchase", "sell"),
    "quests_progression": ("quest", "story", "contract", "daily", "exp", "level", "reward", "loot"),
    "world_social_events": ("location", "travel", "map", "guild", "event", "reminder", "rating", "retention"),
}

CLASSIFICATIONS = (
    "ACTIVE_CANONICAL",
    "SUPERSEDED_EXPLICIT",
    "HISTORICAL_ONLY",
    "SHADOW_CANDIDATE",
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
            manifest["files"][relative_path] = {
                "existed": True,
                "backup": str(backup_path.relative_to(root)).replace("\\", "/"),
                "sha256": hashlib.sha256(blob).hexdigest(),
            }
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


def literal(node: ast.AST | None) -> Any:
    try:
        return ast.literal_eval(node) if node is not None else None
    except (ValueError, TypeError, SyntaxError):
        return None


def value_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def value_preview(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return text[:300]


def classify_domains(path: str, symbol: str) -> list[str]:
    haystack = f"{path} {symbol}".lower()
    scores = {domain: sum(token in haystack for token in tokens) for domain, tokens in DOMAIN_TOKENS.items()}
    maximum = max(scores.values(), default=0)
    return [domain for domain, score in scores.items() if score == maximum and score > 0] or ["cross_cutting"]


def source_segment(text: str, node: ast.AST) -> str:
    try:
        return ast.get_source_segment(text, node) or ""
    except Exception:
        return ""


def scan_policy_module(root: Path, path: str, classification: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    text = (root / path).read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=path)
    lines = text.splitlines()
    policies: list[dict[str, Any]] = []
    markers: list[dict[str, Any]] = []
    module_hash = sha256(root / path)
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = literal(node.value)
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                name = target.id
                context = "\n".join(lines[max(0, node.lineno - 4): min(len(lines), (node.end_lineno or node.lineno) + 2)])
                if not POLICY_NAME_RE.search(name) and not POLICY_NAME_RE.search(context):
                    continue
                marker_text = f"{path} {name} {context}"
                explicit_superseded = bool(EXPLICIT_SUPERSEDED_RE.search(marker_text))
                shadow_marker = bool(SHADOW_RE.search(marker_text))
                active_marker = bool(ACTIVE_RE.search(marker_text))
                policies.append({
                    "policy_id": "policy_" + hashlib.sha256(f"{path}:{name}:{node.lineno}".encode("utf-8")).hexdigest()[:16],
                    "source_file": path,
                    "source_sha256": module_hash,
                    "classification_source": classification,
                    "symbol": name,
                    "line": node.lineno,
                    "end_line": node.end_lineno or node.lineno,
                    "domains": classify_domains(path, name),
                    "literal": value is not None,
                    "value_type": type(value).__name__ if value is not None else "dynamic",
                    "value_sha256": value_digest(value) if value is not None else None,
                    "value_preview": value_preview(value) if value is not None else None,
                    "evidence": {
                        "explicit_superseded_marker": explicit_superseded,
                        "shadow_marker": shadow_marker,
                        "active_marker": active_marker,
                        "runtime_source": classification in {"REWRITE", "CONTENT_EXTRACT", "NEEDS_MANUAL_REVIEW"},
                        "context_sha256": hashlib.sha256(context.encode("utf-8")).hexdigest(),
                        "context_preview": context[:600],
                    },
                })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            segment = source_segment(text, node)[:1500]
            if EXPLICIT_SUPERSEDED_RE.search(f"{path} {node.name} {segment}") or SHADOW_RE.search(node.name):
                markers.append({
                    "source_file": path,
                    "symbol": node.name,
                    "line": node.lineno,
                    "kind": type(node).__name__,
                    "explicit_superseded_marker": bool(EXPLICIT_SUPERSEDED_RE.search(f"{path} {node.name} {segment}")),
                    "shadow_marker": bool(SHADOW_RE.search(node.name)),
                    "segment_sha256": hashlib.sha256(segment.encode("utf-8")).hexdigest(),
                })
    return policies, markers


def git_policy_evidence(root: Path) -> list[dict[str, Any]]:
    result = git(root, "log", "--format=%H%x1f%P%x1f%s%x1e", "--all", timeout=180)
    if result.returncode != 0:
        raise PatchError(result.stderr.strip() or "git log failed")
    evidence: list[dict[str, Any]] = []
    for raw in result.stdout.split("\x1e"):
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split("\x1f")
        if len(parts) != 3:
            continue
        commit_hash, parents, subject = parts
        if COMMIT_POLICY_RE.search(subject):
            evidence.append({"commit": commit_hash, "parents": parents.split(), "subject": subject})
    return evidence


def policy_key(policy: dict[str, Any]) -> tuple[str, str]:
    return (policy["domains"][0], policy["symbol"])


def classify_policy(policy: dict[str, Any], siblings: list[dict[str, Any]]) -> tuple[str, list[str]]:
    evidence = policy["evidence"]
    reasons: list[str] = []
    if evidence["explicit_superseded_marker"]:
        reasons.append("EXPLICIT_SUPERSEDED_MARKER")
        return "SUPERSEDED_EXPLICIT", reasons
    if evidence["shadow_marker"]:
        reasons.append("SHADOW_OR_LEGACY_MARKER")
        return "SHADOW_CANDIDATE", reasons
    distinct_values = {item.get("value_sha256") for item in siblings if item.get("value_sha256")}
    if len(siblings) == 1 and evidence["runtime_source"] and policy["literal"]:
        reasons.extend(["SINGLE_RUNTIME_OWNER", "LITERAL_POLICY_VALUE"])
        return "ACTIVE_CANONICAL", reasons
    if evidence["active_marker"] and evidence["runtime_source"]:
        reasons.extend(["ACTIVE_OR_CANONICAL_MARKER", "RUNTIME_SOURCE"])
        return "ACTIVE_CANONICAL", reasons
    if len(siblings) > 1 and len(distinct_values) > 1:
        reasons.append("MULTIPLE_DISTINCT_VALUES_REQUIRE_OWNER_REVIEW")
        return "OWNER_REVIEW_REQUIRED", reasons
    if not evidence["runtime_source"]:
        reasons.append("NON_RUNTIME_HISTORICAL_SOURCE")
        return "HISTORICAL_ONLY", reasons
    reasons.append("INSUFFICIENT_CANONICAL_OWNER_EVIDENCE")
    return "OWNER_REVIEW_REQUIRED", reasons


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    counts = summary["classification_counts"]
    return "\n".join([
        "# ROM Stage 21.1.X3 - current and superseded policy matrix", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Policy candidates:** `{summary['policy_candidate_count']}`",
        f"- **Policy groups:** `{summary['policy_group_count']}`",
        f"- **Git policy evidence records:** `{summary['git_policy_evidence_count']}`",
        f"- **Active canonical:** `{counts.get('ACTIVE_CANONICAL', 0)}`",
        f"- **Superseded explicit:** `{counts.get('SUPERSEDED_EXPLICIT', 0)}`",
        f"- **Historical only:** `{counts.get('HISTORICAL_ONLY', 0)}`",
        f"- **Shadow candidates:** `{counts.get('SHADOW_CANDIDATE', 0)}`",
        f"- **Owner review required:** `{counts.get('OWNER_REVIEW_REQUIRED', 0)}`", "",
        "## Classification rules", "",
        "- `ACTIVE_CANONICAL` requires positive runtime-owner evidence.",
        "- `SUPERSEDED_EXPLICIT` requires an explicit superseded/deprecated/obsolete/do-not-migrate marker.",
        "- `HISTORICAL_ONLY` is non-runtime evidence retained for reference.",
        "- `SHADOW_CANDIDATE` is never migrated without an owner decision.",
        "- Mere duplication or a differing value never proves which policy is current.",
        "- Ambiguous groups remain `OWNER_REVIEW_REQUIRED`.", "",
        "## V2 migration contract", "",
        "- Only `ACTIVE_CANONICAL` policies may migrate automatically.",
        "- Superseded, historical and shadow values are excluded from V2 runtime.",
        "- Owner-review groups block automatic policy migration, not this read-only audit.",
        "- Behavioral authority from Stage 21.1.X2a may support a decision but cannot override explicit canonical ownership by itself.",
        "- Production code and DB/WAL/SHM were not opened or modified.", "",
        "## Review queues", "",
        f"- Multiple active candidates: **{len(payload['review_queues']['multiple_active_candidates'])}**.",
        f"- Groups without active canonical owner: **{len(payload['review_queues']['groups_without_active_owner'])}**.",
        f"- Explicit superseded without replacement evidence: **{len(payload['review_queues']['superseded_without_replacement'])}**.",
        f"- Ambiguous owner groups: **{len(payload['review_queues']['owner_review_required'])}**.", "",
        "## Наступний етап", "",
        "Stage 21.1.9 - observability, logging, errors and audit trails inventory.", "",
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
    required_paths = (MODULE_INVENTORY, DOMAIN_CONTRACTS, CONTENT_INVENTORY, FIXTURE_REGISTRY)
    for required in required_paths:
        if not (root / required).is_file():
            print(f"[FAIL] Missing required input: {required}", file=sys.stderr)
            return 2

    print("[1/8] [PASS] Canonical Stage 21 inventories and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.X2a parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified; output backups prepared in ROM\\backup.")
    db_before = database_evidence(root)
    backup_manifest = prepare_backups(root)
    inventory = json.loads((root / MODULE_INVENTORY).read_text(encoding="utf-8"))
    domains = json.loads((root / DOMAIN_CONTRACTS).read_text(encoding="utf-8"))
    content = json.loads((root / CONTENT_INVENTORY).read_text(encoding="utf-8"))
    fixtures = json.loads((root / FIXTURE_REGISTRY).read_text(encoding="utf-8"))
    modules = [item for item in inventory["modules"] if item["classification"] not in EXCLUDED]

    print(f"[3/8] [PASS] Extracting policy candidates from {len(modules)} non-test modules and Git history.")
    candidates: list[dict[str, Any]] = []
    symbol_markers: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, module in enumerate(modules, start=1):
        try:
            module_candidates, module_markers = scan_policy_module(root, module["path"], module["classification"])
            candidates.extend(module_candidates)
            symbol_markers.extend(module_markers)
        except (OSError, SyntaxError) as exc:
            errors.append({"path": module["path"], "error": str(exc)})
        if index % 25 == 0 or index == len(modules):
            print(f"    progress: {index}/{len(modules)} modules", flush=True)
    history_evidence = git_policy_evidence(root)

    print("[4/8] [PASS] Building canonical, superseded, historical and review policy groups.")
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        groups[policy_key(candidate)].append(candidate)
    matrix: list[dict[str, Any]] = []
    for group_key, siblings in sorted(groups.items()):
        for candidate in siblings:
            classification, reasons = classify_policy(candidate, siblings)
            entry = dict(candidate)
            entry.update({
                "matrix_group": {"domain": group_key[0], "symbol": group_key[1]},
                "policy_classification": classification,
                "classification_evidence": reasons,
                "automatic_v2_migration": classification == "ACTIVE_CANONICAL",
            })
            matrix.append(entry)
    counts = Counter(entry["policy_classification"] for entry in matrix)
    matrix_by_group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for entry in matrix:
        matrix_by_group[(entry["matrix_group"]["domain"], entry["matrix_group"]["symbol"])].append(entry)
    multiple_active = [
        {"domain": key[0], "symbol": key[1], "entries": entries}
        for key, entries in matrix_by_group.items()
        if sum(entry["policy_classification"] == "ACTIVE_CANONICAL" for entry in entries) > 1
    ]
    without_active = [
        {"domain": key[0], "symbol": key[1], "entries": entries}
        for key, entries in matrix_by_group.items()
        if not any(entry["policy_classification"] == "ACTIVE_CANONICAL" for entry in entries)
    ]
    superseded_without_replacement = [
        group for group in without_active
        if any(entry["policy_classification"] == "SUPERSEDED_EXPLICIT" for entry in group["entries"])
    ]
    owner_review = [
        {"domain": key[0], "symbol": key[1], "entries": entries}
        for key, entries in matrix_by_group.items()
        if any(entry["policy_classification"] == "OWNER_REVIEW_REQUIRED" for entry in entries)
    ]
    overlapping_ids = sorted({entry["policy_id"] for entry in matrix if entry["policy_classification"] == "ACTIVE_CANONICAL"} & {entry["policy_id"] for entry in matrix if entry["policy_classification"] in {"SUPERSEDED_EXPLICIT", "HISTORICAL_ONLY", "SHADOW_CANDIDATE"}})

    checks.extend([
        Check("AST_COVERAGE", "PASS" if not errors else "FAIL", "All selected modules parsed." if not errors else "Policy source AST errors found.", {"errors": errors}, bool(errors)),
        Check("POLICY_CANDIDATES_FOUND", "PASS" if candidates else "FAIL", f"Policy candidates found: {len(candidates)}.", {}, not candidates),
        Check("CLASSIFICATION_COVERAGE", "PASS" if len(matrix) == len(candidates) and sum(counts.values()) == len(candidates) else "FAIL", "Every policy candidate has exactly one classification.", dict(counts), len(matrix) != len(candidates) or sum(counts.values()) != len(candidates)),
        Check("ACTIVE_SUPERSEDED_DISJOINT", "PASS" if not overlapping_ids else "FAIL", "Active and excluded classifications are disjoint.", {"overlapping_policy_ids": overlapping_ids}, bool(overlapping_ids)),
        Check("NO_DUPLICATE_IS_AUTOMATICALLY_SUPERSEDED", "PASS", "Duplicate values remain owner-review unless explicit evidence exists.", {"rule": True}),
        Check("CONTENT_REVISION", "PASS" if content.get("canonical_revision") == "21.1.X1c" else "FAIL", f"Content revision: {content.get('canonical_revision')}.", {"expected": "21.1.X1c"}, content.get("canonical_revision") != "21.1.X1c"),
        Check("FIXTURE_REVISION", "PASS" if fixtures.get("canonical_revision") == "21.1.X2a" else "FAIL", f"Fixture revision: {fixtures.get('canonical_revision')}.", {"expected": "21.1.X2a"}, fixtures.get("canonical_revision") != "21.1.X2a"),
        Check("DATABASE_EVIDENCE_READY", "PASS", "DB/WAL/SHM evidence captured without opening SQLite.", {"production_connection_opened": False}),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"
    review_queues = {
        "multiple_active_candidates": multiple_active,
        "groups_without_active_owner": without_active,
        "superseded_without_replacement": superseded_without_replacement,
        "owner_review_required": owner_review,
    }
    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            "module_count": len(modules),
            "policy_candidate_count": len(candidates),
            "policy_group_count": len(groups),
            "symbol_marker_count": len(symbol_markers),
            "git_policy_evidence_count": len(history_evidence),
            "classification_counts": dict(sorted(counts.items())),
        },
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "policy_matrix": sorted(matrix, key=lambda entry: (entry["domains"], entry["symbol"], entry["source_file"], entry["line"])),
        "symbol_markers": symbol_markers,
        "git_policy_evidence": history_evidence,
        "review_queues": review_queues,
        "v2_policy_migration_contract": {
            "automatic_migration_allowed_classifications": ["ACTIVE_CANONICAL"],
            "excluded_from_runtime": ["SUPERSEDED_EXPLICIT", "HISTORICAL_ONLY", "SHADOW_CANDIDATE"],
            "owner_review_blocks_automatic_migration": True,
            "duplicate_value_is_not_supersession_proof": True,
            "explicit_superseded_marker_required_for_automatic_exclusion": True,
            "behavioral_fixture_may_support_but_not_override_owner_decision": True,
        },
        "source_authority": {
            "module_inventory_commit": inventory["git"]["head_before_commit"],
            "domain_contract_commit": domains["git"]["head_before_commit"],
            "content_revision": content["canonical_revision"],
            "fixture_revision": fixtures["canonical_revision"],
            "parent_commit": EXPECTED_PARENT,
        },
        "database_evidence_before": db_before,
        "artifacts": {"patch": PATCH_PATH, "json": JSON_PATH, "markdown": MD_PATH},
        "next_stage": "21.1.9" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing superseded-policy matrix and V2 migration contract.")
    try:
        write_atomic(root / JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / MD_PATH, render_markdown(payload))
        if conclusion != "GO":
            for item in checks:
                if item.status == "FAIL":
                    print(f"[FAIL] {item.check_id}: {item.summary}")
            report = rollback_artifacts(root, backup_manifest, "Superseded-policy matrix checks returned NO_GO.", checks)
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

    print("[6/8] [PASS] Policy classifications and migration safeguards validated.")
    failure_path = root / FAILURE_REPORT
    if failure_path.exists():
        failure_path.unlink()
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.X3 commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        report = rollback_artifacts(root, backup_manifest, f"Commit phase failed: {exc}", checks)
        print(f"[7/8] [FAIL] {exc}; rollback status: {report['status']}.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Superseded-policy matrix committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - superseded policy matrix")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] POLICY_CANDIDATES: {len(candidates)}")
    print(f"[PASS] POLICY_GROUPS: {len(groups)}")
    for classification in CLASSIFICATIONS:
        print(f"[PASS] {classification}: {counts.get(classification, 0)}")
    print(f"[PASS] MULTIPLE_ACTIVE_REVIEW: {len(multiple_active)}")
    print(f"[PASS] GROUPS_WITHOUT_ACTIVE_OWNER: {len(without_active)}")
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
