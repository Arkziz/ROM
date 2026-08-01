#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


class CountingRandom:
    def __init__(self):
        self.calls = 0
    def __call__(self):
        self.calls += 1
        return 0.0


def main():
    from data.drop_tables import (
        CENTRAL_DROP_MIGRATED_RULES,
        DROP_RULES,
        DROP_RULES_BY_ID,
        SPECIAL_MATERIAL_MOB_DROP_DENYLIST,
        SPECIAL_MATERIAL_SOURCE_POLICY,
    )
    from systems.drop_system import (
        assert_item_allowed_for_enemy_drop,
        roll_drop_rule,
        validate_drop_tables,
        validate_special_material_drop_policy,
    )

    if tuple(CENTRAL_DROP_MIGRATED_RULES) != (
        "rune", "refine_stone", "equipment", "trophy", "potion"
    ):
        fail(f"migrated rules changed unexpectedly: {CENTRAL_DROP_MIGRATED_RULES}")
    if SPECIAL_MATERIAL_MOB_DROP_DENYLIST != frozenset((402, 527, 528)):
        fail(f"denylist mismatch: {SPECIAL_MATERIAL_MOB_DROP_DENYLIST}")
    expected_sources = {
        402: "future_crystal_shop",
        527: "rune_master_gold_shop",
        528: "future_crystal_shop",
    }
    for item_id, source in expected_sources.items():
        if SPECIAL_MATERIAL_SOURCE_POLICY[item_id]["primary_source"] != source:
            fail(f"source mismatch for {item_id}")

    validation = validate_drop_tables()
    if not validation["success"]:
        fail(validation["errors"])
    policy = validate_special_material_drop_policy()
    if not policy["success"] or policy["checked_items"] != [402, 527, 528]:
        fail(policy)

    # Disabled rules must consume zero RNG values and produce zero drops for
    # every enemy category, even across a large simulated sample.
    for rule_id in ("success_rune", "simple_extractor", "perfect_extractor"):
        rule = DROP_RULES_BY_ID[rule_id]
        if rule.get("enabled") or rule.get("production_enabled"):
            fail(f"{rule_id} unexpectedly enabled")
        rng = CountingRandom()
        for mob in ({}, {"is_elite": True}, {"is_boss": True}):
            for _ in range(100000):
                result = roll_drop_rule(rule, mob, rng)
                if result.get("rolled") or result.get("reason") != "rule_disabled":
                    fail(f"protected rule produced a drop: {rule_id}, {result}")
        if rng.calls != 0:
            fail(f"disabled rule consumed RNG: {rule_id}, calls={rng.calls}")

    # Validator must reject accidental activation or nonzero protected chance.
    broken = copy.deepcopy(list(DROP_RULES))
    next(rule for rule in broken if rule["rule_id"] == "success_rune")["enabled"] = True
    if validate_drop_tables(broken)["success"]:
        fail("validator accepted enabled Rune of Success")
    broken = copy.deepcopy(list(DROP_RULES))
    next(rule for rule in broken if rule["rule_id"] == "perfect_extractor")["enemy"]["boss"]["chance"] = 0.01
    if validate_drop_tables(broken)["success"]:
        fail("validator accepted Perfect Extractor boss chance")
    broken = copy.deepcopy(list(DROP_RULES))
    simple = next(rule for rule in broken if rule["rule_id"] == "simple_extractor")
    simple["enabled"] = True
    simple["production_enabled"] = True
    if validate_drop_tables(broken)["success"]:
        fail("validator accepted enabled Simple Extractor candidate")

    for item_id in (402, 527, 528):
        try:
            assert_item_allowed_for_enemy_drop(item_id)
        except ValueError:
            pass
        else:
            fail(f"deny guard accepted protected item {item_id}")
    if not assert_item_allowed_for_enemy_drop(401):
        fail("deny guard rejected Refine Stone")

    # Confirm protected item definitions still exist in the real item catalog.
    conn = sqlite3.connect(f"file:{(ROOT / 'game.db').as_posix()}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        rows = conn.execute(
            "SELECT id FROM items WHERE id IN (402,527,528) ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    if [row[0] for row in rows] != [402, 527, 528]:
        fail(f"protected item definitions missing: {rows}")

    print("[OK] Special material drop policy contracts")
    print("- item 402 Rune of Success: mob drop disabled, future crystal shop")
    print("- item 527 Simple Extractor: mob drop disabled, Rune Master gold shop")
    print("- item 528 Perfect Extractor: mob drop disabled, future crystal shop")
    print("- disabled simulations: 900000 rolls, 0 drops, 0 RNG calls")
    print("- accidental enable/chance validator guards: OK")
    print("- fail-closed enemy-drop item guard: OK")
    print("- current migrated production rules unchanged")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
