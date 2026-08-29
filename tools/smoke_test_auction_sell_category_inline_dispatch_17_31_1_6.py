import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'handlers/auction_house.py').read_text(encoding='utf-8')
t=ast.parse(s)
nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_auction_send_sell_category_listing_v1']
assert len(nodes)==1,len(nodes)
body=ast.get_source_segment(s,nodes[0]) or ''
assert 'build_auction_sell_inline_list_text_v1' in body
assert 'isinstance(inline_kb, types.InlineKeyboardMarkup)' in body
assert '_auction_call_equipment_sell_list_v1(' not in body
assert '_auction_try_stack_sell_list_v1(' not in body
assert 'скинь handlers/auction_house.py' not in body
for category in ('equipment','potion','material','rune','consumable'):
 assert f'"{category}"' in body,category
assert 'reply_markup=auction_sell_listing_back_kb_v1()' in body
assert '_auction_sanitize_sell_inline_kb_v1(inline_kb)' in body
assert 'callback_data=AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V1' in s
assert 'AUCTION_SELL_CATEGORY_BUTTONS_V1["consumable"])\n    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1)' in s
assert 'auction_sell_category_consumable_v1' in s
assert 'auction_sell_category_rune_v1' in s
print('[PASS] All Auction sell categories use the canonical inline item-list dispatcher')
