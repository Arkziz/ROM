#!/usr/bin/env python3
from __future__ import annotations
import ast,hashlib,json,sqlite3,subprocess,sys,tempfile,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'/'stage_18_31_1_final_closure_audit.json'
SKIP={'backup','patch','reports','.git','.venv','venv','__pycache__'}
ACCEPTED_RISKS=[
 {'id':'stage_18_30_experimental','text':'Stage 18.30 closed as experimental tooling; long progression runs are not an approved balance baseline.'},
 {'id':'stage_18_30_14c_not_applied','text':'Stage 18.30.14c was not applied; last successful Stage 18.30 commit is 756963f117ac3a785ad87f7dba7541b1d908f98c.'},
 {'id':'guild_drop_40000_deferred','text':'The guild/drop 40,000-victory fixture was not completed and is deferred.'},
 {'id':'guild_contract_log_name','text':'Guild contract log target-mob naming remains separate future work if still reproducible.'},
]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cmd(args,timeout=300):return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
def add(checks,name,status,details=None,blocking=True):checks.append({'name':name,'status':'PASS' if status else 'FAIL','blocking':blocking,'details':details})
def pyfiles():
 for p in ROOT.rglob('*.py'):
  rel=p.relative_to(ROOT)
  if not any(x in SKIP for x in rel.parts):yield p
def compile_audit():
 errors=[];count=0
 for p in pyfiles():
  count+=1
  try:s=p.read_text(encoding='utf-8-sig');ast.parse(s);compile(s,str(p),'exec')
  except Exception as e:errors.append({'file':p.relative_to(ROOT).as_posix(),'error':repr(e)})
 return count,errors
def db_audit():
 # Never open live game.db. Copy DB/WAL/SHM into an isolated temporary snapshot first.
 with tempfile.TemporaryDirectory(prefix='rom_stage18_closure_') as td:
  t=Path(td);dst=t/'game.db';shutil.copy2(ROOT/'game.db',dst)
  copied=['game.db']
  for suffix in ('-wal','-shm'):
   src=ROOT/('game.db'+suffix)
   if src.is_file():shutil.copy2(src,t/('game.db'+suffix));copied.append('game.db'+suffix)
  uri=dst.resolve().as_uri()+'?mode=ro';con=sqlite3.connect(uri,uri=True);cur=con.cursor()
  quick=[r[0] for r in cur.execute('PRAGMA quick_check').fetchall()];foreign=[list(r) for r in cur.execute('PRAGMA foreign_key_check').fetchall()];tables=[r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()];con.close()
  return {'quick_check':quick,'foreign_key_check':foreign,'table_count':len(tables),'tables':tables,'snapshot_files':copied}
def migration_audit():
 files=sorted((ROOT/'migrations').glob('*.py')) if (ROOT/'migrations').is_dir() else []
 names=[p.name for p in files]
 attribute_chain=['042_attribute_points_foundation.py','043_existing_character_attribute_point_policy.py','044_attribute_respec_foundation.py']
 return {'count':len(files),'files':names,'attribute_migration_chain':attribute_chain,'attribute_migration_chain_present':all(x in names for x in attribute_chain),'migration_050_actual':'050_event_kill_statistics.py' if '050_event_kill_statistics.py' in names else None}
def smoke_inventory():
 candidates=[]
 for p in sorted((ROOT/'tools').glob('smoke_test_*.py')):
  n=p.name.lower()
  if any(x in n for x in ('final','stage_18','item_id','migration','startup','import','production_parity','player_progression_direct','boss_completion_contract','event')):candidates.append(p)
 return candidates
def main():
 before={p.as_posix():digest(p) for p in [ROOT/'game.db',ROOT/'main.py'] if p.is_file()};checks=[]
 g=cmd(['git','status','--porcelain']);branch=cmd(['git','branch','--show-current']);head=cmd(['git','rev-parse','HEAD']);subject=cmd(['git','show','-s','--format=%s','HEAD'])
 allowed=('tools/run_final_stage_18_closure_audit.py','tools/smoke_test_final_stage_18_closure_audit.py','MD/STAGE_18_31_1_FINAL_CLOSURE_AUDIT.md','reports/stage_18_31_1_')
 dirty=[x for x in g.stdout.splitlines() if not any(a in x.replace('\\','/') for a in allowed)]
 add(checks,'git status contains only current closure artifacts',g.returncode==0 and not dirty,{'raw':g.stdout,'blocking':dirty});add(checks,'branch develop',branch.stdout.strip()=='develop',branch.stdout.strip());add(checks,'expected Stage 18.30 checkpoint',head.stdout.strip()=='756963f117ac3a785ad87f7dba7541b1d908f98c' and subject.stdout.strip()=='Stage 18.30.14b: audit drop adapter and guild projection contract',{'head':head.stdout.strip(),'subject':subject.stdout.strip()})
 count,errors=compile_audit();add(checks,'all production Python parses and compiles',not errors,{'file_count':count,'errors':errors})
 db=db_audit();add(checks,'database quick_check',db['quick_check']==['ok'],db['quick_check']);add(checks,'database foreign_key_check',not db['foreign_key_check'],db['foreign_key_check'])
 mig=migration_audit();add(checks,'canonical attribute migration chain 042-044 present',mig['attribute_migration_chain_present'],mig)
 smokes=smoke_inventory();add(checks,'compact regression inventory present',bool(smokes),[p.relative_to(ROOT).as_posix() for p in smokes])
 # Static import-surface check avoids starting the Telegram bot or writing production state.
 main_source=(ROOT/'main.py').read_text(encoding='utf-8-sig');main_tree=ast.parse(main_source);imports=sum(isinstance(n,(ast.Import,ast.ImportFrom)) for n in ast.walk(main_tree));add(checks,'startup import surface parses',imports>0,{'import_nodes':imports})
 # Namespace evidence only; no mutation and no allocator calls.
 namespace_files=[]
 for p in pyfiles():
  try:s=p.read_text(encoding='utf-8-sig')
  except Exception:continue
  if ('4000' in s and '9999' in s) or '10010000' in s or 'generated equipment' in s.lower():namespace_files.append(p.relative_to(ROOT).as_posix())
 add(checks,'item namespace evidence present',bool(namespace_files),namespace_files[:100])
 after={p.as_posix():digest(p) for p in [ROOT/'game.db',ROOT/'main.py'] if p.is_file()};add(checks,'production hashes unchanged',before==after,{'before':before,'after':after})
 blocking=[x for x in checks if x['blocking'] and x['status']!='PASS'];status='PASS' if not blocking else 'FAIL'
 report={'stage':'18.31.1','status':status,'generated_at':datetime.now(timezone.utc).isoformat(),'scope':'final read-only Stage 18 closure audit','git':{'branch':branch.stdout.strip(),'head':head.stdout.strip(),'subject':subject.stdout.strip()},'checks':checks,'database':db,'migrations':mig,'compact_regression_inventory':[p.relative_to(ROOT).as_posix() for p in smokes],'accepted_risks':ACCEPTED_RISKS,'explicitly_not_an_accepted_risk':'The duplicate auto-escape notification defect is already fixed and is not listed as open debt.','manual_acceptance_required':True,'manual_acceptance_groups':['registration/profile','PvE normal/elite/boss','inventory/equipment/refinement/runes/repair','progression/economy','world UI','guilds/contracts','PvP/trade','events','restart/no traceback'],'next_step':'Run manual acceptance matrix, then Stage 18.31.2 documentation/final dump and optional develop-to-master merge after explicit approval.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8');print('[AUDIT] Python files:',count);print('[AUDIT] DB tables:',db['table_count']);print('[AUDIT] compact checks inventoried:',len(smokes));print('[AUDIT] blocking failures:',len(blocking));print('[REPORT]',OUT.relative_to(ROOT));print('[STATUS]',status);return 0 if status=='PASS' else 2
if __name__=='__main__':raise SystemExit(main())
