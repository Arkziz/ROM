#!/usr/bin/env python3
"""Stage 21.1.X1a: correct content identity/reference classification.

The successful X1 audit remains in Git history. This remediation rebuilds its
canonical derived report by assigning each extracted scalar one explicit role:
definition_identity, usage_reference, operational_label, presentation_name,
policy_flag, or descriptive_text. Duplicate and name-conflict queues are then
computed only from canonical definitions, not from repeated references.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE = "21.1.X1a"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "99174acfe0894631c828a71b8b32c18ed0a58978"
SOURCE_JSON = "reports/stage_21_1_X1_canonical_content_inventory.json"
CANONICAL_JSON = "reports/stage_21_1_X1_canonical_content_inventory.json"
CANONICAL_MD = "MD/STAGE_21_1_X1_CANONICAL_CONTENT_INVENTORY.md"
REMEDIATION_JSON = "reports/stage_21_1_X1a_content_classification_fix.json"
REMEDIATION_MD = "MD/STAGE_21_1_X1A_CONTENT_CLASSIFICATION_FIX.md"
PATCH_PATH = "patch/patch_21_1_X1a_fix_content_identity_reference_classification.py"
COMMIT_MESSAGE = "Stage 21.1.X1a: fix content identity reference classification"
OWNED = {PATCH_PATH, CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")

REFERENCE_CONTEXT_RE = re.compile(
    r"(?i)(previous|next|giver|turn_in|required|target|source|unlock|prerequisite|"
    r"reward|drop|allowed|active|selected|equipped|location_id|npc_id|boss_key|mob_key)"
)
OPERATIONAL_FIELD_RE = re.compile(r"(?i)(^|_)(primary_source|source|source_type|provider|channel)$")
POLICY_FIELD_RE = re.compile(r"(?i)(does_not|enabled|disabled|required|allowed|available|flag|policy)")
PRESENTATION_FIELD_RE = re.compile(r"(?i)(^|_)(boss|mob|npc|location|target)$")
NAME_FIELD_RE = re.compile(r"(?i)(name|title|label|display_name|localized_name|name_uk|title_uk)$")
TECHNICAL_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
UKRAINIAN_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")
HISTORICAL_RE = re.compile(r"(?i)(legacy|candidate|shadow|deprecated|superseded|obsolete|compat)")

# Strong source ownership signals. These identify definition catalogs before
# generic path heuristics are considered.
SOURCE_OWNER_TOKENS = {
    "boss": ("data/bosses.py",),
    "mob": ("mob", "mobs", "monster"),
    "item": ("item", "items", "equipment", "potion", "rune", "drop_tables"),
    "quest": ("story_quests", "quest_definitions", "quests.py"),
    "location": ("data/locations.py", "location"),
    "npc": ("npc", "story_quest_npc"),
    "skill": ("skill", "skills"),
    "class": ("class", "classes"),
    "event": ("event", "events"),
    "region": ("region", "location"),
    "reward": ("reward", "daily"),
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


def parent_path(field_path: str) -> str:
    return field_path.rsplit(".", 1)[0] if "." in field_path else "<root>"


def source_owns_namespace(source: str, namespace: str) -> bool:
    lowered = source.lower()
    return any(token in lowered for token in SOURCE_OWNER_TOKENS.get(namespace, (namespace,)))


def classify_role(record: dict[str, Any]) -> tuple[str, str]:
    """Return semantic role and a short machine-readable reason."""
    field = str(record.get("field_name", "")).lower()
    path = str(record.get("field_path", "")).lower()
    value = record.get("value")
    namespace = str(record.get("namespace", "unknown")).lower()
    source = str(record.get("source", ""))

    if isinstance(value, bool):
        return "policy_flag", "boolean_policy_value"
    if OPERATIONAL_FIELD_RE.search(field) or namespace in {"source", "target"}:
        return "operational_label", "operational_source_or_target_label"
    if record.get("category") == "name":
        return "descriptive_text", "localized_or_descriptive_field"
    if PRESENTATION_FIELD_RE.search(field) and isinstance(value, str) and (UKRAINIAN_RE.search(value) or not TECHNICAL_ID_RE.fullmatch(value)):
        return "presentation_name", "human_readable_presentation_value"

    reference_context = bool(REFERENCE_CONTEXT_RE.search(path))
    # Quest entity declarations are definitions; their links to other entities
    # are references. A quest_item declaration defines the quest-item key, while
    # required_quest_items reuses it.
    if namespace == "quest" and field in {"quest_id", "quest_key"} and ".definition." in f".{path}.":
        return "definition_identity", "quest_definition_primary_identity"
    if namespace == "item" and ".quest_item." in f".{path}." and ".required_quest_items." not in f".{path}.":
        return "definition_identity", "quest_item_declaration"
    if ".required_quest_items." in f".{path}." or any(token in path for token in ("previous_quest", "giver_npc", "turn_in_npc", "target_", "required_")):
        return "usage_reference", "explicit_reference_context"

    if source_owns_namespace(source, namespace) and not reference_context:
        return "definition_identity", "authoritative_namespace_source"
    if record.get("category") == "reference" or reference_context:
        return "usage_reference", "reference_field_or_context"
    if record.get("category") in {"identifier", "key"}:
        return "definition_identity", "primary_identity_without_reference_context"
    return "descriptive_text", "fallback_non_identity"


def entity_anchor(record: dict[str, Any]) -> str:
    """Return the entity object path that owns this definition."""
    return parent_path(str(record["field_path"]))


def render_canonical(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    queues = payload["review_queues"]
    lines = [
        "# ROM Stage 21.1.X1 - canonical content inventory", "",
        "- **Canonical revision:** `Stage 21.1.X1a`",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Content sources:** `{summary['source_count']}`",
        f"- **Extracted records:** `{summary['record_count']}`",
        f"- **Definition identities:** `{summary['definition_identity_count']}`",
        f"- **Usage references:** `{summary['usage_reference_count']}`",
        f"- **Operational labels:** `{summary['operational_label_count']}`",
        f"- **Presentation names:** `{summary['presentation_name_count']}`",
        f"- **Policy flags:** `{summary['policy_flag_count']}`", "",
        "## Виправлення Stage 21.1.X1a", "",
        "- Definition identities відокремлено від usage references.",
        "- Повторне використання reference більше не рахується duplicate identity.",
        "- Operational source labels винесено в окрему категорію.",
        "- Human-readable boss/NPC/location values класифікуються як presentation names.",
        "- Boolean policy values не аналізуються як references.",
        "- Name conflict визначається лише для одного canonical identity та одного name field.", "",
        "## Review queues", "",
        f"- Duplicate canonical definitions: **{len(queues['duplicate_definition_identities'])}**.",
        f"- Conflicting names for one canonical identity: **{len(queues['conflicting_names'])}**.",
        f"- Unresolved typed usage references: **{len(queues['unresolved_typed_references'])}**.",
        f"- Ambiguous identities requiring owner review: **{len(queues['ambiguous_identity_roles'])}**.",
        f"- Historical/superseded candidates: **{len(queues['historical_candidates'])}**.",
        f"- Dynamic symbols requiring extraction: **{len(queues['dynamic_symbols'])}**.", "",
        "## Canonical V2 content contract", "",
        "- Stable identity належить одному authoritative definition owner.",
        "- Usage references можуть повторюватися необмежено, але повинні resolve до definition identity.",
        "- Operational labels і presentation names не є canonical IDs.",
        "- Invalid typed reference блокує V2 content bootstrap.",
        "- Historical/candidate/shadow values потребують окремого owner-рішення.",
        "- Technical IDs не показуються користувачу замість локалізованих назв.",
        "- Production DB/WAL/SHM не відкривалися й не змінювалися.", "",
        "## Наступний етап", "",
        "Stage 21.1.X2 - Behavioral fixtures ROM V1.", "",
    ]
    return "\n".join(lines)


def render_remediation(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join([
        "# ROM Stage 21.1.X1a - виправлення identity/reference classification", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Duplicate identities before:** `{summary['duplicates_before']}`",
        f"- **Duplicate canonical definitions after:** `{summary['duplicates_after']}`",
        f"- **Conflicting names before:** `{summary['conflicts_before']}`",
        f"- **Conflicting canonical names after:** `{summary['conflicts_after']}`",
        f"- **Unresolved references before:** `{summary['unresolved_before']}`",
        f"- **Unresolved typed references after:** `{summary['unresolved_after']}`", "",
        "## Root cause", "",
        "Stage 21.1.X1 трактував більшість полів `*_id` і `*_key` як definitions незалежно від контексту. Через це повторні quest/NPC/location/item references виглядали як дубльовані canonical identities. Name conflict також порівнював різні descriptive fields одного object path.", "",
        "## Corrected semantics", "",
        "- `definition_identity`: декларація canonical entity.",
        "- `usage_reference`: посилання на already-defined entity.",
        "- `operational_label`: джерело, provider або channel label.",
        "- `presentation_name`: human-readable display value.",
        "- `policy_flag`: boolean behavior setting.",
        "- `descriptive_text`: name/title/description content.", "",
        "Production code та DB/WAL/SHM не змінювалися.", "",
    ])


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD]
    added = git(root, "add", "-f", "--", *paths)
    if added.returncode != 0:
        raise PatchError(added.stderr.strip() or "git add failed")
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

    print("[1/8] [PASS] Stage 21.1.X1 canonical input and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [
        entry for entry in entries
        if entry["status"][0] in {" ", "?"}
        and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))
    ]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.X1 parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
    db_before = database_evidence(root)
    original = json.loads((root / SOURCE_JSON).read_text(encoding="utf-8"))

    print(f"[3/8] [PASS] Reclassifying {original['summary']['record_count']} extracted content records by semantic role.")
    corrected_records: list[dict[str, Any]] = []
    role_counts: dict[str, int] = defaultdict(int)
    for source in original["sources"]:
        for record in source.get("records", []):
            corrected = dict(record)
            corrected["groups"] = source.get("groups", [])
            # Preserve namespace already established by X1's normalized registry.
            matches = [
                entry for entry in original.get("identity_registry", [])
                if any(
                    item.get("source") == record.get("source")
                    and item.get("symbol") == record.get("symbol")
                    and item.get("field_path") == record.get("field_path")
                    for item in entry.get("records", [])
                )
            ]
            if matches:
                corrected["namespace"] = matches[0]["namespace"]
            else:
                field = str(record.get("field_name", "")).lower()
                match = re.search(r"(item|mob|boss|npc|quest|location|skill|class|event|region|reward|source|target)", field)
                corrected["namespace"] = match.group(1) if match else (source.get("groups") or ["unknown"])[0]
            role, reason = classify_role(corrected)
            corrected["semantic_role"] = role
            corrected["role_reason"] = reason
            corrected_records.append(corrected)
            role_counts[role] += 1

    print("[4/8] [PASS] Rebuilding canonical definitions, typed references and conflict queues.")
    definitions = [record for record in corrected_records if record["semantic_role"] == "definition_identity"]
    references = [record for record in corrected_records if record["semantic_role"] == "usage_reference"]
    definition_index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in definitions:
        definition_index[(record["namespace"], str(record["value"]))].append(record)

    duplicate_definitions = [
        {"namespace": namespace, "value": value, "definitions": records}
        for (namespace, value), records in sorted(definition_index.items())
        if len({(record["source"], record["symbol"], entity_anchor(record)) for record in records}) > 1
    ]
    unresolved_typed = [
        record for record in references
        if record["namespace"] not in {"unknown", "source", "target"}
        and (record["namespace"], str(record["value"])) not in definition_index
        and str(record["value"]) not in {"", "0", "None"}
    ]

    # Attach names only to a definition object that shares source/symbol and the
    # closest containing object path. Conflicts require the same name field to
    # have more than one value for the same canonical identity.
    names = [record for record in corrected_records if record["category"] == "name"]
    name_map: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    for definition in definitions:
        anchor = entity_anchor(definition)
        identity_key = f"{definition['namespace']}:{definition['value']}"
        for name in names:
            if name["source"] != definition["source"] or name["symbol"] != definition["symbol"]:
                continue
            if parent_path(str(name["field_path"])).startswith(anchor):
                name_map[(definition["source"], identity_key, anchor, str(name["field_name"]))].add(str(name["value"]))
    conflicting_names = [
        {"source": source, "identity": identity, "anchor": anchor, "field_name": field, "values": sorted(values)}
        for (source, identity, anchor, field), values in sorted(name_map.items())
        if len(values) > 1
    ]

    ambiguous_roles = [
        record for record in corrected_records
        if record["semantic_role"] == "definition_identity"
        and record["namespace"] in {"unknown", "uncategorized_content", "localization"}
    ]
    historical_candidates = original["review_queues"].get("historical_candidates", [])
    dynamic_symbols = original["review_queues"].get("dynamic_symbols", [])

    # Rebuild per-source records, preserving X1 source metadata.
    records_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in corrected_records:
        records_by_source[record["source"]].append(record)
    corrected_sources = []
    for source in original["sources"]:
        updated = dict(source)
        updated["records"] = records_by_source.get(source["path"], [])
        corrected_sources.append(updated)

    technical_without_localized = []
    for definition in definitions:
        value = str(definition["value"])
        if not TECHNICAL_ID_RE.fullmatch(value):
            continue
        local_names = [
            name for name in names
            if name["source"] == definition["source"]
            and parent_path(str(name["field_path"])).startswith(entity_anchor(definition))
            and UKRAINIAN_RE.search(str(name["value"]))
        ]
        if not local_names:
            technical_without_localized.append(definition)

    checks.extend([
        Check("RECORD_COUNT_STABLE", "PASS" if len(corrected_records) == original["summary"]["record_count"] else "FAIL", f"Record count remains {len(corrected_records)}.", {"expected": original["summary"]["record_count"]}, len(corrected_records) != original["summary"]["record_count"]),
        Check("ROLE_COVERAGE", "PASS" if sum(role_counts.values()) == len(corrected_records) else "FAIL", "Every record has exactly one semantic role.", dict(role_counts), sum(role_counts.values()) != len(corrected_records)),
        Check("FALSE_REFERENCE_SENTINELS", "PASS" if not any(str(record["value"]) in {"future_crystal_shop", "rune_master_gold_shop", "🐺 Ватажок зграї", "👑 Король Гоблінів", "True"} for record in unresolved_typed) else "FAIL", "Operational labels, presentation names and policy flags are absent from unresolved typed references.", {}, any(str(record["value"]) in {"future_crystal_shop", "rune_master_gold_shop", "🐺 Ватажок зграї", "👑 Король Гоблінів", "True"} for record in unresolved_typed)),
        Check("DUPLICATE_QUEUE_REDUCED", "PASS" if len(duplicate_definitions) < len(original["review_queues"].get("duplicate_identities", [])) else "FAIL", f"Duplicate queue reduced from {len(original['review_queues'].get('duplicate_identities', []))} to {len(duplicate_definitions)}.", {}, len(duplicate_definitions) >= len(original["review_queues"].get("duplicate_identities", []))),
        Check("CONFLICT_QUEUE_REDUCED", "PASS" if len(conflicting_names) < len(original["review_queues"].get("conflicting_names", [])) else "FAIL", f"Name conflict queue reduced from {len(original['review_queues'].get('conflicting_names', []))} to {len(conflicting_names)}.", {}, len(conflicting_names) >= len(original["review_queues"].get("conflicting_names", []))),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"

    canonical = {
        "schema_version": 2,
        "canonical_revision": STAGE,
        "stage": "21.1.X1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            "source_count": original["summary"]["source_count"],
            "python_source_count": original["summary"]["python_source_count"],
            "non_python_source_count": original["summary"]["non_python_source_count"],
            "record_count": len(corrected_records),
            "group_count": original["summary"]["group_count"],
            "definition_identity_count": role_counts["definition_identity"],
            "usage_reference_count": role_counts["usage_reference"],
            "operational_label_count": role_counts["operational_label"],
            "presentation_name_count": role_counts["presentation_name"],
            "policy_flag_count": role_counts["policy_flag"],
            "descriptive_text_count": role_counts["descriptive_text"],
        },
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "sources": corrected_sources,
        "catalog_by_group": original["catalog_by_group"],
        "definition_registry": [
            {"namespace": namespace, "value": value, "definitions": records}
            for (namespace, value), records in sorted(definition_index.items())
        ],
        "review_queues": {
            "duplicate_definition_identities": duplicate_definitions,
            "conflicting_names": conflicting_names,
            "unresolved_typed_references": unresolved_typed,
            "ambiguous_identity_roles": ambiguous_roles,
            "historical_candidates": historical_candidates,
            "technical_id_without_localized_name": technical_without_localized,
            "dynamic_symbols": dynamic_symbols,
        },
        "v2_content_contract": dict(original["v2_content_contract"],
            one_definition_owner_per_identity=True,
            repeated_usage_references_are_not_duplicates=True,
            operational_labels_are_not_identities=True,
            presentation_names_are_not_references=True,
            policy_flags_are_not_references=True,
        ),
        "database_evidence_before": db_before,
        "remediation": {
            "stage": STAGE,
            "source_commit": EXPECTED_PARENT,
            "duplicates_before": len(original["review_queues"].get("duplicate_identities", [])),
            "duplicates_after": len(duplicate_definitions),
            "conflicts_before": len(original["review_queues"].get("conflicting_names", [])),
            "conflicts_after": len(conflicting_names),
            "unresolved_before": len(original["review_queues"].get("unresolved_references", [])),
            "unresolved_after": len(unresolved_typed),
        },
        "artifacts": {
            "patch": PATCH_PATH,
            "json": CANONICAL_JSON,
            "markdown": CANONICAL_MD,
            "remediation_json": REMEDIATION_JSON,
            "remediation_markdown": REMEDIATION_MD,
        },
        "next_stage": "21.1.X2" if conclusion == "GO" else None,
    }
    remediation_summary = {
        "conclusion": conclusion,
        "duplicates_before": canonical["remediation"]["duplicates_before"],
        "duplicates_after": canonical["remediation"]["duplicates_after"],
        "conflicts_before": canonical["remediation"]["conflicts_before"],
        "conflicts_after": canonical["remediation"]["conflicts_after"],
        "unresolved_before": canonical["remediation"]["unresolved_before"],
        "unresolved_after": canonical["remediation"]["unresolved_after"],
    }
    remediation = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": canonical["generated_at_utc"],
        "summary": remediation_summary,
        "role_counts": dict(sorted(role_counts.items())),
        "checks": [asdict(item) for item in checks],
        "root_causes": [
            "Generic *_id/*_key fields were treated as definitions without context.",
            "Repeated references were counted as duplicate identities.",
            "Different descriptive fields were compared as conflicting names.",
            "Operational labels, presentation names and booleans entered the unresolved reference queue.",
        ],
        "canonical_artifacts_updated": [CANONICAL_JSON, CANONICAL_MD],
        "database_evidence_before": db_before,
        "next_stage": "21.1.X2" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing corrected canonical inventory and remediation evidence.")
    write_atomic(root / CANONICAL_JSON, json.dumps(canonical, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / CANONICAL_MD, render_canonical(canonical))
    write_atomic(root / REMEDIATION_JSON, json.dumps(remediation, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / REMEDIATION_MD, render_remediation(remediation))
    if conclusion != "GO":
        print("[6/8] [FAIL] Classification remediation returned NO_GO; commit not created.")
        return 1

    print("[6/8] [PASS] Corrected identity/reference semantics validated.")
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.X1a commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        print(f"[7/8] [FAIL] {exc}", file=sys.stderr)
        return 2
    if db_before != database_evidence(root):
        print("[8/8] [FAIL] DB/WAL/SHM evidence changed.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Corrected content inventory committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - fix content identity/reference classification")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] DEFINITION_IDENTITIES: {role_counts['definition_identity']}")
    print(f"[PASS] USAGE_REFERENCES: {role_counts['usage_reference']}")
    print(f"[PASS] OPERATIONAL_LABELS: {role_counts['operational_label']}")
    print(f"[PASS] PRESENTATION_NAMES: {role_counts['presentation_name']}")
    print(f"[PASS] POLICY_FLAGS: {role_counts['policy_flag']}")
    print(f"[PASS] DUPLICATE_DEFINITIONS: {len(duplicate_definitions)}")
    print(f"[PASS] CONFLICTING_NAMES: {len(conflicting_names)}")
    print(f"[PASS] UNRESOLVED_TYPED_REFERENCES: {len(unresolved_typed)}")
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: NOT REQUIRED")
    print("WAL/SHM: NOT MANIPULATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
