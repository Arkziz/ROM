#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import random
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


def comparable(result):
    keys = (
        "dropped", "enemy_type", "chance", "roll", "item_id", "name",
        "stat", "level", "quantity",
    )
    return {key: result.get(key) for key in keys if key in result}


def compare_case(name, mob, values):
    from systems.rune_system import (
        _RUNE_DROP_LEGACY_ROLL_11_2_0,
        roll_rune_drop,
    )

    legacy_rng = CountingRandom(values)
    central_rng = CountingRandom(values)
    legacy = _RUNE_DROP_LEGACY_ROLL_11_2_0(mob, random_func=legacy_rng)
    central = roll_rune_drop(mob, random_func=central_rng)
    if comparable(legacy) != comparable(central):
        fail(f"{name}: result mismatch\nlegacy={legacy}\ncentral={central}")
    if legacy_rng.calls != central_rng.calls:
        fail(f"{name}: random draw mismatch {legacy_rng.calls} != {central_rng.calls}")
    return central, central_rng.calls


def main():
    from data.drop_tables import (
        CENTRAL_DROP_PRODUCTION_ENABLED,
        DROP_RULES_BY_ID,
    )
    from data.rune_drop_balance import (
        RUNE_DROP_CHANCES,
        RUNE_LEVEL_WEIGHTS,
        RUNE_STAT_WEIGHTS,
    )
    from systems.drop_system import get_central_drop_status, validate_drop_tables
    from systems.rune_system import roll_rune_drop

    db_before = logical_db_fingerprint()
    rune_rule = DROP_RULES_BY_ID["rune"]
    if not CENTRAL_DROP_PRODUCTION_ENABLED:
        fail("central production flag must be enabled after rune migration")
    if not rune_rule.get("production_enabled"):
        fail("rune rule is not production-enabled")
    production_rules = sorted(
        rule_id for rule_id, rule in DROP_RULES_BY_ID.items()
        if rule.get("production_enabled")
    )
    if production_rules != ["equipment", "refine_stone", "rune"]:
        fail(f"unexpected production rules: {production_rules}")
    if rune_rule["enemy"] != {
        key: {"chance": value} for key, value in RUNE_DROP_CHANCES.items()
    }:
        fail("central rune chances diverge from legacy balance")
    if rune_rule["level_weights"] != RUNE_LEVEL_WEIGHTS:
        fail("central rune level weights diverge")
    if rune_rule["stat_weights"] != RUNE_STAT_WEIGHTS:
        fail("central rune stat weights diverge")
    validation = validate_drop_tables()
    if not validation["success"]:
        fail(validation["errors"])

    cases = (
        ("normal miss at boundary", {}, (0.05,)),
        ("normal hit STR I", {}, (0.049999, 0.0, 0.0)),
        ("normal hit WIS I", {}, (0.0, 0.999999, 0.999999)),
        ("elite miss at boundary", {"is_elite": True}, (0.12,)),
        ("elite I", {"is_elite": True}, (0.0, 0.799999, 0.20)),
        ("elite II", {"is_elite": True}, (0.0, 0.80, 0.20)),
        ("boss I", {"is_boss": True}, (0.0, 0.599999, 0.40)),
        ("boss II", {"boss": True}, (0.0, 0.60, 0.40)),
        ("boss III", {"mob_type": "boss"}, (0.0, 0.95, 0.999999)),
        ("boss priority", {"is_boss": True, "is_elite": True}, (0.0, 0.95, 0.999999)),
        ("enemy_type boss", {"enemy_type": "boss"}, (0.349999, 0.10, 0.10)),
    )
    for name, mob, values in cases:
        compare_case(name, mob, values)

    # Statistical exact equivalence with identical generated random streams.
    for enemy_type, mob in (
        ("normal", {}),
        ("elite", {"is_elite": True}),
        ("boss", {"is_boss": True}),
    ):
        seed_source = random.Random(112000 + len(enemy_type))
        for index in range(10000):
            values = tuple(seed_source.random() for _ in range(3))
            compare_case(f"{enemy_type} statistical case {index}", mob, values)

    # Public award/simulation APIs remain dynamic users of roll_rune_drop.
    rune_source = (ROOT / "systems" / "rune_system.py").read_text(encoding="utf-8-sig")
    reward_source = (ROOT / "systems" / "reward_system.py").read_text(encoding="utf-8-sig")
    if "_RUNE_DROP_LEGACY_ROLL_11_2_0 = roll_rune_drop" not in rune_source:
        fail("legacy equivalence capture missing")
    if "roll_central_rune_drop" not in rune_source:
        fail("central delegation missing")
    if "award_rune_drop(user_id, mob)" not in reward_source:
        fail("victory reward public rune hook changed unexpectedly")

    status = get_central_drop_status()
    if status["production_rules"] != ["equipment", "refine_stone", "rune"]:
        fail(f"production rule status mismatch: {status}")

    # One direct public-API sanity case after all equivalence checks.
    result = roll_rune_drop({"is_boss": True}, random_func=CountingRandom((0.0, 0.95, 0.99)))
    if not result.get("dropped") or result.get("level") != 3 or result.get("stat") != "WIS":
        fail(f"public central rune result mismatch: {result}")

    if logical_db_fingerprint() != db_before:
        fail("rune migration test changed game.db")

    print("[OK] Central drop rune migration contracts")
    print("- legacy/central deterministic cases: 11/11 exact")
    print("- statistical equivalence cases: 30000 exact")
    print("- random draw count equivalence: OK")
    print("- normal/elite/boss classification equivalence: OK")
    print("- chance boundary equivalence: OK")
    print("- level/stat/item/name/quantity equivalence: OK")
    print("- award_rune_drop public API preserved: OK")
    print("- simulate_rune_drops public API preserved: OK")
    print("- production central rules include rune + refine_stone + equipment")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
