from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from data.bosses import BOSS_CORE_STAT_MULTIPLIER,BOSS_HP_MULTIPLIER,BOSS_ATTACK_MULTIPLIER,BOSS_DEFINITIONS,BOSS_ENCOUNTERS_ENABLED,BOSS_ENCOUNTER_CHANCE_PERCENT
from systems.combat_system import ELITE_CORE_STAT_MULTIPLIER
assert BOSS_CORE_STAT_MULTIPLIER==2.0
assert BOSS_HP_MULTIPLIER==2.0
assert BOSS_ATTACK_MULTIPLIER==2.0
king=BOSS_DEFINITIONS["goblin_king"]
pack=BOSS_DEFINITIONS["pack_leader"]
assert king["skills"]["skull_splitter"]["damage_multiplier"]==1.3
assert king["skills"]["tyrant_strike"]["damage_multiplier"]==1.6
assert pack["skills"]["fang_rend"]["damage_multiplier"]==1.4
assert pack["skills"]["enraged_rend"]["damage_multiplier"]==1.7
print("[PASS] boss core recalibration",{"boss":2.0,"elite_unchanged":ELITE_CORE_STAT_MULTIPLIER,"skull":1.3,"tyrant":1.6,"boss_gate":BOSS_ENCOUNTERS_ENABLED,"boss_chance":BOSS_ENCOUNTER_CHANCE_PERCENT})
