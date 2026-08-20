#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
city = (ROOT / "handlers/city.py").read_text(encoding="utf-8")
keyboards = (ROOT / "keyboards.py").read_text(encoding="utf-8")
ast.parse(city)
ast.parse(keyboards)

assert "🪙 Продати весь хлам" not in city
assert "🪙 Продати весь хлам" not in keyboards
assert "🪙 Продати весь мотлох" in city
assert "🪙 Продати весь мотлох" in keyboards
assert "def trade_district_submenu_kb_17_11_1" in city
assert "TRADE_DISTRICT_BACK_BUTTON_17_11_1 = \"🔙 Торговий ряд\"" in city
assert "TRADE_DISTRICT_CITY_BUTTON_17_11_1 = \"⬅️ Місто\"" in city
assert city.count("send_trade_district_submenu_17_11_1(bot, message.chat.id)") == 2
assert "reply_markup=trade_district_submenu_kb_17_11_1()" in city

# Trade District text no longer duplicates the visible reply actions.
trade_start = city.index("def build_trade_district_text")
trade_end = city.index("\ndef ", trade_start + 5)
trade_text = city[trade_start:trade_end]
assert "Доступні дії" not in trade_text
assert "Продати весь мотлох" not in trade_text
assert "Продати спорядження" not in trade_text
assert "Базове спорядження" not in trade_text

# The scoped list/shop builders must not duplicate Trade District return inline.
for function_name in (
    "build_common_equipment_shop_text",
    "build_common_equipment_slot_choice_text",
    "build_sell_equipment_list_text",
):
    nodes = [
        node for node in ast.walk(ast.parse(city))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    ]
    assert nodes, function_name
    for node in nodes:
        text = ast.get_source_segment(city, node) or ""
        assert 'callback_data="back_to_trade_district"' not in text, (function_name, node.lineno)
        assert "⬅️ До торгового ряду" not in text, (function_name, node.lineno)

# Internal inline navigation remains available.
assert "⬅️ Назад до слотів" in city
assert "⬅️ Назад до базового спорядження" in city
assert "sell_eq_page:" in city
assert "sell_eq_confirm:" in city

# Selling a single item must keep contextual reply navigation, not restore trader_kb.
assert 'result["message"],\n            reply_markup=trade_district_submenu_kb_17_11_1()' in city
print("[PASS] Stage 17.11.1 Trade District text/navigation contract")
