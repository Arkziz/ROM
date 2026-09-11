#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,hashlib,json,sqlite3,sys
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]; DB=R/"game.db"
REPORT=R/"reports/stage_18_18_0_pve_auto_escape_read_only_audit.json"; MD=R/"MD/STAGE_18_18_0_PVE_AUTO_ESCAPE_READ_ONLY_AUDIT.md"
SCAN=("main.py","handlers","systems","db_modules","data","tools")
TOKENS=("combat","battle","fight","mob","boss","elite","reward","loot","exp","gold","busy","escape","flee","timeout","deadline","started_at","worker","recovery")
def read(p):return p.read_text(encoding="utf-8-sig")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dotted(n):
 parts=[]
 while isinstance(n,ast.Attribute):parts.append(n.attr);n=n.value
 if isinstance(n,ast.Name):parts.append(n.id);return ".".join(reversed(parts))
 return ""
def scan():
 files=[]; defs=[]; globals_=[]; calls=[]; sql=[]; imports=[]; registrations=[]
 paths=[]
 for entry in SCAN:
  p=R/entry
  paths += [p] if p.is_file() else list(p.rglob("*.py")) if p.exists() else []
 for p in sorted(set(paths)):
  rel=str(p.relative_to(R)).replace("\\","/")
  try:text=read(p);tree=ast.parse(text)
  except Exception as e:files.append({"file":rel,"parse_error":str(e)});continue
  files.append({"file":rel,"parse_error":None,"sha256":sha(p)})
  for n in tree.body:
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    low=n.name.lower()
    if any(t in low for t in TOKENS):
     segment=ast.get_source_segment(text,n) or ""
     defs.append({"file":rel,"name":n.name,"line":n.lineno,"end":n.end_lineno,"async":isinstance(n,ast.AsyncFunctionDef),"args":[a.arg for a in n.args.args],"has_lock":any(x in segment for x in ("Lock(","RLock(","BEGIN IMMEDIATE","transaction","atomic")),"has_reward_terms":any(x in segment.lower() for x in ("reward","loot","exp","gold","quest","contract")),"has_cleanup_terms":any(x in segment.lower() for x in ("pop(","del ","delete ","clear","busy","combat")),"has_time_terms":any(x in segment.lower() for x in ("time.","datetime","started_at","deadline","timeout"))})
   elif isinstance(n,(ast.Assign,ast.AnnAssign)):
    targets=n.targets if isinstance(n,ast.Assign) else [n.target]
    for t in targets:
     if isinstance(t,ast.Name) and any(k in t.id.lower() for k in ("combat","battle","fight","mob","boss","busy","session","state")):
      globals_.append({"file":rel,"name":t.id,"line":n.lineno,"kind":type(n.value).__name__ if getattr(n,"value",None) else None})
  for n in ast.walk(tree):
   if isinstance(n,ast.Call):
    name=dotted(n.func)
    if any(t in name.lower() for t in TOKENS):calls.append({"file":rel,"name":name,"line":n.lineno})
    if any(x in name for x in ("message_handler","callback_query_handler","register_message_handler","register_callback_query_handler")):registrations.append({"file":rel,"name":name,"line":n.lineno})
   elif isinstance(n,ast.Constant) and isinstance(n.value,str):
    up=n.value.upper()
    if any(k in up for k in ("CREATE TABLE","ALTER TABLE","INSERT INTO","UPDATE ","DELETE FROM")) and any(t.upper() in up for t in ("COMBAT","BATTLE","FIGHT","BUSY")):sql.append({"file":rel,"line":n.lineno,"sql":n.value[:1000]})
   elif isinstance(n,(ast.Import,ast.ImportFrom)):
    mod=n.module if isinstance(n,ast.ImportFrom) else ",".join(a.name for a in n.names)
    if mod and any(t in mod.lower() for t in ("combat","boss","mob","notification","scheduler")):imports.append({"file":rel,"module":mod,"line":n.lineno})
 return {"files":files,"functions":defs,"state_globals":globals_,"calls":calls,"combat_sql":sql,"imports":imports,"handler_registrations":registrations}
def db_audit():
 before=sha(DB);c=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True)
 try:
  c.execute("PRAGMA query_only=ON");tables=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")];detail={}
  for table in tables:
   cols=[{"name":r[1],"type":r[2],"notnull":bool(r[3]),"default":r[4],"pk":bool(r[5])} for r in c.execute(f'PRAGMA table_info("{table}")')]
   if any(k in table.lower() for k in ("combat","battle","fight","session","user")) or any(any(k in x["name"].lower() for k in ("combat","battle","busy","started","deadline","timeout")) for x in cols):detail[table]=cols
  out={"quick_check":c.execute("PRAGMA quick_check").fetchone()[0],"foreign_key_violations":c.execute("PRAGMA foreign_key_check").fetchall(),"total_changes":c.total_changes,"relevant_schema":detail}
 finally:c.close()
 out.update(sha256_before=before,sha256_after=sha(DB));out["unchanged"]=out["sha256_before"]==out["sha256_after"];return out
def main():
 repo=scan(); db=db_audit(); parse_errors=[x for x in repo["files"] if x["parse_error"]]
 state_names=sorted({x["name"] for x in repo["state_globals"]}); schema_text=json.dumps(db["relevant_schema"],ensure_ascii=False).lower()
 persistent=any(k in schema_text for k in ("combat_started_at","combat_deadline","battle_started_at","battle_deadline","combat_state"))
 workers=[x for x in repo["functions"] if any(k in x["name"].lower() for k in ("worker","recover","startup","maintenance","timeout"))]
 completion=[x for x in repo["functions"] if any(k in x["name"].lower() for k in ("complete","finish","end_combat","victory","defeat","escape","flee"))]
 findings=[]
 if not persistent:findings.append({"severity":"BLOCKER","code":"NO_PERSISTENT_DEADLINE","detail":"No authoritative PvE started_at/deadline persistence was found."})
 if not workers:findings.append({"severity":"BLOCKER","code":"NO_TIMEOUT_RECOVERY_OWNER","detail":"No clear timeout/startup recovery owner was found."})
 if not completion:findings.append({"severity":"HIGH","code":"COMPLETION_OWNER_UNCLEAR","detail":"No uniquely named canonical PvE completion API was identified by static scan."})
 report={"stage":"18.18.0","status":"PASS","generated_at_utc":datetime.now(timezone.utc).isoformat(),"read_only":True,"production_mutation":False,"approved_policy":{"timeout_seconds":300,"deadline_origin":"encounter_started_at","hp_mp":"preserve_actual","energy":"not_refunded","extra_durability_penalty":False,"death_penalty":False,"rewards_and_progress":False,"enemy_state":"discard","normal_elite_boss_same_policy":True,"restart_preserves_original_deadline":True,"completion":"first_atomic_completion_wins","stale_callback_message":"⚠️ Цей бій уже завершено.","production_message":"🏃 Бій завершено автоматично\n\nМинуло 5 хвилин із початку бою, тому персонаж утік.\n\nНагороди за цей бій не нараховано."},"repository":repo,"database":db,"summary":{"python_files_scanned":len(repo["files"]),"combat_related_functions":len(repo["functions"]),"state_globals":state_names,"relevant_tables":sorted(db["relevant_schema"]),"persistent_deadline_found":persistent,"recovery_candidates":workers,"completion_candidates":completion},"findings":findings,"recommended_mutation":{"architecture":"persistent deadline plus single atomic terminal completion API","required_components":["schema migration for authoritative started_at/deadline if absent","pure timeout eligibility policy","atomic completion guard shared by attack and timeout","startup recovery for expired and pending encounters","single background sweeper or existing worker integration","stale callback rejection","notification after committed escape"],"test_matrix":["299/300/301 seconds","attack versus timeout race","duplicate sweeper","restart before deadline","restart after deadline","normal/elite/boss","HP/MP preserved","energy not refunded","no durability death penalty","no EXP/gold/loot/quest/contract/event progress"]},"next_patch":"18.18.1 production implementation based on this audit"}
 if parse_errors or db["quick_check"]!="ok" or db["foreign_key_violations"] or db["total_changes"] or not db["unchanged"]:report["status"]="FAIL"
 REPORT.parent.mkdir(exist_ok=True);MD.parent.mkdir(exist_ok=True);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
 lines=["# Stage 18.18.0: PvE Auto-Escape Read-only Audit","",f"**Status:** {report['status']}","**Production mutation:** none","", "## Approved policy","","- Deadline: 300 seconds from authoritative encounter start.","- HP and MP remain at their actual values.","- Energy is not refunded.","- No extra durability or death penalty is applied.","- No EXP, gold, loot, kill, quest, contract, boss or event progress is awarded.","- Normal, elite and boss encounters use the same timeout policy.","- Restart preserves the original deadline.","- First atomic terminal completion wins; later attacks become stale.","", "## Audit summary","",f"- Python files scanned: `{len(repo['files'])}`.",f"- Combat-related functions: `{len(repo['functions'])}`.",f"- State globals: `{state_names}`.",f"- Relevant DB tables: `{sorted(db['relevant_schema'])}`.",f"- Persistent deadline found: `{persistent}`.",f"- Findings: `{len(findings)}`.","", "## Findings",""]
 lines += [f"- **{x['severity']} {x['code']}**: {x['detail']}" for x in findings] or ["- No blocking architecture gaps found by static audit."]
 lines += ["", "## Required mutation architecture","","- Persistent authoritative started_at/deadline.","- One atomic terminal completion API shared by attack and timeout.","- Restart recovery and one sweeper owner.","- Rewards committed only by victory completion, never by timeout.","- User notification only after escape commit.","", "## Database safety","",f"- quick_check: `{db['quick_check']}`.",f"- FK violations: `{len(db['foreign_key_violations'])}`.",f"- DB unchanged: `{db['unchanged']}`."]
 MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
 if report["status"]!="PASS":raise RuntimeError("Audit execution invariants failed")
 print(json.dumps({"status":"PASS","files":len(repo["files"]),"functions":len(repo["functions"]),"findings":len(findings),"persistent_deadline":persistent,"db_unchanged":True,"json":str(REPORT.relative_to(R)),"md":str(MD.relative_to(R))},ensure_ascii=False))
if __name__=="__main__":main()
