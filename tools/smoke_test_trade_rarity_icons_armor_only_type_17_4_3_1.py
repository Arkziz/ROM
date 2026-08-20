#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8')
tree=ast.parse(source)
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_trade_add_list_display_name_12_6_3a']
assert len(nodes)==1
code=ast.get_source_segment(source,nodes[0])
ns={'ARMOR_TYPE_LABELS':{'cloth':'Тканина'},'_TRADE_ARMOR_SLOT_KEYS_12_6_3A':frozenset(('helmet','shoulders','chest','gloves','legs','boots'))}
exec(code,ns); f=ns['_trade_add_list_display_name_12_6_3a']
assert f({'item_name':'Наплічники 7 рівня','category':'equipment','slot_key':'shoulders','armor_type':'cloth','rarity':'uncommon','item_level':7})=='🟢 Наплічники [Тканина] 7 рівня'
assert f({'item_name':'Обладунок 8 рівня [+5]','category':'equipment','slot_key':'chest','armor_type':'cloth','rarity':'common','item_level':8})=='⚪ Обладунок [Тканина] 8 рівня [+5]'
assert f({'item_name':'Дворучний посох 8 рівня','category':'weapon','slot_key':'main_hand','armor_type':'cloth','item_subtype':'staff_2h','rarity':'common','item_level':8})=='⚪ Дворучний посох 8 рівня'
assert f({'item_name':'Амулет 8 рівня','category':'jewelry','slot_key':'necklace','armor_type':'cloth','rarity':'common','item_level':8})=='⚪ Амулет 8 рівня'
assert f({'item_name':'Кільце 8 рівня','category':'jewelry','slot_key':'ring','armor_type':'cloth','rarity':'uncommon','item_level':8})=='🟢 Кільце 8 рівня'
assert f({'item_name':'🟢 Наплічники [Тканина] 7 рівня','category':'equipment','slot_key':'shoulders','armor_type':'cloth','rarity':'uncommon','item_level':7})=='🟢 Наплічники [Тканина] 7 рівня'
assert f({'item_name':'🔴 Середнє зілля здоров’я','category':'potion','rarity':'common'})=='🔴 Середнє зілля здоров’я'
assert 'ITEM_SUBTYPE_LABELS' not in code
assert 'elif armor_type' not in code
assert source.count('ROM 17.4.3.1 RESTORE TRADE RARITY ICONS AND ARMOR-ONLY TYPE')==1
print('[PASS] Stage 17.4.3.1 trade rarity icons and armor-only type')
