#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "handlers" / "inventory.py"
source = TARGET.read_text(encoding="utf-8-sig")
tree = ast.parse(source, filename=str(TARGET))
assert source.count("def _inventory_selected_rune_block_18_11_2") == 1
assert "format_equipment_rune_slots_text(" in source
assert "int(user_id), int(inventory_id)" in source
assert "selected_runes = _inventory_selected_rune_block_18_11_2(user_id, inventory_id)" in source
assert 'target["equipped_inventory_id"]' in source

# The inherited text stripper must discard both automatic comparison and any
# inherited rune block. Selected runes are rebuilt explicitly afterward.
functions = {n.name:n for n in tree.body if isinstance(n, ast.FunctionDef)}
strip_node = functions["_inventory_remove_automatic_comparison_18_11_1"]
small = ast.Module(body=[strip_node], type_ignores=[]); ast.fix_missing_locations(small)
ns = {
    "_EQUIPMENT_COMPARISON_MARKER_18_11_1":"⚖️ Зараз вдягнено для порівняння:",
    "_EQUIPMENT_RUNE_MARKER_18_11_1":"💠 Рунні слоти:",
}
exec(compile(small,"strip-test","exec"),ns)
stripper=ns["_inventory_remove_automatic_comparison_18_11_1"]
legacy="📦 Кольчуга\n\n⚖️ Зараз вдягнено для порівняння:\n📦 Шкіра\n\n💠 Рунні слоти:\n• Руна Спритності II"
assert stripper(legacy)=="📦 Кольчуга"
legacy2="📦 Кольчуга\n\n💠 Рунні слоти:\n• чужий успадкований блок"
assert stripper(legacy2)=="📦 Кольчуга"

# Identity contract: selected formatter receives selected ID, equipped formatter
# receives equipped ID. They must never share one pre-rendered text block.
details = ast.get_source_segment(source, functions["build_item_details"]) or ""
comparison = ast.get_source_segment(source, functions["build_equipped_comparison_text"]) or ""
assert "_inventory_selected_rune_block_18_11_2(user_id, inventory_id)" in details
assert 'target["equipped_inventory_id"]' in comparison
assert "selected_runes" not in comparison

# Comparison callback remains read-only.
callback = functions["register_inventory_handlers"]
block = ast.get_source_segment(source, callback) or ""
for forbidden in ("UPDATE ", "INSERT ", "DELETE ", "commit(", "equip_item(", "unequip"):
    assert forbidden not in block
print("PASS: inherited ambiguous rune text discarded; selected and equipped rune blocks are rebuilt from distinct exact inventory IDs")
