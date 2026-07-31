#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def sequence(values):
    iterator = iter(values)
    return lambda: next(iterator)


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


def main():
    from data.drop_tables import (
        CENTRAL_DROP_PRODUCTION_ENABLED, CENTRAL_DROP_MIGRATED_RULES,
        DROP_RULES, DROP_RULES_BY_ID,
    )
    from systems.drop_system import (
        classify_enemy, get_central_drop_status, get_drop_rule,
        resolve_enemy_config, roll_drop_rule, roll_enemy_drops,
        validate_drop_tables, weighted_choice,
    )

    db_before = logical_db_fingerprint()
    validation = validate_drop_tables()
    if not CENTRAL_DROP_PRODUCTION_ENABLED:
        fail("central production must be enabled after 11.2.0")
    if tuple(CENTRAL_DROP_MIGRATED_RULES) != ("rune", "refine_stone", "equipment"):
        fail(f"migrated rules mismatch: {CENTRAL_DROP_MIGRATED_RULES}")
    if not validation["success"]:
        fail(validation["errors"])
    if validation["rule_count"] != 8:
        fail(f"rule count mismatch: {validation}")
    production_rules = [
        rule["rule_id"] for rule in DROP_RULES
        if rule.get("production_enabled")
    ]
    if production_rules != ["equipment", "refine_stone", "rune"]:
        fail(f"production rules mismatch: {production_rules}")

    if classify_enemy({"is_boss": True, "is_elite": True}) != "boss":
        fail("boss priority failed")
    if classify_enemy({"enemy_type": "elite", "is_boss": False}) != "elite":
        fail("elite classification failed")
    if classify_enemy({}) != "normal":
        fail("normal classification failed")

    rune = get_drop_rule("rune")
    if rune != DROP_RULES_BY_ID["rune"] or rune is DROP_RULES_BY_ID["rune"]:
        fail("get_drop_rule must return an equal defensive copy")
    hit = roll_drop_rule(rune, {"is_boss": True}, sequence([0.10, 0.99, 0.99]))
    if not hit["rolled"] or hit["payload"]["level"] != 3 or hit["payload"]["stat"] != "WIS":
        fail(f"boss rune shadow roll mismatch: {hit}")
    miss = roll_drop_rule(rune, {}, sequence([0.05]))
    if miss["rolled"] or miss["reason"] != "chance_miss":
        fail(f"normal rune boundary mismatch: {miss}")

    stone = get_drop_rule("refine_stone")
    if stone["enemy"]["boss"] != {"chance": 0.50}:
        fail(f"explicit boss stone balance mismatch: {stone}")
    from systems.drop_system import roll_central_refine_stone_drop
    boss_hit = roll_central_refine_stone_drop(
        {"is_boss": True, "is_elite": True}, sequence([0.50])
    )
    boss_miss = roll_central_refine_stone_drop(
        {"mob_type": "boss"}, sequence([0.500001])
    )
    if not boss_hit["rolled"] or boss_miss["rolled"]:
        fail(f"boss stone 50% boundary failed: hit={boss_hit}, miss={boss_miss}")
    normal_stone = roll_central_refine_stone_drop({}, sequence([0.08]))
    if not normal_stone["rolled"] or normal_stone["payload"]["item_id"] != 401:
        fail(f"normal stone inclusive boundary failed: {normal_stone}")

    trophy = get_drop_rule("trophy")
    normal_cfg = resolve_enemy_config(trophy, "normal", {"mob": {"loot_chance": 0.58}})
    elite_cfg = resolve_enemy_config(trophy, "elite", {"mob": {"loot_chance": 0.58}})
    if normal_cfg["chance"] != 0.58 or elite_cfg["chance"] != 0.78:
        fail(f"dynamic trophy chance mismatch: {normal_cfg}, {elite_cfg}")

    if weighted_choice((("a", 0.5), ("b", 0.5)), 0.5) != "b":
        fail("weighted boundary mismatch")
    broken = copy.deepcopy(list(DROP_RULES))
    broken[0]["enemy"]["normal"]["chance"] = 1.50
    invalid = validate_drop_tables(broken)
    if invalid["success"] or not invalid["errors"]:
        fail("validator accepted invalid probability")

    all_results = roll_enemy_drops({}, sequence([0.99, 0.99, 0.99, 0.99]))
    if len(all_results) != len(DROP_RULES):
        fail("full table result count mismatch")
    if any(result["awarded"] for result in all_results):
        fail("pure engine awarded a real item")

    status = get_central_drop_status()
    if status["shadow_only"] or status["production_rules"] != ["equipment", "refine_stone", "rune"]:
        fail(f"central status mismatch: {status}")

    reward_source = (ROOT / "systems" / "reward_system.py").read_text(encoding="utf-8-sig")
    if "process_enemy_drops" in reward_source:
        fail("full central victory flow was connected prematurely")
    if "roll_central_refine_stone_drop" not in reward_source:
        fail("targeted refine-stone central delegation missing")

    if logical_db_fingerprint() != db_before:
        fail("pure engine changed game.db")

    print("[OK] Central drop config model contracts")
    print("- schema validation: OK")
    print("- enemy priority boss > elite > normal: OK")
    print("- current rune balance represented exactly: OK")
    print("- refine-stone boss chance: 50% inclusive")
    print("- trophy dynamic chance resolver: OK")
    print("- disabled potion/premium rules: OK")
    print("- migrated production rules: rune + refine_stone + equipment")
    print("- full-table victory integration enabled: no")
    print("- database mutations: 0")
    print("- gameplay drop behavior changed: no")


if __name__ == "__main__":
    main()
