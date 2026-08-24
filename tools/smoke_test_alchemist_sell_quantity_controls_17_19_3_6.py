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
assert source.count("ROM 17.19.3.6 ALCHEMIST SELL QUANTITY CONTROLS") == 1
assert source.count('parts[1]=="sellset"') == 1
assert 'callback_data=f"alchemist:sellset:{item_id}:{max(1, quantity - 1)}"' in source
assert 'callback_data=f"alchemist:sellset:{item_id}:{min(available, quantity + 1)}"' in source
assert 'callback_data=f"alchemist:sellset:{item_id}:{available}"' in source
assert 'callback_data=f"alchemist:sellconfirm:{item_id}:{quantity}"' in source
assert '"💰 Продати 1"' not in source
import handlers.city as city
original_stock = city.get_alchemist_potion_stock_17_19_3
original_wallet = city.get_wallet
try:
    city.get_wallet = lambda user_id: 100.0
    city.get_alchemist_potion_stock_17_19_3 = lambda user_id: [{
        "item_id": 202,
        "name": "🔵 Мале зілля мани",
        "sell_price": 0.8,
        "total": 9,
        "reserved": 0,
        "available": 9,
    }]
    text, keyboard = city.build_alchemist_sell_preview_17_19_3(1, 202, 2)
    callbacks = [button.callback_data for row in keyboard.keyboard for button in row]
    assert callbacks == [
        "alchemist:sellset:202:1",
        "alchemist:sellqty:202",
        "alchemist:sellset:202:3",
        "alchemist:sellset:202:9",
        "alchemist:sellqty:202",
        "alchemist:sellconfirm:202:2",
        "alchemist:sell",
    ], callbacks
    assert "📦 Кількість: 2" in text
    assert "💰 Отримаєш: 1.60" in text
finally:
    city.get_alchemist_potion_stock_17_19_3 = original_stock
    city.get_wallet = original_wallet
print("[PASS] Stage 17.19.3.6 Alchemist sell quantity controls contract")
