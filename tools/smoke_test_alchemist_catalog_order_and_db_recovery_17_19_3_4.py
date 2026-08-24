#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
if str(R) not in sys.path:
    sys.path.insert(0, str(R))
path = R / "handlers/city.py"
source = path.read_text(encoding="utf-8")
ast.parse(source)
assert source.count("ROM 17.19.3.4 ALCHEMIST CATALOG ORDER AND DB RECOVERY") == 1
assert 'callback_data=f"alchemist:buyitem:{item_id}"' in source
assert 'parts[1]=="buyitem"' in source
assert 'm.text == "🛒 Купити зілля"' in source
assert 'm.text == "💰 Продати зілля"' in source
assert 'kb.row("🛒 Купити зілля", "💰 Продати зілля")' in source
assert 'kb.row("🔙 Ремісничий квартал")' in source
assert source.count("def alchemist_reply_kb_17_19_3_1") == 1
assert source.count("def alchemist_buy_message_17_19_3_1") == 1
assert source.count("def alchemist_sell_message_17_19_3_1") == 1
import handlers.city as city
kb = city.alchemist_reply_kb_17_19_3_1()
rows = [[button.get("text") if isinstance(button, dict) else getattr(button, "text", None) for button in row] for row in kb.keyboard]
assert rows == [["🛒 Купити зілля", "💰 Продати зілля"], ["🔙 Ремісничий квартал"]], rows
text, inline = city.build_alchemist_buy_list_17_19_3(0)
callbacks = [button.callback_data for row in inline.keyboard for button in row]
from systems.potion_system import ALCHEMIST_SHOP
expected_callbacks = [f"alchemist:buyitem:{int(item_id)}" for item_id in ALCHEMIST_SHOP]
assert callbacks == expected_callbacks, (callbacks, expected_callbacks)
assert set(callbacks) == {"alchemist:buyitem:201", "alchemist:buyitem:202", "alchemist:buyitem:203", "alchemist:buyitem:204"}, callbacks
print("[PASS] Stage 17.19.3.4 Alchemist catalog order and DB recovery contract")
