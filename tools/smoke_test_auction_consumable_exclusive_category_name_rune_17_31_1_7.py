import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=(R/'systems/auction_house_system.py').read_text(encoding='utf-8');t=ast.parse(s)
assert 'AUCTION_PROTECTED_TRANSFER_ITEM_IDS = frozenset((301, 402, 526, 528, 10000))' in s
assert '10000: "Руну імені"' in s
assert 'is_consumable = item_id == 50000 or item_type == "consumable" or item_category == "consumable"' in s
assert 'if category == AUCTION_CATEGORY_CONSUMABLE:\n        return is_consumable\n    if is_consumable:\n        return False' in s
assert 'AUCTION_CATEGORY_RUNE, AUCTION_CATEGORY_CONSUMABLE' in s
assert '_AUCTION_BASE_IS_MATERIAL_17_31_1_1' not in s
assert 'fatigue_artifact_consumable_17_31_1_1' not in s
nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_auction_stack_category_matches'];assert len(nodes)==2,len(nodes)
active=ast.get_source_segment(s,nodes[-1]) or ''
assert active.index('if category == AUCTION_CATEGORY_CONSUMABLE') < active.index('if category == AUCTION_CATEGORY_MATERIAL')
print('[PASS] Consumables are exclusive and Name Rune is denied by canonical auction policy')
