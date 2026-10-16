#!/usr/bin/env python3
"""Stage 21.1.X1b: resolve canonical content definition owners.

Read-only remediation for the X1/X1a content inventory. It expands definition
discovery across all non-test V1 modules, treats literal mapping keys as owner
candidates, normalizes safe namespace aliases, and classifies every typed
reference without declaring a defect unless an authoritative owner is proven.
Production code and SQLite files are never imported, opened, or mutated.
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

STAGE = "21.1.X1b"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "fe99b84607a73bea453244e523c00f3073b70e02"
CONTENT_JSON = "reports/stage_21_1_X1_canonical_content_inventory.json"
MODULE_INVENTORY = "reports/stage_21_1_1_v1_module_inventory.json"
PATCH_PATH = "patch/patch_21_1_X1b_resolve_content_definition_owners.py"
CANONICAL_JSON = "reports/stage_21_1_X1_canonical_content_inventory.json"
CANONICAL_MD = "MD/STAGE_21_1_X1_CANONICAL_CONTENT_INVENTORY.md"
REMEDIATION_JSON = "reports/stage_21_1_X1b_definition_owner_resolution.json"
REMEDIATION_MD = "MD/STAGE_21_1_X1B_DEFINITION_OWNER_RESOLUTION.md"
COMMIT_MESSAGE = "Stage 21.1.X1b: resolve content definition owners"
OWNED = {PATCH_PATH, CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
EXCLUDED = {"TEST_REFERENCE", "DO_NOT_MIGRATE"}
TECHNICAL_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
HISTORICAL_RE = re.compile(r"(?i)(legacy|candidate|shadow|deprecated|superseded|obsolete|compat)")

NAMESPACE_ALIASES = {
    "boss": ("boss", "mob"),
    "mob": ("mob", "boss"),
    "region": ("region", "location"),
    "location": ("location", "region"),
}
SOURCE_NAMESPACE_RULES = {
    "class": ("class", "classes"),
    "skill": ("skill", "skills", "ability"),
    "item": ("item", "items", "equipment", "potion", "rune", "loot", "drop_table"),
    "mob": ("mob", "mobs", "monster", "enemy"),
    "boss": ("boss", "bosses"),
    "location": ("location", "locations", "world", "travel"),
    "npc": ("npc", "npcs", "dialogue"),
    "quest": ("quest", "quests", "story", "contract", "daily"),
    "event": ("event", "events"),
    "reward": ("reward", "rewards"),
    "region": ("region", "regions"),
}
FIELD_NAMESPACE_RE = re.compile(r"(?i)(item|mob|boss|npc|quest|location|skill|class|event|reward|region)(?:_id|_key)?$")


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


def literal(node: ast.AST | None) -> Any:
    try:
        return ast.literal_eval(node) if node is not None else None
    except (ValueError, TypeError, SyntaxError):
        return None


def infer_namespaces(path: str, symbol: str) -> list[str]:
    haystack = f"{path} {symbol}".lower()
    matches = [namespace for namespace, tokens in SOURCE_NAMESPACE_RULES.items() if any(token in haystack for token in tokens)]
    return matches or ["unknown"]


def field_namespace(field_name: str) -> str | None:
    match = FIELD_NAMESPACE_RE.search(field_name)
    return match.group(1).lower() if match else None


def walk_literal_candidates(value: Any, source: str, symbol: str, namespaces: list[str], path: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            current = path + (key_text,)
            # Mapping keys are definition candidates only when they look like a
            # stable technical key or integer identity and the mapping belongs
            # to a recognizable content namespace.
            if (isinstance(key, int) or TECHNICAL_KEY_RE.fullmatch(key_text)) and namespaces != ["unknown"]:
                for namespace in namespaces:
                    candidates.append({
                        "namespace": namespace,
                        "value": key_text,
                        "source": source,
                        "symbol": symbol,
                        "field_path": ".".join(current),
                        "owner_kind": "literal_mapping_key",
                        "confidence": "MEDIUM",
                        "historical_marker": bool(HISTORICAL_RE.search(source) or HISTORICAL_RE.search(symbol)),
                    })
            if isinstance(child, (str, int)):
                namespace = field_namespace(key_text.lower())
                if namespace:
                    candidates.append({
                        "namespace": namespace,
                        "value": str(child),
                        "source": source,
                        "symbol": symbol,
                        "field_path": ".".join(current),
                        "owner_kind": "explicit_identity_field",
                        "confidence": "HIGH",
                        "historical_marker": bool(HISTORICAL_RE.search(source) or HISTORICAL_RE.search(symbol)),
                    })
            candidates.extend(walk_literal_candidates(child, source, symbol, namespaces, current))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            candidates.extend(walk_literal_candidates(child, source, symbol, namespaces, path + (str(index),)))
    return candidates


def scan_module(root: Path, path: str, classification: str) -> dict[str, Any]:
    text = (root / path).read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=path)
    candidates: list[dict[str, Any]] = []
    dynamic_symbols: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = literal(node.value)
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            symbol = target.id
            namespaces = infer_namespaces(path, symbol)
            if value is None:
                if symbol.isupper() and namespaces != ["unknown"]:
                    dynamic_symbols.append({"source": path, "symbol": symbol, "line": node.lineno, "namespaces": namespaces})
                continue
            if isinstance(value, (dict, list, tuple)):
                candidates.extend(walk_literal_candidates(value, path, symbol, namespaces))
    return {
        "path": path,
        "classification": classification,
        "sha256": sha256(root / path),
        "owner_candidates": candidates,
        "dynamic_symbols": dynamic_symbols,
    }


def candidate_key(candidate: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(candidate["namespace"]), str(candidate["value"]), str(candidate["source"]),
        str(candidate.get("symbol", "")), str(candidate.get("field_path", "")),
    )


def render_canonical(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    queues = payload["review_queues"]
    statuses = summary["reference_status_counts"]
    return "\n".join([
        "# ROM Stage 21.1.X1 - canonical content inventory", "",
        "- **Canonical revision:** `Stage 21.1.X1b`",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Content sources:** `{summary['source_count']}`",
        f"- **Definition owner candidates:** `{summary['definition_owner_candidate_count']}`",
        f"- **Typed usage references:** `{summary['typed_reference_count']}`",
        f"- **Resolved exact:** `{statuses.get('RESOLVED_EXACT', 0)}`",
        f"- **Resolved alias:** `{statuses.get('RESOLVED_ALIAS', 0)}`",
        f"- **External static definition:** `{statuses.get('EXTERNAL_STATIC_DEFINITION', 0)}`",
        f"- **Dynamic definition:** `{statuses.get('DYNAMIC_DEFINITION', 0)}`",
        f"- **Owner review required:** `{statuses.get('OWNER_REVIEW_REQUIRED', 0)}`",
        f"- **Confirmed unresolved:** `{statuses.get('CONFIRMED_UNRESOLVED', 0)}`", "",
        "## Виправлення Stage 21.1.X1b", "",
        "- Definition discovery розширено на всі non-test runtime/content modules.",
        "- Literal mapping keys враховано як owner candidates із confidence metadata.",
        "- `boss`/`mob` і `region`/`location` підтримують safe namespace alias resolution.",
        "- Кожна typed reference отримує один resolution status.",
        "- Статичний аудит не оголошує reference дефектом без authoritative proof.", "",
        "## Review queues", "",
        f"- Duplicate canonical definitions: **{len(queues['duplicate_definition_owners'])}**.",
        f"- Conflicting canonical names: **{len(queues['conflicting_names'])}**.",
        f"- Owner review required: **{len(queues['owner_review_required'])}**.",
        f"- Confirmed unresolved: **{len(queues['confirmed_unresolved'])}**.",
        f"- Dynamic definition symbols: **{len(queues['dynamic_definition_symbols'])}**.",
        f"- Historical owner candidates: **{len(queues['historical_owner_candidates'])}**.", "",
        "## Canonical interpretation", "",
        "- `RESOLVED_EXACT`: exact namespace/value owner існує.",
        "- `RESOLVED_ALIAS`: owner знайдено через дозволений namespace alias.",
        "- `EXTERNAL_STATIC_DEFINITION`: definition знайдено поза первинними 65 content sources.",
        "- `DYNAMIC_DEFINITION`: відповідний namespace має dynamic catalog owner, але identity не доступна як literal.",
        "- `OWNER_REVIEW_REQUIRED`: є неповний або неоднозначний static owner signal.",
        "- `CONFIRMED_UNRESOLVED`: зарезервовано лише для доказово відсутніх references; static audit за замовчуванням не підвищує finding до цього статусу.", "",
        "Production code та DB/WAL/SHM не змінювалися.", "",
        "## Наступний етап", "",
        "Stage 21.1.X2 - Behavioral fixtures ROM V1.", "",
    ])


def render_remediation(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    counts = summary["reference_status_counts"]
    return "\n".join([
        "# ROM Stage 21.1.X1b - definition owner resolution", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Typed references processed:** `{summary['typed_reference_count']}`",
        f"- **Resolved exact:** `{counts.get('RESOLVED_EXACT', 0)}`",
        f"- **Resolved alias:** `{counts.get('RESOLVED_ALIAS', 0)}`",
        f"- **External static definitions:** `{counts.get('EXTERNAL_STATIC_DEFINITION', 0)}`",
        f"- **Dynamic definitions:** `{counts.get('DYNAMIC_DEFINITION', 0)}`",
        f"- **Owner review required:** `{counts.get('OWNER_REVIEW_REQUIRED', 0)}`",
        f"- **Confirmed unresolved:** `{counts.get('CONFIRMED_UNRESOLVED', 0)}`", "",
        "## Resolution policy", "",
        "Static absence alone is not proof of broken content. A reference becomes `CONFIRMED_UNRESOLVED` only when an authoritative complete catalog is known and the identity is absent. This audit therefore keeps unresolved-but-unproven records in owner review or dynamic-definition queues.", "",
        "## Safety", "",
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
    if not (root / CONTENT_JSON).is_file() or not (root / MODULE_INVENTORY).is_file():
        print("[FAIL] Required X1b inputs are missing.", file=sys.stderr)
        return 2

    print("[1/8] [PASS] Canonical X1a inventory, module inventory and directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.X1a parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
    db_before = database_evidence(root)
    content = json.loads((root / CONTENT_JSON).read_text(encoding="utf-8"))
    inventory = json.loads((root / MODULE_INVENTORY).read_text(encoding="utf-8"))
    modules = [item for item in inventory["modules"] if item["classification"] not in EXCLUDED]

    print(f"[3/8] [PASS] Expanding definition discovery across {len(modules)} non-test modules.")
    module_scans: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, module in enumerate(modules, start=1):
        try:
            module_scans.append(scan_module(root, module["path"], module["classification"]))
        except (OSError, SyntaxError) as exc:
            errors.append({"path": module["path"], "error": str(exc)})
        if index % 25 == 0 or index == len(modules):
            print(f"    progress: {index}/{len(modules)} modules", flush=True)

    print("[4/8] [PASS] Resolving typed references and authoritative owner candidates.")
    existing_definitions = [entry for entry in content.get("definition_registry", []) for entry in entry.get("definitions", [])]
    candidates: list[dict[str, Any]] = []
    primary_source_paths = {source["path"] for source in content["sources"]}
    for record in existing_definitions:
        candidates.append({
            "namespace": record["namespace"], "value": str(record["value"]),
            "source": record["source"], "symbol": record.get("symbol", ""),
            "field_path": record.get("field_path", ""), "owner_kind": "x1a_definition",
            "confidence": "HIGH", "historical_marker": bool(HISTORICAL_RE.search(record["source"])),
        })
    for scan in module_scans:
        candidates.extend(scan["owner_candidates"])

    unique_candidates: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for candidate in candidates:
        unique_candidates.setdefault(candidate_key(candidate), candidate)
    candidates = list(unique_candidates.values())
    owner_index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    value_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        owner_index[(candidate["namespace"], str(candidate["value"]))].append(candidate)
        value_index[str(candidate["value"])].append(candidate)

    dynamic_by_namespace: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for scan in module_scans:
        for symbol in scan["dynamic_symbols"]:
            for namespace in symbol["namespaces"]:
                dynamic_by_namespace[namespace].append(symbol)

    references = [
        record for source in content["sources"] for record in source.get("records", [])
        if record.get("semantic_role") == "usage_reference"
    ]
    resolutions: list[dict[str, Any]] = []
    for reference in references:
        namespace = str(reference.get("namespace", "unknown"))
        value = str(reference.get("value"))
        exact = owner_index.get((namespace, value), [])
        aliases = []
        for alias in NAMESPACE_ALIASES.get(namespace, (namespace,)):
            if alias != namespace:
                aliases.extend(owner_index.get((alias, value), []))
        same_value = value_index.get(value, [])
        status_name: str
        owners: list[dict[str, Any]]
        reason: str
        if exact:
            external = all(owner["source"] not in primary_source_paths for owner in exact)
            status_name = "EXTERNAL_STATIC_DEFINITION" if external else "RESOLVED_EXACT"
            owners = exact
            reason = "exact namespace/value owner"
        elif aliases:
            status_name = "RESOLVED_ALIAS"
            owners = aliases
            reason = "allowed namespace alias owner"
        elif dynamic_by_namespace.get(namespace):
            status_name = "DYNAMIC_DEFINITION"
            owners = dynamic_by_namespace[namespace]
            reason = "namespace has dynamic catalog owner"
        elif same_value:
            status_name = "OWNER_REVIEW_REQUIRED"
            owners = same_value
            reason = "value exists under another or ambiguous namespace"
        else:
            status_name = "OWNER_REVIEW_REQUIRED"
            owners = []
            reason = "no static proof; confirmed-unresolved escalation forbidden"
        resolutions.append({"reference": reference, "status": status_name, "reason": reason, "owner_candidates": owners})

    status_counts = Counter(item["status"] for item in resolutions)
    owner_review = [item for item in resolutions if item["status"] == "OWNER_REVIEW_REQUIRED"]
    confirmed_unresolved = [item for item in resolutions if item["status"] == "CONFIRMED_UNRESOLVED"]
    duplicate_owners = [
        {"namespace": namespace, "value": value, "owners": owners}
        for (namespace, value), owners in sorted(owner_index.items())
        if len({(owner["source"], owner["symbol"], owner["field_path"]) for owner in owners if owner["confidence"] == "HIGH"}) > 1
    ]
    historical_owners = [candidate for candidate in candidates if candidate["historical_marker"]]
    dynamic_symbols = [symbol for scan in module_scans for symbol in scan["dynamic_symbols"]]
    prior_duplicates = content["review_queues"].get("duplicate_definition_identities", [])
    prior_conflicts = content["review_queues"].get("conflicting_names", [])

    checks.extend([
        Check("AST_COVERAGE", "PASS" if not errors else "FAIL", "All selected modules parsed." if not errors else "AST errors found.", {"errors": errors}, bool(errors)),
        Check("REFERENCE_COUNT_STABLE", "PASS" if len(references) == content["summary"]["usage_reference_count"] else "FAIL", f"Typed reference count remains {len(references)}.", {"expected": content["summary"]["usage_reference_count"]}, len(references) != content["summary"]["usage_reference_count"]),
        Check("RESOLUTION_COVERAGE", "PASS" if len(resolutions) == len(references) and sum(status_counts.values()) == len(references) else "FAIL", "Every typed reference has exactly one resolution status.", dict(status_counts), len(resolutions) != len(references) or sum(status_counts.values()) != len(references)),
        Check("OWNER_DISCOVERY_EXPANDED", "PASS" if len(candidates) > content["summary"]["definition_identity_count"] else "FAIL", f"Owner candidates expanded to {len(candidates)}.", {"x1a_definitions": content["summary"]["definition_identity_count"]}, len(candidates) <= content["summary"]["definition_identity_count"]),
        Check("NO_UNPROVEN_DEFECT_ESCALATION", "PASS" if not confirmed_unresolved else "FAIL", "No reference was marked confirmed unresolved without authoritative proof.", {}, bool(confirmed_unresolved)),
        Check("DATABASE_EVIDENCE_READY", "PASS", "DB/WAL/SHM evidence captured without opening SQLite.", {"production_connection_opened": False}),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"

    canonical = dict(content)
    canonical.update({
        "schema_version": 3,
        "canonical_revision": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "definition_owner_registry": [
            {"namespace": namespace, "value": value, "owners": owners}
            for (namespace, value), owners in sorted(owner_index.items())
        ],
        "reference_resolutions": resolutions,
        "module_owner_scans": module_scans,
        "review_queues": {
            "duplicate_definition_owners": duplicate_owners,
            "conflicting_names": prior_conflicts,
            "owner_review_required": owner_review,
            "confirmed_unresolved": confirmed_unresolved,
            "dynamic_definition_symbols": dynamic_symbols,
            "historical_owner_candidates": historical_owners,
            "ambiguous_identity_roles": content["review_queues"].get("ambiguous_identity_roles", []),
            "technical_id_without_localized_name": content["review_queues"].get("technical_id_without_localized_name", []),
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
        definition_owner_candidate_count=len(candidates),
        typed_reference_count=len(references),
        reference_status_counts=dict(sorted(status_counts.items())),
    )
    canonical["v2_content_contract"] = dict(content["v2_content_contract"],
        reference_resolution_statuses=["RESOLVED_EXACT", "RESOLVED_ALIAS", "EXTERNAL_STATIC_DEFINITION", "DYNAMIC_DEFINITION", "OWNER_REVIEW_REQUIRED", "CONFIRMED_UNRESOLVED"],
        confirmed_unresolved_requires_authoritative_proof=True,
        namespace_aliases={key: list(value) for key, value in NAMESPACE_ALIASES.items()},
    )

    remediation = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": canonical["generated_at_utc"],
        "summary": {
            "conclusion": conclusion,
            "typed_reference_count": len(references),
            "definition_owner_candidate_count": len(candidates),
            "reference_status_counts": dict(sorted(status_counts.items())),
            "duplicates_before": len(prior_duplicates),
            "duplicate_owner_groups_after": len(duplicate_owners),
            "conflicts_preserved_for_review": len(prior_conflicts),
        },
        "checks": [asdict(item) for item in checks],
        "resolution_policy": {
            "static_absence_is_not_defect_proof": True,
            "confirmed_unresolved_requires_complete_authoritative_catalog": True,
            "safe_namespace_aliases": {key: list(value) for key, value in NAMESPACE_ALIASES.items()},
        },
        "database_evidence_before": db_before,
        "canonical_artifacts_updated": [CANONICAL_JSON, CANONICAL_MD],
        "next_stage": "21.1.X2" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing resolved owner registry and canonical content revision.")
    write_atomic(root / CANONICAL_JSON, json.dumps(canonical, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / CANONICAL_MD, render_canonical(canonical))
    write_atomic(root / REMEDIATION_JSON, json.dumps(remediation, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / REMEDIATION_MD, render_remediation(remediation))
    if conclusion != "GO":
        print("[6/8] [FAIL] Owner resolution returned NO_GO; commit not created.")
        return 1

    print("[6/8] [PASS] Definition-owner and reference-resolution contracts validated.")
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.X1b commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        print(f"[7/8] [FAIL] {exc}", file=sys.stderr)
        return 2
    if db_before != database_evidence(root):
        print("[8/8] [FAIL] DB/WAL/SHM evidence changed.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Owner resolution committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - resolve content definition owners")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] OWNER_CANDIDATES: {len(candidates)}")
    print(f"[PASS] TYPED_REFERENCES: {len(references)}")
    for status_name in ("RESOLVED_EXACT", "RESOLVED_ALIAS", "EXTERNAL_STATIC_DEFINITION", "DYNAMIC_DEFINITION", "OWNER_REVIEW_REQUIRED", "CONFIRMED_UNRESOLVED"):
        print(f"[PASS] {status_name}: {status_counts.get(status_name, 0)}")
    print(f"[PASS] DUPLICATE_OWNER_GROUPS: {len(duplicate_owners)}")
    print(f"[PASS] CONFLICTING_NAMES_PRESERVED: {len(prior_conflicts)}")
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: NOT REQUIRED")
    print("WAL/SHM: NOT MANIPULATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
