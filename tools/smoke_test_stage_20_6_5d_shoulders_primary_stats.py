#!/usr/bin/env python3
from __future__ import annotations
import ast,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRIMARY=('str','dex','int','wis','sta')
def main():
 text=(ROOT/'db_modules/generated_equipment.py').read_text(encoding='utf-8-sig');tree=ast.parse(text)
 node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='generate_dynamic_equipment_stats')
 source=ast.get_source_segment(text,node)
 assert 'elif slot_key == "shoulders":' in source
 assert 'stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.40)' in source
 assert 'extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta", "str"])' in source
 shoulders=next(x for x in ast.walk(node) if isinstance(x,ast.If) and isinstance(x.test,ast.Compare) and ast.unparse(x.test)=='slot_key == \'shoulders\'')
 assert not any(isinstance(x,ast.Return) for x in shoulders.body)
 mod=ast.Module(body=[node],type_ignores=[]);ast.fix_missing_locations(mod)
 def stat(level,rarity,base=1.0):return max(1,int(round(float(base)*10)))
 def add(stats,key,value):stats['bonus_'+key]=stats.get('bonus_'+key,0)+int(value)
 ns={'random':random,'get_dynamic_stat_value':stat,'add_stat_value':add,'ARMOR_EXTRA_STATS_BY_SLOT':{'shoulders':['sta','str']},'get_random_main_hand_profile':lambda:'sword_1h','get_random_off_hand_profile':lambda:'shield','MAIN_HAND_PROFILES':{},'OFF_HAND_PROFILES':{}}
 exec(compile(mod,'shoulders','exec'),ns)
 minimum_chunks={'common':1,'uncommon':2,'rare':3,'epic':4}
 for rarity in ('common','uncommon','rare','epic'):
  random.seed(20650+len(rarity));stats=ns['generate_dynamic_equipment_stats']('shoulders',10,rarity)
  assert stats['pdef']>0 and stats['mdef']>0
  values={s:int(stats.get('bonus_'+s,0) or 0) for s in PRIMARY}
  assert sum(1 for value in values.values() if value>0)>=1,(rarity,values)
  assert sum(values.values())>=minimum_chunks[rarity],(rarity,values)
  assert values['int']==0 and values['wis']==0 and values['dex']==0,(rarity,values)
 # Source-specific resolvers must remain intact after raw shoulder budget generation.
 shop=(ROOT/'db_modules/shop.py').read_text(encoding='utf-8-sig')
 assert 'redistribute_primary_stat_budget' in shop
 assert 'redistribute_identity_primary_stats' in text
 print('[OK] shoulders generate primary-stat budget for all rarities; shop/loot resolvers remain source-specific PASS')
if __name__=='__main__':main()
