#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
profile=(ROOT/"handlers/profile.py").read_text(encoding="utf-8-sig")
ptree=ast.parse(profile)
functions={n.name:n for n in ptree.body if isinstance(n,ast.FunctionDef)}
assert "profile_inline_kb" in functions and "register_profile_handlers" in functions
pseg=ast.get_source_segment(profile,functions["profile_inline_kb"]) or ""
assert pseg.count('callback_data="profile_attributes"')==1
assert 'active_tab != "attributes"' in pseg
rseg=ast.get_source_segment(profile,functions["register_profile_handlers"]) or ""
assert rseg.count("register_attribute_allocation_handlers(bot, profile_inline_kb, build_character_text)")==1
handler=(ROOT/"handlers/attribute_allocation.py").read_text(encoding="utf-8-sig")
htree=ast.parse(handler)
names={n.name for n in htree.body if isinstance(n,ast.FunctionDef)}
for required in ("build_attribute_allocation_text","attribute_allocation_kb","register_attribute_allocation_handlers"):
 assert required in names,required
assert handler.count('callback_data="attr:confirm"')==1
assert handler.count('callback_data="attr:cancel"')>=1
assert "expected_free_attribute_points" in handler
assert "allocate_attribute_points(" in handler
print("[PASS] Stage 18.16.5 profile allocation UI structure")
