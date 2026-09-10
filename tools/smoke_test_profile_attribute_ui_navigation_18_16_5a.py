#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
handler=(ROOT/"handlers/attribute_allocation.py").read_text(encoding="utf-8-sig")
profile=(ROOT/"handlers/profile.py").read_text(encoding="utf-8-sig")
h_tree=ast.parse(handler);p_tree=ast.parse(profile)
assignments={}
for node in h_tree.body:
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name):assignments[target.id]=node
labels=ast.literal_eval(assignments["ATTRIBUTE_LABELS"].value)
assert labels=={"strength":"Сила","dexterity":"Спритність","intelligence":"Інтелект","wisdom":"Мудрість","stamina":"Витривалість"},labels
assert 'callback_data="attr:back"' in handler
assert 'navigation = navigation_kb_factory(active_tab="attributes")' not in handler
assert 'for row in navigation.keyboard' not in handler
h_functions={n.name:n for n in h_tree.body if isinstance(n,ast.FunctionDef)}
keyboard=ast.get_source_segment(handler,h_functions["attribute_allocation_kb"]) or ""
assert keyboard.count('callback_data="attr:back"')==1
register=ast.get_source_segment(handler,h_functions["register_attribute_allocation_handlers"]) or ""
assert "character_text_factory" in register
assert register.count('action == "back"')==1
assert "character_text_factory(user_id)" in register
assert "navigation_kb_factory(active_tab=\"character\")" in register
p_functions={n.name:n for n in p_tree.body if isinstance(n,ast.FunctionDef)}
p_register=ast.get_source_segment(profile,p_functions["register_profile_handlers"]) or ""
assert p_register.count("register_attribute_allocation_handlers(bot, profile_inline_kb, build_character_text)")==1
print("[PASS] Stage 18.16.5a localized compact navigation contract")
