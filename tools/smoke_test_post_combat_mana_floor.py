#!/usr/bin/env python3
"""Executable acceptance checks for the canonical 50% post-combat Mana floor."""
from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.mana_policy import (
 MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT,
 MANA_POST_COMBAT_FLOOR_TARGET_PERCENT,
 MANA_REGEN_PERCENT_PER_FULL_MINUTE,
 apply_post_combat_mp_floor_value,
 calculate_post_combat_mp_floor,
)

def main():
 assert MANA_REGEN_PERCENT_PER_FULL_MINUTE==30
 assert MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT==50
 assert MANA_POST_COMBAT_FLOOR_TARGET_PERCENT==50
 assert calculate_post_combat_mp_floor(170)==85
 vectors={(0,170):85,(40,170):85,(84,170):85,(85,170):85,(120,170):120,(170,170):170,(999,170):170,(0,0):0,(1,1):1,(0,1):1}
 for (current,maximum),expected in vectors.items():assert apply_post_combat_mp_floor_value(current,maximum)==expected,(current,maximum)
 source=(ROOT/'systems/character_system.py').read_text(encoding='utf-8-sig')
 assert 'MP_POST_COMBAT_FLOOR_PERCENT_17_15_1' not in source
 assert 'new_mp = apply_post_combat_mp_floor_value(current, maximum)' in source
 assert 'reset_mp_regen_clock_17_15_1(user_id, paused=False)' in source
 combat=(ROOT/'handlers/combat.py').read_text(encoding='utf-8-sig')
 assert combat.count('apply_post_combat_mp_floor_17_15_1(user_id)')==5
 print('[OK] Post-combat Mana floor - 50% vectors, non-additive floor, regen reset and 5 terminal calls')
 return 0
if __name__=='__main__':raise SystemExit(main())
