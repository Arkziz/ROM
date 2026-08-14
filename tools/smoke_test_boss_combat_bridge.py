from __future__ import annotations
import random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from systems.boss_system import build_location_boss,prepare_boss_turn,build_boss_damage_request,finalize_boss_turn,render_boss_action_text
b=build_location_boss("start_path",5,rng=random.Random(154100))
turn=prepare_boss_turn(b,rng=random.Random(1)); req=build_boss_damage_request(turn["action_plan"])
assert req is not None and req["attack_type"] in {"physical","magical"}
result=finalize_boss_turn(b,turn["action_plan"],actual_damage=50)
assert isinstance(result["boss_state"],dict)
text=render_boss_action_text(b,turn,actual_damage=50); assert turn["action_plan"]["skill_name"] in text
# no-damage action returns no damage request and full timer survives its own cast
k=build_location_boss("dark_forest",10,rng=random.Random(154101))
from systems.boss_system import build_boss_action_plan
plan=build_boss_action_plan(k,forced_skill_key="battle_cry")
assert build_boss_damage_request(plan) is None
finalize_boss_turn(k,plan,0); assert k["boss_state"]["attack_buff_turns"]==3
print("[PASS] production combat bridge requests, effect finalization and localized text")
