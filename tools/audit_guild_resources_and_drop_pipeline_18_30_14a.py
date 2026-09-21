#!/usr/bin/env python3
from __future__ import annotations
import ast,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'/'stage_18_30_14a_guild_resource_and_drop_audit.json'
SKIP={'backup','reports','.git','.venv','venv','__pycache__','patch'}
TERMS={
 'guild':['guild','гільд','resource','ресурс','treasury','contribution'],
 'contract':['contract','контракт'],
 'encounter':['elite','boss','normal','encounter_type'],
 'drop':['drop','loot','equipment_chance','rune','potion','enhancement','refinement','rebirth','artifact'],
 'limits':['daily','weekly','monthly','limit','cap','reset'],
}
def pyfiles():
 for p in ROOT.rglob('*.py'):
  if not any(x in SKIP for x in p.relative_to(ROOT).parts): yield p
def source_rows():
 rows=[]
 for p in pyfiles():
  try:s=p.read_text(encoding='utf-8-sig')
  except Exception:continue
  low=s.lower();cats=[k for k,v in TERMS.items() if any(t in low for t in v)]
  if not cats:continue
  lines=s.splitlines()
  hits=[]
  for n,line in enumerate(lines,1):
   ll=line.lower()
   matched=sorted({t for vals in TERMS.values() for t in vals if t in ll})
   if matched:hits.append({'line':n,'terms':matched,'text':line.strip()[:500]})
  rows.append({'file':p.relative_to(ROOT).as_posix(),'categories':cats,'hits':hits[:400]})
 return rows
def ast_evidence(rows):
 out=[]
 for row in rows:
  p=ROOT/row['file']
  try:tree=ast.parse(p.read_text(encoding='utf-8-sig'))
  except Exception:continue
  for node in ast.walk(tree):
   if isinstance(node,(ast.Assign,ast.AnnAssign)):
    targets=node.targets if isinstance(node,ast.Assign) else [node.target]
    names=[]
    for t in targets:
     if isinstance(t,ast.Name):names.append(t.id)
    for name in names:
     nl=name.lower()
     if any(term in nl for vals in TERMS.values() for term in vals):
      try:value=ast.literal_eval(node.value)
      except Exception:value='<dynamic>'
      out.append({'file':row['file'],'line':getattr(node,'lineno',0),'name':name,'value':value})
   elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
    nl=node.name.lower()
    if any(term in nl for vals in TERMS.values() for term in vals):out.append({'file':row['file'],'line':node.lineno,'function':node.name})
 return out
def classify(evidence):
 configured=[]
 for e in evidence:
  if 'name' not in e:continue
  n=e['name'].lower();v=e['value']
  if any(x in n for x in ('chance','rate','probab','weight','reward','resource','limit','cap','reset')):configured.append(e)
 return configured
def main():
 rows=source_rows();evidence=ast_evidence(rows);configured=classify(evidence)
 required={'guild':False,'contract':False,'drop':False,'encounter':False}
 for r in rows:
  for k in required:
   if k in r['categories']:required[k]=True
 findings=[]
 for k,v in required.items():findings.append({'check':f'{k}_owner_evidence_found','status':'PASS' if v else 'FAIL'})
 status='PASS' if all(required.values()) else 'FAIL'
 report={'stage':'18.30.14a','status':status,'generated_at':datetime.now(timezone.utc).isoformat(),'scope':'read-only repository audit','approved_workloads':{'guild_month_days':30,'guild_member_counts':[1,10],'contracts_completed':True,'elite_kills_completed':True,'drop_scenarios':[{'name':'mixed','normal':8500,'elite':1400,'boss':100,'total':10000},{'name':'normal_10000','normal':10000,'elite':0,'boss':0,'total':10000},{'name':'elite_10000','normal':0,'elite':10000,'boss':0,'total':10000},{'name':'boss_10000','normal':0,'elite':0,'boss':10000,'total':10000}],'total_kills':40000},'source_files':rows,'ast_evidence':evidence,'configured_values':configured,'checks':findings,'recommended_contract':{'guild_calculator':'derive rewards and limits from audited production owners; no duplicated reward constants','drop_runner':'invoke canonical post-victory drop entrypoint without combat, progression, DB persistence, or production mutations','reporting':['configured chance','expected count','actual count','actual rate','difference percentage points','z score when binomial assumptions are valid','item and category conservation']},'follow_up':'Stage 18.30.14b implements only after this audit identifies authoritative owners'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8')
 print('[AUDIT] files:',len(rows));print('[AUDIT] evidence:',len(evidence));print('[AUDIT] configured values:',len(configured));print('[REPORT]',OUT.relative_to(ROOT));print('[STATUS]',status)
 return 0 if status=='PASS' else 2
if __name__=='__main__':raise SystemExit(main())
