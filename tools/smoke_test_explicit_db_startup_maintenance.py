#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contracts for explicit DB startup maintenance ownership."""
from __future__ import annotations

import ast
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "game.db"
DB_PY = ROOT / "db.py"
MAIN_PY = ROOT / "main.py"
TARGETS = (
    "ensure_refine_material_stack_sizes",
    "migrate_active_contracts_target_kills_to_5",
)


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint(path):
    return (
        hashlib.sha256(path.read_bytes()).hexdigest(),
        path.stat().st_size,
        path.stat().st_mtime_ns,
    )


def call_name(node):
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def module_scope_target_calls(tree):
    findings = []
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                  ast.Import, ast.ImportFrom)):
            continue
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and call_name(node) in TARGETS:
                findings.append((call_name(node), node.lineno))
    return findings


def run_import(temp_dir):
    probe = temp_dir / "probe.py"
    probe.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        "import db\n"
        "print('[OK] import db without explicit maintenance')\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(probe)], cwd=temp_dir, env=env,
        text=True, encoding="utf-8", errors="replace",
        capture_output=True, check=False,
    )
    return result


def main():
    real_before = fingerprint(DB_PATH)
    db_source = DB_PY.read_text(encoding="utf-8-sig")
    db_tree = ast.parse(db_source, filename=str(DB_PY))
    main_source = MAIN_PY.read_text(encoding="utf-8-sig")
    main_tree = ast.parse(main_source, filename=str(MAIN_PY))

    hidden = module_scope_target_calls(db_tree)
    if hidden:
        fail(f"module-scope maintenance calls remain: {hidden}")

    runners = [
        node for node in db_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "run_db_startup_maintenance"
    ]
    if len(runners) != 1:
        fail(f"run_db_startup_maintenance definitions={len(runners)}, expected 1")
    runner_source = ast.get_source_segment(db_source, runners[0]) or ""
    positions = [runner_source.find(name + "()") for name in TARGETS]
    if min(positions) < 0 or positions != sorted(positions):
        fail(f"maintenance call order invalid: {positions}")
    if 'result["success"] = True' not in runner_source or "return result" not in runner_source:
        fail("structured startup summary contract missing")

    imports = [
        node for node in main_tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "db"
    ]
    imported = {
        alias.asname or alias.name for node in imports for alias in node.names
    }
    if "run_db_startup_maintenance" not in imported:
        fail("main.py does not import run_db_startup_maintenance")

    startup_calls = [
        node for node in main_tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_db_startup_maintenance_result" for target in node.targets)
        and isinstance(node.value, ast.Call)
        and call_name(node.value) == "run_db_startup_maintenance"
    ]
    if len(startup_calls) != 1:
        fail(f"explicit startup calls={len(startup_calls)}, expected 1")
    startup_line = startup_calls[0].lineno
    seed_lines = [
        node.lineno for node in main_tree.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and call_name(node.value) in {"seed_items", "seed_location_trash_items"}
    ]
    migration_lines = [
        node.lineno for node in ast.walk(main_tree)
        if isinstance(node, ast.Call) and call_name(node) == "run_pending_migrations"
    ]
    if not seed_lines or startup_line >= min(seed_lines):
        fail("explicit maintenance is not before item seeding")
    if migration_lines and startup_line <= max(migration_lines):
        fail("explicit maintenance is not after migration execution")

    # Import must not invoke either maintenance function.  A byte-for-byte copy
    # is used so all writes, if any, stay outside the real project database.
    with tempfile.TemporaryDirectory(prefix="rom_9_0_13j_") as temp_name:
        temp_dir = Path(temp_name)
        sandbox_db = temp_dir / "game.db"
        shutil.copy2(DB_PATH, sandbox_db)
        sandbox_before = fingerprint(sandbox_db)
        imported_result = run_import(temp_dir)
        sandbox_after = fingerprint(sandbox_db)
        if imported_result.returncode != 0:
            fail(f"sandbox import failed: {imported_result.stderr or imported_result.stdout}")
        if sandbox_before != sandbox_after:
            fail("plain import db changed the sandbox database file")

    # Pure call-order and structured-result probe.  The real implementations are
    # temporarily replaced, so no real database mutation is possible here.
    import db
    original_refine = db.ensure_refine_material_stack_sizes
    original_contract = db.migrate_active_contracts_target_kills_to_5
    calls = []
    try:
        db.ensure_refine_material_stack_sizes = lambda: calls.append("refine") or {"updated": 0}
        db.migrate_active_contracts_target_kills_to_5 = lambda: calls.append("contract") or {"updated": 0}
        first = db.run_db_startup_maintenance()
        second = db.run_db_startup_maintenance()
    finally:
        db.ensure_refine_material_stack_sizes = original_refine
        db.migrate_active_contracts_target_kills_to_5 = original_contract

    if calls != ["refine", "contract", "refine", "contract"]:
        fail(f"explicit maintenance order/idempotent invocation failed: {calls}")
    for result in (first, second):
        if result.get("success") is not True:
            fail(f"startup summary success contract failed: {result}")
        if set(result) != {"success", "refine_material_stack_sizes", "contract_target_kills"}:
            fail(f"startup summary keys changed: {result}")

    if real_before != fingerprint(DB_PATH):
        fail("real game.db changed during tests")

    print("[OK] explicit DB startup maintenance contracts")
    print("- module-scope target calls: 0")
    print("- plain import db database changes: 0")
    print("- explicit startup owner in main.py: exactly 1")
    print("- startup order: migrations -> maintenance -> seeds")
    print("- maintenance order: refine stacks -> contract targets")
    print("- structured summary contract: OK")
    print("- repeated explicit invocation contract: OK")
    print("- real database mutations during tests: 0")


if __name__ == "__main__":
    main()
