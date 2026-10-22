"""Pure exact level-up reward calculation for ROM V2.

Source contract hash: 9fcff9d31933698149eabf2afc7379916c6f6b23672519dbdaccca19a269a3bb. No persistence, settlement, presentation,
runtime, Telegram, fallback formula, or extrapolation is implemented here.
"""
from __future__ import annotations
from types import MappingProxyType
from typing import Any, Mapping

_LEVEL_UP_GOLD_BY_REACHED_LEVEL = {2: 0.45, 3: 1.43, 4: 4.3, 5: 11.98, 6: 34.4, 7: 69.58, 8: 130.73, 9: 255.74, 10: 479.19, 11: 881.25}
LEVEL_UP_GOLD_BY_REACHED_LEVEL: Mapping[int,float] = MappingProxyType(_LEVEL_UP_GOLD_BY_REACHED_LEVEL)
CONFIGURED_MIN_REACHED_LEVEL=min(LEVEL_UP_GOLD_BY_REACHED_LEVEL)
CONFIGURED_MAX_REACHED_LEVEL=max(LEVEL_UP_GOLD_BY_REACHED_LEVEL)

def calculate_v2_level_up_reward(reached_level: int) -> dict[str,Any]:
    """Return the exact V1 reward row and fail closed if gold is unconfigured."""
    level=int(reached_level)
    if level not in LEVEL_UP_GOLD_BY_REACHED_LEVEL:
        raise ValueError(f"Level-up gold is not configured for reached level {level}. Add an audited combat-income matrix before enabling this level.")
    milestone=level%5==0
    return {"reached_level":level,"gold":LEVEL_UP_GOLD_BY_REACHED_LEVEL[level],"small_health_potions":3,"small_mana_potions":1,"refine_stones":4 if milestone else 2,"medium_health_potions":2 if milestone else 0,"medium_mana_potions":1 if milestone else 0,"crystals":0,"milestone":milestone}

def calculate_v2_level_up_rewards(old_level: int,new_level: int) -> dict[str,Any]:
    """Aggregate every reached level in ascending V1 order."""
    old_level=int(old_level);new_level=int(new_level)
    levels=list(range(old_level+1,new_level+1)) if new_level>old_level else []
    rows=[calculate_v2_level_up_reward(level) for level in levels]
    return {"old_level":old_level,"new_level":new_level,"reached_levels":levels,"milestone_levels":[row["reached_level"] for row in rows if row["milestone"]],"gold":sum(row["gold"] for row in rows),"small_health_potions":sum(row["small_health_potions"] for row in rows),"small_mana_potions":sum(row["small_mana_potions"] for row in rows),"refine_stones":sum(row["refine_stones"] for row in rows),"medium_health_potions":sum(row["medium_health_potions"] for row in rows),"medium_mana_potions":sum(row["medium_mana_potions"] for row in rows),"crystals":sum(row["crystals"] for row in rows),"rows":rows}
