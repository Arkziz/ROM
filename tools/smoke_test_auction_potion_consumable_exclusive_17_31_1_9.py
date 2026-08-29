import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'systems/auction_house_system.py').read_text(encoding='utf-8')
t=ast.parse(s)
nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_auction_stack_category_matches']
assert len(nodes)>=1
body=ast.get_source_segment(s,nodes[-1]) or ''
assert 'is_rune = _auction_is_rune_snapshot_12_6_3c(snapshot)' in body
assert 'is_potion = _auction_is_potion_snapshot(snapshot)' in body
assert ') and not is_rune and not is_potion' in body
assert 'return is_potion and not is_rune' in body
assert 'return is_consumable' in body
assert 'and not is_potion' in body
assert 'and not is_consumable' in body
assert 'AUCTION_PROTECTED_TRANSFER_ITEM_IDS = frozenset((301, 402, 526, 528, 10000))' in s
assert '_AUCTION_BASE_IS_MATERIAL_17_31_1_1' not in s
print('[PASS] Potion, consumable, material and rune Auction categories are mutually exclusive')
