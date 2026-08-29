import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'handlers/auction_house.py').read_text(encoding='utf-8')
t=ast.parse(s)
registered=[]
legacy={'auction_sell_placeholder','auction_sell_start_v1','auction_sell_start_v2','auction_sell_start_inline_v1','auction_sell_start_review_v1'}
all_names=set()
for n in ast.walk(t):
 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
  all_names.add(n.name)
  decorators='\n'.join(ast.get_source_segment(s,d) or '' for d in n.decorator_list)
  if 'message_handler' in decorators and ('AUCTION_SELL_BUTTON' in decorators or '➕ Виставити товар' in decorators):
   registered.append(n.name)
assert registered==['auction_sell_start_categories_v1'],registered
assert legacy.issubset(all_names),legacy-all_names
assert 'auction_sell_start_categories_v2_safe' not in all_names
assert 'AUCTION_SELL_CATEGORY_BUTTONS_V1["material"], AUCTION_SELL_CATEGORY_BUTTONS_V1["rune"]' in s
assert 'AUCTION_SELL_CATEGORY_BUTTONS_V1["consumable"])\n    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1)' in s
assert 'auction_sell_category_rune_v1' in all_names
assert 'auction_sell_category_consumable_v1' in all_names
print('[PASS] Exactly one Auction sell-entry handler is registered and it is canonical V1')
