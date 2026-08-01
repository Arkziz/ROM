#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import hashlib
import json
import random
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

USER_ID = -101300003


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


class CountingRandom:
    def __init__(self, values):
        self.values = iter(values)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return next(self.values)


def logical_db_fingerprint():
    uri = f"file:{(ROOT / 'game.db').as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        digest = hashlib.sha256()
        tables = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        for table in tables:
            quoted = '"' + str(table).replace('"', '""') + '"'
            rows = [list(row) for row in conn.execute(f"SELECT * FROM {quoted}")]
            rows.sort(key=lambda row: json.dumps(row, ensure_ascii=False, default=str))
            digest.update(json.dumps([table, rows], ensure_ascii=False, default=str).encode("utf-8"))
        return digest.hexdigest()
    finally:
        conn.close()


def cleanup(db):
    # Remove the isolated fixture from every current/future user-owned table.
    # Stage 11 adds systems over time, so a hard-coded three-table cleanup is
    # no longer sufficient for a whole-database logical fingerprint.
    tables = [
        row[0] for row in db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]
    owned = []
    for table in tables:
        try:
            columns = {
                str(row[1]) for row in db.conn.execute(
                    f'PRAGMA table_info("{table}")'
                ).fetchall()
            }
            if "user_id" in columns and table != "users":
                owned.append(table)
        except Exception:
            pass
    # Repeat to tolerate foreign-key dependency order between owned tables.
    for _ in range(3):
        for table in owned:
            quoted = '"' + str(table).replace('"', '""') + '"'
            try:
                db.conn.execute(
                    f"DELETE FROM {quoted} WHERE user_id=?", (USER_ID,)
                )
            except Exception:
                pass
    db.conn.execute("DELETE FROM users WHERE user_id=?", (USER_ID,))
    db.conn.commit()


def compare_legacy_case(name, mob, value):
    from systems.drop_system import roll_central_refine_stone_drop
    from systems.reward_system import (
        ELITE_REFINE_STONE_DROP_CHANCE,
        NORMAL_REFINE_STONE_DROP_CHANCE,
    )

    legacy_rng = CountingRandom((value,))
    central_rng = CountingRandom((value,))
    legacy_chance = (
        ELITE_REFINE_STONE_DROP_CHANCE
        if bool(mob.get("is_elite", False))
        else NORMAL_REFINE_STONE_DROP_CHANCE
    )
    legacy_hit = float(legacy_rng()) <= float(legacy_chance)
    central = roll_central_refine_stone_drop(mob, central_rng)
    if bool(central.get("rolled")) != legacy_hit:
        fail(f"{name}: legacy={legacy_hit}, central={central}")
    if legacy_rng.calls != central_rng.calls or central_rng.calls != 1:
        fail(f"{name}: RNG calls differ")


def main():
    import db
    from data.drop_tables import (
        CENTRAL_DROP_MIGRATED_RULES,
        CENTRAL_DROP_PRODUCTION_ENABLED,
        DROP_RULES_BY_ID,
    )
    from systems.drop_system import (
        get_central_drop_status,
        roll_central_refine_stone_drop,
        validate_drop_tables,
    )
    from systems.reward_system import roll_refine_stone_drop

    before = logical_db_fingerprint()
    rule = DROP_RULES_BY_ID["refine_stone"]
    expected_enemy = {
        "normal": {"chance": 0.08},
        "elite": {"chance": 0.20},
        "boss": {"chance": 0.50},
    }
    if not CENTRAL_DROP_PRODUCTION_ENABLED:
        fail("central production disabled")
    if tuple(CENTRAL_DROP_MIGRATED_RULES) != ("rune", "refine_stone", "equipment", "trophy", "potion"):
        fail(f"migrated rules mismatch: {CENTRAL_DROP_MIGRATED_RULES}")
    if rule["enemy"] != expected_enemy:
        fail(f"refine stone chances mismatch: {rule['enemy']}")
    if not rule.get("production_enabled") or rule.get("item_id") != 401:
        fail(f"refine stone rule contract mismatch: {rule}")
    if rule.get("max_per_kill") != 1 or rule["quantity"] != {"min": 1, "max": 1}:
        fail("quantity/max-per-kill mismatch")
    if not validate_drop_tables()["success"]:
        fail(validate_drop_tables()["errors"])

    # Exact legacy equivalence for normal and elite boundaries.
    for name, mob, value in (
        ("normal hit", {}, 0.08),
        ("normal miss", {}, 0.080001),
        ("elite hit", {"is_elite": True}, 0.20),
        ("elite miss", {"is_elite": True}, 0.200001),
    ):
        compare_legacy_case(name, mob, value)

    # Explicit new boss policy and classifier priority.
    boss_hit = roll_central_refine_stone_drop(
        {"is_boss": True, "is_elite": True}, CountingRandom((0.50,))
    )
    boss_miss = roll_central_refine_stone_drop(
        {"mob_type": "boss"}, CountingRandom((0.500001,))
    )
    if not boss_hit.get("rolled") or boss_hit["enemy_type"] != "boss":
        fail(f"boss 50% hit failed: {boss_hit}")
    if (boss_hit.get("payload") or {}).get("boundary") != "inclusive":
        fail(f"inclusive Refine Stone boundary marker missing: {boss_hit}")
    if boss_miss.get("rolled") or boss_miss["enemy_type"] != "boss":
        fail(f"boss 50% miss failed: {boss_miss}")

    # Statistical range checks.
    for enemy_type, mob, target in (
        ("normal", {}, 0.08),
        ("elite", {"is_elite": True}, 0.20),
        ("boss", {"is_boss": True}, 0.50),
    ):
        rng = random.Random(113000 + len(enemy_type))
        dropped = sum(
            1 for _ in range(100000)
            if roll_central_refine_stone_drop(mob, rng.random).get("rolled")
        )
        actual = dropped / 100000
        if abs(actual - target) > 0.008:
            fail(f"{enemy_type}: actual={actual}, target={target}")

    status = get_central_drop_status()
    if status["production_rules"] != ["equipment", "trophy", "refine_stone", "rune", "potion"]:
        fail(f"production status mismatch: {status}")
    if DROP_RULES_BY_ID["success_rune"].get("production_enabled"):
        fail("Rune of Success was production-enabled")

    # Public award flow: one hit, one stone, no duplicate.
    cleanup(db)
    try:
        db.create_user(USER_ID)
        start = int(db.conn.execute(
            "SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=401",
            (USER_ID,),
        ).fetchone()[0] or 0)
        message = roll_refine_stone_drop(USER_ID, {"is_boss": True}, CountingRandom((0.0,)))
        end = int(db.conn.execute(
            "SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=401",
            (USER_ID,),
        ).fetchone()[0] or 0)
        if end != start + 1 or not message or "Камінь Посилення" not in message:
            fail(f"public award mismatch: start={start}, end={end}, message={message}")
        miss = roll_refine_stone_drop(USER_ID, {"is_boss": True}, CountingRandom((0.9,)))
        final = int(db.conn.execute(
            "SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=401",
            (USER_ID,),
        ).fetchone()[0] or 0)
        if miss is not None or final != end:
            fail("miss path mutated inventory")
    finally:
        cleanup(db)

    if logical_db_fingerprint() != before:
        fail("test fixture residue changed game.db")

    reward_source = (ROOT / "systems" / "reward_system.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(reward_source)
    functions = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "roll_refine_stone_drop"
    ]
    if len(functions) != 1 or "roll_central_refine_stone_drop" not in reward_source:
        fail("final Refine Stone compatibility API missing or duplicated")

    print("[OK] Central drop Refine Stone migration contracts")
    print("- normal chance: 8%")
    print("- elite chance: 20%")
    print("- boss chance: 50%")
    print("- normal/elite legacy boundary equivalence: OK")
    print("- boss priority over elite: OK")
    print("- RNG calls per roll: 1")
    print("- item ID 401, quantity 1, max per kill 1: OK")
    print("- Rune of Success item 402 drops: disabled")
    print("- public award adds exactly one stone: OK")
    print("- production central rules: rune + refine_stone + equipment + trophy + potion")
    print("- real user mutations: 0")


if __name__ == "__main__":
    main()
