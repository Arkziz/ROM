"""Canonical pure player EXP progression rules shared by production and simulation."""
from __future__ import annotations

BASE_EXP_BY_LEVEL = {
    # 1-10: smoothed early progression
    1: 10, 2: 12, 3: 14, 4: 16, 5: 19,
    6: 22, 7: 25, 8: 29, 9: 33, 10: 38,
    # 11-14: bridge to unchanged level 15
    11: 48, 12: 60, 13: 76, 14: 95,
    # 15-30: unchanged production baseline
    15: 120, 16: 135, 17: 150, 18: 170, 19: 190,
    20: 220, 21: 240, 22: 270, 23: 300, 24: 340,
    25: 380, 26: 420, 27: 460, 28: 520, 29: 600,
    30: 600,
    # 31-50: explicit endgame curve
    31: 650, 32: 700, 33: 760, 34: 820, 35: 890,
    36: 960, 37: 1040, 38: 1120, 39: 1210, 40: 1300,
    41: 1400, 42: 1500, 43: 1620, 44: 1740, 45: 1870,
    46: 2000, 47: 2150, 48: 2300, 49: 2470, 50: 2650,
}

CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL = {
    # 1-10: smoothed early progression
    1: 50, 2: 100, 3: 200, 4: 406, 5: 800,
    6: 1136, 7: 1660, 8: 2379, 9: 3485, 10: 5000,
    # 11-14: bridge to unchanged level 15
    11: 5312, 12: 5750, 13: 6118, 14: 6579,
    # 15-30: unchanged production baseline
    15: 7000, 16: 7259, 17: 7667, 18: 7941, 19: 8158,
    20: 8182, 21: 8750, 22: 9074, 23: 9500, 24: 9853,
    25: 10263, 26: 10833, 27: 11522, 28: 11923, 29: 12000,
    30: 14000,
    # 31-50: explicit endgame curve
    31: 14308, 32: 14643, 33: 15132, 34: 15549, 35: 15730,
    36: 16146, 37: 16587, 38: 17188, 39: 17562, 40: 18077,
    41: 18750, 42: 19333, 43: 19907, 44: 20546, 45: 21123,
    46: 21875, 47: 22558, 48: 23478, 49: 24190, 50: 25000,
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
