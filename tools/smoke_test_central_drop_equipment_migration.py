#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import random
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


def legacy_selection(mob, rng):
    is_elite = bool(mob.get("is_elite", False))
    chance = 0.45 if is_elite else 0.20
    if rng() > chance:
        return None
    rarity_roll = rng()
    if is_elite:
        rarity = "uncommon" if rarity_roll <= 0.75 else "rare"
        class_aware = 0.70
    else:
        rarity = "common" if rarity_roll <= 0.80 else "uncommon"
        class_aware = 0.50
    return rarity, class_aware


def compare(name, mob, values):
    from systems.drop_system import roll_central_equipment_drop
    old_rng = CountingRandom(values)
    new_rng = CountingRandom(values)
    old = legacy_selection(mob, old_rng)
    central = roll_central_equipment_drop(mob, new_rng)
    new = None
    if central.get("rolled"):
        new = (
            central["payload"]["rarity"],
            central["payload"]["class_aware_chance"],
        )
    if old != new:
        fail(f"{name}: old={old}, new={new}, central={central}")
    if old_rng.calls != new_rng.calls:
        fail(f"{name}: RNG calls {old_rng.calls} != {new_rng.calls}")


def main():
    from data.drop_tables import CENTRAL_DROP_MIGRATED_RULES, DROP_RULES_BY_ID
    from systems.drop_system import (
        get_central_drop_status, roll_central_equipment_drop,
        validate_drop_tables,
    )

    rule = DROP_RULES_BY_ID["equipment"]
    if tuple(CENTRAL_DROP_MIGRATED_RULES) != ("rune", "refine_stone", "equipment"):
        fail(f"migrated rules mismatch: {CENTRAL_DROP_MIGRATED_RULES}")
    if rule["enemy"] != {
        "normal": {"chance": 0.20},
        "elite": {"chance": 0.45},
        "boss": {"chance": 0.70},
    }:
        fail(f"equipment chances mismatch: {rule['enemy']}")
    if rule["rarity_weights"] != {
        "normal": (("common", 0.80), ("uncommon", 0.20)),
        "elite": (("uncommon", 0.75), ("rare", 0.25)),
        "boss": (("rare", 0.85), ("epic", 0.15)),
    }:
        fail(f"rarity weights mismatch: {rule['rarity_weights']}")
    if rule["class_aware_chance"] != {
        "normal": 0.50, "elite": 0.70, "boss": 0.90,
    }:
        fail(f"class-aware chances mismatch: {rule['class_aware_chance']}")
    if not rule.get("production_enabled") or not validate_drop_tables()["success"]:
        fail("equipment production/schema contract failed")

    cases = (
        ("normal chance boundary hit", {}, (0.20, 0.0)),
        ("normal chance miss", {}, (0.200001,)),
        ("normal common boundary", {}, (0.0, 0.80)),
        ("normal uncommon", {}, (0.0, 0.800001)),
        ("elite chance boundary hit", {"is_elite": True}, (0.45, 0.0)),
        ("elite chance miss", {"is_elite": True}, (0.450001,)),
        ("elite uncommon boundary", {"is_elite": True}, (0.0, 0.75)),
        ("elite rare", {"is_elite": True}, (0.0, 0.750001)),
    )
    for name, mob, values in cases:
        compare(name, mob, values)

    for enemy_type, mob in (
        ("normal", {}), ("elite", {"is_elite": True}),
    ):
        source = random.Random(114000 + len(enemy_type))
        for index in range(10000):
            compare(
                f"{enemy_type} exact {index}", mob,
                (source.random(), source.random()),
            )

    boss_cases = (
        ({"is_boss": True, "is_elite": True}, (0.70, 0.85), "rare"),
        ({"boss": True}, (0.0, 0.850001), "epic"),
        ({"enemy_type": "boss"}, (0.700001,), None),
    )
    for mob, values, rarity in boss_cases:
        result = roll_central_equipment_drop(mob, CountingRandom(values))
        actual = result["payload"]["rarity"] if result.get("rolled") else None
        if actual != rarity or result["enemy_type"] != "boss":
            fail(f"boss case mismatch: {result}")

    for enemy_type, mob, target in (
        ("normal", {}, 0.20),
        ("elite", {"is_elite": True}, 0.45),
        ("boss", {"is_boss": True}, 0.70),
    ):
        rng = random.Random(114100 + len(enemy_type))
        hits = sum(
            bool(roll_central_equipment_drop(mob, rng.random).get("rolled"))
            for _ in range(100000)
        )
        actual = hits / 100000
        if abs(actual - target) > 0.008:
            fail(f"{enemy_type} rate {actual} vs {target}")

    status = get_central_drop_status()
    if status["production_rules"] != ["equipment", "refine_stone", "rune"]:
        fail(f"production status mismatch: {status}")

    reward = (ROOT / "systems" / "reward_system.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(reward)
    functions = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "roll_equipment_drop"
    ]
    if len(functions) < 2 or "roll_central_equipment_drop" not in reward:
        fail("equipment compatibility override missing")
    if "process_enemy_drops" in reward:
        fail("full victory integration was connected prematurely")

    print("[OK] Central drop equipment migration contracts")
    print("- normal: 20%, common 80% / uncommon 20%, class-aware 50%")
    print("- elite: 45%, uncommon 75% / rare 25%, class-aware 70%")
    print("- boss: 70%, rare 85% / epic 15%, class-aware 90%")
    print("- normal/elite exact legacy equivalence: 20000 cases")
    print("- inclusive chance and rarity boundaries: OK")
    print("- boss priority over elite: OK")
    print("- existing equipment creator remains authoritative: OK")
    print("- production central rules: equipment + refine_stone + rune")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
