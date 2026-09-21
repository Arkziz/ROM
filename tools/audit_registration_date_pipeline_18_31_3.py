#!/usr/bin/env python3
from __future__ import annotations
import ast,json,re,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports'/'stage_18_31_3_registration_date_pipeline_audit.json'
DOC=ROOT/'MD'/'STAGE_18_31_3_REGISTRATION_DATE_PIPELINE_AUDIT.md'
CANDIDATE_COLUMNS=('created_at','registered_at','registration_date','created_date','signup_at','joined_at')

def read(rel):return (ROOT/rel).read_text(encoding='utf-8')
def functions(src,name):
 tree=ast.parse(src);return [n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
def source_segment(src,node):return ast.get_source_segment(src,node) or ''
def scan_sources():
 hits=[]
 patterns=('Дата реєстрації','не зафіксована','created_at','registered_at','registration_date','signup_at','joined_at')
 for base in ('handlers','systems','db_modules','migrations'):
  for path in sorted((ROOT/base).rglob('*.py')):
   text=path.read_text(encoding='utf-8')
   matched=[p for p in patterns if p in text]
   if matched:hits.append({'file':path.relative_to(ROOT).as_posix(),'patterns':matched})
 return hits

def schema_from_source():
 connection=read('db_modules/connection.py');player=read('db_modules/player.py')
 create_nodes=functions(player,'create_user')
 if len(create_nodes)!=1:raise RuntimeError('Expected one create_user owner')
 create_src=source_segment(player,create_nodes[0])
 users_create='CREATE TABLE IF NOT EXISTS users' in connection
 declared={c for c in CANDIDATE_COLUMNS if re.search(r'\b'+re.escape(c)+r'\b',connection)}
 inserted={c for c in CANDIDATE_COLUMNS if re.search(r'\b'+re.escape(c)+r'\b',create_src)}
 return {'users_create_present':users_create,'candidate_columns_declared':sorted(declared),'candidate_columns_inserted_by_create_user':sorted(inserted),'create_user_imports_datetime':'from datetime import datetime' in create_src,'create_user_sets_last_energy_update':'last_energy_update' in create_src}

def live_schema_read_only():
 db=ROOT/'game.db'
 if not db.exists():return {'exists':False,'users_columns':[],'candidate_columns':[],'candidate_values':{}}
 uri='file:'+db.as_posix()+'?mode=ro'
 conn=sqlite3.connect(uri,uri=True);conn.row_factory=sqlite3.Row
 try:
  cols=[str(r['name']) for r in conn.execute('PRAGMA table_info(users)').fetchall()]
  candidates=[c for c in CANDIDATE_COLUMNS if c in cols]
  values={}
  if candidates:
   row=conn.execute('SELECT '+','.join('"'+c+'"' for c in candidates)+' FROM users ORDER BY user_id LIMIT 1').fetchone()
   values={} if row is None else {c:row[c] for c in candidates}
  return {'exists':True,'users_columns':cols,'candidate_columns':candidates,'candidate_values':values,'user_count':int(conn.execute('SELECT COUNT(*) FROM users').fetchone()[0])}
 finally:conn.close()

def classify(source_schema,live,hits):
 display_files=[h['file'] for h in hits if 'Дата реєстрації' in h['patterns'] or 'не зафіксована' in h['patterns']]
 declared=source_schema['candidate_columns_declared'];inserted=source_schema['candidate_columns_inserted_by_create_user'];live_cols=live.get('candidate_columns',[])
 if not declared and not live_cols:
  cause='NO_CANONICAL_REGISTRATION_TIMESTAMP_FIELD'
  conclusion='Схема users не має canonical поля дати реєстрації; create_user не може його записувати, а UI закономірно показує fallback.'
 elif (declared or live_cols) and not inserted:
  cause='FIELD_EXISTS_BUT_CREATE_USER_DOES_NOT_WRITE_IT'
  conclusion='Поле існує, але canonical create_user не записує дату реєстрації.'
 else:
  cause='READ_OR_LEGACY_DATA_MISMATCH'
  conclusion='Поле і запис існують; потрібне виправлення читання UI або policy для legacy NULL/empty значень.'
 return cause,conclusion,display_files

def main():
 before={p.name:(p.exists(),p.stat().st_size if p.exists() else None,p.stat().st_mtime_ns if p.exists() else None) for p in (ROOT/'game.db',ROOT/'game.db-wal',ROOT/'game.db-shm')}
 hits=scan_sources();source_schema=schema_from_source();live=live_schema_read_only();cause,conclusion,display_files=classify(source_schema,live,hits)
 result={'stage':'18.31.3','status':'PASS','audit_mode':'READ_ONLY','generated_at':datetime.now(timezone.utc).isoformat(),'source_schema':source_schema,'live_database':live,'source_hits':hits,'display_owner_candidates':display_files,'root_cause':cause,'conclusion':conclusion,'recommended_fix_stage':'18.31.4','recommended_scope':['add one canonical UTC registration timestamp field if absent','write it only on first account creation','preserve it on existing-account /start and DEV reset','read the same canonical field in menu/profile','define non-destructive legacy backfill policy','add fresh-DB and existing-account regression'],'production_mutated':False}
 after={p.name:(p.exists(),p.stat().st_size if p.exists() else None,p.stat().st_mtime_ns if p.exists() else None) for p in (ROOT/'game.db',ROOT/'game.db-wal',ROOT/'game.db-shm')}
 if before!=after:raise RuntimeError('Production DB/WAL/SHM changed during audit')
 REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 DOC.parent.mkdir(parents=True,exist_ok=True);DOC.write_text('# Stage 18.31.3: Аудит дати реєстрації\n\n**Статус:** PASS  \n**Режим:** READ-ONLY\n\n## Висновок\n\n'+conclusion+'\n\n## Root cause\n\n`'+cause+'`\n\n## Наступний підетап\n\nStage 18.31.4 має виправити canonical запис, збереження, читання та legacy policy без зміни інших account timestamps.\n',encoding='utf-8')
 print('[AUDIT] root cause:',cause);print('[AUDIT] live candidate columns:',live.get('candidate_columns',[]));print('[AUDIT] display owners:',display_files);print('[STATUS] PASS')
if __name__=='__main__':main()
