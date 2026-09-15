#!/usr/bin/env python3
from pathlib import Path
import ast,random,sys
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.combat_system import calculate_player_hit_chance,skill_requires_pve_hit_roll,roll_player_pve_skill_hit
class Fixed:
 def __init__(self,n):self.n=n
 def randint(self,a,b):return self.n
assert calculate_player_hit_chance(999,0)==95.0
assert calculate_player_hit_chance(0,999)==50.0
physical={"damage_multiplier":1.0,"attack_type":"physical"};magical={"damage_multiplier":1.0,"attack_type":"magical"}
suppression={"damage_multiplier":0.0,"attack_type":"physical","effect":"enemy_pdef_down"}
trap={"damage_multiplier":0.0,"attack_type":"physical","effect":"enemy_pdef_trap"}
shield={"damage_multiplier":0.0,"attack_type":"physical","effect":"player_shield"}
mana={"damage_multiplier":0.0,"attack_type":"magical","effect":"restore_mana_percent"}
heal={"damage_multiplier":0.0,"attack_type":"magical","effect":"player_hot"}
cleanse={"damage_multiplier":0.0,"attack_type":"magical","effect":"player_cleanse_mdef_buff"}
mob={"dex":10,"wis":20}
assert roll_player_pve_skill_hit(physical,10,999,mob,Fixed(95))["hit"]
assert not roll_player_pve_skill_hit(physical,10,999,mob,Fixed(96))["hit"]
assert roll_player_pve_skill_hit(magical,0,20,mob,Fixed(95))["hit"]
assert not roll_player_pve_skill_hit(magical,0,20,mob,Fixed(96))["hit"]
assert all(skill_requires_pve_hit_roll(x) for x in (physical,magical,suppression,trap))
for x in (shield,mana,heal,cleanse):
 r=roll_player_pve_skill_hit(x,0,0,{},Fixed(100));assert r["required"] is False and r["hit"] is True
source=(ROOT/'handlers/combat.py').read_text(encoding='utf-8-sig')
assert source.count('roll_player_pve_skill_hit(')==2
assert source.count('if skill_hit:')>=4
assert source.count('if skill_hit and combo_gain > 0:')==2
assert source.count('if skill_hit and not skill.get("no_damage"):')==2
assert source.count('if not skill_hit:')==2
print('PVE_OFFENSIVE_SKILL_HIT_18_21_6_OK')