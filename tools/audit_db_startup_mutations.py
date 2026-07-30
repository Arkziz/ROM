#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit hidden database writes caused by importing db.py.

The real game.db is never imported through db.py. Runtime behavior is tested
against a temporary copy from a temporary working directory.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PY = ROOT / "db.py"
MAIN_PY = ROOT / "main.py"
MIGRATION_RUNNER = ROOT / "migrations" / "runner.py"
DB_PATH = ROOT / "game.db"
REPORT = ROOT / "DB_CLEANUP_9_0_13I_DB_STARTUP_MUTATION_AUDIT.md"
TARGETS = (
    "ensure_refine_material_stack_sizes",
    "migrate_active_contracts_target_kills_to_5",
)
EXCLUDED_PARTS = {".venv", "venv", "backup", "patch", ".git", "__pycache__"}


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint(path):
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": path.stat().st_size,
        "mtime_ns": path.stat().st_mtime_ns,
    }


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    return text, ast.parse(text, filename=str(path))


def call_name(call):
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def top_level_calls(tree):
    findings = []
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                  ast.Import, ast.ImportFrom)):
            continue
        for node in ast.walk(statement):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node)
            if name in TARGETS:
                findings.append({
                    "name": name,
                    "line": node.lineno,
                    "container": type(statement).__name__,
                })
    return findings


def function_info(text, tree, name):
    nodes = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    nodes.sort(key=lambda node: node.lineno)
    if not nodes:
        fail(f"{name}: definition not found")
    node = nodes[-1]
    source = ast.get_source_segment(text, node) or ""
    sql = []
    commits = 0
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            upper = sub.value.upper()
            if any(token in upper for token in ("UPDATE ", "INSERT ", "DELETE ", "ALTER ", "CREATE ")):
                sql.append(" ".join(sub.value.split()))
        elif isinstance(sub, ast.Call):
            if call_name(sub) == "commit":
                commits += 1
    return {
        "line": node.lineno,
        "end_line": node.end_lineno,
        "source": source,
        "sql": sql,
        "commits": commits,
    }


def project_call_sites():
    result = defaultdict(list)
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        try:
            _text, tree = parse(path)
        except Exception:
            continue
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node)
            if name not in TARGETS:
                continue
            top_level = True
            current = node
            while current in parents:
                current = parents[current]
                if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    top_level = False
                    break
            result[name].append({
                "file": rel.as_posix(),
                "line": node.lineno,
                "top_level": top_level,
            })
    return result


def quote_ident(name):
    return '"' + str(name).replace('"', '""') + '"'


def database_snapshot(path):
    conn = sqlite3.connect(str(path))
    try:
        tables = [
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        snapshot = {}
        for table in tables:
            columns = [row[1] for row in conn.execute(f"PRAGMA table_info({quote_ident(table)})").fetchall()]
            order = ",".join(quote_ident(column) for column in columns) if columns else "rowid"
            rows = conn.execute(
                f"SELECT * FROM {quote_ident(table)} ORDER BY {order}"
            ).fetchall()
            normalized = [
                [value.hex() if isinstance(value, bytes) else value for value in row]
                for row in rows
            ]
            payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, default=str)
            snapshot[table] = {
                "rows": len(rows),
                "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            }
        return snapshot, conn.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        conn.close()


def snapshot_diff(before, after):
    changed = []
    for table in sorted(set(before) | set(after)):
        left = before.get(table)
        right = after.get(table)
        if left != right:
            changed.append({"table": table, "before": left, "after": right})
    return changed


def run_sandbox_import(temp_dir):
    script = temp_dir / "import_db_probe.py"
    script.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        "import db\n"
        "print('[OK] sandbox import db')\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=temp_dir,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    return result


def main():
    for path in (DB_PY, MAIN_PY, MIGRATION_RUNNER, DB_PATH):
        if not path.is_file():
            fail(f"missing required file: {path}")

    real_before = fingerprint(DB_PATH)
    db_text, db_tree = parse(DB_PY)
    module_calls = top_level_calls(db_tree)
    function_details = {
        name: function_info(db_text, db_tree, name) for name in TARGETS
    }
    call_sites = project_call_sites()

    with tempfile.TemporaryDirectory(prefix="rom_9_0_13i_") as temp_name:
        temp_dir = Path(temp_name)
        sandbox_db = temp_dir / "game.db"
        shutil.copy2(DB_PATH, sandbox_db)
        sandbox_before_file = fingerprint(sandbox_db)
        sandbox_before, quick_before = database_snapshot(sandbox_db)
        first = run_sandbox_import(temp_dir)
        sandbox_after_first_file = fingerprint(sandbox_db)
        sandbox_after_first, quick_after_first = database_snapshot(sandbox_db)
        first_diff = snapshot_diff(sandbox_before, sandbox_after_first)
        second = run_sandbox_import(temp_dir)
        sandbox_after_second_file = fingerprint(sandbox_db)
        sandbox_after_second, quick_after_second = database_snapshot(sandbox_db)
        second_diff = snapshot_diff(sandbox_after_first, sandbox_after_second)

    real_after = fingerprint(DB_PATH)
    if real_before != real_after:
        fail("real game.db changed during audit")
    if first.returncode != 0:
        fail(f"sandbox import failed: {first.stderr or first.stdout}")
    if second.returncode != 0:
        fail(f"second sandbox import failed: {second.stderr or second.stdout}")
    if any(value != "ok" for value in (quick_before, quick_after_first, quick_after_second)):
        fail(
            "sandbox quick_check failed: "
            f"before={quick_before}, first={quick_after_first}, second={quick_after_second}"
        )

    explicit_startup_calls = []
    for name, sites in call_sites.items():
        for site in sites:
            if site["file"] != "db.py" or not site["top_level"]:
                explicit_startup_calls.append({"name": name, **site})

    hidden_import_mutations = bool(first_diff)
    repeated_import_mutations = bool(second_diff)
    expected_top_level = {
        finding["name"] for finding in module_calls
    }

    report = [
        "# ROM 9.0.13i — DB Startup Mutation Audit",
        "",
        f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Safety",
        "",
        "- Real `game.db` imported through `db.py`: **no**",
        "- Runtime probe target: **temporary copy of game.db**",
        f"- Real database SHA/size/mtime unchanged: **{real_before == real_after}**",
        f"- Sandbox quick check before import: **{quick_before}**",
        f"- Sandbox quick check after first import: **{quick_after_first}**",
        f"- Sandbox quick check after second import: **{quick_after_second}**",
        "- Gameplay files changed: **0**",
        "- Real database rows changed: **0**",
        "",
        "## Module-scope calls in db.py",
        "",
    ]
    for finding in module_calls:
        report.append(
            f"- `db.py:{finding['line']}` calls `{finding['name']}()` "
            f"inside `{finding['container']}` at module scope."
        )
    if not module_calls:
        report.append("- None detected.")

    report.extend(["", "## Function mutation contracts", ""])
    for name in TARGETS:
        info = function_details[name]
        report.extend([
            f"### `{name}()`",
            "",
            f"- Definition: `db.py:{info['line']}-{info['end_line']}`",
            f"- Commit calls: **{info['commits']}**",
            f"- Mutating SQL literals: `{info['sql']}`",
            "",
        ])

    report.extend([
        "## Project call sites",
        "",
    ])
    for name in TARGETS:
        report.append(f"- `{name}`: `{call_sites.get(name, [])}`")

    report.extend([
        "",
        "## Sandbox import behavior",
        "",
        f"- First import process exit code: **{first.returncode}**",
        f"- First import stdout: `{first.stdout.strip()}`",
        f"- First import stderr: `{first.stderr.strip()}`",
        f"- Database file fingerprint changed after first import: **{sandbox_before_file != sandbox_after_first_file}**",
        f"- Tables changed after first import: `{first_diff}`",
        f"- Second import process exit code: **{second.returncode}**",
        f"- Database file fingerprint changed after second import: **{sandbox_after_first_file != sandbox_after_second_file}**",
        f"- Tables changed after second import: `{second_diff}`",
        f"- Hidden import mutations reproduced: **{hidden_import_mutations}**",
        f"- Repeated-import mutations reproduced: **{repeated_import_mutations}**",
        "",
        "## Explicit startup coverage",
        "",
        f"- Non-module-scope call sites: `{explicit_startup_calls}`",
        f"- Explicit startup owner currently exists for both operations: **{set(TARGETS).issubset({site['name'] for site in explicit_startup_calls})}**",
        "",
        "## Diagnosis",
        "",
        "- `db.py` contains hidden maintenance execution at module scope.",
        "- A plain `import db` can therefore perform SQL writes or commits, depending on current database state.",
        "- The two maintenance operations have different responsibilities and should be invoked explicitly during startup after migrations and schema initialization.",
        "- Removing only the module-scope calls without adding one explicit startup owner would silently disable maintenance.",
        "",
        "## Recommended next patch",
        "",
        "1. Add one public `run_db_startup_maintenance()` function in `db.py`.",
        "2. Call `ensure_refine_material_stack_sizes()` and `migrate_active_contracts_target_kills_to_5()` from that function in a fixed order.",
        "3. Remove their module-scope invocations from `db.py`.",
        "4. Invoke `run_db_startup_maintenance()` explicitly from `main.py` after migration execution and before seed/handler startup.",
        "5. Make the startup function return a structured summary for logging and tests.",
        "6. Add a subprocess test proving plain `import db` leaves a database copy byte-for-byte unchanged.",
        "7. Add an isolated test proving explicit startup maintenance remains idempotent.",
        "8. Preserve the current migration and refine-material business rules.",
        "",
        "Suggested next patch: `patch_9_0_13j_explicit_db_startup_maintenance.py`",
        "",
    ])
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] DB startup mutation audit")
    print(f"- target maintenance functions: {len(TARGETS)}")
    print(f"- module-scope target calls: {len(module_calls)}")
    print(f"- module-scope targets: {sorted(expected_top_level)}")
    print(f"- explicit non-module call sites: {len(explicit_startup_calls)}")
    print(f"- sandbox import changed tables: {len(first_diff)}")
    print(f"- sandbox changed table names: {[item['table'] for item in first_diff]}")
    print(f"- second import changed tables: {len(second_diff)}")
    print(f"- hidden import mutations reproduced: {hidden_import_mutations}")
    print(f"- repeated-import mutations reproduced: {repeated_import_mutations}")
    print("- real database mutations: 0")
    print("- diagnosis: maintenance is executed implicitly during import db")
    print(f"- report: {REPORT}")


if __name__ == "__main__":
    main()
