#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Executable regression for Stage 20.2.2a weaponless stat routing."""
from __future__ import annotations
import ast
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
import db_modules.player as player

EXPECTED={
    "warrior":("physical",11),"knight":("physical",11),
    "scout":("physical",11),"rogue":("physical",11),
    "mage":("magical",37),"priest":("magical",37),
}

def exercise(class_key,equipped_slot=None,is_weapon=False):
    with patch.object(player,"get_character_class",return_value=class_key), \
         patch.object(player,"get_player_stats",return_value=(10,10,10,10,10,1)), \
         patch.object(player,"get_attack",return_value=11), \
         patch.object(player,"get_magic_attack",return_value=37), \
         patch("db_modules.equipment.get_equipped_slot",return_value=equipped_slot), \
         patch("db_modules.equipment.get_weapon_damage_by_inventory_id",return_value={"is_weapon":is_weapon}):
        return player.get_player_attack_profile(1001)

for class_key,(attack_type,stat_attack) in EXPECTED.items():
    no_weapon=exercise(class_key,None,False)
    assert no_weapon["attack_type"]==attack_type,(class_key,no_weapon)
    assert no_weapon["stat_attack"]==stat_attack,(class_key,no_weapon)
    assert no_weapon["display_attack"]==stat_attack,(class_key,no_weapon)
    assert no_weapon["weapon_min_damage"]==0 and no_weapon["weapon_max_damage"]==0
    invalid_equipped=exercise(class_key,777,False)
    assert invalid_equipped["attack_type"]==attack_type,(class_key,invalid_equipped)
    assert invalid_equipped["stat_attack"]==stat_attack,(class_key,invalid_equipped)
    assert invalid_equipped["display_attack"]==stat_attack,(class_key,invalid_equipped)

source=(ROOT/"db_modules/player.py").read_text(encoding="utf-8-sig")
tree=ast.parse(source)
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="get_player_attack_profile"]
assert len(functions)==1
fn=functions[0]
assignments={}
for node in ast.walk(fn):
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        assignments.setdefault(node.targets[0].id,[]).append(node)
assert len(assignments.get("attack_type",[]))==1
assert len(assignments.get("stat_attack",[]))==1
stat_value=assignments["stat_attack"][0].value
assert isinstance(stat_value,ast.IfExp)
assert isinstance(stat_value.test,ast.Compare)
# No fallback dictionary may route stat/display attack directly to physical_stat_attack.
for node in ast.walk(fn):
    if not isinstance(node,ast.Dict):
        continue
    payload={}
    for key,value in zip(node.keys,node.values):
        if isinstance(key,ast.Constant) and isinstance(key.value,str):
            payload[key.value]=value
    for key in ("stat_attack","display_attack"):
        value=payload.get(key)
        assert not (isinstance(value,ast.Name) and value.id=="physical_stat_attack"), (key,node.lineno)
print("PASS")
