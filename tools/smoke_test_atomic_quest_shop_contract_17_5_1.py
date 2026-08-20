#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def fn(rel,name):
 s=(ROOT/rel).read_text(encoding='utf-8'); t=ast.parse(s); n=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==name]; assert len(n)==1,(name,len(n)); return ast.get_source_segment(s,n[0]),s
inv,_=fn('db_modules/inventory.py','add_item'); quest,_=fn('db_modules/quests.py','claim_daily_quest_reward'); shop,_=fn('db_modules/shop.py','purchase_shop_preview_item')
assert 'commit=True' in inv and 'if commit:' in inv and 'commit=False' in quest and 'commit=False' in shop
assert 'BEGIN IMMEDIATE' in quest and 'conn.rollback()' in quest and 'conn.commit()' in quest
assert "status='claimed'" in quest and 'result.get("added"' in quest and 'result.get("lost"' in quest
assert 'BEGIN IMMEDIATE' in shop and 'conn.rollback()' in shop and 'conn.commit()' in shop
assert shop.find('add_item(') < shop.find('UPDATE users SET gold=COALESCE(gold,0)-?')
assert 'AND COALESCE(gold,0)>=?' in shop
assert inv.count('ROM 17.5.1 ADD_ITEM TRANSACTION OWNERSHIP')==1
assert quest.count('ROM 17.5.1 ATOMIC DAILY QUEST REWARD')==1
assert shop.count('ROM 17.5.1 ATOMIC SHOP PURCHASE')==1
print('[PASS] Stage 17.5.1 atomic quest and shop contracts')
