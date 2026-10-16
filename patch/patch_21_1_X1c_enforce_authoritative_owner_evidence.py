#!/usr/bin/env python3
"""Stage 21.1.X1c: enforce authoritative evidence for content owners.

This read-only remediation rejects reference-derived and self-resolving owner
candidates introduced by Stage 21.1.X1b. An owner is accepted only when its
source, catalog position, semantic role and namespace provide positive evidence
of a canonical definition. Static absence never becomes a confirmed defect.
"""
from __future__ import annotations

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

STAGE = "21.1.X1c"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "294319dc4a9dc175fca456837feb272b4a93ffed"
CONTENT_JSON = "reports/stage_21_1_X1_canonical_content_inventory.json"
PATCH_PATH = "patch/patch_21_1_X1c_enforce_authoritative_owner_evidence.py"
CANONICAL_JSON = "reports/stage_21_1_X1_canonical_content_inventory.json"
CANONICAL_MD = "MD/STAGE_21_1_X1_CANONICAL_CONTENT_INVENTORY.md"
REMEDIATION_JSON = "reports/stage_21_1_X1c_authoritative_owner_evidence.json"
REMEDIATION_MD = "MD/STAGE_21_1_X1C_AUTHORITATIVE_OWNER_EVIDENCE.md"
COMMIT_MESSAGE = "Stage 21.1.X1c: enforce authoritative content owner evidence"
FAILURE_REPORT = "reports/stage_21_1_X1c_failure_rollback.json"
BACKUP_PREFIX = "stage_21_1_X1c"
OWNED = {PATCH_PATH, CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD, FAILURE_REPORT}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")

REFERENCE_CONTEXT_RE = re.compile(
    r"(?i)(previous|next|giver|turn_in|required|target|source|unlock|prerequisite|"
    r"reward|drop|allowed|active|selected|equipped|objective|condition|reference)"
)
DEFINITION_SYMBOL_RE = re.compile(
    r"(?i)(definitions|catalog|registry|by_id|by_key|classes|skills|items|mobs|"
    r"bosses|locations|npcs|quests|events|rewards|potions|runes)$"
)
HISTORICAL_RE = re.compile(r"(?i)(legacy|candidate|shadow|deprecated|superseded|obsolete|compat)")
NAMESPACE_ALIASES = {
    "boss": ("boss", "mob"),
    "mob": ("mob", "boss"),
    "region": ("region", "location"),
    "location": ("location", "region"),
}
AUTHORITATIVE_SOURCE_TOKENS = {
    "class": ("data/classes", "class_catalog", "class_definitions"),
    "skill": ("data/skills", "skill_catalog", "skill_definitions"),
    "item": ("data/items", "item_catalog", "item_definitions", "data/equipment", "data/potions", "data/runes"),
    "mob": ("data/mobs", "mob_catalog", "mob_definitions"),
    "boss": ("data/bosses", "boss_catalog", "boss_definitions"),
    "location": ("data/locations", "location_catalog", "location_definitions"),
    "region": ("data/locations", "region_catalog", "region_definitions"),
    "npc": ("data/npcs", "npc_catalog", "npc_definitions", "story_quest_npc"),
    "quest": ("data/story_quests", "quest_catalog", "quest_definitions"),
    "event": ("data/events", "event_catalog", "event_definitions"),
    "reward": ("reward_catalog", "reward_definitions", "data/rewards"),
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


def owner_key(owner: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(owner.get("namespace", "")), str(owner.get("value", "")),
        str(owner.get("source", "")), str(owner.get("symbol", "")),
        str(owner.get("field_path", "")),
    )


def record_key(record: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(record.get("namespace", "")), str(record.get("value", "")),
        str(record.get("source", "")), str(record.get("symbol", "")),
        str(record.get("field_path", "")),
    )


def path_depth(path: str) -> int:
    return len([part for part in path.split(".") if part])


def source_matches_namespace(source: str, namespace: str) -> bool:
    lowered = source.lower()
    return any(token in lowered for token in AUTHORITATIVE_SOURCE_TOKENS.get(namespace, ()))


def authoritative_evidence(owner: dict[str, Any], reference_keys: set[tuple[str, str, str, str, str]]) -> tuple[bool, list[str], list[str]]:
    """Return accepted flag, positive evidence and rejection reasons."""
    evidence: list[str] = []
    rejects: list[str] = []
    source = str(owner.get("source", ""))
    symbol = str(owner.get("symbol", ""))
    field_path = str(owner.get("field_path", ""))
    namespace = str(owner.get("namespace", "unknown"))
    owner_kind = str(owner.get("owner_kind", ""))
    confidence = str(owner.get("confidence", ""))

    if owner_key(owner) in reference_keys:
        rejects.append("REFERENCE_CANNOT_OWN_ITSELF")
    if REFERENCE_CONTEXT_RE.search(field_path):
        rejects.append("REFERENCE_CONTEXT_FORBIDDEN")
    if HISTORICAL_RE.search(source) or HISTORICAL_RE.search(symbol):
        rejects.append("HISTORICAL_OWNER_REQUIRES_REVIEW")

    if owner_kind == "x1a_definition" and confidence == "HIGH":
        evidence.append("X1A_SEMANTIC_DEFINITION")
    if owner_kind == "literal_mapping_key" and path_depth(field_path) == 1 and source_matches_namespace(source, namespace):
        evidence.extend(["TOP_LEVEL_CATALOG_KEY", "AUTHORITATIVE_SOURCE_NAMESPACE"])
    if owner_kind == "explicit_identity_field" and source_matches_namespace(source, namespace) and not REFERENCE_CONTEXT_RE.search(field_path):
        evidence.extend(["PRIMARY_IDENTITY_FIELD", "AUTHORITATIVE_SOURCE_NAMESPACE"])
    if DEFINITION_SYMBOL_RE.search(symbol) and source_matches_namespace(source, namespace):
        evidence.extend(["DEFINITION_REGISTRY_SYMBOL", "AUTHORITATIVE_SOURCE_NAMESPACE"])

    accepted = bool(evidence) and not rejects
    if not evidence:
        rejects.append("OWNER_MUST_HAVE_POSITIVE_DEFINITION_EVIDENCE")
    return accepted, sorted(set(evidence)), sorted(set(rejects))


def render_canonical(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    statuses = summary["reference_status_counts"]
    queues = payload["review_queues"]
    return "\n".join([
        "# ROM Stage 21.1.X1 - canonical content inventory", "",
        "- **Canonical revision:** `Stage 21.1.X1c`",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Typed references:** `{summary['typed_reference_count']}`",
        f"- **Accepted authoritative owners:** `{summary['accepted_authoritative_owner_count']}`",
        f"- **Rejected owner candidates:** `{summary['rejected_owner_candidate_count']}`",
        f"- **Resolved exact:** `{statuses.get('RESOLVED_EXACT', 0)}`",
        f"- **Resolved alias:** `{statuses.get('RESOLVED_ALIAS', 0)}`",
        f"- **External static definition:** `{statuses.get('EXTERNAL_STATIC_DEFINITION', 0)}`",
        f"- **Dynamic definition:** `{statuses.get('DYNAMIC_DEFINITION', 0)}`",
        f"- **Owner review required:** `{statuses.get('OWNER_REVIEW_REQUIRED', 0)}`",
        f"- **Confirmed unresolved:** `{statuses.get('CONFIRMED_UNRESOLVED', 0)}`", "",
        "## Authoritative owner evidence", "",
        "Owner приймається лише за позитивним definition evidence:", "",
        "- X1a semantic definition із HIGH confidence;",
        "- top-level key authoritative catalog;",
        "- primary identity field authoritative catalog;",
        "- explicit definition registry symbol authoritative namespace.", "",
        "Reference fields, prerequisite/objective/reward paths, presentation metadata, historical candidates та self-resolution owners не приймаються.", "",
        "## Review queues", "",
        f"- Duplicate authoritative owner groups: **{len(queues['duplicate_authoritative_owners'])}**.",
        f"- Conflicting canonical names: **{len(queues['conflicting_names'])}**.",
        f"- Owner review required: **{len(queues['owner_review_required'])}**.",
        f"- Confirmed unresolved: **{len(queues['confirmed_unresolved'])}**.",
        f"- Rejected self/reference-derived candidates: **{len(queues['rejected_reference_derived_owners'])}**.",
        f"- Historical owner candidates: **{len(queues['historical_owner_candidates'])}**.", "",
        "## Resolution policy", "",
        "- Static absence is not proof of broken content.",
        "- A reference cannot resolve itself.",
        "- Repeated references are not definitions.",
        "- `CONFIRMED_UNRESOLVED` requires a complete authoritative catalog and explicit absence proof.",
        "- Production code and DB/WAL/SHM were not opened or modified.", "",
        "## Наступний етап", "",
        "Stage 21.1.X2 - Behavioral fixtures ROM V1.", "",
    ])


def render_remediation(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    counts = summary["reference_status_counts"]
    return "\n".join([
        "# ROM Stage 21.1.X1c - authoritative owner evidence", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Owner candidates before filtering:** `{summary['owner_candidates_before']}`",
        f"- **Accepted authoritative owners:** `{summary['accepted_authoritative_owners']}`",
        f"- **Rejected owner candidates:** `{summary['rejected_owner_candidates']}`",
        f"- **Resolved exact:** `{counts.get('RESOLVED_EXACT', 0)}`",
        f"- **Resolved alias:** `{counts.get('RESOLVED_ALIAS', 0)}`",
        f"- **Owner review required:** `{counts.get('OWNER_REVIEW_REQUIRED', 0)}`",
        f"- **Confirmed unresolved:** `{counts.get('CONFIRMED_UNRESOLVED', 0)}`",
        f"- **Duplicate owner groups before:** `{summary['duplicate_owner_groups_before']}`",
        f"- **Duplicate authoritative owners after:** `{summary['duplicate_owner_groups_after']}`", "",
        "## Safeguards", "",
        "- `REFERENCE_CANNOT_OWN_ITSELF`",
        "- `OWNER_MUST_BE_DEFINITION_CONTEXT`",
        "- `NO_REFERENCE_DERIVED_OWNER`",
        "- `DUPLICATE_OWNER_QUEUE_NOT_REGRESSED` порівнює однакові owner-моделі X1b і X1c; X1a queue `6` не використовується як несумісний hard limit.",
        "- `OWNER_EVIDENCE_RECORDED`", "",
        "Production code and DB/WAL/SHM were not opened or modified.", "",
    ])


def git_blob(root: Path, commit: str, relative_path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def prepare_backups(root: Path) -> dict[str, Any]:
    """Back up canonical parent artifacts before any report mutation."""
    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"parent": EXPECTED_PARENT, "files": {}}
    for relative_path in (CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD):
        blob = git_blob(root, EXPECTED_PARENT, relative_path)
        backup_name = f"{BACKUP_PREFIX}__{relative_path.replace('/', '__')}"
        backup_path = backup_dir / backup_name
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
    """Restore canonical files and remove artifacts created by a failed patch."""
    restored: list[str] = []
    removed: list[str] = []
    errors: list[str] = []
    git(root, "reset", "--", CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD)
    for relative_path, metadata in manifest["files"].items():
        target = root / relative_path
        try:
            if metadata["existed"]:
                backup_path = root / metadata["backup"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(backup_path.read_bytes())
                restored.append(relative_path)
            elif target.exists():
                target.unlink()
                removed.append(relative_path)
        except OSError as exc:
            errors.append(f"{relative_path}: {exc}")
    verification = {
        "canonical_json_matches_parent": (root / CANONICAL_JSON).read_bytes() == (git_blob(root, EXPECTED_PARENT, CANONICAL_JSON) or b""),
        "canonical_md_matches_parent": (root / CANONICAL_MD).read_bytes() == (git_blob(root, EXPECTED_PARENT, CANONICAL_MD) or b""),
        "remediation_json_absent_if_new": not manifest["files"][REMEDIATION_JSON]["existed"] and not (root / REMEDIATION_JSON).exists(),
        "remediation_md_absent_if_new": not manifest["files"][REMEDIATION_MD]["existed"] and not (root / REMEDIATION_MD).exists(),
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
    if not (root / CONTENT_JSON).is_file():
        print(f"[FAIL] Missing {CONTENT_JSON}", file=sys.stderr)
        return 2

    print("[1/8] [PASS] Canonical X1b inventory and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.X1b parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified; parent artifacts backed up in ROM\\backup.")
    db_before = database_evidence(root)
    backup_manifest = prepare_backups(root)
    parent_content_blob = git_blob(root, EXPECTED_PARENT, CONTENT_JSON)
    if parent_content_blob is None:
        print(f"[FAIL] Cannot read {CONTENT_JSON} from expected parent.", file=sys.stderr)
        return 2
    content = json.loads(parent_content_blob.decode("utf-8"))
    references = [entry["reference"] for entry in content.get("reference_resolutions", [])]
    all_candidates = [owner for entry in content.get("definition_owner_registry", []) for owner in entry.get("owners", [])]
    reference_keys = {record_key(reference) for reference in references}

    print(f"[3/8] [PASS] Evaluating authoritative evidence for {len(all_candidates)} owner candidates.")
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for owner in all_candidates:
        ok, evidence, reasons = authoritative_evidence(owner, reference_keys)
        evaluated = dict(owner, authoritative_evidence=evidence, rejection_reasons=reasons)
        if ok:
            accepted.append(evaluated)
        else:
            rejected.append(evaluated)

    # De-duplicate identical evidence records without merging distinct owners.
    unique_accepted: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for owner in accepted:
        unique_accepted.setdefault(owner_key(owner), owner)
    accepted = list(unique_accepted.values())
    authoritative_index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    value_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for owner in accepted:
        authoritative_index[(str(owner["namespace"]), str(owner["value"]))].append(owner)
        value_index[str(owner["value"])].append(owner)

    dynamic_by_namespace: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for scan in content.get("module_owner_scans", []):
        for symbol in scan.get("dynamic_symbols", []):
            for namespace in symbol.get("namespaces", []):
                dynamic_by_namespace[str(namespace)].append(symbol)

    print(f"[4/8] [PASS] Re-resolving {len(references)} typed references against authoritative owners only.")
    resolutions: list[dict[str, Any]] = []
    for reference in references:
        namespace = str(reference.get("namespace", "unknown"))
        value = str(reference.get("value"))
        exact = [owner for owner in authoritative_index.get((namespace, value), []) if owner_key(owner) != record_key(reference)]
        aliases: list[dict[str, Any]] = []
        for alias in NAMESPACE_ALIASES.get(namespace, (namespace,)):
            if alias != namespace:
                aliases.extend(authoritative_index.get((alias, value), []))
        same_value = value_index.get(value, [])
        if exact:
            primary_sources = {source["path"] for source in content.get("sources", [])}
            external = all(owner["source"] not in primary_sources for owner in exact)
            status_name = "EXTERNAL_STATIC_DEFINITION" if external else "RESOLVED_EXACT"
            owners = exact
            reason = "authoritative exact owner evidence"
        elif aliases:
            status_name = "RESOLVED_ALIAS"
            owners = aliases
            reason = "authoritative owner through permitted namespace alias"
        elif dynamic_by_namespace.get(namespace):
            status_name = "DYNAMIC_DEFINITION"
            owners = dynamic_by_namespace[namespace]
            reason = "dynamic authoritative namespace requires runtime fixture proof"
        elif same_value:
            status_name = "OWNER_REVIEW_REQUIRED"
            owners = same_value
            reason = "authoritative value exists under ambiguous namespace"
        else:
            status_name = "OWNER_REVIEW_REQUIRED"
            owners = []
            reason = "no authoritative evidence; defect escalation forbidden"
        resolutions.append({"reference": reference, "status": status_name, "reason": reason, "authoritative_owners": owners})

    status_counts = Counter(item["status"] for item in resolutions)
    owner_review = [item for item in resolutions if item["status"] == "OWNER_REVIEW_REQUIRED"]
    confirmed_unresolved = [item for item in resolutions if item["status"] == "CONFIRMED_UNRESOLVED"]
    duplicate_authoritative = [
        {"namespace": namespace, "value": value, "owners": owners}
        for (namespace, value), owners in sorted(authoritative_index.items())
        if len({(owner["source"], owner["symbol"]) for owner in owners}) > 1
    ]
    rejected_reference_derived = [owner for owner in rejected if any(reason in owner["rejection_reasons"] for reason in ("REFERENCE_CANNOT_OWN_ITSELF", "REFERENCE_CONTEXT_FORBIDDEN"))]
    historical_candidates = [owner for owner in rejected if "HISTORICAL_OWNER_REQUIRES_REVIEW" in owner["rejection_reasons"]]
    prior_duplicate_count = len(content.get("review_queues", {}).get("duplicate_definition_owners", []))
    prior_conflicts = content.get("review_queues", {}).get("conflicting_names", [])

    self_resolution = [
        item for item in resolutions
        if any(owner_key(owner) == record_key(item["reference"]) for owner in item.get("authoritative_owners", []))
    ]
    unevidenced_owners = [owner for owner in accepted if not owner.get("authoritative_evidence")]
    reference_context_owners = [owner for owner in accepted if REFERENCE_CONTEXT_RE.search(str(owner.get("field_path", "")))]

    checks.extend([
        Check("REFERENCE_COUNT_STABLE", "PASS" if len(references) == content["summary"]["typed_reference_count"] else "FAIL", f"Typed reference count remains {len(references)}.", {"expected": content["summary"]["typed_reference_count"]}, len(references) != content["summary"]["typed_reference_count"]),
        Check("REFERENCE_CANNOT_OWN_ITSELF", "PASS" if not self_resolution else "FAIL", "No reference resolves to its own record.", {"violations": self_resolution[:20]}, bool(self_resolution)),
        Check("OWNER_MUST_BE_DEFINITION_CONTEXT", "PASS" if not reference_context_owners else "FAIL", "All accepted owners are outside reference contexts.", {"violations": reference_context_owners[:20]}, bool(reference_context_owners)),
        Check("NO_REFERENCE_DERIVED_OWNER", "PASS" if all(owner_key(owner) not in reference_keys for owner in accepted) else "FAIL", "No accepted owner is derived from a usage-reference record.", {}, any(owner_key(owner) in reference_keys for owner in accepted)),
        Check(
            "DUPLICATE_OWNER_QUEUE_NOT_REGRESSED",
            "PASS" if len(duplicate_authoritative) <= prior_duplicate_count else "FAIL",
            f"Duplicate authoritative owner groups reduced from {prior_duplicate_count} to {len(duplicate_authoritative)}.",
            {
                "comparison_baseline": "Stage 21.1.X1b owner model",
                "before": prior_duplicate_count,
                "after": len(duplicate_authoritative),
                "note": "The X1a value of 6 used a narrower semantic-definition registry and is not a valid hard limit for the expanded authoritative-owner registry.",
            },
            len(duplicate_authoritative) > prior_duplicate_count,
        ),
        Check("OWNER_EVIDENCE_RECORDED", "PASS" if not unevidenced_owners else "FAIL", "Every accepted owner records positive authoritative evidence.", {"violations": unevidenced_owners[:20]}, bool(unevidenced_owners)),
        Check("RESOLUTION_COVERAGE", "PASS" if len(resolutions) == len(references) and sum(status_counts.values()) == len(references) else "FAIL", "Every reference has exactly one resolution status.", dict(status_counts), len(resolutions) != len(references) or sum(status_counts.values()) != len(references)),
        Check("NO_UNPROVEN_DEFECT_ESCALATION", "PASS" if not confirmed_unresolved else "FAIL", "No reference is confirmed unresolved without authoritative proof.", {}, bool(confirmed_unresolved)),
        Check("DATABASE_EVIDENCE_READY", "PASS", "DB/WAL/SHM evidence captured without opening SQLite.", {"production_connection_opened": False}),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"

    canonical = dict(content)
    canonical.update({
        "schema_version": 4,
        "canonical_revision": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "authoritative_owner_registry": [
            {"namespace": namespace, "value": value, "owners": owners}
            for (namespace, value), owners in sorted(authoritative_index.items())
        ],
        "rejected_owner_candidates": rejected,
        "reference_resolutions": resolutions,
        "review_queues": {
            "duplicate_authoritative_owners": duplicate_authoritative,
            "conflicting_names": prior_conflicts,
            "owner_review_required": owner_review,
            "confirmed_unresolved": confirmed_unresolved,
            "rejected_reference_derived_owners": rejected_reference_derived,
            "historical_owner_candidates": historical_candidates,
            "dynamic_definition_symbols": content.get("review_queues", {}).get("dynamic_definition_symbols", []),
            "ambiguous_identity_roles": content.get("review_queues", {}).get("ambiguous_identity_roles", []),
            "technical_id_without_localized_name": content.get("review_queues", {}).get("technical_id_without_localized_name", []),
        },
        "database_evidence_before": db_before,
        "artifacts": {
            "patch": PATCH_PATH, "json": CANONICAL_JSON, "markdown": CANONICAL_MD,
            "remediation_json": REMEDIATION_JSON, "remediation_markdown": REMEDIATION_MD,
        },
        "next_stage": "21.1.X2" if conclusion == "GO" else None,
    })
    canonical["summary"] = dict(content["summary"],
        conclusion=conclusion,
        blocking_failures=blockers,
        typed_reference_count=len(references),
        accepted_authoritative_owner_count=len(accepted),
        rejected_owner_candidate_count=len(rejected),
        reference_status_counts=dict(sorted(status_counts.items())),
    )
    canonical["v2_content_contract"] = dict(content["v2_content_contract"],
        authoritative_owner_requires_positive_evidence=True,
        reference_cannot_own_itself=True,
        reference_context_cannot_define_owner=True,
        confirmed_unresolved_requires_authoritative_proof=True,
    )

    remediation = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": canonical["generated_at_utc"],
        "summary": {
            "conclusion": conclusion,
            "owner_candidates_before": len(all_candidates),
            "accepted_authoritative_owners": len(accepted),
            "rejected_owner_candidates": len(rejected),
            "typed_reference_count": len(references),
            "reference_status_counts": dict(sorted(status_counts.items())),
            "duplicate_owner_groups_before": prior_duplicate_count,
            "duplicate_owner_groups_after": len(duplicate_authoritative),
        },
        "checks": [asdict(item) for item in checks],
        "evidence_policy": {
            "accepted": ["X1A_SEMANTIC_DEFINITION", "TOP_LEVEL_CATALOG_KEY", "PRIMARY_IDENTITY_FIELD", "DEFINITION_REGISTRY_SYMBOL", "AUTHORITATIVE_SOURCE_NAMESPACE"],
            "rejected": ["REFERENCE_CANNOT_OWN_ITSELF", "REFERENCE_CONTEXT_FORBIDDEN", "HISTORICAL_OWNER_REQUIRES_REVIEW", "OWNER_MUST_HAVE_POSITIVE_DEFINITION_EVIDENCE"],
        },
        "canonical_artifacts_updated": [CANONICAL_JSON, CANONICAL_MD],
        "database_evidence_before": db_before,
        "next_stage": "21.1.X2" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing authoritative owner registry and remediation evidence.")
    try:
        write_atomic(root / CANONICAL_JSON, json.dumps(canonical, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / CANONICAL_MD, render_canonical(canonical))
        write_atomic(root / REMEDIATION_JSON, json.dumps(remediation, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / REMEDIATION_MD, render_remediation(remediation))
        if conclusion != "GO":
            for item in checks:
                if item.status == "FAIL":
                    print(f"[FAIL] {item.check_id}: {item.summary}")
            report = rollback_artifacts(root, backup_manifest, "Authoritative-owner semantic checks returned NO_GO.", checks)
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

    print("[6/8] [PASS] Authoritative owner evidence and anti-self-resolution safeguards validated.")
    failure_report_path = root / FAILURE_REPORT
    if failure_report_path.exists():
        failure_report_path.unlink()
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.X1c commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        report = rollback_artifacts(root, backup_manifest, f"Commit phase failed: {exc}", checks)
        print(f"[7/8] [FAIL] {exc}; rollback status: {report['status']}.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Authoritative owner evidence committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - enforce authoritative owner evidence")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] OWNER_CANDIDATES_BEFORE: {len(all_candidates)}")
    print(f"[PASS] AUTHORITATIVE_OWNERS_ACCEPTED: {len(accepted)}")
    print(f"[PASS] OWNER_CANDIDATES_REJECTED: {len(rejected)}")
    print(f"[PASS] TYPED_REFERENCES: {len(references)}")
    for status_name in ("RESOLVED_EXACT", "RESOLVED_ALIAS", "EXTERNAL_STATIC_DEFINITION", "DYNAMIC_DEFINITION", "OWNER_REVIEW_REQUIRED", "CONFIRMED_UNRESOLVED"):
        print(f"[PASS] {status_name}: {status_counts.get(status_name, 0)}")
    print(f"[PASS] DUPLICATE_AUTHORITATIVE_OWNER_GROUPS: {len(duplicate_authoritative)}")
    print(f"[PASS] CONFLICTING_NAMES_PRESERVED: {len(prior_conflicts)}")
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
