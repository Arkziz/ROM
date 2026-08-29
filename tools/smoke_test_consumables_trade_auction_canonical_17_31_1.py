import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
paths=['handlers/player_interaction.py','systems/player_interaction_system.py','handlers/auction_house.py','systems/auction_house_system.py']
text={p:(R/p).read_text(encoding='utf-8') for p in paths}
for p,s in text.items(): ast.parse(s,filename=p)
assert '_PLAYER_TRADE_CATEGORY_LABELS_12_6_4' in text[paths[0]] and ':consumable:0' in text[paths[0]]
assert 'PLAYER_TRADE_ITEM_CATEGORIES = ("equipment", "potion", "material", "rune", "consumable")' in text[paths[1]]
assert 'item_id == 50000 or category == "consumable"' in text[paths[1]]
ah=text[paths[2]]
assert '"consumable": "🧰 Витратні предмети"' in ah
assert 'auction_sell_category_consumable_v1' in ah
assert 'kb.row(AUCTION_SELL_CATEGORY_BUTTONS_V1["consumable"])\n    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1)' in ah
assert 'kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["consumable"])\n    kb.row(AUCTION_BACK_TO_MENU_BUTTON)' in ah
asys=text[paths[3]]
assert 'AUCTION_CATEGORY_CONSUMABLE = "consumable"' in asys
assert 'category == AUCTION_CATEGORY_CONSUMABLE' in asys
for marker in ('_AH_BUY_CATEGORY_KB_BEFORE','_AH_SELL_CATEGORY_KB_BEFORE','consumables_auction_ui_17_31_1_5'):
 assert marker not in ah
print('[PASS] canonical consumables trade and auction integration')
