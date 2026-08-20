#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "handlers/city.py").read_text(encoding="utf-8")
tree = ast.parse(source)

assert source.count("ROM 17.11.1.2 TRADE SUBMENU CITY BUTTON RECOVERY") == 1
assert '@bot.message_handler(func=lambda m: m.text in ("🔙 Місто", "⬅️ Місто"))' in source
assert 'TRADE_DISTRICT_CITY_BUTTON_17_11_1 = "⬅️ Місто"' in source
assert 'TRADE_DISTRICT_BACK_BUTTON_17_11_1 = "🔙 Торговий ряд"' in source
assert "def trade_district_submenu_kb_17_11_1" in source

handlers = []
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "back_to_city":
        handlers.append(ast.get_source_segment(source, node) or "")
assert handlers, "back_to_city handler missing"
assert any("build_city_text(user_id)" in text and "reply_markup=city_kb()" in text for text in handlers)

# Recovery must not alter the contextual Trade District navigation contract.
assert "def build_base_equipment_return_view_17_11_1_1" in source
assert "reply_markup=trade_district_submenu_kb_17_11_1()" in source
print("[PASS] Stage 17.11.1.2 contextual City button handler recovery")
