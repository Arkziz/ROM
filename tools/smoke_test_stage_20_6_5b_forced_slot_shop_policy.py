#!/usr/bin/env python3
from __future__ import annotations
import ast,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
PRIMARY=('str','dex','int','wis','sta')
def fn_source(text,name):
 n=next(x for x in ast.parse(text).body if isinstance(x,ast.FunctionDef) and x.name==name);return ast.get_source_segment(text,n)
def main():
 gen=(ROOT/'db_modules/generated_equipment.py').read_text(encoding='utf-8-sig');shop=(ROOT/'db_modules/shop.py').read_text(encoding='utf-8-sig')
 ast.parse(gen);ast.parse(shop)
 forced=fn_source(gen,'create_generated_equipment_item_for_slot');drop=fn_source(gen,'create_generated_equipment_item');preview=fn_source(shop,'create_common_equipment_shop_preview')
 forced_tree=ast.parse(forced);forced_fn=forced_tree.body[0]
 armor_assignments=[n for n in ast.walk(forced_fn) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='armor_type' for t in n.targets)]
 assert len(armor_assignments)==1
 armor_expr=armor_assignments[0].value
 assert isinstance(armor_expr,ast.IfExp)
 assert isinstance(armor_expr.orelse,ast.Constant) and armor_expr.orelse.value==''
 assert 'get_allowed_armor_type_for_class(get_character_class(user_id))' in ast.unparse(armor_expr.body)
 assert 'redistribute_identity_primary_stats' in forced
 assert 'redistribute_identity_primary_stats' in drop
 assert 'redistribute_primary_stat_budget' in preview and 'get_character_class(user_id)' in preview
 assert 'redistribute_identity_primary_stats' not in preview
 assert 'if slot_key != "shoulders" and rarity in ["uncommon", "rare", "epic"]:' in gen
 from data.equipment_stat_policy import get_allowed_equipment_stats
 assert get_allowed_equipment_stats('rogue','jewelry')==('dex','str','sta')
 assert 'int' not in get_allowed_equipment_stats('rogue','jewelry') and 'wis' not in get_allowed_equipment_stats('rogue','jewelry')
 from data.equipment_identity_stat_policy import get_identity_stat_weights
 assert set(x for x,_ in get_identity_stat_weights('necklace'))==set(PRIMARY)
 assert set(x for x,_ in get_identity_stat_weights('ring'))==set(PRIMARY)
 # Execute the actual shoulder-stat function in an isolated namespace with pure stubs.
 node=next(x for x in ast.parse(gen).body if isinstance(x,ast.FunctionDef) and x.name=='generate_dynamic_equipment_stats')
 mod=ast.Module(body=[node],type_ignores=[]);ast.fix_missing_locations(mod)
 def stat(level,rarity,base=1.0):return max(1,int(round(float(base)*10)))
 def add(stats,key,value):stats['bonus_'+key]=stats.get('bonus_'+key,0)+int(value)
 ns={'random':random,'get_dynamic_stat_value':stat,'add_stat_value':add,'ARMOR_EXTRA_STATS_BY_SLOT':{},'get_random_main_hand_profile':lambda:'sword_1h','get_random_off_hand_profile':lambda:'shield','MAIN_HAND_PROFILES':{},'OFF_HAND_PROFILES':{}}
 exec(compile(mod,'shoulder_probe','exec'),ns)
 for rarity in ('common','uncommon','rare','epic'):
  stats=ns['generate_dynamic_equipment_stats']('shoulders',10,rarity)
  assert stats['pdef']>0 and stats['mdef']>0
  assert all(int(stats.get('bonus_'+x,0) or 0)==0 for x in PRIMARY), (rarity,stats)
 print('[OK] forced-slot armor routing, strict class-aware shop, identity-aware loot, universal loot jewelry and defense-only shoulders PASS')
if __name__=='__main__':main()
