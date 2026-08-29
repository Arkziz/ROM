import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'handlers/auction_house.py').read_text(encoding='utf-8')
t=ast.parse(s)
restore=[]
for n in t.body:
 if isinstance(n,ast.FunctionDef) and n.name=='register_auction_house_handlers':
  src=ast.get_source_segment(s,n) or ''
  if 'Restore handler chain before the broken 8.0.9d sell-category wrapper.' in src:
   restore.append(n)
assert len(restore)==1,len(restore)
node=restore[0]
ordered=[]
for statement in node.body:
 if isinstance(statement,ast.Expr) and isinstance(statement.value,ast.Call) and isinstance(statement.value.func,ast.Name):
  ordered.append(statement.value.func.id)
assert ordered[:2]==['_auction_register_reply_back_to_house_restore_v1','_auction_register_sell_category_keyboard_cleanup_v1'],ordered
registered=[]
for n in ast.walk(t):
 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.decorator_list:
  decorators='\n'.join(ast.get_source_segment(s,d) or '' for d in n.decorator_list)
  if 'message_handler' in decorators and ('AUCTION_SELL_BUTTON' in decorators or '➕ Виставити товар' in decorators):
   registered.append(n.name)
assert registered==['auction_sell_start_categories_v1'],registered
assert 'auction_sell_start_categories_v2_safe' not in s
assert 'AUCTION_SELL_CATEGORY_BUTTONS_V1["consumable"])\n    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1)' in s
assert 'auction_sell_category_consumable_v1' in s
print('[PASS] Canonical V1 sell registration is directly reachable before the legacy chain')
