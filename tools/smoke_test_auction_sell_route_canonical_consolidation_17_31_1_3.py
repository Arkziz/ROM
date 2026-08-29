import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'handlers/auction_house.py';s=p.read_text(encoding='utf-8');t=ast.parse(s)
for name in ('auction_sell_category_kb_v1','build_auction_sell_category_text_v1','_auction_send_sell_category_listing_v1','_auction_register_sell_category_keyboard_cleanup_v1'):
 nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name];assert len(nodes)==1,(name,len(nodes))
for name in ('auction_sell_category_kb_v2_safe','build_auction_sell_category_text_v2_safe','_auction_register_sell_category_keyboard_cleanup_v2_safe'):
 assert not [n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name],name
assert 'AUCTION_SELL_CATEGORY_BUTTONS_V1["material"], AUCTION_SELL_CATEGORY_BUTTONS_V1["rune"]' in s
assert 'AUCTION_SELL_CATEGORY_BUTTONS_V1["consumable"])\n    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1)' in s
assert 'auction_sell_category_rune_v1' in s and 'auction_sell_category_consumable_v1' in s
assert 'category in ("potion", "material", "rune", "consumable")' in s
sell_handlers=[]
for n in ast.walk(t):
 if isinstance(n,ast.FunctionDef) and n.decorator_list:
  decorators='\n'.join(ast.get_source_segment(s,d) or '' for d in n.decorator_list)
  if '➕ Виставити товар' in decorators or 'AUCTION_SELL_BUTTON' in decorators:
   sell_handlers.append(n.name)
assert 'auction_sell_start_categories_v1' in sell_handlers,sell_handlers
assert 'auction_sell_start_categories_v2_safe' not in sell_handlers,sell_handlers
# Registration chain must not contain the removed V2 registration layer.
assert '_auction_base_register_handlers_before_sell_keyboard_cleanup_v2_safe' not in s
print('[PASS] Canonical V1 route contains equipment, potion, material, rune and consumable; V2 safe route removed')
