#!/usr/bin/env python3
from __future__ import annotations
import ast,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports'/'stage_18_30_14b_drop_adapter_and_guild_projection_audit.json'
TARGETS=['systems/reward_system.py','systems/guild_system.py','systems/contract_system.py','data/balance.py','systems/combat_system.py','data/bosses.py','db_modules/systems_wrappers.py','db_modules/__init__.py']
DROP_NAMES=('process_enemy_drops','add_item','generate','drop','loot','inventory','capacity','user_id','commit','rollback','cursor','execute')
GUILD_NAMES=('award_guild_elite_kill','award_guild_contract_completion','DAILY_CONTRACT_LIMIT','CONTRACT_TARGET_KILLS','CONTRACT_MOBS_EQUIVALENT','ELITE_CHANCE_PERCENT','BOSS_ENCOUNTER_CHANCE_PERCENT')
def read(rel):return (ROOT/rel).read_text(encoding='utf-8-sig')
def literal(node):
 try:return ast.literal_eval(node)
 except Exception:return '<dynamic>'
def defs(rel):
 s=read(rel);tree=ast.parse(s);out=[]
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
   src=ast.get_source_segment(s,node) or ''
   calls=[]
   for n in ast.walk(node):
    if isinstance(n,ast.Call):
     try:c=ast.unparse(n.func)
     except Exception:c='<call>'
     calls.append(c)
   out.append({'file':rel,'name':node.name,'line':node.lineno,'args':[a.arg for a in node.args.args],'async':isinstance(node,ast.AsyncFunctionDef),'calls':sorted(set(calls)),'uses':sorted({x for x in DROP_NAMES+GUILD_NAMES if x.lower() in src.lower()}),'source':src})
  elif isinstance(node,(ast.Assign,ast.AnnAssign)):
   ts=node.targets if isinstance(node,ast.Assign) else [node.target]
   for t in ts:
    if isinstance(t,ast.Name) and t.id in GUILD_NAMES:out.append({'file':rel,'name':t.id,'line':node.lineno,'value':literal(node.value)})
 return out
def find(rows,name):return [x for x in rows if x.get('name')==name]
def main():
 rows=[]
 for rel in TARGETS:
  if (ROOT/rel).is_file():rows.extend(defs(rel))
 drop=find(rows,'process_enemy_drops');elite=find(rows,'award_guild_elite_kill');contract=find(rows,'award_guild_contract_completion')
 constants={n:[x for x in rows if x.get('name')==n and 'value' in x] for n in GUILD_NAMES if n.isupper()}
 boundaries=[]
 for fn in drop:
  calls=fn.get('calls',[]);boundaries.append({'function':fn['name'],'file':fn['file'],'line':fn['line'],'args':fn['args'],'persistence_calls':[c for c in calls if any(k in c.lower() for k in ('db.','execute','commit','add_item','inventory'))],'rng_calls':[c for c in calls if any(k in c.lower() for k in ('random','randint','choice','choices','uniform'))],'all_calls':calls})
 authoritative={'drop_owner':drop,'guild_elite_owner':[x for x in elite if x['file']=='systems/guild_system.py'],'guild_contract_owner':[x for x in contract if x['file']=='systems/guild_system.py'],'constants':constants}
 checks=[]
 def req(name,value):checks.append({'name':name,'status':'PASS' if value else 'FAIL'});return bool(value)
 req('canonical process_enemy_drops found',drop);req('guild elite owner found',authoritative['guild_elite_owner']);req('guild contract owner found',authoritative['guild_contract_owner']);req('daily contract limit found',constants.get('DAILY_CONTRACT_LIMIT'));req('elite chance found',constants.get('ELITE_CHANCE_PERCENT'));req('boss chance found',constants.get('BOSS_ENCOUNTER_CHANCE_PERCENT'))
 status='PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL'
 report={'stage':'18.30.14b','status':status,'generated_at':datetime.now(timezone.utc).isoformat(),'scope':'deep read-only function and persistence-boundary audit','approved_assumptions':{'month_days':30,'members':[1,10],'contracts_completed':True,'elite_kills_completed':True,'mixed_kills':{'normal':8500,'elite':1400,'boss':100},'control_kills_each':10000,'total_drop_sample':40000},'authoritative_owners':authoritative,'drop_adapter_boundaries':boundaries,'guild_projection_inputs':{'contract_limit_candidates':constants.get('DAILY_CONTRACT_LIMIT',[]),'contract_target_kills':constants.get('CONTRACT_TARGET_KILLS',[]),'contract_mobs_equivalent':constants.get('CONTRACT_MOBS_EQUIVALENT',[]),'elite_chance':constants.get('ELITE_CHANCE_PERCENT',[]),'boss_chance':constants.get('BOSS_ENCOUNTER_CHANCE_PERCENT',[]),'elite_reward_functions':authoritative['guild_elite_owner'],'contract_reward_functions':authoritative['guild_contract_owner']},'implementation_decisions_required':{'drop_adapter':'identify exact persistence collaborators from drop_adapter_boundaries and replace only those with isolated in-memory fakes while executing unmodified canonical decision logic','guild_projection':'calculate one and ten members for 30 days from canonical personal daily contract cap and canonical elite encounter rate; explicitly exclude boss from elite reward because classification priority is boss > elite > normal','database_policy':'no sqlite connection, no production user_id, no game.db/WAL/SHM mutation','statistical_workloads':['8500 normal + 1400 elite + 100 boss','10000 normal','10000 elite','10000 boss']},'checks':checks,'raw_function_evidence':rows}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8');print('[AUDIT] function/constant evidence:',len(rows));print('[AUDIT] drop boundaries:',len(boundaries));print('[REPORT]',OUT.relative_to(ROOT));print('[STATUS]',status);return 0 if status=='PASS' else 2
if __name__=='__main__':raise SystemExit(main())
