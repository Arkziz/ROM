#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "handlers" / "inventory.py"
source = SOURCE.read_text(encoding="utf-8")
tree = ast.parse(source)

register_nodes = [
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "register_inventory_handlers"
]
assert len(register_nodes) == 1, len(register_nodes)
register_source = ast.get_source_segment(source, register_nodes[0]) or ""

assert source.count("ROM 17.5.1 REPEAT POTION USE CATEGORY NAVIGATION") == 1
assert 'if result.get("success"):' in register_source
assert 'stale_inventory = "Предмет не знайдено в інвентарі" in result_message' in register_source
assert 'bot.edit_message_text(' in register_source
assert 'bot.edit_message_reply_markup(' in register_source
assert 'show_alert=True' in register_source
assert 'build_category_list(user_id, back_category, page)' in register_source
assert 'use_potion_from_inventory(user_id, inventory_id)' in register_source

success_pos = register_source.find('if result.get("success"):')
stale_pos = register_source.find('stale_inventory =')
non_stale_pos = register_source.find('# Full HP, full MP')
assert 0 <= success_pos < stale_pos < non_stale_pos

# The ordinary-potion block must have one system call and explicit returns for
# success, stale inventory, and non-stale failure paths.
ordinary = register_source[register_source.find('# Звичайні зілля'):]
assert ordinary.count('use_potion_from_inventory(user_id, inventory_id)') == 1
assert ordinary.count('return') >= 3
print('[PASS] Stage 17.5.1 repeat potion use category navigation')
