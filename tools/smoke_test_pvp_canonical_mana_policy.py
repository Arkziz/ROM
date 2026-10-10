#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.pvp_action_validation import get_pvp_effective_skill_cost,validate_pvp_action_choice
from systems.pvp_models import PvpActorState
from systems.pvp_round_engine import _pay,_special
import random

def actor(mp=170,max_mp=170):
 return PvpActorState(user_id=1,class_key="mage",character_name="x",max_hp=130,hp=130,max_mp=max_mp,mp=mp,resource_type="mana",resource=0,combo=0,physical_attack=10,magical_attack=10,physical_defense=3,magical_defense=3,weapon_physical_min=0,weapon_physical_max=0,weapon_magical_min=0,weapon_magical_max=0,physical_crit_chance=0,magical_crit_chance=0,dodge_chance=0,level=1)

def main():
 fire={"key":"mage_fireball","name":"fire","cost_type":"mana","cost":999,"mana_cost_flat":8,"mana_cost_max_mp_percent":7}
 thunder={"key":"mage_thunder_spell","name":"thunder","cost_type":"mana","cost":999,"mana_cost_flat":15,"mana_cost_max_mp_percent":18}
 assert [get_pvp_effective_skill_cost(fire,m) for m in (170,300,600,1000)]==[20,29,50,78]
 assert [get_pvp_effective_skill_cost(thunder,m) for m in (170,300,600,1000)]==[46,69,123,195]
 catalog={"mage":(fire,)}
 participant={"class_key":"mage","mp":19,"max_mp":170,"resource_type":"mana","cooldowns":{}}
 v=validate_pvp_action_choice(participant,"skill","mage_fireball",catalog=catalog)
 assert not v["success"] and v["required"]==20
 participant["mp"]=20;assert validate_pvp_action_choice(participant,"skill","mage_fireball",catalog=catalog)["success"]
 a=actor(20,170);ok,reason,cost,combo=_pay(a,fire);assert ok and cost==20 and a.mp==0
 a=actor(19,170);assert _pay(a,fire)[:2]==(False,"not_enough_mana") and a.mp==19
 flow={"effect":"restore_mana_percent","restore_max_mp_percent":25};a=actor(64,170);_special(a,actor(),flow,0,random.Random(1));assert a.mp==107
 purify={"effect":"player_cleanse_mdef_buff","restore_max_mp_percent":15,"duration":3};a=actor(65,170);_special(a,actor(),purify,0,random.Random(1));assert a.mp==91
 print("[OK] PvP canonical Mana - projected validation, payment, 24 vectors and half-up restores")
 return 0
if __name__=='__main__':raise SystemExit(main())
