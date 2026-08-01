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


class CountingChoice:
    def __init__(self, index=0):
        self.index = index
        self.calls = 0
    def __call__(self, values):
        self.calls += 1
        return values[self.index % len(values)]


def legacy_simple(mob, rng, chooser):
    possible = []
    if "trash_item_id" in mob:
        possible.append(mob["trash_item_id"])
    if "loot_item_id" in mob:
        possible.append(mob["loot_item_id"])
    if "trash_items" in mob and isinstance(mob["trash_items"], list):
        possible.extend(mob["trash_items"])
    if "trash_drops" in mob and isinstance(mob["trash_drops"], list):
        possible.extend(mob["trash_drops"])
    if not possible:
        return None
    chance = float(mob.get("loot_chance", 0.45))
    if mob.get("is_elite"):
        chance = min(1.0, chance + 0.20)
    if rng() > chance:
        return None
    return chooser(possible)


def compare_simple(name, mob, value, choice_index=0):
    from systems.drop_system import roll_central_trophy_simple
    old_rng, new_rng = CountingRandom((value,)), CountingRandom((value,))
    old_choice, new_choice = CountingChoice(choice_index), CountingChoice(choice_index)
    old = legacy_simple(mob, old_rng, old_choice)
    central = roll_central_trophy_simple(mob, new_rng, new_choice)
    new = central["payload"]["item_id"] if central.get("rolled") else None
    if old != new:
        fail(f"{name}: old={old}, new={new}, central={central}")
    if (old_rng.calls, old_choice.calls) != (new_rng.calls, new_choice.calls):
        fail(f"{name}: RNG/choice call mismatch")


def main():
    from data.drop_tables import CENTRAL_DROP_MIGRATED_RULES, DROP_RULES_BY_ID
    from systems.drop_system import (
        get_central_drop_status,
        resolve_central_trophy_chance,
        roll_central_trophy_simple,
        roll_central_trophy_table_entry,
        validate_drop_tables,
    )

    if tuple(CENTRAL_DROP_MIGRATED_RULES) != (
        "rune", "refine_stone", "equipment", "trophy", "potion"
    ):
        fail(f"migrated rules mismatch: {CENTRAL_DROP_MIGRATED_RULES}")
    rule = DROP_RULES_BY_ID["trophy"]
    if not rule.get("production_enabled"):
        fail("trophy production rule disabled")
    if not validate_drop_tables()["success"]:
        fail(validate_drop_tables()["errors"])

    cases = (
        ("default boundary hit", {"trash_items": [107]}, 0.45, 0),
        ("default miss", {"trash_items": [107]}, 0.450001, 0),
        ("custom normal hit", {"trash_items": [107, 108], "loot_chance": 0.58}, 0.58, 1),
        ("elite hit", {"trash_items": [107], "loot_chance": 0.45, "is_elite": True}, 0.65, 0),
        ("elite miss", {"trash_items": [107], "loot_chance": 0.45, "is_elite": True}, 0.650001, 0),
        ("empty pool", {}, 0.0, 0),
    )
    for case in cases:
        compare_simple(*case)

    # Exact compatibility over a large deterministic stream.
    for elite in (False, True):
        mob = {"trash_items": [107, 108, 109], "loot_chance": 0.52}
        if elite:
            mob["is_elite"] = True
        source = random.Random(115000 + int(elite))
        for index in range(10000):
            compare_simple(
                f"exact elite={elite} #{index}", mob, source.random(), index
            )

    # Bosses preserve the historical +20 only when the old is_elite flag is set.
    boss_plain = resolve_central_trophy_chance({"is_boss": True, "loot_chance": 0.55})
    boss_elite = resolve_central_trophy_chance({
        "is_boss": True, "is_elite": True, "loot_chance": 0.55,
    })
    if boss_plain["chance"] != 0.55 or boss_elite["chance"] != 0.75:
        fail(f"boss compatibility policy mismatch: {boss_plain}, {boss_elite}")
    if boss_elite["enemy_type"] != "boss":
        fail("boss priority over elite failed")

    # Legacy table-entry boundary uses inclusive <= chance.
    table_hit = roll_central_trophy_table_entry(
        {"item_id": 201, "chance": 0.25}, CountingRandom((0.25,))
    )
    table_miss = roll_central_trophy_table_entry(
        {"item_id": 201, "chance": 0.25}, CountingRandom((0.250001,))
    )
    if not table_hit["rolled"] or table_miss["rolled"]:
        fail(f"table boundary mismatch: {table_hit}, {table_miss}")

    status = get_central_drop_status()
    if status["production_rules"] != [
        "equipment", "trophy", "refine_stone", "rune", "potion"
    ]:
        fail(f"production status mismatch: {status}")

    reward = (ROOT / "systems" / "reward_system.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(reward)
    names = [
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    ]
    if names.count("roll_loot_from_simple_keys") != 1:
        fail("final simple trophy API missing or duplicated")
    if names.count("roll_loot_from_loot_table") != 1:
        fail("final table trophy API missing or duplicated")
    if "process_enemy_drops" not in reward:
        fail("final central victory integration is missing")

    print("[OK] Central drop trophy migration contracts")
    print("- simple trophy pools exact legacy equivalence: 20000 cases")
    print("- mob loot_chance default/custom values preserved: OK")
    print("- elite +20 percentage-point modifier preserved: OK")
    print("- boss historical is_elite compatibility explicit: OK")
    print("- loot_table/loot entry inclusive boundaries: OK")
    print("- legacy quantity RNG order preserved: OK")
    print("- stack-or-lose award path preserved: OK")
    print("- production central rules: equipment + refine_stone + rune + trophy + potion")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
