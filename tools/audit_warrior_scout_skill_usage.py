#!/usr/bin/env python3
from __future__ import annotations
import argparse,ast,json,sys
from collections import Counter,defaultdict
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.simulation.battle_models import BattleActor
from systems.simulation.pve_battle import ExactPveBattleEngine
from systems.simulation.skill_catalog import load_production_skill_catalog
CLASSES=('warrior','scout')
def require(v,name,checks):
 checks.append({'name':name,'status':'PASS' if v else 'FAIL'})
 if not v:raise AssertionError(name)
def actor(name='player',resource=100):return BattleActor(name,5,100000,100000,45,45,20,20,20,20,20,'physical',5,9,'rage',resource,100)
def mob(hp=100000):return BattleActor('audit mob',5,hp,hp,1,1,20,20,1,1,1,'physical')
def static_analysis(root):
 path=root/'systems/simulation/pve_battle.py';source=path.read_text(encoding='utf-8-sig');tree=ast.parse(source);choose=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_choose');segment=ast.get_source_segment(source,choose) or ''
 catalog=load_production_skill_catalog(root);findings=[]
 for cls in CLASSES:
  damage=[s for s in catalog[cls] if not s.get('no_damage')];ranking=sorted(((s['key'],float(s.get('damage_multiplier',0)),bool(s.get('scales_with_spent_rage')),str(s.get('effect',''))) for s in damage),key=lambda x:x[1],reverse=True)
  findings.append({'class':cls,'damaging_skill_static_ranking':ranking,'selector_uses_base_multiplier_max':'return max(damaging' in segment,'selector_mentions_spent_rage':'scales_with_spent_rage' in segment,'selector_mentions_dot_value':any(x in segment for x in ('dot','poison','bleed'))})
 return {'selector_source':segment,'classes':findings}
def selection_matrix(root):
 engine=ExactPveBattleEngine(root,3);rows=[]
 for cls in CLASSES:
  for resource in range(0,101,5):
   p=actor(resource=resource);p.resource_type='rage' if cls=='warrior' else 'combat_energy';m=mob();skill=engine._choose(cls,p,m);rows.append({'class':cls,'resource':resource,'selected':skill['key'] if skill else 'basic_attack'})
 return rows
def dynamic_actions(root):
 rows=[]
 for cls in CLASSES:
  engine=ExactPveBattleEngine(root,3);p=actor();p.resource_type='rage' if cls=='warrior' else 'combat_energy';p.resource=0 if cls=='warrior' else 100;m=mob();actions=[]
  for turn in range(1,31):
   engine._tick_start(p,actions,turn);engine._player_action(turn,cls,p,m,actions)
  player=[a for a in actions if a.actor=='player'];counts=Counter(a.action for a in player);rows.append({'class':cls,'action_counts':dict(sorted(counts.items())),'actions':[{'turn':a.turn,'action':a.action,'damage':a.damage,'resource_after':a.details.get('resource'),'combo_after':a.details.get('combo')} for a in player],'final_resource':p.resource})
 return rows
def run_audit(root=ROOT):
 checks=[];static=static_analysis(root);matrix=selection_matrix(root);dynamic=dynamic_actions(root);by_class={x['class']:x for x in dynamic}
 w=by_class['warrior']['action_counts'];s=by_class['scout']['action_counts'];require(w.get('warrior_subjugation_strike',0)==0,'warrior finisher is unreachable in deterministic action sequence',checks);require(w.get('warrior_cleave',0)>0,'warrior cleave is used',checks);require(s.get('scout_sting_arrow',0)==0,'scout poison arrow is unreachable in deterministic action sequence',checks);require(s.get('scout_aimed_shot',0)>0,'scout aimed shot is used',checks)
 wm={x['selected'] for x in matrix if x['class']=='warrior' and x['resource']>=30};sm={x['selected'] for x in matrix if x['class']=='scout' and x['resource']>=35};require('warrior_subjugation_strike' not in wm,'warrior finisher absent from resource selection matrix',checks);require('scout_sting_arrow' not in sm,'scout poison arrow absent from resource selection matrix',checks);require(all(x['selector_uses_base_multiplier_max'] for x in static['classes']),'selector ranks damage skills by base multiplier',checks);require(all(not x['selector_mentions_dot_value'] for x in static['classes']),'selector does not value damage over time',checks)
 verdict={'warrior':'CONFIRMED: base multiplier selection prefers warrior_cleave 1.10 over rage-scaled warrior_subjugation_strike 1.00.','scout':'CONFIRMED: base multiplier selection prefers scout_aimed_shot 1.40 over scout_sting_arrow 1.00 and does not value poison DoT.'}
 return {'status':'PASS','audit_type':'read_only','checks':checks,'check_count':len(checks),'static_analysis':static,'resource_selection_matrix':matrix,'dynamic_action_audit':dynamic,'verdict':verdict,'gameplay_changed':False}
def main():
 p=argparse.ArgumentParser();p.add_argument('--report',required=True);a=p.parse_args();x=run_audit();o=Path(a.report);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('[PASS] warrior/scout skill usage audit checks: '+str(x['check_count']));print('[VERDICT] '+x['verdict']['warrior']);print('[VERDICT] '+x['verdict']['scout']);return 0
if __name__=='__main__':raise SystemExit(main())
