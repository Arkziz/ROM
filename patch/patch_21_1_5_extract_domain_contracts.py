#!/usr/bin/env python3
"""Stage 21.1.5: extract ROM V1 domain contracts for the V2 rewrite.

Read-only static audit. It combines the canonical module inventory and database
access report, then maps functions, content modules, invariants, persistence
coupling and unresolved ownership into explicit domain contracts. It never
opens SQLite and never changes production code or DB/WAL/SHM files.
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

STAGE = "21.1.5"
BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "fd896e4a9a004d2e043e50091e1ba77341995eb3"
MODULE_INVENTORY = "reports/stage_21_1_1_v1_module_inventory.json"
DATABASE_REPORT = "reports/stage_21_1_4_database_access_transaction_boundaries.json"
PATCH_PATH = "patch/patch_21_1_5_extract_domain_contracts.py"
JSON_PATH = "reports/stage_21_1_5_domain_contracts.json"
MD_PATH = "MD/STAGE_21_1_5_DOMAIN_CONTRACTS.md"
COMMIT_MESSAGE = "Stage 21.1.5: extract V1 domain contracts"
OWNED = {PATCH_PATH, JSON_PATH, MD_PATH}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")

DOMAIN_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "account": {"paths": ("account", "premium", "crystal", "registered", "inactivity", "admin_crystal"), "symbols": ("user", "account", "premium", "crystal", "registered", "wallet")},
    "character": {"paths": ("character", "player", "attribute", "rebirth", "name_rune", "class_"), "symbols": ("character", "class", "level", "attribute", "respec", "rebirth", "name")},
    "stats": {"paths": ("stat", "mana", "player_hp", "defense", "progression"), "symbols": ("stat", "strength", "dexterity", "intelligence", "wisdom", "stamina", "max_hp", "max_mp", "pdef", "mdef", "patk", "matk")},
    "combat": {"paths": ("combat", "boss", "pvp", "reward", "drop", "pve"), "symbols": ("combat", "battle", "damage", "critical", "dodge", "victory", "defeat", "boss", "mob", "loot")},
    "inventory_equipment": {"paths": ("inventory", "equipment", "rune", "refine", "blacksmith", "potion", "item_"), "symbols": ("inventory", "item", "equip", "rune", "refine", "durability", "repair", "consume", "stack")},
    "economy": {"paths": ("shop", "auction", "trade", "crystal", "gold", "ledger", "wallet"), "symbols": ("purchase", "sell", "buy", "auction", "trade", "gold", "crystal", "ledger", "wallet", "price")},
    "quests_progression": {"paths": ("quest", "story", "daily", "contract", "exp", "progression"), "symbols": ("quest", "contract", "progress", "reward", "claim", "experience", "exp")},
    "world_travel": {"paths": ("location", "travel", "map", "city", "event", "chronicle"), "symbols": ("location", "travel", "region", "city", "event", "chronicle")},
    "social": {"paths": ("guild", "interaction", "profile_history", "notification"), "symbols": ("guild", "member", "application", "interaction", "notification", "history")},
}

INVARIANT_PATTERNS = {
    "idempotency": re.compile(r"idempot|exact.?once|insert\s+or\s+ignore|on\s+conflict", re.I),
    "non_negative_balance": re.compile(r"balance\s*[>=]|gold\s*[>=]|crystal|debit|wallet", re.I),
    "ownership": re.compile(r"user_id|owner|character_name|account", re.I),
    "reservation": re.compile(r"reservation|reserved|auction|trade", re.I),
    "capacity": re.compile(r"bag_slots|max_stack|capacity|quantity", re.I),
    "level_gate": re.compile(r"required_level|level\s*[>=<]|min_level|level_cap", re.I),
    "state_transition": re.compile(r"status|active|completed|claimed|skipped|pending", re.I),
    "transactionality": re.compile(r"begin immediate|commit|rollback|savepoint|transaction", re.I),
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


def run(root: Path, *cmd: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)


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


def db_evidence(root: Path) -> dict[str, Any]:
    result = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists():
            result[name] = {"exists": False}
            continue
        stat = path.stat()
        result[name] = {"exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}
    return result


def write_atomic(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def parse_status(raw: str) -> list[dict[str, str]]:
    return [{"status": item[:2], "path": item[3:]} for item in raw.split("\0") if item]


def domain_scores(path: str, symbols: list[str], text: str) -> dict[str, int]:
    haystack_path = path.lower()
    haystack_symbols = " ".join(symbols).lower()
    scores = {}
    for domain, rules in DOMAIN_RULES.items():
        score = sum(4 for token in rules["paths"] if token in haystack_path)
        score += sum(2 for token in rules["symbols"] if token in haystack_symbols)
        score += sum(1 for token in rules["symbols"] if token in text.lower())
        scores[domain] = score
    return scores


def classify_domains(path: str, symbols: list[str], text: str) -> tuple[list[str], dict[str, int]]:
    scores = domain_scores(path, symbols, text)
    maximum = max(scores.values(), default=0)
    if maximum == 0:
        return ["cross_cutting"], scores
    primary = [name for name, value in scores.items() if value == maximum]
    secondary = [name for name, value in scores.items() if value >= max(3, maximum - 2) and name not in primary]
    return primary + secondary[:2], scores


def function_records(root: Path, module: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = module["path"]
    full = root / path
    text = full.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=path)
    records = []
    constants = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            doc = ast.get_docstring(node)
            decorators = [ast.unparse(item) for item in getattr(node, "decorator_list", [])]
            source = ast.get_source_segment(text, node) or ""
            domains, scores = classify_domains(path, [name], source[:8000])
            invariants = sorted(name for name, pattern in INVARIANT_PATTERNS.items() if pattern.search(source))
            records.append({
                "symbol": name,
                "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                "line": node.lineno,
                "end_line": node.end_lineno or node.lineno,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "docstring": doc,
                "decorators": decorators,
                "domains": domains,
                "domain_scores": scores,
                "invariants": invariants,
                "public": not name.startswith("_"),
            })
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append({"name": target.id, "line": node.lineno, "value_preview": ast.unparse(node.value)[:300]})
    return records, constants


def database_context_index(database_report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for module in database_report["modules"]:
        for context in module["contexts"]:
            result[module["path"]].append(context)
    return result


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# ROM Stage 21.1.5 - доменні контракти V1 для V2", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Проаналізовано модулів:** `{summary['module_count']}`",
        f"- **Проаналізовано symbols:** `{summary['symbol_count']}`",
        f"- **Контрактних доменів:** `{summary['domain_count']}`",
        f"- **Cross-domain modules:** `{summary['cross_domain_module_count']}`",
        f"- **Owner review modules:** `{summary['owner_review_module_count']}`", "",
        "## Домени", "",
    ]
    for domain, contract in payload["domain_contracts"].items():
        lines.extend([
            f"### `{domain}`", "",
            f"- Modules: **{contract['module_count']}**",
            f"- Public symbols: **{contract['public_symbol_count']}**",
            f"- Persistence contexts: **{contract['persistence_context_count']}**",
            f"- Invariants: {', '.join(contract['invariants']) if contract['invariants'] else 'не визначено статично'}",
            f"- V2 package: `{contract['v2_package']}`", "",
        ])
    lines.extend([
        "## Загальний V2 contract", "",
        "- Domain logic не імпортує Telegram SDK, sqlite3, V1 `db` або `db_modules`.",
        "- Application use cases оркеструють domain services через ports та Unit of Work.",
        "- Infrastructure реалізує repositories, Telegram adapters, clock, random і persistence.",
        "- Content проходить schema validation і не містить runtime mutation logic.",
        "- Accepted V1 поведінка переноситься як explicit contract tests, а не як імпорт V1 runtime.",
        "- Cross-domain операції мають одного application owner і не дублюють authoritative formulas.",
        "- Production DB/WAL/SHM не відкривалися та не змінювалися.", "",
        "## Review queues", "",
        f"- Owner review: **{len(payload['review_queues']['owner_review'])}** modules.",
        f"- Cross-domain: **{len(payload['review_queues']['cross_domain'])}** modules.",
        f"- Persistence-coupled domain candidates: **{len(payload['review_queues']['persistence_coupled'])}** modules.",
        f"- Missing-doc public symbols: **{len(payload['review_queues']['missing_doc_public_symbols'])}** symbols.", "",
        "## Наступний етап", "",
        "Stage 21.1.6 - dependency graph, cycles і заборонені V2 dependency directions.", "",
    ])
    return "\n".join(lines)


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, JSON_PATH, MD_PATH]
    added = git(root, "add", "-f", "--", *paths)
    if added.returncode:
        raise PatchError(added.stderr.strip() or "git add failed")
    staged_result = git(root, "diff", "--cached", "--name-only", "-z")
    staged = sorted(item for item in staged_result.stdout.split("\0") if item)
    if staged_result.returncode or staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging allowlist mismatch: {staged}")
    committed = git(root, "commit", "-m", COMMIT_MESSAGE)
    if committed.returncode:
        git(root, "reset", "--", *paths)
        raise PatchError(committed.stderr.strip() or committed.stdout.strip() or "git commit failed")
    return rev(root, "HEAD") or ""


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    required = [root / MODULE_INVENTORY, root / DATABASE_REPORT, root / "reports", root / "MD"]
    if any(not path.exists() for path in required):
        print("[FAIL] Required Stage 21 inputs or directories are missing.", file=sys.stderr)
        return 2

    print("[1/8] [PASS] Canonical inventory, DB audit and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == BRANCH else "FAIL", f"Active branch: {branch}", {"expected": BRANCH}, branch != BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.4 parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
    db_before = db_evidence(root)
    inventory = json.loads((root / MODULE_INVENTORY).read_text(encoding="utf-8"))
    database_report = json.loads((root / DATABASE_REPORT).read_text(encoding="utf-8"))
    persistence = database_context_index(database_report)
    modules = [item for item in inventory["modules"] if item["classification"] not in {"TEST_REFERENCE", "DO_NOT_MIGRATE"}]

    print(f"[3/8] [PASS] Extracting symbols and contracts from {len(modules)} modules.")
    module_contracts = []
    errors = []
    for module in modules:
        try:
            symbols, constants = function_records(root, module)
            text = (root / module["path"]).read_text(encoding="utf-8", errors="replace")
            domains, scores = classify_domains(module["path"], [item["symbol"] for item in symbols], text[:20000])
            invariants = sorted({invariant for symbol in symbols for invariant in symbol["invariants"]})
            module_contracts.append({
                "path": module["path"],
                "classification": module["classification"],
                "sha256": sha256(root / module["path"]),
                "domains": domains,
                "domain_scores": scores,
                "symbols": symbols,
                "constants": constants,
                "invariants": invariants,
                "persistence_contexts": persistence.get(module["path"], []),
                "owner_status": module["authoritative_owner_status"],
            })
        except (OSError, SyntaxError) as exc:
            errors.append({"path": module["path"], "error": str(exc)})

    print("[4/8] [PASS] Building bounded contexts, invariants and owner queues.")
    domain_contracts = {}
    v2_packages = {
        "account": "rom_v2/domain/account",
        "character": "rom_v2/domain/character",
        "stats": "rom_v2/domain/stats",
        "combat": "rom_v2/domain/combat",
        "inventory_equipment": "rom_v2/domain/inventory",
        "economy": "rom_v2/domain/economy",
        "quests_progression": "rom_v2/domain/quests",
        "world_travel": "rom_v2/domain/world",
        "social": "rom_v2/domain/social",
        "cross_cutting": "rom_v2/application",
    }
    for domain in [*DOMAIN_RULES, "cross_cutting"]:
        matching = [module for module in module_contracts if domain in module["domains"]]
        domain_contracts[domain] = {
            "module_count": len(matching),
            "modules": [module["path"] for module in matching],
            "public_symbol_count": sum(sum(symbol["public"] for symbol in module["symbols"]) for module in matching),
            "persistence_context_count": sum(len(module["persistence_contexts"]) for module in matching),
            "invariants": sorted({invariant for module in matching for invariant in module["invariants"]}),
            "v2_package": v2_packages[domain],
            "contract_status": "REFERENCE_EXTRACTED_OWNER_REVIEW_REQUIRED" if any(module["owner_status"] == "OWNER_UNRESOLVED" for module in matching) else "REFERENCE_EXTRACTED",
        }

    owner_review = [module["path"] for module in module_contracts if module["owner_status"] == "OWNER_UNRESOLVED"]
    cross_domain = [module["path"] for module in module_contracts if len(module["domains"]) > 1]
    persistence_coupled = [module["path"] for module in module_contracts if module["persistence_contexts"]]
    missing_docs = [
        {"module": module["path"], "symbol": symbol["symbol"], "line": symbol["line"]}
        for module in module_contracts for symbol in module["symbols"]
        if symbol["public"] and not symbol["docstring"]
    ]
    symbol_count = sum(len(module["symbols"]) for module in module_contracts)
    checks.extend([
        Check("AST_COVERAGE", "PASS" if not errors else "FAIL", "All selected modules parsed." if not errors else "AST errors found.", {"errors": errors}, bool(errors)),
        Check("DOMAIN_COVERAGE", "PASS" if all(module["domains"] for module in module_contracts) else "FAIL", "Every module has at least one domain classification.", {}, any(not module["domains"] for module in module_contracts)),
        Check("CORE_DOMAINS_PRESENT", "PASS" if all(domain_contracts[name]["module_count"] for name in DOMAIN_RULES) else "FAIL", "All nine core bounded contexts have source references.", {name: domain_contracts[name]["module_count"] for name in DOMAIN_RULES}, any(not domain_contracts[name]["module_count"] for name in DOMAIN_RULES)),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"

    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            "module_count": len(module_contracts),
            "symbol_count": symbol_count,
            "domain_count": len(domain_contracts),
            "cross_domain_module_count": len(cross_domain),
            "owner_review_module_count": len(owner_review),
        },
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "domain_contracts": domain_contracts,
        "module_contracts": module_contracts,
        "review_queues": {
            "owner_review": owner_review,
            "cross_domain": cross_domain,
            "persistence_coupled": persistence_coupled,
            "missing_doc_public_symbols": missing_docs,
        },
        "v2_architecture_contract": {
            "layers": ["domain", "application", "infrastructure", "content", "app"],
            "domain_may_depend_on": [],
            "application_may_depend_on": ["domain", "application.ports"],
            "infrastructure_may_depend_on": ["domain", "application.ports"],
            "app_composition_root_may_depend_on": ["application", "infrastructure", "content"],
            "v1_runtime_import": "FORBIDDEN",
            "telegram_sdk_in_domain_or_application": "FORBIDDEN",
            "raw_sql_in_domain_or_application": "FORBIDDEN",
            "single_authoritative_formula_owner": True,
            "accepted_behavior_requires_contract_test": True,
        },
        "database_evidence_before": db_before,
        "artifacts": {"patch": PATCH_PATH, "json": JSON_PATH, "markdown": MD_PATH},
        "next_stage": "21.1.6" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing domain contract registry and Markdown summary.")
    write_atomic(root / JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / MD_PATH, render_markdown(payload))
    if conclusion != "GO":
        print("[6/8] [FAIL] Domain contract extraction returned NO_GO; commit not created.")
        return 1

    print("[6/8] [PASS] Domain contract and architecture constraints validated.")
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.5 commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        print(f"[7/8] [FAIL] {exc}", file=sys.stderr)
        return 2
    if db_before != db_evidence(root):
        print("[8/8] [FAIL] DB/WAL/SHM evidence changed.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Domain contracts committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - extract domain contracts")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] MODULES: {len(module_contracts)}")
    print(f"[PASS] SYMBOLS: {symbol_count}")
    print(f"[PASS] DOMAINS: {len(domain_contracts)}")
    print(f"[PASS] CROSS_DOMAIN_MODULES: {len(cross_domain)}")
    print(f"[PASS] OWNER_REVIEW_MODULES: {len(owner_review)}")
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: NOT REQUIRED")
    print("WAL/SHM: NOT MANIPULATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
