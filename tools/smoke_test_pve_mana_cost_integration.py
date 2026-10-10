#!/usr/bin/env python3
"""Executable pure checks for Stage 20.3.4 PvE Mana integration."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from systems.pve_skill_action_state import get_pve_effective_skill_cost, get_pve_skill_action_state, format_pve_skill_description

PROFILES={
"mage_fireball":(8,7,{170:20,300:29,600:50,1000:78}),
"mage_thunder_spell":(15,18,{170:46,300:69,600:123,1000:195}),
"mage_arcane_flow":(0,0,{170:0,300:0,600:0,1000:0}),
"priest_holy_ray":(6,4,{170:13,300:18,600:30,1000:46}),
"priest_healing_blessing":(12,10,{170:29,300:42,600:72,1000:112}),
"priest_purify_faith":(10,8,{170:24,300:34,600:58,1000:90}),
}

def main():
 checked=0
 for key,(flat,percent,vectors) in PROFILES.items():
  skill={"key":key,"name":key,"description":"Витрачає 999 MP та виконує дію.","cost_type":"mana","cost":999,"cooldown":0,"mana_cost_flat":flat,"mana_cost_max_mp_percent":percent}
  for maximum,expected in vectors.items():
   current = maximum - 1 if key == "mage_arcane_flow" else maximum
   mob={"player_mp":current,"player_max_mp":maximum,"skill_cooldowns":{},"player_effects":{}}
   assert get_pve_effective_skill_cost(mob,skill)==expected
   description=format_pve_skill_description(mob,skill)
   assert f"Витрачає {expected} MP" in description and "999 MP" not in description
   state=get_pve_skill_action_state(1,mob,skill)
   assert state["available"] and state["effective_cost"]==expected
   if expected:
    mob["player_mp"]=expected-1
    state=get_pve_skill_action_state(1,mob,skill)
    assert not state["available"] and state["reason"]=="not_enough_mana" and state["required"]==expected
   checked+=1
 flow={"key":"mage_arcane_flow","name":"Магічний потік","description":"Не завдає шкоди.","cost_type":"mana","cost":0,"cooldown":0,"mana_cost_flat":0,"mana_cost_max_mp_percent":0,"restore_max_mp_percent":25,"effect":"restore_mana_percent"}
 full={"player_mp":170,"player_max_mp":170,"skill_cooldowns":{},"player_effects":{}}
 assert get_pve_skill_action_state(1,full,flow)["reason"]=="mana_already_full"
 full["player_mp"]=169
 assert get_pve_skill_action_state(1,full,flow)["available"]
 physical={"key":"x","name":"x","description":"x","cost_type":"rage","cost":20,"cooldown":0}
 assert get_pve_effective_skill_cost({"player_max_mp":170},physical)==20
 print(f"[OK] PvE Mana cost integration smoke - {checked} cost vectors, dynamic descriptions, availability, full-MP guard and physical fallback")
 return 0
if __name__=="__main__": raise SystemExit(main())
