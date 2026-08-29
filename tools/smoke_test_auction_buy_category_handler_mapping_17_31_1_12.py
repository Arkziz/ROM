import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'handlers/auction_house.py').read_text(encoding='utf-8')
t=ast.parse(s)
handlers=[]
all_names=set()
canonical=None
for n in ast.walk(t):
 if isinstance(n,ast.FunctionDef):
  all_names.add(n.name)
  decorators='\n'.join(ast.get_source_segment(s,d) or '' for d in n.decorator_list)
  if 'message_handler' in decorators and 'AUCTION_BUY_CATEGORY_BY_BUTTON_V1' in decorators:
   handlers.append(n.name)
  if n.name=='auction_buy_category_selected_clean_keyboard_v1':
   canonical=ast.get_source_segment(s,n) or ''
assert handlers==['auction_buy_category_selected_clean_keyboard_v1'],handlers
assert 'auction_buy_category_selected_v1' in all_names
assert canonical is not None
assert 'AUCTION_BUY_CATEGORY_BY_BUTTON_V1.get(message.text)' in canonical
assert '.get(message.text, "all")' not in canonical
assert 'if category is None:' in canonical
assert '❌ Невідома категорія лотів.' in canonical
assert 'AUCTION_BUY_CATEGORY_BY_BUTTON_V1[AUCTION_BUY_RUNE_CATEGORY_BUTTON_17_31_1_8] = "rune"' in s
assert 'AUCTION_BUY_CATEGORY_BY_BUTTON_V1[AUCTION_BUY_CONSUMABLE_CATEGORY_BUTTON_17_31_1_8] = "consumable"' in s
assert 'AUCTION_BUY_RUNE_CATEGORY_BUTTON_17_31_1_8 = "💠 Руни в продажу"' in s
assert 'AUCTION_BUY_CONSUMABLE_CATEGORY_BUTTON_17_31_1_8 = "🧰 Витратні предмети в продажу"' in s
print('[PASS] Exactly one canonical buy-category handler remains and mapping is fail-closed')
