import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'systems/auction_house_system.py').read_text(encoding='utf-8')
t=ast.parse(s)
nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_auction_buy_normalize_category']
assert nodes
node=nodes[-1]
module=ast.Module(body=[node],type_ignores=[])
ast.fix_missing_locations(module)
ns={
 'AUCTION_BUY_CATEGORY_ALL':'all',
 'AUCTION_CATEGORY_RUNE':'rune',
 'AUCTION_CATEGORY_CONSUMABLE':'consumable',
 '_auction_base_buy_normalize_category_12_6_3c':lambda value: {
   'all':'all','equipment':'equipment','potion':'potion','material':'material'
 }.get(str(value or 'all').strip().lower(),'all'),
}
exec(compile(module,'<auction-normalizer-smoke>','exec'),ns)
f=ns['_auction_buy_normalize_category']
expected={
 None:'all','all':'all','equipment':'equipment','potion':'potion','material':'material',
 'rune':'rune','runes':'rune','руна':'rune','руни':'rune','💠 руни':'rune',
 'consumable':'consumable','consumables':'consumable',
 'витратні предмети':'consumable','🧰 витратні предмети':'consumable',
 '🧰 Витратні предмети в продажу':'consumable',
}
for raw,want in expected.items():
 got=f(raw)
 assert got==want,(raw,got,want)
assert f('consumable')!='all'
active=ast.get_source_segment(s,node) or ''
assert 'return AUCTION_CATEGORY_CONSUMABLE' in active
assert 'where.append("category=?")' in s
print('[PASS] Consumable buy category remains consumable and reaches exact SQL category filtering')
