from __future__ import annotations
import random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from systems.boss_system import build_location_boss,build_boss_action_plan,resolve_boss_combat_action

wolf=build_location_boss("start_path",5,rng=random.Random(153001))
for key,mult,kind in (("ferocious_bite",1.0,"physical"),("fang_rend",1.5,"physical"),("spectral_roar",1.3,"magical"),("enraged_rend",2.0,"physical")):
 plan=build_boss_action_plan(wolf,forced_skill_key=key)
 assert plan["skill_key"]==key and plan["damage_multiplier"]==mult and plan["attack_type"]==kind
 assert plan["effective_attack"]==wolf["attack"] and not plan["no_damage"]

king=build_location_boss("dark_forest",10,rng=random.Random(153002))
for key in ("battle_cry","defense_command"):
 result=resolve_boss_combat_action(king,forced_skill_key=key)
 assert result["plan"]["no_damage"] is True
 assert result["plan"]["effective_attack"]==0
 assert result["effects"] is not None
print("[PASS] all boss combat action plans and no-damage actions")
