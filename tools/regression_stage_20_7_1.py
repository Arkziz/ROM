#!/usr/bin/env python3
from __future__ import annotations
import ast,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ACCEPTANCE=(
 'reports/stage_20_2_6_class_combat_acceptance.json',
 'reports/stage_20_3_9_hybrid_mana_economy_acceptance.json',
 'reports/stage_20_4_7_general_economy_acceptance.json',
 'reports/stage_20_5_7_premium_admin_crystals_acceptance.json',
 'reports/stage_20_6_6_travel_equipment_acceptance.json',
)
OWNERS=('main.py','data/location_graph.py','data/travel_presentation.py','data/equipment_identity_stat_policy.py','data/equipment_stat_policy.py','db_modules/generated_equipment.py','db_modules/shop.py','systems/travel_system.py','handlers/map.py','systems/admin_crystal_credit_system.py','systems/timed_exp_bonus_system.py')
def main():
 for rel in OWNERS:ast.parse((ROOT/rel).read_text(encoding='utf-8-sig'),filename=rel)
 reports=[json.loads((ROOT/x).read_text(encoding='utf-8-sig')) for x in ACCEPTANCE]
 assert all(x.get('status')=='PASS' for x in reports)
 decisions={str(x.get('decision','')) for x in reports}
 assert 'STAGE_20_6_ACCEPTED' in decisions
 main_t=(ROOT/'main.py').read_text(encoding='utf-8-sig')
 assert 'init_admin_crystal_credit_system()' in main_t
 assert main_t.index('init_admin_crystal_credit_system()')<main_t.index('register_admin_crystal_credit_handlers(bot)')
 graph=(ROOT/'data/location_graph.py').read_text(encoding='utf-8-sig');travel=(ROOT/'data/travel_presentation.py').read_text(encoding='utf-8-sig')
 assert 'TRAVEL_SECONDS = 20' in graph and 'ROUTE_PRESENTATION' in travel and 'UNKNOWN_LOCATION_NAME' in travel
 gen=(ROOT/'db_modules/generated_equipment.py').read_text(encoding='utf-8-sig');shop=(ROOT/'db_modules/shop.py').read_text(encoding='utf-8-sig')
 assert 'redistribute_identity_primary_stats' in gen
 assert 'redistribute_primary_stat_budget' in shop
 assert 'bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.40)' in gen
 assert 'get_allowed_armor_type_for_class(get_character_class(user_id))' in gen
 # Stage 19 localization/story invariants retained in production sources.
 dump='\n'.join(p.read_text(encoding='utf-8-sig',errors='replace') for p in ROOT.glob('data/story_quest*.py'))
 dump+='\n'+(ROOT/'data/location_graph.py').read_text(encoding='utf-8-sig')
 assert 'Початок Шляху' in dump and 'Темний Бір' in dump
 # Run maintained Stage 20 tools. Superseded tools are excluded only with an
 # explicit replacement evidence contract; they are never silently ignored.
 superseded={
  'smoke_test_stage_20_5_2_premium_combat_gold.py':{
   'reason':'UI literal superseded by Stage 20.5.2a and final Stage 20.5.7 acceptance',
   'replacement_reports':['reports/stage_20_5_2a_premium_experience_gold_ui.json','reports/stage_20_5_7_premium_admin_crystals_acceptance.json'],
  },
  'smoke_test_stage_20_6_5_identity_aware_equipment_stats.py':{
   'reason':'Stage 20.6.5 shop-equals-loot assertion superseded by source-specific Stage 20.6.5b policy and final Stage 20.6.6 acceptance',
   'replacement_reports':['reports/stage_20_6_5b_forced_slot_shop_class_policy.json','reports/stage_20_6_5d_shoulders_primary_stats.json','reports/stage_20_6_6_travel_equipment_acceptance.json'],
  },
  'smoke_test_stage_20_6_5b_forced_slot_shop_policy.py':{
   'reason':'Stage 20.6.5b temporary shoulders rarity-loop exception superseded by localized 20.6.5c and final primary-stat restoration 20.6.5d',
   'replacement_reports':['reports/stage_20_6_5c_shoulders_stat_policy.json','reports/stage_20_6_5d_shoulders_primary_stats.json','reports/stage_20_6_6_travel_equipment_acceptance.json'],
  },
  'smoke_test_stage_20_6_5c_shoulders_stat_policy.py':{
   'reason':'Stage 20.6.5c defense-only shoulders interpretation superseded by Stage 20.6.5d primary-stat restoration',
   'replacement_reports':['reports/stage_20_6_5d_shoulders_primary_stats.json','reports/stage_20_6_6_travel_equipment_acceptance.json'],
  },
 }
 suites=[];excluded=[]
 for pattern in ('smoke_test_stage_20_*.py','acceptance_stage_20_*.py'):
  for path in sorted((ROOT/'tools').glob(pattern)):
   if path.name=='regression_stage_20_7_1.py':continue
   if path.name in superseded:
    item=superseded[path.name]
    evidence=[json.loads((ROOT/x).read_text(encoding='utf-8-sig')) for x in item['replacement_reports']]
    assert all(x.get('status')=='PASS' for x in evidence),(path.name,item['replacement_reports'])
    excluded.append({'tool':str(path.relative_to(ROOT)).replace('\\','/'),'reason':item['reason'],'replacement_reports':item['replacement_reports']})
    continue
   q=subprocess.run([sys.executable,str(path)],cwd=ROOT,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=300)
   suites.append({'tool':str(path.relative_to(ROOT)).replace('\\','/'),'returncode':q.returncode,'stdout':q.stdout[-1000:],'stderr':q.stderr[-1000:]})
   assert q.returncode==0,(path.name,q.stdout,q.stderr)
 assert suites,'No maintained Stage 20 suites found'
 print(json.dumps({'status':'PASS','maintained_suites':suites,'superseded_tools':excluded},ensure_ascii=False))
 print('[OK] full Stage 20 production/evidence/maintained-suite regression PASS')
if __name__=='__main__':main()
