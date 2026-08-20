#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
h=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8')
s=(ROOT/'systems/player_interaction_system.py').read_text(encoding='utf-8')
t=ast.parse(h)
functions={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
for name in ('_trade_add_list_display_name_12_6_3a','_trade_offer_name','_trade_ux_offer_name','_trade_preview_text_12_6_2'):
 assert name in functions,name
fmt=ast.get_source_segment(h,functions['_trade_add_list_display_name_12_6_3a'])
ns={'ARMOR_TYPE_LABELS':{'cloth':'Тканина'},'ITEM_SUBTYPE_LABELS':{'staff_2h':'Посох'},'_TRADE_ARMOR_SLOT_KEYS_12_6_3A':frozenset(('chest',))}
exec(fmt,ns); f=ns['_trade_add_list_display_name_12_6_3a']
assert f({'item_name':'Обладунок 8 рівня [+5]','category':'equipment','slot_key':'chest','armor_type':'cloth','item_level':8})=='Обладунок [Тканина] 8 рівня [+5]'
assert f({'item_name':'Дворучний посох 8 рівня [+5]','category':'weapon','slot_key':'main_hand','item_subtype':'staff_2h','item_level':8})=='Дворучний посох [Посох] 8 рівня [+5]'
assert f({'item_name':'Мале зілля здоров’я','category':'potion','item_subtype':'potion'})=='Мале зілля здоров’я'
assert f({'item_name':'Обладунок [Тканина] 8 рівня [+5]','category':'equipment','slot_key':'chest','armor_type':'cloth','item_level':8})=='Обладунок [Тканина] 8 рівня [+5]'
assert h.count('ROM 17.4.3 CANONICAL TRADE EQUIPMENT TYPE FORMATTER')==1
assert s.count('ROM 17.4.3 TRADE SNAPSHOT EQUIPMENT TYPE FIELDS')==1
base=[n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='_trade_base_build_item_snapshot_12_6_3']
assert len(base)==1
b=ast.get_source_segment(s,base[0]); assert '("armor_type", ("armor_type",))' in b and '("item_subtype", ("item_subtype", "subtype"))' in b
assert '_trade_add_list_display_name_12_6_3a(snapshot)' in ast.get_source_segment(h,functions['_trade_offer_name'])
assert '_trade_add_list_display_name_12_6_3a(snapshot)' in ast.get_source_segment(h,functions['_trade_ux_offer_name'])
assert '_trade_add_list_display_name_12_6_3a(snapshot)' in ast.get_source_segment(h,functions['_trade_preview_text_12_6_2'])
print('[PASS] Stage 17.4.3 canonical trade equipment type UI')
