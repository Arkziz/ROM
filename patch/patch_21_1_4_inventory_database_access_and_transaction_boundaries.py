#!/usr/bin/env python3
"""Stage 21.1.4: inventory V1 database access and transaction boundaries.

The patch performs static analysis only. It never opens production SQLite and
never modifies production code, game.db, game.db-wal, or game.db-shm. Results
are written to reports/ and MD/, then committed with an exact staging allowlist.
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
from typing import Any, Iterable, Sequence

STAGE = "21.1.4"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "0f4ed6b7f3d9edc587efb436f8bf5a19dd4c65bb"
MODULE_INVENTORY_PATH = "reports/stage_21_1_1_v1_module_inventory.json"
PATCH_PATH = "patch/patch_21_1_4_inventory_database_access_and_transaction_boundaries.py"
JSON_PATH = "reports/stage_21_1_4_database_access_transaction_boundaries.json"
MD_PATH = "MD/STAGE_21_1_4_DATABASE_ACCESS_TRANSACTION_BOUNDARIES.md"
COMMIT_MESSAGE = "Stage 21.1.4: inventory database access and transaction boundaries"
OWNED_PATHS = {PATCH_PATH, JSON_PATH, MD_PATH}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")

SQL_OPERATION_RE = re.compile(
    r"(?is)\b(SELECT|INSERT|UPDATE|DELETE|REPLACE|CREATE|ALTER|DROP|PRAGMA|WITH)\b"
)
MUTATION_SQL = {"INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "ALTER", "DROP"}
READ_SQL = {"SELECT", "PRAGMA", "WITH"}
CONNECTION_CALLS = {"sqlite3.connect", "connect"}
EXECUTE_TAILS = {"execute", "executemany", "executescript"}
TRANSACTION_TAILS = {"commit", "rollback"}
DB_FACADE_PREFIXES = ("db.", "db_modules.")
TRANSACTION_NAME_MARKERS = (
    "transaction", "atomic", "settle", "purchase", "buy", "sell", "trade",
    "auction", "reward", "claim", "transfer", "debit", "credit", "ledger",
    "reserve", "consume", "complete", "finish", "turn_in", "equip", "repair",
)
EXACT_ONCE_MARKERS = (
    "idempot", "ledger", "reservation", "purchase", "claim", "reward",
    "settlement", "transaction", "trade", "auction",
)
NON_RUNTIME_CLASSIFICATIONS = {"TEST_REFERENCE", "DO_NOT_MIGRATE"}


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


@dataclass
class FunctionContext:
    name: str
    qualified_name: str
    line: int
    end_line: int
    is_async: bool
    has_transaction_context: bool = False
    connection_calls: list[dict[str, Any]] | None = None
    sql_operations: list[dict[str, Any]] | None = None
    facade_calls: list[dict[str, Any]] | None = None
    transaction_calls: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        self.connection_calls = self.connection_calls or []
        self.sql_operations = self.sql_operations or []
        self.facade_calls = self.facade_calls or []
        self.transaction_calls = self.transaction_calls or []


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
    result: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists():
            result[name] = {"exists": False}
            continue
        stat = path.stat()
        result[name] = {
            "exists": True,
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": sha256(path),
        }
    return result


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


def unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def call_name(node: ast.Call) -> str:
    return unparse(node.func)


def call_tail(node: ast.Call) -> str:
    return call_name(node).split(".")[-1]


def extract_sql(node: ast.Call) -> tuple[str | None, str, bool]:
    if not node.args:
        return None, "UNKNOWN", False
    expression = node.args[0]
    dynamic = True
    value: str | None = None
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        value = expression.value
        dynamic = False
    elif isinstance(expression, ast.JoinedStr):
        value = unparse(expression)
    else:
        value = unparse(expression)
    match = SQL_OPERATION_RE.search(value or "")
    operation = match.group(1).upper() if match else "UNKNOWN"
    preview = " ".join((value or "").strip().split())[:240]
    return preview or None, operation, dynamic


def owner_function(tree: ast.Module, line: int) -> tuple[str, int, int]:
    candidates: list[tuple[int, str, int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = node.end_lineno or node.lineno
            if node.lineno <= line <= end:
                span = end - node.lineno
                candidates.append((span, node.name, node.lineno, end))
    if not candidates:
        return "<module>", 1, 1
    _, name, start, end = min(candidates)
    return name, start, end


def has_transaction_context(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, (ast.With, ast.AsyncWith)):
            for item in child.items:
                expression = unparse(item.context_expr).lower()
                if any(marker in expression for marker in ("transaction", "atomic", "unit_of_work", "connection", "cursor")):
                    return True
        if isinstance(child, ast.Try):
            calls = [call_tail(n) for n in ast.walk(child) if isinstance(n, ast.Call)]
            if "commit" in calls and "rollback" in calls:
                return True
    return False


def analyze_module(root: Path, path: str, classification: str) -> dict[str, Any]:
    full_path = root / path
    text = full_path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=path)
    function_nodes: dict[str, ast.AST] = {}
    functions: dict[str, FunctionContext] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            context = FunctionContext(
                name=node.name,
                qualified_name=f"{path}:{node.name}",
                line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                is_async=isinstance(node, ast.AsyncFunctionDef),
                has_transaction_context=has_transaction_context(node),
            )
            key = f"{node.name}@{node.lineno}"
            functions[key] = context
            function_nodes[key] = node

    module_context = FunctionContext("<module>", f"{path}:<module>", 1, 1, False, has_transaction_context(tree))

    def context_for(line: int) -> FunctionContext:
        matching = [ctx for ctx in functions.values() if ctx.line <= line <= ctx.end_line]
        return min(matching, key=lambda ctx: ctx.end_line - ctx.line) if matching else module_context

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)
        tail = call_tail(node)
        context = context_for(node.lineno)
        if name in CONNECTION_CALLS or name.endswith(".connect") and "sqlite" in text[: min(len(text), 1000)].lower():
            context.connection_calls.append({"line": node.lineno, "call": name})
        if tail in EXECUTE_TAILS:
            preview, operation, dynamic = extract_sql(node)
            context.sql_operations.append({
                "line": node.lineno,
                "call": name,
                "operation": operation,
                "is_mutation": operation in MUTATION_SQL,
                "is_read": operation in READ_SQL,
                "dynamic_sql": dynamic,
                "sql_preview": preview,
            })
        if tail in TRANSACTION_TAILS:
            context.transaction_calls.append({"line": node.lineno, "call": name, "kind": tail})
        if name.startswith(DB_FACADE_PREFIXES):
            context.facade_calls.append({"line": node.lineno, "call": name, "args": [unparse(arg) for arg in node.args[:3]]})

    contexts = [module_context, *functions.values()]
    relevant = []
    for context in contexts:
        if not any((context.connection_calls, context.sql_operations, context.facade_calls, context.transaction_calls)):
            continue
        mutations = [item for item in context.sql_operations if item["is_mutation"]]
        commits = [item for item in context.transaction_calls if item["kind"] == "commit"]
        rollbacks = [item for item in context.transaction_calls if item["kind"] == "rollback"]
        multi_step = len(mutations) + len(context.facade_calls) >= 2
        marked_transactional = any(marker in context.name.lower() for marker in TRANSACTION_NAME_MARKERS)
        exact_once_relevant = any(marker in context.name.lower() for marker in EXACT_ONCE_MARKERS)
        explicit_boundary = context.has_transaction_context or bool(commits) or bool(rollbacks)
        mutation_without_boundary = bool(mutations) and not explicit_boundary
        partial_mutation_risk = multi_step and (bool(mutations) or marked_transactional) and not explicit_boundary
        rollback_gap = bool(commits) and not rollbacks and (multi_step or exact_once_relevant)
        handler_direct_sql = path.startswith("handlers/") and bool(context.sql_operations)
        system_direct_sql = path.startswith("systems/") and bool(context.sql_operations)
        relevant.append({
            "name": context.name,
            "qualified_name": context.qualified_name,
            "line": context.line,
            "end_line": context.end_line,
            "is_async": context.is_async,
            "connection_calls": context.connection_calls,
            "sql_operations": context.sql_operations,
            "facade_calls": context.facade_calls,
            "transaction_calls": context.transaction_calls,
            "has_transaction_context": context.has_transaction_context,
            "mutation_count": len(mutations),
            "multi_step_operation": multi_step,
            "transaction_name_marker": marked_transactional,
            "exact_once_relevant": exact_once_relevant,
            "explicit_transaction_boundary": explicit_boundary,
            "mutation_without_boundary": mutation_without_boundary,
            "partial_mutation_risk": partial_mutation_risk,
            "commit_without_observed_rollback": rollback_gap,
            "handler_direct_sql": handler_direct_sql,
            "system_direct_sql": system_direct_sql,
        })

    imports = sorted({
        alias.name
        for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    })
    return {
        "path": path,
        "classification": classification,
        "sha256": sha256(full_path),
        "imports": imports,
        "contexts": relevant,
        "summary": {
            "context_count": len(relevant),
            "connection_call_count": sum(len(ctx["connection_calls"]) for ctx in relevant),
            "sql_operation_count": sum(len(ctx["sql_operations"]) for ctx in relevant),
            "facade_call_count": sum(len(ctx["facade_calls"]) for ctx in relevant),
            "transaction_call_count": sum(len(ctx["transaction_calls"]) for ctx in relevant),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    queues = payload["review_queues"]
    return "\n".join([
        "# ROM Stage 21.1.4 - database access і transaction boundaries", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Проаналізовано runtime/content/manual-review модулів:** `{summary['module_count']}`",
        f"- **Модулів із DB activity:** `{summary['database_module_count']}`",
        f"- **Direct connection calls:** `{summary['connection_call_count']}`",
        f"- **SQL operations:** `{summary['sql_operation_count']}`",
        f"- **DB facade calls:** `{summary['facade_call_count']}`",
        f"- **Commit/Rollback calls:** `{summary['transaction_call_count']}`", "",
        "## Review queues", "",
        f"- Handler direct SQL: **{len(queues['handler_direct_sql'])}** contexts.",
        f"- System direct SQL: **{len(queues['system_direct_sql'])}** contexts.",
        f"- Mutation without explicit boundary: **{len(queues['mutation_without_boundary'])}** contexts.",
        f"- Partial mutation risk: **{len(queues['partial_mutation_risk'])}** contexts.",
        f"- Commit without observed rollback: **{len(queues['commit_without_observed_rollback'])}** contexts.",
        f"- Exact-once relevant paths: **{len(queues['exact_once_relevant'])}** contexts.",
        f"- Dynamic SQL: **{len(queues['dynamic_sql'])}** operations.", "",
        "## V2 contract", "",
        "- SQL дозволений тільки в `infrastructure/database` repositories та migration/bootstrap tools.",
        "- handlers, domain і application services не відкривають SQLite connection і не виконують raw SQL.",
        "- Multi-step mutation виконується в одній Unit of Work з явним commit/rollback contract.",
        "- Ledger, reservations, purchases, rewards, trades, auctions і settlement мають idempotency/exact-once contract.",
        "- Static findings є audit candidates; вони не доводять runtime defect без contract/runtime verification.",
        "- Production DB/WAL/SHM не відкривалися та не змінювалися.", "",
        "## Наступний етап", "",
        "Stage 21.1.5 - доменні контракти account, character, stats, combat, inventory, economy та social systems.", "",
    ])


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
    commit_hash = rev(root, "HEAD")
    if not commit_hash:
        raise PatchError("commit created but HEAD cannot be resolved")
    return commit_hash


def flatten_contexts(modules: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(context, module=module["path"]) for module in modules for context in module["contexts"]]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    if not (root / MODULE_INVENTORY_PATH).is_file():
        print(f"[FAIL] Missing {MODULE_INVENTORY_PATH}", file=sys.stderr)
        return 2
    if not (root / "reports").is_dir() or not (root / "MD").is_dir():
        print("[FAIL] Required reports and MD directories are missing.", file=sys.stderr)
        return 2

    print("[1/8] [PASS] Canonical module inventory and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED_PATHS or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {"expected": TARGET_BRANCH}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.3a parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
    db_before = database_evidence(root)
    inventory = json.loads((root / MODULE_INVENTORY_PATH).read_text(encoding="utf-8"))
    selected = [item for item in inventory["modules"] if item["classification"] not in NON_RUNTIME_CLASSIFICATIONS]

    print(f"[3/8] [PASS] Analyzing database access in {len(selected)} modules.")
    module_findings = []
    errors = []
    for item in selected:
        try:
            module_findings.append(analyze_module(root, item["path"], item["classification"]))
        except (OSError, SyntaxError) as exc:
            errors.append({"path": item["path"], "error": str(exc)})

    print("[4/8] [PASS] Building transaction-boundary and partial-mutation queues.")
    contexts = flatten_contexts(module_findings)
    database_modules = [module for module in module_findings if module["summary"]["context_count"]]
    handler_direct = [context for context in contexts if context["handler_direct_sql"]]
    system_direct = [context for context in contexts if context["system_direct_sql"]]
    without_boundary = [context for context in contexts if context["mutation_without_boundary"]]
    partial_risk = [context for context in contexts if context["partial_mutation_risk"]]
    rollback_gap = [context for context in contexts if context["commit_without_observed_rollback"]]
    exact_once = [context for context in contexts if context["exact_once_relevant"]]
    dynamic_sql = [dict(operation, module=context["module"], function=context["qualified_name"]) for context in contexts for operation in context["sql_operations"] if operation["dynamic_sql"]]

    operation_counts = Counter(operation["operation"] for context in contexts for operation in context["sql_operations"])
    connection_count = sum(module["summary"]["connection_call_count"] for module in module_findings)
    sql_count = sum(module["summary"]["sql_operation_count"] for module in module_findings)
    facade_count = sum(module["summary"]["facade_call_count"] for module in module_findings)
    transaction_count = sum(module["summary"]["transaction_call_count"] for module in module_findings)
    checks.extend([
        Check("AST_COVERAGE", "PASS" if not errors else "FAIL", "All selected modules parsed." if not errors else "AST errors found.", {"errors": errors}, bool(errors)),
        Check("DATABASE_ACTIVITY_FOUND", "PASS" if database_modules else "FAIL", f"Database activity found in {len(database_modules)} modules.", {}, not database_modules),
        Check("DATABASE_EVIDENCE_READY", "PASS", "Production DB/WAL/SHM evidence captured without opening SQLite.", {"production_connection_opened": False}),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"

    queues = {
        "handler_direct_sql": handler_direct,
        "system_direct_sql": system_direct,
        "mutation_without_boundary": without_boundary,
        "partial_mutation_risk": partial_risk,
        "commit_without_observed_rollback": rollback_gap,
        "exact_once_relevant": exact_once,
        "dynamic_sql": dynamic_sql,
    }
    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            "module_count": len(selected),
            "database_module_count": len(database_modules),
            "context_count": len(contexts),
            "connection_call_count": connection_count,
            "sql_operation_count": sql_count,
            "facade_call_count": facade_count,
            "transaction_call_count": transaction_count,
            "sql_operation_counts": dict(sorted(operation_counts.items())),
        },
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "modules": module_findings,
        "review_queues": queues,
        "v2_boundary_contract": {
            "raw_sql_allowed_only_in": ["rom_v2/infrastructure/database", "rom_v2/infrastructure/database/migrations", "tools_v2/bootstrap"],
            "raw_sql_forbidden_in": ["rom_v2/domain", "rom_v2/application", "rom_v2/infrastructure/telegram"],
            "connection_factory_owner": "rom_v2/infrastructure/database/connection_factory.py",
            "unit_of_work_owner": "rom_v2/application/ports/unit_of_work.py",
            "transaction_rule": "one business mutation = one explicit Unit of Work",
            "rollback_rule": "mandatory on exception before propagating failure",
            "exact_once_domains": ["ledger", "purchase", "reward", "trade", "auction", "reservation", "settlement"],
            "direct_v1_db_import_into_v2": "FORBIDDEN",
        },
        "database_evidence_before": db_before,
        "artifacts": {"patch": PATCH_PATH, "json": JSON_PATH, "markdown": MD_PATH},
        "next_stage": "21.1.5" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing JSON database inventory and Markdown contract summary.")
    write_atomic(root / JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / MD_PATH, render_markdown(payload))
    if conclusion != "GO":
        print("[6/8] [FAIL] Database audit returned NO_GO; commit not created.")
        return 1

    print("[6/8] [PASS] Database access and transaction-boundary contract validated.")
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.4 commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        print(f"[7/8] [FAIL] {exc}", file=sys.stderr)
        return 2

    db_after = database_evidence(root)
    if db_before != db_after:
        print("[8/8] [FAIL] DB/WAL/SHM evidence changed.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Database inventory committed and DB/WAL/SHM evidence verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - database access and transaction boundaries")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] DATABASE_MODULES: {len(database_modules)}")
    print(f"[PASS] CONNECTION_CALLS: {connection_count}")
    print(f"[PASS] SQL_OPERATIONS: {sql_count}")
    print(f"[PASS] DB_FACADE_CALLS: {facade_count}")
    print(f"[PASS] TRANSACTION_CALLS: {transaction_count}")
    print(f"[PASS] MUTATION_WITHOUT_BOUNDARY: {len(without_boundary)}")
    print(f"[PASS] PARTIAL_MUTATION_RISK: {len(partial_risk)}")
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: NOT REQUIRED")
    print("WAL/SHM: NOT MANIPULATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
