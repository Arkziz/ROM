import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1];h=(R/'handlers/auction_house.py').read_text(encoding='utf-8');s=(R/'systems/auction_house_system.py').read_text(encoding='utf-8');ast.parse(h);ast.parse(s)
assert 'AUCTION_BUY_CATEGORY_BY_BUTTON_V1.pop("🧰 Витратні предмети", None)' in h
assert 'AUCTION_SELL_CATEGORY_BY_BUTTON_V1["🧰 Витратні предмети"] = "consumable"' in h
assert 'kb.keyboard = cleaned' in h
assert 'if not exists:' in h
assert 'AUCTION_CATEGORY_CONSUMABLE = "consumable"' in s
assert 'item_id", 0) or 0) == 50000' in s
print('[PASS] Stage 17.31.1.6 consumables sell-route contracts')
