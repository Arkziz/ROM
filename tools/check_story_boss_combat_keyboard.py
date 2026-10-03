#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static DB-free regression for story-boss combat keyboard parity."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"handlers/combat.py").read_text(encoding="utf-8")
tree=ast.parse(source)
register=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="register_combat_handlers"]
assert len(register)==1
nested=[n for n in ast.walk(register[0]) if isinstance(n,ast.FunctionDef)]
boss=[n for n in nested if n.name=="call_active_story_boss"]
hunt=[n for n in nested if n.name=="hunt"]
assert len(boss)==1 and len(hunt)==1
boss_text=ast.get_source_segment(source,boss[0]);hunt_text=ast.get_source_segment(source,hunt[0])
assert '"⚔️ Бій розпочався!"' in boss_text
assert 'reply_markup=combat_placeholder_kb()' in boss_text
assert 'reply_markup=build_combat_inline_kb(user_id,mob)' in boss_text.replace(' ','')
assert boss_text.index('combat_placeholder_kb()') < boss_text.index('build_combat_inline_kb(user_id,mob)')
assert 'begin_pve_encounter(user_id,message.chat.id,mob)' in boss_text.replace(' ','')
assert 'get_active_pve_encounter(user_id) is not None' in boss_text
assert 'combat_placeholder_kb()' in hunt_text
# Canonical encounter owner remains unique; this patch only aligns presentation.
assert source.count('def call_active_story_boss(message):')==1
print("STORY BOSS COMBAT KEYBOARD PARITY: PASS")
