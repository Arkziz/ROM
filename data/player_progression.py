"""Canonical pure player EXP progression rules shared by production and simulation."""
from __future__ import annotations

BASE_EXP_BY_LEVEL = {
    1: 10, 2: 12, 3: 15, 4: 18, 5: 25, 6: 30, 7: 35, 8: 45, 9: 60, 10: 65,
    11: 75, 12: 85, 13: 95, 14: 110, 15: 120, 16: 135, 17: 150, 18: 170,
    19: 190, 20: 220, 21: 240, 22: 270, 23: 300, 24: 340, 25: 380,
    26: 420, 27: 460, 28: 520, 29: 600, 30: 600,
}

CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL = {
    1: 50, 2: 150, 3: 300, 4: 500, 5: 1200, 6: 1800, 7: 2500, 8: 3500,
    9: 4500, 10: 5000, 11: 5500, 12: 6000, 13: 6000, 14: 6000, 15: 7000,
    16: 7000, 17: 7000, 18: 8000, 19: 8000, 20: 8500, 21: 8500, 22: 9500,
    23: 9500, 24: 9500, 25: 10500, 26: 10500, 27: 10500, 28: 12000,
    29: 12000, 30: 14000,
}

MAX_CONFIGURED_LEVEL = max(BASE_EXP_BY_LEVEL)

def get_base_exp_for_level(level: int) -> int:
    level = int(level)
    if level in BASE_EXP_BY_LEVEL:
        return BASE_EXP_BY_LEVEL[level]
    if level > MAX_CONFIGURED_LEVEL:
        return int(BASE_EXP_BY_LEVEL[MAX_CONFIGURED_LEVEL] * (1.12 ** (level - MAX_CONFIGURED_LEVEL)))
    return BASE_EXP_BY_LEVEL[1]

def get_exp_to_next_level(level: int) -> int:
    level = int(level)
    base_exp = get_base_exp_for_level(level)
    if level in CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL:
        return int(base_exp * CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL[level])
    mobs_required = int(CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL[MAX_CONFIGURED_LEVEL] * (1.10 ** (level - MAX_CONFIGURED_LEVEL)))
    return int(base_exp * mobs_required)

def apply_exp_award(level: int, exp: int, amount: int, level_cap: int | None = None) -> dict:
    level, exp, amount = int(level), int(exp), int(amount)
    level_ups = 0
    while amount > 0:
        if level_cap is not None and level >= int(level_cap):
            break
        required = get_exp_to_next_level(level)
        missing = required - exp
        if amount < missing:
            exp += amount
            amount = 0
        else:
            amount -= missing
            exp = 0
            level += 1
            level_ups += 1
    return {"level": level, "exp": exp, "exp_to_next": get_exp_to_next_level(level), "level_ups": level_ups, "unapplied_exp": amount}
