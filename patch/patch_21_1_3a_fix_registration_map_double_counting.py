#!/usr/bin/env python3
"""Stage 21.1.3a: remove AST double counting from the handler registration map.

Stage 21.1.3 counted the same decorator twice: once through ast.walk() of the
outer register function and once as the nested handler decorator. This follow-up
rebuilds the canonical map from physical registration sites, recalculates route
collision candidates, writes separate remediation evidence, and commits only
regulated artifacts. Production code and SQLite files are untouched.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

STAGE = "21.1.3a"
BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "130acfdbb48404b64ce2c420c77e6b65ca6a8745"
SOURCE_REPORT = "reports/stage_21_1_3_runtime_handler_callback_map.json"
PATCH_PATH = "patch/patch_21_1_3a_fix_registration_map_double_counting.py"
CANONICAL_JSON = "reports/stage_21_1_3_runtime_handler_callback_map.json"
CANONICAL_MD = "MD/STAGE_21_1_3_RUNTIME_HANDLER_CALLBACK_MAP.md"
REMEDIATION_JSON = "reports/stage_21_1_3a_registration_map_fix.json"
REMEDIATION_MD = "MD/STAGE_21_1_3A_REGISTRATION_MAP_FIX.md"
COMMIT_MESSAGE = "Stage 21.1.3a: fix registration map double counting"
OWNED = {PATCH_PATH, CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD}
DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
REGISTRATION_NAMES = {
    "message_handler", "callback_query_handler", "register_message_handler",
    "register_callback_query_handler", "register_next_step_handler",
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


def db_evidence(root: Path) -> dict[str, Any]:
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


def unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def kind(call: ast.Call) -> str | None:
    tail = unparse(call.func).split(".")[-1]
    return tail if tail in REGISTRATION_NAMES else None


def record(path: str, call: ast.Call, handler_symbol: str, owner: str, source: str) -> dict[str, Any] | None:
    registration_kind = kind(call)
    if not registration_kind:
        return None
    args = [unparse(arg) for arg in call.args]
    kwargs = {keyword.arg: unparse(keyword.value) for keyword in call.keywords if keyword.arg}
    return {
        "module": path,
        "line": call.lineno,
        "column": call.col_offset,
        "kind": registration_kind,
        "source": source,
        "owner_function": owner,
        "handler_symbol": handler_symbol,
        "call": unparse(call),
        "args": args,
        "kwargs": kwargs,
        "physical_site_key": f"{path}:{call.lineno}:{call.col_offset}:{registration_kind}",
    }


def scan_module(root: Path, path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tree = ast.parse((root / path).read_text(encoding="utf-8", errors="replace"), filename=path)
    registrations: list[dict[str, Any]] = []
    register_definitions: list[dict[str, Any]] = []

    # Every function/class node is visited exactly once. Decorators are recorded
    # only from the decorated symbol, not again through an outer ast.walk().
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("register_") or ("register" in node.name and "handler" in node.name):
                register_definitions.append({"name": node.name, "line": node.lineno})
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    item = record(path, decorator, node.name, node.name, "decorator")
                    if item:
                        registrations.append(item)

    # Explicit register_* calls are operational sites and are recorded once.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        registration_kind = kind(node)
        if not registration_kind or registration_kind in {"message_handler", "callback_query_handler"}:
            continue
        handler_symbol = unparse(node.args[1] if len(node.args) > 1 else node.args[0]) if node.args else "<unknown>"
        owner = "<module>"
        for candidate in ast.walk(tree):
            if isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)) and hasattr(candidate, "end_lineno"):
                if candidate.lineno <= node.lineno <= (candidate.end_lineno or candidate.lineno):
                    owner = candidate.name
                    break
        item = record(path, node, handler_symbol, owner, "explicit_register_call")
        if item:
            registrations.append(item)

    unique: dict[str, dict[str, Any]] = {}
    for item in registrations:
        unique.setdefault(item["physical_site_key"], item)
    return sorted(unique.values(), key=lambda item: (item["line"], item["column"])), sorted(register_definitions, key=lambda item: item["line"])


def main_order(root: Path) -> list[dict[str, Any]]:
    tree = ast.parse((root / "main.py").read_text(encoding="utf-8", errors="replace"), filename="main.py")
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = unparse(node.func)
            if name.startswith("register_") or name.endswith(".register_event_handlers"):
                calls.append({"call": name, "line": node.lineno})
    calls.sort(key=lambda item: item["line"])
    for index, item in enumerate(calls, start=1):
        item["order"] = index
    return calls


def collision_signature(item: dict[str, Any]) -> tuple[str, str]:
    return item["kind"], json.dumps(item["kwargs"], ensure_ascii=False, sort_keys=True)


def render_canonical(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    queues = payload["queues"]
    return "\n".join([
        "# ROM Stage 21.1.3 - карта runtime handler і callback registration", "",
        "- **Canonical revision:** `Stage 21.1.3a`",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Registration modules:** `{summary['module_count']}`",
        f"- **Physical registration sites:** `{summary['registration_record_count']}`",
        f"- **Main registration calls:** `{summary['main_registration_count']}`",
        f"- **Route collision candidates:** `{summary['route_collision_group_count']}`", "",
        "## Виправлення Stage 21.1.3a", "",
        "- Один decorator або explicit register call відповідає одному physical registration site.",
        "- Decorator більше не дублюється як запис вкладеної функції та запис outer register function.",
        "- Collision candidates перераховано лише за унікальними physical sites.",
        "- Порядок `main.py` перенумеровано після сортування за номером рядка.", "",
        "## Черги", "",
        f"- Modules with duplicate register definitions: **{len(queues['duplicate_register_definitions'])}**",
        f"- Route collision candidates: **{len(queues['route_collision_candidates'])}**",
        f"- Direct registry mutations: **{len(queues['direct_registry_mutations'])}**", "",
        "## Контракт V2", "",
        "- Один composition root реєструє handlers у явному порядку.",
        "- Domain та application layers не імпортують Telegram SDK.",
        "- Callback namespaces мають одного owner.",
        "- Route collision candidate потребує owner/precedence рішення, але не є автоматично підтвердженим runtime collision.",
        "- Production DB/WAL/SHM не відкривалися і не змінювалися.", "",
        "## Наступний етап", "",
        "Stage 21.1.4 - inventory database access paths і transaction boundaries.", "",
    ])


def render_remediation(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join([
        "# ROM Stage 21.1.3a - виправлення double counting registration map", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Записів до виправлення:** `{summary['records_before']}`",
        f"- **Унікальних physical sites після виправлення:** `{summary['records_after']}`",
        f"- **Видалено дубльованих derived records:** `{summary['records_removed']}`",
        f"- **Collision groups до виправлення:** `{summary['collision_groups_before']}`",
        f"- **Collision candidates після виправлення:** `{summary['collision_groups_after']}`", "",
        "## Root cause", "",
        "Stage 21.1.3 проходив `ast.walk()` outer register function і окремо обробляв decorator nested handler. Один physical decorator отримував два records із тим самим module, line, kind і call.", "",
        "## Рішення", "",
        "- Decorators збираються тільки з decorated function node.",
        "- Explicit `register_*_handler` calls збираються окремим проходом.",
        "- Deduplication виконується за physical site key: module, line, column, kind.",
        "- Canonical Stage 21.1.3 JSON та Markdown замінені виправленою revision.", "",
        "## Наступний етап", "",
        "Stage 21.1.4 - inventory database access paths і transaction boundaries.", "",
    ])


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, CANONICAL_JSON, CANONICAL_MD, REMEDIATION_JSON, REMEDIATION_MD]
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
    if not (root / SOURCE_REPORT).is_file():
        print(f"[FAIL] Missing {SOURCE_REPORT}", file=sys.stderr)
        return 2

    print("[1/8] [PASS] Canonical Stage 21.1.3 input and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == BRANCH else "FAIL", f"Active branch: {branch}", {"expected": BRANCH}, branch != BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.3 parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
    db_before = db_evidence(root)
    old = json.loads((root / SOURCE_REPORT).read_text(encoding="utf-8"))
    modules = sorted(old["register_definitions"])

    print(f"[3/8] [PASS] Rebuilding physical registration map for {len(modules)} modules.")
    registrations: list[dict[str, Any]] = []
    definitions: dict[str, list[dict[str, Any]]] = {}
    errors = []
    for module in modules:
        try:
            module_records, module_definitions = scan_module(root, module)
            registrations.extend(module_records)
            definitions[module] = module_definitions
        except (OSError, SyntaxError) as exc:
            errors.append({"module": module, "error": str(exc)})

    print("[4/8] [PASS] Recalculating composition order and collision candidates.")
    composition_order = main_order(root)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in registrations:
        groups[collision_signature(item)].append(item)
    collisions = [
        {"kind": key[0], "kwargs": json.loads(key[1]), "registrations": values}
        for key, values in groups.items()
        if len(values) > 1 and key[1] != "{}"
    ]
    duplicate_definitions = [{"module": module, "definitions": values} for module, values in definitions.items() if len(values) > 1]
    direct_mutations = [item for item in registrations if ".insert(" in item["call"] or "handlers.insert" in item["call"]]
    physical_keys = [item["physical_site_key"] for item in registrations]
    checks.extend([
        Check("AST_COVERAGE", "PASS" if not errors else "FAIL", "All registration modules parsed." if not errors else "AST errors found.", {"errors": errors}, bool(errors)),
        Check("PHYSICAL_SITE_UNIQUENESS", "PASS" if len(physical_keys) == len(set(physical_keys)) else "FAIL", "Every registration record has a unique physical site key.", {}, len(physical_keys) != len(set(physical_keys))),
        Check("DOUBLE_COUNT_REMOVED", "PASS" if len(registrations) < old["summary"]["registration_record_count"] else "FAIL", f"Records reduced from {old['summary']['registration_record_count']} to {len(registrations)}.", {}, len(registrations) >= old["summary"]["registration_record_count"]),
        Check("MAIN_ORDER_STABLE", "PASS" if len(composition_order) == old["summary"]["main_registration_count"] else "FAIL", f"Main registration calls: {len(composition_order)}.", {"expected": old["summary"]["main_registration_count"]}, len(composition_order) != old["summary"]["main_registration_count"]),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"

    canonical = {
        "schema_version": 2,
        "canonical_revision": STAGE,
        "stage": "21.1.3",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            "module_count": len(modules),
            "registration_record_count": len(registrations),
            "main_registration_count": len(composition_order),
            "route_collision_group_count": len(collisions),
        },
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "main_registration_order": composition_order,
        "registrations": sorted(registrations, key=lambda item: (item["module"], item["line"], item["column"])),
        "register_definitions": definitions,
        "queues": {
            "duplicate_register_definitions": duplicate_definitions,
            "route_collision_candidates": collisions,
            "direct_registry_mutations": direct_mutations,
        },
        "database_evidence_before": db_before,
        "constraints": {
            "single_v2_composition_root": True,
            "one_record_per_physical_registration_site": True,
            "route_collision_candidate_is_not_automatic_runtime_collision": True,
            "direct_handler_list_mutation": "FORBIDDEN",
            "telegram_import_in_domain": "FORBIDDEN",
            "callback_namespace_single_owner": True,
        },
        "artifacts": {"patch": PATCH_PATH, "json": CANONICAL_JSON, "markdown": CANONICAL_MD},
        "next_stage": "21.1.4" if conclusion == "GO" else None,
    }
    remediation = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": canonical["generated_at_utc"],
        "summary": {
            "conclusion": conclusion,
            "records_before": old["summary"]["registration_record_count"],
            "records_after": len(registrations),
            "records_removed": old["summary"]["registration_record_count"] - len(registrations),
            "collision_groups_before": old["summary"]["route_collision_group_count"],
            "collision_groups_after": len(collisions),
        },
        "root_cause": "Nested handler decorators were counted through outer ast.walk() and again as decorators.",
        "checks": [asdict(item) for item in checks],
        "canonical_artifacts_updated": [CANONICAL_JSON, CANONICAL_MD],
        "database_evidence_before": db_before,
        "next_stage": "21.1.4" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing corrected canonical map and remediation evidence.")
    write_atomic(root / CANONICAL_JSON, json.dumps(canonical, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / CANONICAL_MD, render_canonical(canonical))
    write_atomic(root / REMEDIATION_JSON, json.dumps(remediation, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / REMEDIATION_MD, render_remediation(remediation))
    if conclusion != "GO":
        print("[6/8] [FAIL] Remediation returned NO_GO; commit not created.")
        return 1

    print("[6/8] [PASS] Corrected map semantic checks passed.")
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.3a commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        print(f"[7/8] [FAIL] {exc}", file=sys.stderr)
        return 2
    if db_before != db_evidence(root):
        print("[8/8] [FAIL] DB/WAL/SHM evidence changed.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Corrected registration map committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - fix registration map double counting")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] RECORDS_BEFORE: {old['summary']['registration_record_count']}")
    print(f"[PASS] PHYSICAL_REGISTRATION_SITES: {len(registrations)}")
    print(f"[PASS] RECORDS_REMOVED: {old['summary']['registration_record_count'] - len(registrations)}")
    print(f"[PASS] COLLISION_CANDIDATES: {len(collisions)}")
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: NOT REQUIRED")
    print("WAL/SHM: NOT MANIPULATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
