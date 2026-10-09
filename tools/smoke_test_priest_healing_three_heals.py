#!/usr/bin/env python3
"""Executable contract for the Priest three-heal lifecycle."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.priest_healing_policy import (
    PRIEST_HEALING_COOLDOWN_TURNS,
    PRIEST_HEALING_DURATION_TURNS,
    PRIEST_HEALING_IMMEDIATE_HEALS,
    PRIEST_HEALING_REAPPLICATION_POLICY,
    PRIEST_HEALING_TOTAL_HEALS,
    build_priest_healing_effect,
    calculate_priest_heal_amount,
)


def main():
    assert PRIEST_HEALING_IMMEDIATE_HEALS == 1
    assert PRIEST_HEALING_DURATION_TURNS == 2
    assert PRIEST_HEALING_TOTAL_HEALS == 3
    assert PRIEST_HEALING_COOLDOWN_TURNS == 4
    assert PRIEST_HEALING_REAPPLICATION_POLICY == "replace"

    heal_amount = calculate_priest_heal_amount(130)
    assert heal_amount == 13

    heals = [heal_amount]
    effect = build_priest_healing_effect(heal_amount)
    while effect["turns"] > 0:
        heals.append(effect["heal"])
        effect["turns"] -= 1

    assert heals == [13, 13, 13], heals
    assert effect["turns"] == 0

    effects = {"hot": build_priest_healing_effect(10)}
    effects["hot"] = build_priest_healing_effect(20)
    assert effects["hot"]["heal"] == 20
    assert effects["hot"]["turns"] == 2

    cooldown = PRIEST_HEALING_COOLDOWN_TURNS
    blocked = []
    for _ in range(4):
        blocked.append(cooldown > 0)
        cooldown = max(0, cooldown - 1)
    assert blocked == [True, True, True, True]
    assert cooldown == 0

    print("[OK] Priest healing: 1 immediate + 2 delayed = 3 total; cooldown=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
