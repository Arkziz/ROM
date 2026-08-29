import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'handlers/auction_house.py').read_text(encoding='utf-8')
ast.parse(s)
assert 'AUCTION_BUY_RUNE_CATEGORY_BUTTON_17_31_1_8 = "💠 Руни в продажу"' in s
assert 'AUCTION_BUY_CONSUMABLE_CATEGORY_BUTTON_17_31_1_8 = "🧰 Витратні предмети в продажу"' in s
assert 'AUCTION_BUY_CATEGORY_BY_BUTTON_V1[AUCTION_BUY_RUNE_CATEGORY_BUTTON_17_31_1_8] = "rune"' in s
assert 'AUCTION_BUY_CATEGORY_BY_BUTTON_V1[AUCTION_BUY_CONSUMABLE_CATEGORY_BUTTON_17_31_1_8] = "consumable"' in s
assert 'AUCTION_SELL_CATEGORY_BUTTONS_V1["rune"] = AUCTION_RUNE_CATEGORY_BUTTON_12_6_3C' in s
assert '"rune": "💠 Руни"' in s
assert '"consumable": "🧰 Витратні предмети"' in s
assert 'AUCTION_BUY_CATEGORY_BY_BUTTON_V1[AUCTION_RUNE_CATEGORY_BUTTON_12_6_3C]' not in s
assert 'AUCTION_BUY_CATEGORY_BUTTONS_V1["consumable"] = "🧰 Витратні предмети"' not in s
assert 'kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["consumable"])\n    kb.row(AUCTION_BACK_TO_MENU_BUTTON)' in s
print('[PASS] Rune and consumable buy labels are distinct from sell labels and retain buy mappings')
