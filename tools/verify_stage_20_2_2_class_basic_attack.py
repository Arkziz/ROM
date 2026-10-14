#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maintained verification for Stage 20.2.2 class-aware basic attacks."""
from __future__ import annotations
import ast
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from systems.stat_system import BASIC_ATTACK_TYPE_BY_CLASS, resolve_basic_attack_type
from systems.character_system import get_character_class

EXPECTED={
    "warrior":"physical","knight":"physical","scout":"physical",
    "rogue":"physical","mage":"magical","priest":"magical",
}
assert BASIC_ATTACK_TYPE_BY_CLASS==EXPECTED
for class_key,attack_type in EXPECTED.items():
    assert resolve_basic_attack_type(class_key)==attack_type
    assert resolve_basic_attack_type(class_key.upper())==attack_type
for invalid in (None,"","unknown"):
    try:
        resolve_basic_attack_type(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError(f"Unsupported class did not fail closed: {invalid!r}")

source=(ROOT/"db_modules/player.py").read_text(encoding="utf-8-sig")
tree=ast.parse(source)
assert "from systems.character_system import get_character_class" in source
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="get_player_attack_profile"]
assert len(functions)==1
calls=[]
for node in ast.walk(functions[0]):
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="resolve_basic_attack_type":
        calls.append(node)
assert len(calls)>=2, f"Expected resolver use in assignment and fallback payloads, got {len(calls)}"
assignments=[]
for node in ast.walk(functions[0]):
    if isinstance(node,(ast.Assign,ast.AnnAssign)):
        targets=node.targets if isinstance(node,ast.Assign) else [node.target]
        if any(isinstance(target,ast.Name) and target.id=="attack_type" for target in targets):
            assignments.append(node)
assert len(assignments)==1
value=assignments[0].value
assert isinstance(value,ast.Call) and isinstance(value.func,ast.Name) and value.func.id=="resolve_basic_attack_type"
assert not any(isinstance(node,ast.Constant) and node.value=="physical" for node in ast.walk(functions[0]))

combat=(ROOT/"systems/combat_system.py").read_text(encoding="utf-8-sig")
handler=(ROOT/"handlers/combat.py").read_text(encoding="utf-8-sig")
assert "def calculate_player_attack(" in combat
assert "def get_effective_mob_def(" in handler
assert 'attack_type == "magical"' in handler
print("PASS")
