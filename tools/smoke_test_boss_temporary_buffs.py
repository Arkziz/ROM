from __future__ import annotations
import random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from systems.boss_system import build_location_boss,resolve_boss_combat_action,get_effective_boss_attack,get_effective_boss_defenses,tick_boss_temporary_buffs

boss=build_location_boss("dark_forest",10,rng=random.Random(153020))
base_attack=boss["attack"]; base_pdef=boss["pdef"]; base_mdef=boss["mdef"]
# Battle Cry: +15%, three completed actions, refresh without stacking.
resolve_boss_combat_action(boss,forced_skill_key="battle_cry")
assert boss["boss_state"]["attack_buff_turns"]==3
assert get_effective_boss_attack(boss)==round(base_attack*1.15)
tick_boss_temporary_buffs(boss); assert boss["boss_state"]["attack_buff_turns"]==2
resolve_boss_combat_action(boss,forced_skill_key="battle_cry")
assert boss["boss_state"]["attack_buff_turns"]==3
assert get_effective_boss_attack(boss)==round(base_attack*1.15)
for _ in range(3): tick_boss_temporary_buffs(boss)
assert get_effective_boss_attack(boss)==base_attack
# Defense Command: +30% PDEF/MDEF, two actions, replace policy.
resolve_boss_combat_action(boss,forced_skill_key="defense_command")
pdef,mdef=get_effective_boss_defenses(boss)
assert pdef==round(base_pdef*1.30) and mdef==round(base_mdef*1.30)
tick_boss_temporary_buffs(boss); assert boss["boss_state"]["defense_buff_turns"]==1
tick_boss_temporary_buffs(boss); assert get_effective_boss_defenses(boss)==(base_pdef,base_mdef)
# Permanent and temporary ATK are additive.
boss["boss_state"]["permanent_attack_buff_percent"]=30
resolve_boss_combat_action(boss,forced_skill_key="battle_cry")
assert get_effective_boss_attack(boss)==round(base_attack*1.45)
print("[PASS] temporary boss buffs, refresh semantics, expiry and additive ATK")
