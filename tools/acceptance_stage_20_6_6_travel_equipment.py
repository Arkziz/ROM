#!/usr/bin/env python3
from __future__ import annotations
import ast,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
PRIMARY=('str','dex','int','wis','sta')
def function(text,name):
 return next(x for x in ast.parse(text).body if isinstance(x,ast.FunctionDef) and x.name==name)
def source(text,name):return ast.get_source_segment(text,function(text,name))
def main():
 files={x:(ROOT/x).read_text(encoding='utf-8-sig') for x in ('data/location_graph.py','data/travel_presentation.py','handlers/map.py','systems/travel_system.py','data/equipment_identity_stat_policy.py','data/equipment_stat_policy.py','db_modules/generated_equipment.py','db_modules/shop.py')}
 for x,t in files.items():ast.parse(t,filename=x)
 from data.location_graph import LOCATION_GRAPH,WORLD_NODES,TRAVEL_SECONDS
 from data.travel_presentation import ROUTE_PRESENTATION,get_node_name
 assert TRAVEL_SECONDS==20 and len(WORLD_NODES)==3 and sum(len(x) for x in LOCATION_GRAPH.values())==4
 assert set(ROUTE_PRESENTATION)=={(a,b) for a,bs in LOCATION_GRAPH.items() for b in bs}
 assert all(set(v)=={'preview','active','arrival'} and all(v.values()) for v in ROUTE_PRESENTATION.values())
 assert get_node_name('unknown_technical_id',WORLD_NODES)=='🧭 Невідома місцевість'
 assert 'CITY_MAP_INTRO' in files['handlers/map.py'] and 'get_route_presentation' in files['handlers/map.py']
 assert 'format_arrival_destination' in files['systems/travel_system.py']
 from data.equipment_stat_policy import get_allowed_equipment_stats
 assert get_allowed_equipment_stats('rogue','jewelry')==('dex','str','sta')
 from data.equipment_identity_stat_policy import get_identity_stat_weights
 assert set(x for x,_ in get_identity_stat_weights('ring'))==set(PRIMARY)
 assert set(x for x,_ in get_identity_stat_weights('necklace'))==set(PRIMARY)
 gen=files['db_modules/generated_equipment.py'];shop=files['db_modules/shop.py']
 forced=source(gen,'create_generated_equipment_item_for_slot');drop=source(gen,'create_generated_equipment_item');preview=source(shop,'create_common_equipment_shop_preview')
 assert 'get_allowed_armor_type_for_class(get_character_class(user_id))' in forced
 assert 'redistribute_identity_primary_stats' in forced and 'redistribute_identity_primary_stats' in drop
 assert 'redistribute_primary_stat_budget' in preview and 'redistribute_identity_primary_stats' not in preview
 node=function(gen,'generate_dynamic_equipment_stats');src=ast.get_source_segment(gen,node)
 assert 'stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.40)' in src
 assert 'if slot_key != "shoulders"' not in src
 mod=ast.Module(body=[node],type_ignores=[]);ast.fix_missing_locations(mod)
 def stat(level,rarity,base=1.0):return max(1,int(round(float(base)*10)))
 def add(stats,key,value):stats['bonus_'+key]=stats.get('bonus_'+key,0)+int(value)
 ns={'random':random,'get_dynamic_stat_value':stat,'add_stat_value':add,'ARMOR_EXTRA_STATS_BY_SLOT':{'shoulders':['sta','str']},'get_random_main_hand_profile':lambda:'sword_1h','get_random_off_hand_profile':lambda:'shield','MAIN_HAND_PROFILES':{},'OFF_HAND_PROFILES':{}}
 exec(compile(mod,'acceptance','exec'),ns)
 for rarity in ('common','uncommon','rare','epic'):
  random.seed(2066+len(rarity));stats=ns['generate_dynamic_equipment_stats']('shoulders',10,rarity)
  assert stats['pdef']>0 and stats['mdef']>0 and sum(int(stats.get('bonus_'+x,0) or 0) for x in PRIMARY)>0
 print('[OK] Stage 20.6 travel and final source-specific equipment policies PASS')
if __name__=='__main__':main()
