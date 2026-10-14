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
 assert 'if slot_key != "shoulders" and rarity' not in source
 assert 'elif slot_key == "shoulders":' in source
 shoulders=next(x for x in ast.walk(node) if isinstance(x,ast.If) and isinstance(x.test,ast.Compare) and ast.unparse(x.test)=='slot_key == \'shoulders\'')
 assert any(isinstance(x,ast.Return) and isinstance(x.value,ast.Name) and x.value.id=='stats' for x in shoulders.body)
 mod=ast.Module(body=[node],type_ignores=[]);ast.fix_missing_locations(mod)
 def stat(level,rarity,base=1.0):return max(1,int(round(float(base)*10)))
 def add(stats,key,value):stats['bonus_'+key]=stats.get('bonus_'+key,0)+int(value)
 ns={'random':random,'get_dynamic_stat_value':stat,'add_stat_value':add,'ARMOR_EXTRA_STATS_BY_SLOT':{},'get_random_main_hand_profile':lambda:'sword_1h','get_random_off_hand_profile':lambda:'shield','MAIN_HAND_PROFILES':{},'OFF_HAND_PROFILES':{}}
 exec(compile(mod,'shoulders','exec'),ns)
 for rarity in ('common','uncommon','rare','epic'):
  stats=ns['generate_dynamic_equipment_stats']('shoulders',10,rarity)
  assert stats['pdef']>0 and stats['mdef']>0
  assert all(int(stats.get('bonus_'+s,0) or 0)==0 for s in PRIMARY), (rarity,stats)
 # A non-shoulder rarity still reaches the shared rarity bonus mechanism.
 random.seed(2065);other=ns['generate_dynamic_equipment_stats']('chest',10,'uncommon')
 assert any(int(other.get('bonus_'+s,0) or 0)>0 for s in PRIMARY)
 print('[OK] shoulders own defense-only return; shared rarity logic remains generic PASS')
if __name__=='__main__':main()
