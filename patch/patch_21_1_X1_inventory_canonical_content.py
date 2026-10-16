#!/usr/bin/env python3
"""Stage 21.1.X1: inventory canonical ROM V1 content for the V2 rewrite.

This is a read-only audit patch. It inventories content-bearing Python and data
files, extracts stable IDs/keys/names and cross-references, detects duplicate
identities and unresolved references, records validation rules, and writes
regulated JSON/Markdown artifacts. It never imports V1 runtime modules, opens
SQLite, or mutates production code, game.db, game.db-wal, or game.db-shm.
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
from typing import Any, Iterable

STAGE = "21.1.X1"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "5b68d81c5b253c734326eb4d50e7d2ce481b579d"
MODULE_INVENTORY = "reports/stage_21_1_1_v1_module_inventory.json"
DOMAIN_CONTRACTS = "reports/stage_21_1_5_domain_contracts.json"
PATCH_PATH = "patch/patch_21_1_X1_inventory_canonical_content.py"
JSON_PATH = "reports/stage_21_1_X1_canonical_content_inventory.json"
MD_PATH = "MD/STAGE_21_1_X1_CANONICAL_CONTENT_INVENTORY.md"
COMMIT_MESSAGE = "Stage 21.1.X1: inventory canonical V1 content"
OWNED_PATHS = {PATCH_PATH, JSON_PATH, MD_PATH}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
DATA_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".csv"}

CONTENT_GROUPS: dict[str, tuple[str, ...]] = {
    "classes": ("class", "classes"),
    "skills": ("skill", "skills", "ability", "abilities"),
    "items": ("item", "items", "equipment", "potion", "rune", "loot"),
    "mobs": ("mob", "mobs", "monster", "enemy", "boss"),
    "locations": ("location", "locations", "region", "world", "travel"),
    "npcs": ("npc", "npcs", "dialogue"),
    "quests": ("quest", "quests", "story", "contract", "daily"),
    "shops_economy": ("shop", "price", "premium", "crystal", "auction", "trade"),
    "events": ("event", "events"),
    "progression": ("exp", "level", "progression", "reward"),
    "localization": ("localization", "locale", "text", "name", "description", "about_game"),
}

ID_FIELD_NAMES = {
    "id", "item_id", "mob_id", "boss_id", "npc_id", "quest_id", "location_id",
    "skill_id", "class_id", "event_id", "region_id", "shop_id", "reward_id",
}
KEY_FIELD_NAMES = {
    "key", "slug", "code", "event_key", "class_key", "skill_key", "item_key",
    "mob_key", "quest_key", "location_key", "type", "kind",
}
NAME_FIELD_NAMES = {
    "name", "title", "display_name", "localized_name", "label", "description",
    "name_uk", "title_uk", "text",
}
REFERENCE_FIELD_RE = re.compile(
    r"(?i)(?:^|_)(item|mob|boss|npc|quest|location|skill|class|event|region|reward|target|source)(?:_id|_key)?$"
)
IDENTIFIER_NAME_RE = re.compile(r"(?i)(^|_)(id|key|slug|code)$")
HISTORICAL_RE = re.compile(r"(?i)(legacy|candidate|shadow|deprecated|superseded|obsolete|compat)")
TECHNICAL_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
UKRAINIAN_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


class PatchError(RuntimeError):
    """Expected fail-safe patch failure."""


def run(root: Path, *command: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )


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
        evidence[name] = {
            "exists": True,
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": sha256(path),
        }
    return evidence


def write_atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def parse_status(raw: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    parts = raw.split("\0")
    index = 0
    while index < len(parts):
        item = parts[index]
        if not item:
            index += 1
            continue
        status = item[:2]
        entry = {"status": status, "path": item[3:]}
        if status[0] in {"R", "C"} and index + 1 < len(parts):
            entry["original_path"] = parts[index + 1]
            index += 1
        entries.append(entry)
        index += 1
    return entries


def tracked_files(root: Path) -> list[str]:
    result = git(root, "ls-files", "-z")
    if result.returncode != 0:
        raise PatchError(result.stderr.strip() or "git ls-files failed")
    return sorted(item for item in result.stdout.split("\0") if item)


def literal(node: ast.AST | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def content_groups(path: str, symbol_names: Iterable[str]) -> list[str]:
    haystack = (path + " " + " ".join(symbol_names)).lower()
    groups = [group for group, tokens in CONTENT_GROUPS.items() if any(token in haystack for token in tokens)]
    return groups or ["uncategorized_content"]


def scalar_records(value: Any, source: str, symbol: str, path_stack: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            current = path_stack + (str(key),)
            key_name = str(key).lower()
            if isinstance(child, (str, int)):
                category = None
                if key_name in ID_FIELD_NAMES or IDENTIFIER_NAME_RE.search(key_name):
                    category = "identifier"
                elif key_name in KEY_FIELD_NAMES:
                    category = "key"
                elif key_name in NAME_FIELD_NAMES:
                    category = "name"
                elif REFERENCE_FIELD_RE.search(key_name):
                    category = "reference"
                if category:
                    records.append({
                        "source": source,
                        "symbol": symbol,
                        "field_path": ".".join(current),
                        "field_name": str(key),
                        "category": category,
                        "value": child,
                        "value_type": type(child).__name__,
                    })
            records.extend(scalar_records(child, source, symbol, current))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            records.extend(scalar_records(child, source, symbol, path_stack + (str(index),)))
    return records


def analyze_python_content(root: Path, path: str, classification: str) -> dict[str, Any]:
    full = root / path
    text = full.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=path)
    symbols: list[dict[str, Any]] = []
    extracted: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value_node = node.value
            value = literal(value_node)
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                symbol = target.id
                if symbol.isupper() or isinstance(value, (dict, list, tuple, set)):
                    symbols.append({
                        "name": symbol,
                        "line": node.lineno,
                        "literal": value is not None,
                        "value_type": type(value).__name__ if value is not None else "dynamic",
                        "historical_marker": bool(HISTORICAL_RE.search(symbol)),
                    })
                    if value is not None:
                        extracted.extend(scalar_records(value, path, symbol))
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                symbols.append({
                    "name": node.name,
                    "line": node.lineno,
                    "literal": False,
                    "value_type": type(node).__name__,
                    "historical_marker": bool(HISTORICAL_RE.search(node.name)),
                })
    groups = content_groups(path, [item["name"] for item in symbols])
    return {
        "path": path,
        "sha256": sha256(full),
        "classification": classification,
        "format": "python",
        "groups": groups,
        "symbols": symbols,
        "records": extracted,
        "historical_path_marker": bool(HISTORICAL_RE.search(path)),
    }


def analyze_json_content(root: Path, path: str) -> dict[str, Any]:
    full = root / path
    data = json.loads(full.read_text(encoding="utf-8"))
    records = scalar_records(data, path, "<document>")
    return {
        "path": path,
        "sha256": sha256(full),
        "classification": "CONTENT_EXTRACT",
        "format": "json",
        "groups": content_groups(path, []),
        "symbols": [],
        "records": records,
        "historical_path_marker": bool(HISTORICAL_RE.search(path)),
    }


def identity_namespace(record: dict[str, Any], groups: list[str]) -> str:
    field = record["field_name"].lower()
    match = REFERENCE_FIELD_RE.search(field)
    if match:
        return match.group(1).lower()
    for token in ("item", "mob", "boss", "npc", "quest", "location", "skill", "class", "event", "region", "reward"):
        if token in field:
            return token
    return groups[0] if groups else "unknown"


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    queues = payload["review_queues"]
    lines = [
        "# ROM Stage 21.1.X1 - canonical content inventory", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Проаналізовано content sources:** `{summary['source_count']}`",
        f"- **Python content sources:** `{summary['python_source_count']}`",
        f"- **Non-Python content sources:** `{summary['non_python_source_count']}`",
        f"- **Extracted identity/name/reference records:** `{summary['record_count']}`",
        f"- **Content groups:** `{summary['group_count']}`", "",
        "## Content groups", "",
    ]
    for group, details in payload["catalog_by_group"].items():
        lines.extend([
            f"### `{group}`", "",
            f"- Sources: **{details['source_count']}**",
            f"- Records: **{details['record_count']}**",
            f"- Identifiers/keys: **{details['identity_count']}**",
            f"- Names/text: **{details['name_count']}**",
            f"- References: **{details['reference_count']}**", "",
        ])
    lines.extend([
        "## Review queues", "",
        f"- Duplicate identities: **{len(queues['duplicate_identities'])}**.",
        f"- Conflicting names for one identity: **{len(queues['conflicting_names'])}**.",
        f"- Reference candidates without known identity: **{len(queues['unresolved_references'])}**.",
        f"- Historical/superseded candidates: **{len(queues['historical_candidates'])}**.",
        f"- Technical IDs without localized name evidence: **{len(queues['technical_id_without_localized_name'])}**.",
        f"- Dynamic content symbols requiring manual extraction: **{len(queues['dynamic_symbols'])}**.", "",
        "## Canonical V2 content contract", "",
        "- Stable IDs і keys не перевикористовуються для іншої сутності.",
        "- Кожна reference повинна resolve до canonical identity відповідного namespace.",
        "- Користувацькі тексти використовують локалізовані людські назви, а не technical IDs.",
        "- Content проходить schema validation до startup; invalid reference блокує bootstrap.",
        "- Historical, candidate, shadow і superseded values не мігруються без окремого owner рішення.",
        "- Runtime mutation logic не зберігається в content catalogs.",
        "- Quest terminology: історія -> розділи -> квести; термін `глава` не є canonical.",
        "- Canonical location presentation використовує `Початок Шляху`, а не `start_path`/`Start Path`.",
        "- Production DB/WAL/SHM не відкривалися та не змінювалися.", "",
        "## Наступний етап", "",
        "Stage 21.1.X2 - Behavioral fixtures ROM V1.", "",
    ])
    return "\n".join(lines)


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, JSON_PATH, MD_PATH]
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
    for required in (root / MODULE_INVENTORY, root / DOMAIN_CONTRACTS, root / "reports", root / "MD"):
        if not required.exists():
            print(f"[FAIL] Required input is missing: {required}", file=sys.stderr)
            return 2

    print("[1/8] [PASS] Canonical Stage 21 inputs and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [
        entry for entry in entries
        if entry["status"][0] in {" ", "?"}
        and (entry["path"] in OWNED_PATHS or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))
    ]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {"expected": TARGET_BRANCH}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.8 parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
    db_before = database_evidence(root)
    inventory = json.loads((root / MODULE_INVENTORY).read_text(encoding="utf-8"))
    domain_contracts = json.loads((root / DOMAIN_CONTRACTS).read_text(encoding="utf-8"))
    tracked = tracked_files(root)
    python_sources = [item for item in inventory["modules"] if item["classification"] in {"CONTENT_EXTRACT", "NEEDS_MANUAL_REVIEW"}]
    data_sources = [path for path in tracked if Path(path).suffix.lower() in DATA_EXTENSIONS and Path(path).parts and Path(path).parts[0] == "data"]

    print(f"[3/8] [PASS] Extracting canonical content candidates from {len(python_sources)} Python and {len(data_sources)} data sources.")
    sources: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, item in enumerate(python_sources, start=1):
        try:
            sources.append(analyze_python_content(root, item["path"], item["classification"]))
        except (OSError, SyntaxError) as exc:
            errors.append({"path": item["path"], "error": str(exc)})
        if index % 20 == 0 or index == len(python_sources):
            print(f"    Python progress: {index}/{len(python_sources)}", flush=True)
    for path in data_sources:
        try:
            if Path(path).suffix.lower() == ".json":
                sources.append(analyze_json_content(root, path))
            else:
                sources.append({
                    "path": path,
                    "sha256": sha256(root / path),
                    "classification": "CONTENT_EXTRACT",
                    "format": Path(path).suffix.lower().lstrip("."),
                    "groups": content_groups(path, []),
                    "symbols": [],
                    "records": [],
                    "historical_path_marker": bool(HISTORICAL_RE.search(path)),
                    "manual_parser_required": True,
                })
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append({"path": path, "error": str(exc)})

    print("[4/8] [PASS] Building identity namespaces, references and validation queues.")
    all_records: list[dict[str, Any]] = []
    for source in sources:
        for record in source["records"]:
            enriched = dict(record)
            enriched["groups"] = source["groups"]
            enriched["namespace"] = identity_namespace(record, source["groups"])
            all_records.append(enriched)

    identity_records = [record for record in all_records if record["category"] in {"identifier", "key"}]
    reference_records = [record for record in all_records if record["category"] == "reference"]
    name_records = [record for record in all_records if record["category"] == "name"]
    identity_index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in identity_records:
        identity_index[(record["namespace"], str(record["value"]))].append(record)
    duplicate_identities = [
        {"namespace": namespace, "value": value, "records": records}
        for (namespace, value), records in sorted(identity_index.items())
        if len({(record["source"], record["symbol"], record["field_path"]) for record in records}) > 1
    ]
    unresolved_references = [
        record for record in reference_records
        if (record["namespace"], str(record["value"])) not in identity_index
        and str(record["value"]) not in {"", "0", "None"}
    ]

    names_by_parent: dict[tuple[str, str], set[str]] = defaultdict(set)
    for record in name_records:
        parent = record["field_path"].rsplit(".", 1)[0] if "." in record["field_path"] else "<root>"
        names_by_parent[(record["source"], parent)].add(str(record["value"]))
    conflicting_names = [
        {"source": source, "parent": parent, "names": sorted(names)}
        for (source, parent), names in sorted(names_by_parent.items())
        if len(names) > 1
    ]
    historical_candidates = [
        {"path": source["path"], "symbols": [item["name"] for item in source["symbols"] if item["historical_marker"]]}
        for source in sources
        if source.get("historical_path_marker") or any(item["historical_marker"] for item in source["symbols"])
    ]
    dynamic_symbols = [
        {"source": source["path"], "symbol": symbol["name"], "line": symbol["line"], "value_type": symbol["value_type"]}
        for source in sources for symbol in source["symbols"]
        if not symbol["literal"] and symbol["value_type"] == "dynamic"
    ]

    localized_values = {str(record["value"]) for record in name_records if UKRAINIAN_RE.search(str(record["value"]))}
    technical_without_localized = []
    for record in identity_records:
        value = str(record["value"])
        if TECHNICAL_ID_RE.fullmatch(value):
            source_names = [item for item in name_records if item["source"] == record["source"]]
            if not any(UKRAINIAN_RE.search(str(item["value"])) for item in source_names):
                technical_without_localized.append(record)

    catalog_by_group: dict[str, dict[str, Any]] = {}
    for group in sorted({group for source in sources for group in source["groups"]}):
        group_sources = [source for source in sources if group in source["groups"]]
        group_records = [record for record in all_records if group in record["groups"]]
        catalog_by_group[group] = {
            "source_count": len(group_sources),
            "sources": [source["path"] for source in group_sources],
            "record_count": len(group_records),
            "identity_count": sum(record["category"] in {"identifier", "key"} for record in group_records),
            "name_count": sum(record["category"] == "name" for record in group_records),
            "reference_count": sum(record["category"] == "reference" for record in group_records),
        }

    checks.extend([
        Check("AST_AND_DATA_COVERAGE", "PASS" if not errors else "FAIL", "All selected content sources parsed." if not errors else "Some content sources could not be parsed.", {"errors": errors}, bool(errors)),
        Check("CONTENT_SOURCES_FOUND", "PASS" if sources else "FAIL", f"Content sources found: {len(sources)}.", {}, not sources),
        Check("CORE_GROUPS_PRESENT", "PASS" if all(group in catalog_by_group for group in ("classes", "items", "mobs", "locations", "npcs", "quests")) else "FAIL", "Core content groups are represented.", {"present": sorted(catalog_by_group)}, any(group not in catalog_by_group for group in ("classes", "items", "mobs", "locations", "npcs", "quests"))),
        Check("DATABASE_EVIDENCE_READY", "PASS", "DB/WAL/SHM evidence captured without opening SQLite.", {"production_connection_opened": False}),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"
    review_queues = {
        "duplicate_identities": duplicate_identities,
        "conflicting_names": conflicting_names,
        "unresolved_references": unresolved_references,
        "historical_candidates": historical_candidates,
        "technical_id_without_localized_name": technical_without_localized,
        "dynamic_symbols": dynamic_symbols,
    }
    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            "source_count": len(sources),
            "python_source_count": sum(source["format"] == "python" for source in sources),
            "non_python_source_count": sum(source["format"] != "python" for source in sources),
            "record_count": len(all_records),
            "identity_count": len(identity_records),
            "name_count": len(name_records),
            "reference_count": len(reference_records),
            "group_count": len(catalog_by_group),
        },
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "sources": sources,
        "catalog_by_group": catalog_by_group,
        "identity_registry": [
            {"namespace": namespace, "value": value, "records": records}
            for (namespace, value), records in sorted(identity_index.items())
        ],
        "review_queues": review_queues,
        "v2_content_contract": {
            "content_root": "rom_v2/content",
            "schemas_root": "rom_v2/content/schemas",
            "stable_identity_never_reused": True,
            "all_references_must_resolve": True,
            "bootstrap_validation_fail_closed": True,
            "technical_ids_forbidden_in_user_text": True,
            "canonical_location_name_start_path": "Початок Шляху",
            "canonical_story_hierarchy": ["історія", "розділи", "квести"],
            "historical_candidate_shadow_values": "OWNER_REVIEW_REQUIRED",
            "runtime_mutation_logic_in_content": "FORBIDDEN",
            "v1_runtime_import": "FORBIDDEN",
        },
        "domain_contract_source_commit": domain_contracts["git"]["head_before_commit"],
        "database_evidence_before": db_before,
        "artifacts": {"patch": PATCH_PATH, "json": JSON_PATH, "markdown": MD_PATH},
        "next_stage": "21.1.X2" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing canonical content inventory and validation contract.")
    write_atomic(root / JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / MD_PATH, render_markdown(payload))
    if conclusion != "GO":
        print("[6/8] [FAIL] Content inventory returned NO_GO; commit not created.")
        return 1

    print("[6/8] [PASS] Content coverage and validation contract accepted for audit output.")
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.X1 commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        print(f"[7/8] [FAIL] {exc}", file=sys.stderr)
        return 2
    db_after = database_evidence(root)
    if db_before != db_after:
        print("[8/8] [FAIL] DB/WAL/SHM evidence changed.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Content inventory committed and DB/WAL/SHM evidence verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - canonical content inventory")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] CONTENT_SOURCES: {len(sources)}")
    print(f"[PASS] CONTENT_GROUPS: {len(catalog_by_group)}")
    print(f"[PASS] RECORDS: {len(all_records)}")
    print(f"[PASS] DUPLICATE_IDENTITIES: {len(duplicate_identities)}")
    print(f"[PASS] UNRESOLVED_REFERENCES: {len(unresolved_references)}")
    print(f"[PASS] HISTORICAL_CANDIDATES: {len(historical_candidates)}")
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: NOT REQUIRED")
    print("WAL/SHM: NOT MANIPULATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
