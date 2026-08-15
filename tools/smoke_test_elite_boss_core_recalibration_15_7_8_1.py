from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from systems.combat_system import ELITE_CORE_STAT_MULTIPLIER, ELITE_HP_MULTIPLIER, ELITE_ATTACK_MULTIPLIER
from data.bosses import BOSS_CORE_STAT_MULTIPLIER, BOSS_HP_MULTIPLIER, BOSS_ATTACK_MULTIPLIER, BOSS_DEFINITIONS, BOSS_ENCOUNTERS_ENABLED, BOSS_ENCOUNTER_CHANCE_PERCENT
assert ELITE_CORE_STAT_MULTIPLIER==1.8
assert ELITE_HP_MULTIPLIER==1.8
assert ELITE_ATTACK_MULTIPLIER==1.8
assert BOSS_CORE_STAT_MULTIPLIER==2.2
assert BOSS_HP_MULTIPLIER==2.2
assert BOSS_ATTACK_MULTIPLIER==2.2
king=BOSS_DEFINITIONS["goblin_king"]
pack=BOSS_DEFINITIONS["pack_leader"]
assert king["skills"]["skull_splitter"]["damage_multiplier"]==1.3
assert king["skills"]["tyrant_strike"]["damage_multiplier"]==1.6
assert pack["skills"]["fang_rend"]["damage_multiplier"]==1.4
assert pack["skills"]["enraged_rend"]["damage_multiplier"]==1.7
assert king["skills"]["battle_cry"]["attack_buff_percent"]==15
assert king["enrage"]["permanent_attack_buff_percent"]==30
print("[PASS] elite/boss core and boss skill tuning",{"elite":1.8,"boss":2.2,"skull":1.3,"tyrant":1.6,"boss_gate":BOSS_ENCOUNTERS_ENABLED,"boss_chance":BOSS_ENCOUNTER_CHANCE_PERCENT})
