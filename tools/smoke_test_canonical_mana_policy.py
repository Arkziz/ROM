#!/usr/bin/env python3
"""Executable acceptance checks for the disconnected canonical Mana policy."""
from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.mana_policy import (
    MANA_COST_ROUNDING_POLICY,
    MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT,
    MANA_POST_COMBAT_FLOOR_TARGET_PERCENT,
    MANA_REGEN_PERCENT_PER_FULL_MINUTE,
    ManaPolicyError,
    apply_post_combat_mp_floor_value,
    calculate_mana_restore_amount,
    calculate_mana_skill_cost,
    calculate_passive_mp_regen_per_full_minute,
    calculate_post_combat_mp_floor,
    round_mana_value,
    validate_mana_skill_definition,
)

PROFILES = {
    "mage_fireball": (8, 7, {170: 20, 300: 29, 600: 50, 1000: 78}),
    "mage_thunder_spell": (15, 18, {170: 46, 300: 69, 600: 123, 1000: 195}),
    "mage_arcane_flow": (0, 0, {170: 0, 300: 0, 600: 0, 1000: 0}),
    "priest_holy_ray": (6, 4, {170: 13, 300: 18, 600: 30, 1000: 46}),
    "priest_healing_blessing": (12, 10, {170: 29, 300: 42, 600: 72, 1000: 112}),
    "priest_purify_faith": (10, 8, {170: 24, 300: 34, 600: 58, 1000: 90}),
}


def expect_error(callable_object, *args):
    try:
        callable_object(*args)
    except ManaPolicyError:
        return
    raise AssertionError(f"ManaPolicyError was not raised: {callable_object.__name__}{args!r}")


def main() -> int:
    assert MANA_COST_ROUNDING_POLICY == "ROUND_HALF_UP"
    assert MANA_REGEN_PERCENT_PER_FULL_MINUTE == 30
    assert MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT == 50
    assert MANA_POST_COMBAT_FLOOR_TARGET_PERCENT == 50
    assert [round_mana_value(value) for value in ("12.4", "12.5", "12.6")] == [12, 13, 13]

    checked = 0
    for key, (flat, percent, vectors) in PROFILES.items():
        skill = {
            "key": key,
            "cost_type": "mana",
            "mana_cost_flat": flat,
            "mana_cost_max_mp_percent": percent,
        }
        validate_mana_skill_definition(skill)
        for max_mp, expected in vectors.items():
            actual = calculate_mana_skill_cost(skill, max_mp)
            assert actual == expected, (key, max_mp, actual, expected)
            checked += 1

    assert calculate_mana_restore_amount(170, 25) == 43
    assert calculate_mana_restore_amount(170, 15) == 26
    assert calculate_passive_mp_regen_per_full_minute(170) == 51
    assert calculate_post_combat_mp_floor(170) == 85
    assert calculate_post_combat_mp_floor(170, 50) == 85
    assert apply_post_combat_mp_floor_value(0, 170, 50) == 85
    assert apply_post_combat_mp_floor_value(84, 170, 50) == 85
    assert apply_post_combat_mp_floor_value(85, 170, 50) == 85
    assert apply_post_combat_mp_floor_value(120, 170, 50) == 120
    assert apply_post_combat_mp_floor_value(999, 170, 50) == 170
    assert apply_post_combat_mp_floor_value(0, 0, 50) == 0

    valid = {"cost_type": "mana", "mana_cost_flat": 1, "mana_cost_max_mp_percent": 2}
    for invalid_max in (-1, 1.5, None, True, math.nan, math.inf, "bad"):
        expect_error(calculate_mana_skill_cost, valid, invalid_max)
    expect_error(validate_mana_skill_definition, {})
    expect_error(validate_mana_skill_definition, {"cost_type": "rage", "mana_cost_flat": 1, "mana_cost_max_mp_percent": 2})
    expect_error(validate_mana_skill_definition, {"cost_type": "mana", "mana_cost_flat": -1, "mana_cost_max_mp_percent": 2})
    expect_error(validate_mana_skill_definition, {"cost_type": "mana", "mana_cost_flat": 1, "mana_cost_max_mp_percent": -2})
    expect_error(validate_mana_skill_definition, {"cost_type": "mana", "mana_cost_flat": True, "mana_cost_max_mp_percent": 2})
    expect_error(round_mana_value, -1)
    print(f"[OK] Canonical Mana policy smoke test - {checked} hybrid cost vectors, rounding, restore, floor and invalid-input contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
