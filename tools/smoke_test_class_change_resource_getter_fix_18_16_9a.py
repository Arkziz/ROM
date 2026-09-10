#!/usr/bin/env python3
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
source=(R/"systems/character_system.py").read_text(encoding="utf-8-sig")
tree=ast.parse(source)
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="confirm_character_class_change_17_13_1"]
assert len(functions)==1
segment=ast.get_source_segment(source,functions[0]) or ""
assert segment.count("from systems.player_system import get_max_hp")==1
assert segment.count("from systems.character_system import get_max_mp")==0
assert "get_max_mp" in segment
assert "max_mp_getter=get_max_mp" in segment
import systems.player_system as player
import systems.character_system as character
assert callable(player.get_max_hp)
assert callable(character.get_max_mp)
print("[PASS] Stage 18.16.9a class-change resource getter import contract")
