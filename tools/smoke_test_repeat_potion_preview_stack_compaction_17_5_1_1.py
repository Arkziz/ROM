#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
h=(ROOT/'handlers/inventory.py').read_text(encoding='utf-8')
s=(ROOT/'systems/potion_system.py').read_text(encoding='utf-8')
ht=ast.parse(h); st=ast.parse(s)
hf={n.name:n for n in ht.body if isinstance(n,ast.FunctionDef)}
sf={n.name:n for n in st.body if isinstance(n,ast.FunctionDef)}
assert h.count('ROM 17.5.1.1 KEEP POTION PREVIEW OPEN')==1
assert s.count('ROM 17.5.1.1 ATOMIC POTION CONSUME AND STACK COMPACTION')==1
assert '_consume_potion_and_compact_stacks_17_5_1_1' in sf
assert 'use_potion_from_inventory' in sf
register=ast.get_source_segment(h,hf['register_inventory_handlers'])
assert 'build_item_details(' in register
assert 'canonical_inventory_id = result.get("inventory_id")' in register
assert 'build_category_list(user_id, back_category, page)' in register
use=ast.get_source_segment(s,sf['use_potion_from_inventory'])
helper=ast.get_source_segment(s,sf['_consume_potion_and_compact_stacks_17_5_1_1'])
assert use.count('_consume_potion_and_compact_stacks_17_5_1_1(')==2
assert 'ORDER BY id ASC' in helper
assert 'total_after = total_before - 1' in helper
assert 'UPDATE users SET hp=?' in helper and 'UPDATE users SET mp=?, max_mp=?' in helper
assert 'conn.commit()' in helper and 'ROLLBACK TO' in helper
assert 'consume_inventory_item' not in use
print('[PASS] Stage 17.5.1.1 repeat preview and potion stack compaction')
