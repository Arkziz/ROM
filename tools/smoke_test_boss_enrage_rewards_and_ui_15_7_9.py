from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.bosses import BOSS_DEFINITIONS
from systems.boss_system import build_location_boss
assert BOSS_DEFINITIONS["pack_leader"]["enrage"]["permanent_attack_buff_percent"]==20
assert BOSS_DEFINITIONS["goblin_king"]["enrage"]["permanent_attack_buff_percent"]==20
for location,level in (("start_path",1),("dark_forest",8)):
 boss=build_location_boss(location,level)
 assert boss["elite_exp_multiplier"]==5.0
 assert boss["elite_gold_multiplier"]==5.0
 assert boss["boss_exp_multiplier"]==5.0
 assert boss["boss_gold_multiplier"]==5.0
combat=(ROOT/"handlers"/"combat.py").read_text(encoding="utf-8")
ast.parse(combat)
assert combat.count('👑 БОС ЛОКАЦІЇ!')==1
assert combat.count('🏆👑 ВИ ПЕРЕМОГЛИ БОСА!')==1
assert 'elif mob.get("is_elite")' in combat
print("[PASS] boss enrage/reward/UI contract",{"enrage":20,"exp":5.0,"gold":5.0,"banner":True})
