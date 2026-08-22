#!/usr/bin/env python3
import ast,random
from pathlib import Path
R=Path(__file__).resolve().parent.parent
for rel in ("systems/equipment_system.py","db_modules/player.py","systems/combat_system.py","handlers/combat.py"):
 s=(R/rel).read_text(encoding="utf-8");ast.parse(s);assert s.count("ROM 17.18.2 BOW CROSSBOW DAMAGE DIFFERENTIATION")==1,rel
from systems.combat_system import calculate_player_attack
old_randint=random.randint;old_uniform=random.uniform
try:
 random.randint=lambda a,b:100;random.uniform=lambda a,b:100
 common=dict(player_stat_attack=0,mob_def=0,dex=10,wis=10,level=1,weapon_min_damage=100,weapon_max_damage=100)
 bow=calculate_player_attack(**common,weapon_subtype="bow_2h")
 cross=calculate_player_attack(**common,weapon_subtype="crossbow_2h")
 sword=calculate_player_attack(**common,weapon_subtype="sword_1h")
 assert bow["weapon_damage"]==95,bow
 assert cross["weapon_damage"]==110,cross
 assert sword["weapon_damage"]==100,sword
 assert bow["damage"]==95 and cross["damage"]==110 and sword["damage"]==100
finally:
 random.randint=old_randint;random.uniform=old_uniform
print("[PASS] Stage 17.18.2 bow/crossbow damage contract")
