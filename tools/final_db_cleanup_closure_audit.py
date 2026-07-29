#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12 final closure audit.

This tool does not alter gameplay code. It validates the final cleanup state,
runs the approved post-cleanup contract suite, checks for leaked fixture rows,
and writes DB_CLEANUP_9_0_12_FINAL_CLOSURE.md.
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPORT = ROOT / "DB_CLEANUP_9_0_12_FINAL_CLOSURE.md"
READINESS = ROOT / "tools" / "db_cleanup_readiness.py"

# Curated final-state suites only. Historical pre-cleanup audits are intentionally
# excluded because their structural expectations describe earlier migration stages.
TESTS = (
    "smoke_test_character_mutation_contracts.py",
    "smoke_test_player_contracts.py",
    "smoke_test_player_progression_direct.py",
    "smoke_test_player_combat_stats.py",
    "smoke_test_energy_contracts.py",
    "smoke_test_regen_contracts.py",
    "smoke_test_equipment_class_compatibility.py",
    "smoke_test_equipment_readonly_core.py",
    "smoke_test_equipment_write_contracts.py",
    "smoke_test_equipment_durability_contracts.py",
    "smoke_test_equipment_trader_contracts.py",
    "smoke_test_dynamic_equipment_repair_contracts.py",
    "smoke_test_inventory_refine_contracts.py",
    "smoke_test_weapon_damage_contracts.py",
    "smoke_test_contract_contracts.py",
    "smoke_test_contract_reward_direct_facade.py",
    "smoke_test_auction_lifecycle_contracts.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)

FORBIDDEN_IDENTIFIERS = (
    "_base_claim_contract_reward_before_guild_reward_v1",
    "_guild_contract_reward_result_success_v1",
    "_guild_contract_reward_append_message_v1",
)


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def parse_python(path):
    text = path.read_text(encoding="utf-8-sig")
    return text, ast.parse(text, filename=str(path))


def top_level_definitions(tree):
    definitions = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.setdefault(node.name, []).append(node)
    return definitions


VOLATILE_USER_COLUMNS = {
    # Runtime smoke tests intentionally synchronize derived HP and regeneration state.
    "hp",
    "max_hp",
    "last_hp_regen_update",
    "hp_full_notified",
    "last_regen_at",
    "energy",
    "last_energy_update",
    "energy_full_notified",
}


def users_snapshot(db, include_volatile=False):
    all_columns = [row[1] for row in db.conn.execute("PRAGMA table_info(users)").fetchall()]
    columns = [
        name for name in all_columns
        if include_volatile or name not in VOLATILE_USER_COLUMNS
    ]
    select_list = ",".join(f'"{name}"' for name in columns)
    rows = [
        tuple(row)
        for row in db.conn.execute(
            f"SELECT {select_list} FROM users WHERE user_id>=0 ORDER BY user_id"
        ).fetchall()
    ]
    return columns, rows


def volatile_user_changes(before, after):
    before_columns, before_rows = before
    after_columns, after_rows = after
    if before_columns != after_columns:
        return ["volatile schema changed"]
    before_map = {row[before_columns.index("user_id")]: row for row in before_rows}
    after_map = {row[after_columns.index("user_id")]: row for row in after_rows}
    changes = []
    for user_id in sorted(set(before_map) | set(after_map)):
        if user_id not in before_map or user_id not in after_map:
            changes.append(f"user set changed for {user_id}")
            continue
        for index, column in enumerate(before_columns):
            if before_map[user_id][index] != after_map[user_id][index]:
                changes.append(f"user_id={user_id} column={column}")
    return changes


def negative_fixture_counts(db):
    result = {}
    tables = [
        row[0]
        for row in db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]
    for table in tables:
        try:
            columns = {
                row[1] for row in db.conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            }
            if "user_id" not in columns:
                continue
            count = int(
                db.conn.execute(
                    f'SELECT COUNT(*) FROM "{table}" WHERE user_id<0'
                ).fetchone()[0]
                or 0
            )
            if count:
                result[table] = count
        except Exception:
            continue
    return result


def run_capture(path):
    env = os.environ.copy()
    # Force UTF-8 for every child test, independent of the current PowerShell session.
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    print(output, end="" if output.endswith("\n") or not output else "\n")
    return result.returncode, output


def main():
    db_path = ROOT / "db.py"
    tools = ROOT / "tools"

    if not db_path.is_file():
        fail("db.py not found")
    if not READINESS.is_file():
        fail("tools/db_cleanup_readiness.py not found")

    missing_tests = [name for name in TESTS if not (tools / name).is_file()]
    if missing_tests:
        fail(f"missing final test files: {missing_tests}")

    db_text, db_tree = parse_python(db_path)
    definitions = top_level_definitions(db_tree)
    duplicates = {
        name: [node.lineno for node in nodes]
        for name, nodes in definitions.items()
        if len(nodes) > 1
    }
    if duplicates:
        fail(f"top-level duplicates remain: {duplicates}")

    for identifier in FORBIDDEN_IDENTIFIERS:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(identifier)}(?![A-Za-z0-9_])", db_text):
            fail(f"obsolete identifier remains in db.py: {identifier}")

    claim_nodes = definitions.get("claim_contract_reward", [])
    if len(claim_nodes) != 1:
        fail(f"claim_contract_reward definitions={len(claim_nodes)}, expected 1")
    claim_source = ast.get_source_segment(db_text, claim_nodes[0]) or ""
    if "systems.contract_system" not in claim_source:
        fail("claim_contract_reward is not the final Contract System facade")

    # Import only after structural checks.
    import db

    users_before = users_snapshot(db, include_volatile=False)
    volatile_before = users_snapshot(db, include_volatile=True)
    negative_before = negative_fixture_counts(db)
    if negative_before:
        fail(f"negative fixture rows exist before closure tests: {negative_before}")

    test_results = []
    for test_name in TESTS:
        code, output = run_capture(tools / test_name)
        summary = "PASS" if code == 0 else f"FAIL ({code})"
        test_results.append((test_name, summary, output))
        if code != 0:
            fail(f"final suite failed: {test_name}, exit code {code}")

    readiness_code, readiness_output = run_capture(READINESS)
    if readiness_code != 0:
        fail(f"readiness failed with exit code {readiness_code}")

    expected_readiness = (
        "definitions: 348",
        "duplicates: 0",
        "legacy_refs: 0",
        "unsafe_delete: 0",
        "maybe_cleanup_later: 0",
    )
    for expected in expected_readiness:
        if expected not in readiness_output:
            fail(f"readiness missing expected value: {expected}")

    users_after = users_snapshot(db, include_volatile=False)
    if users_before != users_after:
        fail("stable real-user fields changed during final closure suite")

    volatile_after = users_snapshot(db, include_volatile=True)
    volatile_changes = volatile_user_changes(volatile_before, volatile_after)
    disallowed_volatile = [
        item for item in volatile_changes
        if not any(f"column={column}" in item for column in VOLATILE_USER_COLUMNS)
    ]
    if disallowed_volatile:
        fail(f"unexpected real-user changes detected: {disallowed_volatile}")

    negative_after = negative_fixture_counts(db)
    if negative_after:
        fail(f"fixture rows leaked after closure tests: {negative_after}")

    generated_at = datetime.now().isoformat(timespec="seconds")
    report = [
        "# ROM 9.0.12 — Final DB Cleanup Closure",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Final status",
        "",
        "**ROM 9.0.12 DB cleanup: COMPLETE**",
        "",
        "- Top-level definitions in `db.py`: **348**",
        "- Duplicate definition names: **0**",
        "- Legacy references: **0**",
        "- Unsafe-delete candidates: **0**",
        "- Deferred cleanup candidates: **0**",
        "- Obsolete Contract Reward capture/helpers: **0**",
        "- Negative fixture rows before tests: **0**",
        "- Negative fixture rows after tests: **0**",
        "- Stable real-user field mutations during closure suite: **0**",
        f"- Allowed derived/volatile user-field synchronizations: **{len(volatile_changes)}**",
        "",
        "## Final Contract Reward architecture",
        "",
        "- `db.claim_contract_reward()` is a single public facade.",
        "- Runtime implementation lives in `systems.contract_system`.",
        "- Base reward, EXP, daily counter, Guild reward, and repeat-claim protection are contract-tested.",
        "",
        "## Final verification suite",
        "",
    ]
    for test_name, status, _output in test_results:
        report.append(f"- `{test_name}` — **{status}**")
    report.extend([
        "- `db_cleanup_readiness.py` — **PASS**",
        "",
        "## Closure decision",
        "",
        "The duplicate-removal program is closed. Historical audit and patch files may remain for traceability, but no further duplicate cleanup is required for ROM 9.0.12.",
        "",
        "Future functional refactors should start under a new versioned plan and must not reuse the completed 9.0.12 cleanup sequence.",
        "",
    ])
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] ROM 9.0.12 final DB cleanup closure")
    print("- definitions: 348")
    print("- duplicates: 0")
    print("- legacy refs: 0")
    print("- unsafe delete: 0")
    print("- deferred cleanup: 0")
    print(f"- final suites passed: {len(TESTS)}")
    print("- fixture leaks: 0")
    print("- stable real user mutations: 0")
    print(f"- allowed volatile field synchronizations: {len(volatile_changes)}")
    print("- status: COMPLETE")
    print(f"- report: {REPORT}")


if __name__ == "__main__":
    main()
