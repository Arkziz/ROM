#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "handlers" / "inventory.py"
source = TARGET.read_text(encoding="utf-8-sig")
tree = ast.parse(source, filename=str(TARGET))
assert source.count("ROM STAGE 18.11.1 EQUIPMENT RUNE COMPARISON START") == 1
assert source.count("ROM STAGE 18.11.1 EQUIPMENT RUNE COMPARISON END") == 1
assert 'text="⚖️ Порівняти"' in source
assert 'startswith("itemcmp:")' in source
assert 'text="⬅️ Назад до предмета"' in source
assert "_inventory_comparison_owned_item_18_11_1" in source
assert "SELECT id FROM inventory WHERE id=? AND user_id=?" in source
assert 'target["equipped_inventory_id"]' in source
assert "format_equipment_rune_slots_text" in source
assert "_inventory_remove_automatic_comparison_18_11_1" in source
assert "_EQUIPMENT_COMPARISON_BASE_REGISTER_HANDLERS_18_11_1(bot)" in source
assert source.index('startswith("itemcmp:")') < source.index("_EQUIPMENT_COMPARISON_BASE_REGISTER_HANDLERS_18_11_1(bot)")

# Pure ordering contract: old auto comparison is removed, selected rune block survives.
namespace = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "_inventory_remove_automatic_comparison_18_11_1":
        small = ast.Module(body=[node], type_ignores=[])
        ast.fix_missing_locations(small)
        namespace["_EQUIPMENT_COMPARISON_MARKER_18_11_1"] = "⚖️ Зараз вдягнено для порівняння:"
        namespace["_EQUIPMENT_RUNE_MARKER_18_11_1"] = "💠 Рунні слоти:"
        exec(compile(small, "pure-strip", "exec"), namespace)
        break
stripper = namespace["_inventory_remove_automatic_comparison_18_11_1"]
raw = "📦 Предмет\n📊 Бонуси:\n• +1\n\n⚖️ Зараз вдягнено для порівняння:\nOLD\n\n💠 Рунні слоти:\n• Слот 1: порожній"
clean = stripper(raw)
assert "OLD" not in clean and "⚖️ Зараз" not in clean
assert clean.endswith("💠 Рунні слоти:\n• Слот 1: порожній")

# No mutation statements are allowed in the dedicated comparison callback.
callbacks = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "equipment_comparison_callback_18_11_1"]
assert len(callbacks) == 1
block = ast.get_source_segment(source, callbacks[0]) or ""
for forbidden in ("UPDATE ", "INSERT ", "DELETE ", "equip_item(", "unequip", "commit("):
    assert forbidden not in block
print("PASS: initial card strips automatic comparison; conditional inline compare, ownership reload, equipped rune formatter, return route and read-only callback contracts present")
