#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "handlers/city.py").read_text(encoding="utf-8")
tree = ast.parse(source)

assert source.count("ROM 17.11.1.1 BASE EQUIPMENT CONTEXT NAVIGATION RECOVERY") == 1
assert "def build_base_equipment_return_view_17_11_1_1" in source
assert "def get_base_equipment_preview_slot_17_11_1_1" in source
assert 'if slot_key in ("main_hand", "off_hand")' in source

functions = {
    node.name: ast.get_source_segment(source, node) or ""
    for node in ast.walk(tree)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
for name in ("confirm_common_shop_purchase", "cancel_common_shop_purchase"):
    text = functions[name]
    assert "get_base_equipment_preview_slot_17_11_1_1" in text, name
    assert "build_base_equipment_return_view_17_11_1_1" in text, name
    assert "reply_markup=trade_district_submenu_kb_17_11_1()" in text, name
    assert "reply_markup=trader_kb()" not in text, name

preview = functions["preview_common_equipment"]
assert "reply_markup=trade_district_submenu_kb_17_11_1()" in preview
assert "reply_markup=trader_kb()" not in preview

# Stage 17.11.1 navigation remains intact.
assert "def trade_district_submenu_kb_17_11_1" in source
assert 'TRADE_DISTRICT_BACK_BUTTON_17_11_1 = "🔙 Торговий ряд"' in source
assert 'TRADE_DISTRICT_CITY_BUTTON_17_11_1 = "⬅️ Місто"' in source

# No duplicate Trade District inline return is reintroduced.
for name in ("build_common_equipment_shop_text", "build_common_equipment_slot_choice_text"):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            text = ast.get_source_segment(source, node) or ""
            assert 'callback_data="back_to_trade_district"' not in text, (name, node.lineno)

print("[PASS] Stage 17.11.1.1 base-equipment context navigation recovery")
