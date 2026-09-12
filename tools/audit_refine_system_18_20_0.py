#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];DB=R/"game.db";REPORT=R/"reports/stage_18_20_0_refine_system_read_only_audit.json";MD=R/"MD/STAGE_18_20_0_REFINE_SYSTEM_READ_ONLY_AUDIT.md"
FILES=("systems/refine_system.py","handlers/refine.py","db_modules/refine.py","db.py","main.py")
def read(rel):return (R/rel).read_text(encoding="utf-8-sig")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def top_functions(rel):
 text=read(rel);tree=ast.parse(text);rows=[]
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   seg=ast.get_source_segment(text,n) or ""
   if any(k in (n.name+seg).lower() for k in ("refine","заточ")):rows.append({"name":n.name,"line":n.lineno,"end":n.end_lineno,"source":seg})
 return rows
def registrations(rel):
 text=read(rel);tree=ast.parse(text);rows=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.FunctionDef):
   for d in n.decorator_list:
    src=ast.get_source_segment(text,d) or ""
    if "callback_query_handler" in src and "refine" in src:rows.append({"owner":n.name,"line":n.lineno,"decorator":src})
 return rows
def db_audit():
 before=sha(DB);c=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True);c.row_factory=sqlite3.Row
 try:
  c.execute("PRAGMA query_only=ON");tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")};attempts=[];schema=[]
  if "refine_attempts" in tables:
   schema=[dict(r) for r in c.execute("PRAGMA table_info('refine_attempts')")]
   attempts=[dict(r) for r in c.execute("SELECT id,user_id,inventory_id,item_id,refine_kind,old_level,new_level,success_chance,roll,refine_success,used_success_rune,stone_quantity,success_rune_quantity,idempotency_key,created_at FROM refine_attempts ORDER BY id DESC LIMIT 50")]
  out={"quick_check":c.execute("PRAGMA quick_check").fetchone()[0],"foreign_key_violations":[tuple(r) for r in c.execute("PRAGMA foreign_key_check")],"total_changes":c.total_changes,"attempt_schema":schema,"recent_attempts":attempts}
 finally:c.close()
 out.update(sha256_before=before,sha256_after=sha(DB));out["unchanged"]=out["sha256_before"]==out["sha256_after"]
 out["impossible_failures"]=[x for x in out["recent_attempts"] if int(x.get("success_chance") or 0)>=100 and not bool(x.get("refine_success"))]
 return out
def main():
 for rel in FILES:
  if not (R/rel).is_file():raise RuntimeError("missing "+rel)
  ast.parse(read(rel),filename=rel)
 system=read("systems/refine_system.py");handler=read("handlers/refine.py")
 funcs={r["name"]:r for r in top_functions("systems/refine_system.py")};hfuncs={r["name"]:r for r in top_functions("handlers/refine.py")}
 required=("get_refine_success_chance","roll_refine_success","get_refine_failure_level","perform_refine_attempt")
 for name in required:
  if name not in funcs:raise RuntimeError("missing canonical function "+name)
 tables={}
 tree=ast.parse(system)
 for n in tree.body:
  if isinstance(n,ast.Assign):
   for t in n.targets:
    if isinstance(t,ast.Name) and t.id in ("WEAPON_REFINE_SUCCESS_CHANCES","ARMOR_REFINE_SUCCESS_CHANCES"):
     tables[t.id]=ast.literal_eval(n.value)
 callbacks=registrations("handlers/refine.py");db=db_audit();findings=[]
 if tables.get("WEAPON_REFINE_SUCCESS_CHANCES",{}).get(1)!=100:findings.append({"severity":"CRITICAL","code":"WEAPON_PLUS_1_CHANCE_NOT_100","detail":"Canonical weapon +1 to +2 chance is not 100%."})
 if db["impossible_failures"]:findings.append({"severity":"CRITICAL","code":"PERSISTED_FAILURE_AT_100_PERCENT","detail":"refine_attempts contains at least one failure persisted with success_chance >= 100.","rows":db["impossible_failures"]})
 roll_src=funcs["roll_refine_success"]["source"]
 if "random.randint(1, 100)" not in roll_src or "roll <= chance" not in roll_src:findings.append({"severity":"HIGH","code":"ROLL_BOUNDARY_UNEXPECTED","detail":"Canonical roll contract is not randint(1,100) with roll<=chance."})
 perform=funcs["perform_refine_attempt"]["source"]
 for token,code in (("BEGIN IMMEDIATE","NO_IMMEDIATE_TRANSACTION"),("conn.rollback()","NO_EXCEPTION_ROLLBACK"),("idempotency_key","NO_IDEMPOTENCY"),("refine target changed concurrently","NO_CONCURRENCY_GUARD")):
  if token not in perform:findings.append({"severity":"HIGH","code":code,"detail":token+" not found in perform_refine_attempt."})
 mismatch=[]
 for row in db["recent_attempts"]:
  table=tables.get("WEAPON_REFINE_SUCCESS_CHANCES" if row.get("refine_kind")=="weapon" else "ARMOR_REFINE_SUCCESS_CHANCES",{})
  expected=100 if row.get("used_success_rune") else table.get(int(row.get("old_level") or 0),0)
  if int(row.get("success_chance") or 0)!=int(expected):mismatch.append({"row":row,"expected_chance":expected})
 if mismatch:findings.append({"severity":"CRITICAL","code":"PERSISTED_CHANCE_DIFFERS_FROM_CANONICAL_TABLE","detail":"Persisted attempt chance differs from current canonical table.","rows":mismatch})
 ui_truth="after_level" in hfuncs.get("build_refine_attempt_result_text",{}).get("source","") and "after_level > before_level" in hfuncs.get("build_refine_attempt_result_text",{}).get("source","")
 report={"stage":"18.20.0","status":"PASS","generated_at_utc":datetime.now(timezone.utc).isoformat(),"read_only":True,"production_mutation":False,"user_evidence":{"item":"common one-handed sword level 1","old_refine_level":1,"displayed_success_chance":100,"observed_result":"failure without level change","stone_consumed":True},"ownership":{"system_owner":"systems/refine_system.py","handler_owner":"handlers/refine.py","system_functions":sorted(funcs),"handler_functions":sorted(hfuncs),"callbacks":callbacks,"callback_count":len(callbacks)},"canonical_tables":tables,"contracts":{"roll_source":roll_src,"transaction_source":perform,"result_ui_uses_level_delta":ui_truth},"database":db,"findings":findings,"diagnosis":{"confirmed_invariant":"At current weapon level +1, canonical chance is 100%; a normal stone attempt must succeed to +2.","likely_failure_classes":["persisted audit row contradicts canonical chance/roll","runtime import or duplicate owner differs from inspected source","handler derives visible success from stale before/after snapshots","attempt replay/idempotency returns an earlier terminal result","transaction updates a different DB or inventory row"],"mutation_not_yet_allowed":"Use exact persisted attempt row and owner map to select one proven cause; do not change balance tables."},"recommended_next":{"patch":"18.20.1 minimal refine production recovery","required_tests":["weapon +0/+1/+2 100% boundaries","armor +0/+1 100% boundaries","forced failure at non-100 chance","success rune exact success","one stone consumed exactly once","exception rollback","stale callback","foreign item","max level","idempotent replay","preview/result parity"]}}
 if db["quick_check"]!="ok" or db["foreign_key_violations"] or db["total_changes"] or not db["unchanged"]:report["status"]="FAIL"
 REPORT.parent.mkdir(exist_ok=True);MD.parent.mkdir(exist_ok=True);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
 lines=["# Stage 18.20.0: Refine System Read-only Audit","",f"**Status:** {report['status']}","**Production mutation:** none","","## User reproduction","","A common one-handed level-1 sword refined successfully to +1, then a normal-stone attempt at displayed 100% reported failure, preserved +1 and consumed one stone.","","## Confirmed policy boundary","",f"- Canonical weapon chance at +1 is `{tables.get('WEAPON_REFINE_SUCCESS_CHANCES',{}).get(1)}` percent.","- Balance tables were not changed.","","## Ownership","","- `systems/refine_system.py` owns chance, roll, failure level and atomic attempt.","- `handlers/refine.py` owns preview, callbacks and result rendering.",f"- Refine callback registrations found: `{len(callbacks)}`.","","## Database evidence","",f"- Recent attempts reviewed: `{len(db['recent_attempts'])}`.",f"- Failures persisted at chance >=100: `{len(db['impossible_failures'])}`.","", "## Findings",""]
 lines += [f"- **{x['severity']} {x['code']}**: {x['detail']}" for x in findings] or ["- No persisted contradiction found; runtime owner/import and snapshot paths remain primary suspects."]
 lines += ["","## Safety decision","","Do not modify success chances. The next mutation must address only the proven owner, transaction, replay or rendering defect identified from this audit.","","## Database safety","",f"- quick_check: `{db['quick_check']}`.",f"- FK violations: `{len(db['foreign_key_violations'])}`.",f"- DB unchanged: `{db['unchanged']}`."]
 MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
 if report["status"]!="PASS":raise RuntimeError("audit safety invariants failed")
 print(json.dumps({"status":"PASS","callbacks":len(callbacks),"recent_attempts":len(db["recent_attempts"]),"impossible_100_failures":len(db["impossible_failures"]),"findings":len(findings),"db_unchanged":True,"json":str(REPORT.relative_to(R)),"md":str(MD.relative_to(R))},ensure_ascii=False))
if __name__=="__main__":main()
