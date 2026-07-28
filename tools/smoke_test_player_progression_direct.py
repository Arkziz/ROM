#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i4c: Player Progression post-cleanup contracts."""
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

APIS = ("add_exp", "get_user_progress")
CAPTURES = (
    "_legacy_add_exp_before_player_system_v1",
    "_legacy_get_user_progress_before_player_system_v1",
)
TEST_USER_ID = -90120403


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def parse_functions(path):
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text, filename=str(path))
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return text, result


def cleanup(db):
    for table in ("equipment_slots", "inventory", "user_active_contracts", "user_daily_quests"):
        try:
            db.cursor.execute(f"DELETE FROM {table} WHERE user_id=?", (TEST_USER_ID,))
        except Exception:
            pass
    db.cursor.execute("DELETE FROM users WHERE user_id=?", (TEST_USER_ID,))
    db.conn.commit()


def insert_fixture(db, level, exp, stats=10):
    cleanup(db)
    db.cursor.execute(
        """
        INSERT INTO users (
            user_id, hp, max_hp, level, exp, gold, kills, bag_slots,
            current_location, str, dex, intelligence, wis, sta, daily_hunts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            TEST_USER_ID, 170, 170, int(level), int(exp), 12.5, 7, 40,
            "start_path", int(stats), int(stats), int(stats), int(stats), int(stats), 3,
        ),
    )
    db.conn.commit()


def snapshot(db):
    row = db.cursor.execute(
        """
        SELECT level, exp, str, dex, intelligence, wis, sta, max_hp
        FROM users WHERE user_id=?
        """,
        (TEST_USER_ID,),
    ).fetchone()
    return tuple(row) if row is not None else None


def main():
    db_text, db_defs = parse_functions(ROOT / "db.py")
    player_text, player_defs = parse_functions(ROOT / "systems" / "player_system.py")

    for name in APIS:
        if len(db_defs.get(name, [])) != 1:
            fail(f"db.py: {name} definitions={len(db_defs.get(name, []))}, expected 1")
        if len(player_defs.get(name, [])) != 1:
            fail(f"player_system.py: {name} definitions={len(player_defs.get(name, []))}, expected 1")
        db_source = ast.get_source_segment(db_text, db_defs[name][0]) or ""
        player_source = ast.get_source_segment(player_text, player_defs[name][0]) or ""
        if "player_system" not in db_source:
            fail(f"db.{name} is not a player_system wrapper")
        if "_legacy_function" in player_source:
            fail(f"player_system.{name} still depends on _legacy_function")

    for capture in CAPTURES:
        if capture in db_text:
            fail(f"legacy capture text remains: {capture}")

    import db
    from systems import player_system

    for capture in CAPTURES:
        if hasattr(db, capture):
            fail(f"legacy capture is still exported: {capture}")

    required_keys = {"level", "exp", "exp_to_next", "gold", "kills", "daily_hunts"}
    real_rows = db.cursor.execute(
        "SELECT user_id FROM users WHERE user_id>=0 ORDER BY user_id"
    ).fetchall()
    progress_comparisons = 0
    for (user_id,) in real_rows:
        public = db.get_user_progress(user_id)
        direct = player_system.get_user_progress(user_id)
        progress_comparisons += 1
        if public != direct:
            fail(f"progress mismatch for user {user_id}")
        if not isinstance(public, dict) or not required_keys.issubset(public):
            fail(f"progress contract failed for user {user_id}")

    if db.get_user_progress(-987654321) is not None:
        fail("missing-user progress contract failed")

    cases = []
    threshold_1 = int(db.get_exp_to_next_level(1))
    threshold_2 = int(db.get_exp_to_next_level(2))
    cases.append(("no_level_up", 1, 0, max(1, threshold_1 // 2), 0))
    cases.append(("one_level_up", 1, max(0, threshold_1 - 3), 5, 1))
    cases.append(("multiple_level_ups", 1, 0, threshold_1 + threshold_2 + 11, 2))

    try:
        for label, level, exp, amount, expected_level_ups in cases:
            insert_fixture(db, level, exp)
            before = snapshot(db)
            result = db.add_exp(TEST_USER_ID, amount)
            after = snapshot(db)
            if not isinstance(result, dict):
                fail(f"{label}: add_exp result is not dict")
            if int(result.get("level_ups", -1)) != expected_level_ups:
                fail(f"{label}: level_ups mismatch: {result}")
            if after is None or before is None:
                fail(f"{label}: fixture row missing")
            stat_delta = tuple(after[index] - before[index] for index in range(2, 7))
            expected_delta = (expected_level_ups,) * 5
            if stat_delta != expected_delta:
                fail(f"{label}: stat delta {stat_delta}, expected {expected_delta}")
            if int(after[7] or 0) != int(player_system.get_max_hp(TEST_USER_ID)):
                fail(f"{label}: stored max_hp is not synchronized")
            if db.get_user_progress(TEST_USER_ID) != player_system.get_user_progress(TEST_USER_ID):
                fail(f"{label}: public/direct progress mismatch")
    finally:
        cleanup(db)

    leftover = db.cursor.execute(
        "SELECT COUNT(*) FROM users WHERE user_id=?", (TEST_USER_ID,)
    ).fetchone()[0]
    if int(leftover or 0) != 0:
        fail("isolated test user cleanup failed")

    print("[OK] player progression post-cleanup")
    print("- public APIs: 2")
    print("- direct system implementations: 2")
    print("- legacy captures: 0")
    print(f"- get_user_progress comparisons: {progress_comparisons}")
    print("- add_exp contract cases: 3")
    print("- level-up stat increments: OK")
    print("- max HP synchronization: OK")
    print("- missing-user contract: OK")
    print("- isolated test user cleanup: OK")
    print("- real user mutations: 0")


if __name__ == "__main__":
    main()
