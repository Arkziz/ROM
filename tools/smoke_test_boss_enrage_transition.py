from __future__ import annotations
import random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from systems.boss_system import build_location_boss,get_boss_enrage_threshold_hp,prepare_boss_turn,build_boss_damage_request,finalize_boss_turn
for location,level,special,buff in (("start_path",5,"enraged_rend",25),("dark_forest",10,"tyrant_strike",30)):
 b=build_location_boss(location,level,rng=random.Random(154000+level)); threshold=get_boss_enrage_threshold_hp(b)
 b["hp"]=threshold+1
 ordinary=prepare_boss_turn(b,rng=random.Random(1)); assert not ordinary["enrage_triggered"]
 b["hp"]=threshold
 first=prepare_boss_turn(b,rng=random.Random(2)); assert first["enrage_triggered"]
 assert first["action_plan"]["skill_key"]==special
 assert b["boss_state"]["enrage_used"] and b["boss_state"]["special_attack_used"]
 assert b["boss_state"]["permanent_attack_buff_percent"]==buff
 request=build_boss_damage_request(first["action_plan"]); assert request and request["mob_attack"]>b["attack"]
 second=prepare_boss_turn(b,rng=random.Random(3)); assert not second["enrage_triggered"]
 assert second["action_plan"]["phase"]=="ai_after_enrage"
 assert second["action_plan"]["skill_key"]!=special
 dead=build_location_boss(location,level,rng=random.Random(4));dead["hp"]=0
 assert not prepare_boss_turn(dead,rng=random.Random(5))["enrage_triggered"]
print("[PASS] one-time enrage, automatic special, replacement and post-enrage AI")
