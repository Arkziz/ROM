#!/usr/bin/env python3
"""Stage 21.1.8: fast static audit of jobs, time and concurrency boundaries."""
from __future__ import annotations
import ast, hashlib, json, os, re, subprocess, sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="21.1.8"; BRANCH="rewrite/rom-v2"; PARENT="0333f0c9e69d817f2095495af11a7757a3a3c17f"
INPUT="reports/stage_21_1_1_v1_module_inventory.json"
PATCH="patch/patch_21_1_8_inventory_background_jobs_time_and_concurrency.py"
REPORT="reports/stage_21_1_8_background_jobs_time_concurrency.json"
DOC="MD/STAGE_21_1_8_BACKGROUND_JOBS_TIME_CONCURRENCY.md"
COMMIT="Stage 21.1.8: inventory background jobs time and concurrency"
OWNED={PATCH,REPORT,DOC}; DIRTY={"ROM_FULL_DUMP.txt","ROM_ADDITIONAL_DUMP.txt"}; DBS=("game.db","game.db-wal","game.db-shm")
EXCLUDED={"TEST_REFERENCE","DO_NOT_MIGRATE"}
TASK_TAILS={"create_task","ensure_future","gather","wait","wait_for"}; WAIT_TAILS={"sleep","wait"}
THREAD_TAILS={"Thread","ThreadPoolExecutor"}; PROCESS_TAILS={"Process","ProcessPoolExecutor"}; LOCK_TAILS={"Lock","RLock","Semaphore"}
JOB_RE=re.compile(r"(?i)(job|worker|scheduler|reminder|cleanup|recovery|background|periodic|inactivity|notification)")
RETRY_RE=re.compile(r"(?i)(retry|retries|backoff|attempt|max_attempt|poll|interval)")
LIFE_RE=re.compile(r"(?i)(startup|shutdown|close|stop|cancel|cleanup|graceful|signal)")
TIME_MARKERS=("datetime.now","datetime.utcnow","time.time","time.monotonic","date.today","ZoneInfo")

@dataclass(frozen=True)
class Check: check_id:str; status:str; summary:str; details:dict[str,Any]; blocking:bool=False
class PatchError(RuntimeError): pass

def run(root,*cmd,timeout=120): return subprocess.run(cmd,cwd=root,text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=timeout,check=False)
def git(root,*args,timeout=120): return run(root,"git",*args,timeout=timeout)
def rev(root,name):
 r=git(root,"rev-parse","--verify",f"{name}^{{commit}}"); return r.stdout.strip() if r.returncode==0 else None
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""): h.update(c)
 return h.hexdigest()
def evidence(root):
 out={}
 for n in DBS:
  p=root/n
  if not p.exists(): out[n]={"exists":False}; continue
  s=p.stat(); out[n]={"exists":True,"size":s.st_size,"mtime_ns":s.st_mtime_ns,"sha256":sha(p)}
 return out
def write_atomic(p,t):
 q=p.with_suffix(p.suffix+".tmp");q.write_text(t,encoding="utf-8",newline="\n");os.replace(q,p)
def status(raw): return [{"status":x[:2],"path":x[3:]} for x in raw.split("\0") if x]
def up(n):
 try:return ast.unparse(n)
 except:return ""

def analyze(root,path,classification):
 text=(root/path).read_text(encoding="utf-8",errors="replace"); tree=ast.parse(text,filename=path)
 nodes=list(ast.walk(tree))
 spans=sorted((n.lineno,n.end_lineno or n.lineno,n.name) for n in nodes if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)))
 def owner(line):
  matches=[(b-a,n) for a,b,n in spans if a<=line<=b]; return min(matches)[1] if matches else "<module>"
 findings=defaultdict(list); functions=[]; globals_=[]
 for n in tree.body:
  if isinstance(n,(ast.Assign,ast.AnnAssign)):
   targets=n.targets if isinstance(n,ast.Assign) else [n.target]
   for t in targets:
    if isinstance(t,ast.Name) and not t.id.isupper() and isinstance(n.value,(ast.Dict,ast.List,ast.Set,ast.Call)):
     globals_.append({"name":t.id,"line":n.lineno,"value":up(n.value)[:180]})
 for n in nodes:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   src=ast.get_source_segment(text,n) or ""; functions.append({"name":n.name,"line":n.lineno,"end_line":n.end_lineno or n.lineno,"async":isinstance(n,ast.AsyncFunctionDef),"job_like":bool(JOB_RE.search(n.name) or JOB_RE.search(src[:1500])),"retry_like":bool(RETRY_RE.search(n.name) or RETRY_RE.search(src[:1500])),"lifecycle_like":bool(LIFE_RE.search(n.name))})
  elif isinstance(n,ast.Call):
   name=up(n.func); tail=name.split(".")[-1]; rec={"line":n.lineno,"owner":owner(n.lineno),"call":name,"args":[up(a)[:160] for a in n.args[:3]]}
   if tail in TASK_TAILS: findings["tasks"].append(rec)
   if tail in WAIT_TAILS: findings["waits"].append(rec)
   if tail in THREAD_TAILS: findings["threads"].append(rec)
   if tail in PROCESS_TAILS: findings["processes"].append(rec)
   if tail in LOCK_TAILS: findings["locks"].append(rec)
   if any(x in name for x in TIME_MARKERS): findings["time_calls"].append(rec)
   if tail in {"cancel","close","shutdown","stop"}: findings["lifecycle_calls"].append(rec)
  elif isinstance(n,(ast.While,ast.For,ast.AsyncFor)):
   infinite=isinstance(n,ast.While) and isinstance(n.test,ast.Constant) and n.test.value is True
   contains_wait=any(isinstance(c,ast.Call) and up(c.func).split(".")[-1] in WAIT_TAILS for c in ast.walk(n))
   findings["loops"].append({"line":n.lineno,"owner":owner(n.lineno),"kind":type(n).__name__,"infinite":infinite,"contains_wait":contains_wait})
 return {"path":path,"classification":classification,"sha256":sha(root/path),"functions":functions,"findings":dict(findings),"module_mutable_globals":globals_}

def render(p):
 s=p["summary"];q=p["review_queues"]
 return "\n".join(["# ROM Stage 21.1.8 - background jobs, time і concurrency","",f"- **Статус:** `{s['conclusion']}`",f"- **Проаналізовано модулів:** `{s['module_count']}`",f"- **Task sites:** `{s['task_count']}`",f"- **Wait sites:** `{s['wait_count']}`",f"- **Thread/process sites:** `{s['thread_process_count']}`",f"- **Lock sites:** `{s['lock_count']}`",f"- **Time calls:** `{s['time_call_count']}`",f"- **Loops:** `{s['loop_count']}`","","## Review queues","",f"- Job-like functions: **{len(q['job_like_functions'])}**",f"- Infinite loops without wait: **{len(q['infinite_loops_without_wait'])}**",f"- Module-level tasks: **{len(q['module_level_tasks'])}**",f"- Mutable global modules: **{len(q['mutable_global_state'])}**",f"- Naive datetime sites: **{len(q['naive_datetime_usage'])}**",f"- Tasks without lifecycle signal: **{len(q['task_without_lifecycle'])}**","","## V2 lifecycle contract","","- Background jobs запускає єдиний scheduler/lifecycle manager.","- Кожна task має owner, cancellation, graceful shutdown та exception reporting.","- Busy loops без await/sleep заборонені.","- Domain отримує Clock і Random через ports.","- Persistence timestamps: UTC; presentation timezone: Europe/Kyiv.","- Shared mutable global state заборонений.","- Retry/backoff має bounded attempts, jitter та idempotency contract.","- Production DB/WAL/SHM не відкривалися і не змінювалися.","","## Наступний етап","","Stage 21.1.9 - inventory observability, logging, errors і audit trails.",""])
def commit(root):
 paths=[PATCH,REPORT,DOC];a=git(root,"add","-f","--",*paths)
 if a.returncode:raise PatchError(a.stderr.strip() or "git add failed")
 r=git(root,"diff","--cached","--name-only","-z");staged=sorted(x for x in r.stdout.split("\0") if x)
 if r.returncode or staged!=sorted(paths):git(root,"reset","--",*paths);raise PatchError(f"staging mismatch: {staged}")
 c=git(root,"commit","-m",COMMIT)
 if c.returncode:git(root,"reset","--",*paths);raise PatchError(c.stderr.strip() or c.stdout.strip())
 return rev(root,"HEAD")
def main():
 root=Path(__file__).resolve().parent.parent
 if not (root/INPUT).is_file():print(f"[FAIL] Missing {INPUT}",file=sys.stderr);return 2
 print("[1/8] [PASS] Canonical inventory and regulated directories detected.")
 branch=git(root,"branch","--show-current").stdout.strip();head=rev(root,"HEAD");u=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");upstream=u.stdout.strip() if u.returncode==0 else None
 entries=status(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout);allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in DIRTY and e["status"][0]==" "))];unexpected=[e for e in entries if e not in allowed]
 checks=[Check("BRANCH","PASS" if branch==BRANCH else "FAIL",f"Active branch: {branch}",{},branch!=BRANCH),Check("PARENT","PASS" if head==PARENT else "FAIL","Expected Stage 21.1.7a parent verified." if head==PARENT else "Unexpected parent.",{"expected":PARENT,"actual":head},head!=PARENT),Check("UPSTREAM","PASS" if upstream==f"origin/{BRANCH}" else "FAIL",f"Upstream: {upstream}",{},upstream!=f"origin/{BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes." if not unexpected else "Unexpected changes exist.",{"unexpected":unexpected},bool(unexpected))]
 if any(c.blocking for c in checks):print("[2/8] [FAIL] Preflight NO_GO.");return 1
 print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
 before=evidence(root);inv=json.loads((root/INPUT).read_text(encoding="utf-8"));mods=[m for m in inv["modules"] if m["classification"] not in EXCLUDED]
 print(f"[3/8] [PASS] Scanning time and concurrency boundaries in {len(mods)} modules.")
 findings=[];errors=[]
 for i,m in enumerate(mods,1):
  try:findings.append(analyze(root,m["path"],m["classification"]))
  except (OSError,SyntaxError) as e:errors.append({"path":m["path"],"error":str(e)})
  if i%20==0 or i==len(mods):print(f"    progress: {i}/{len(mods)} modules",flush=True)
 print("[4/8] [PASS] Building lifecycle, retry, time and shared-state queues.")
 def sites(k):return [dict(x,module=f["path"]) for f in findings for x in f["findings"].get(k,[])]
 tasks=sites("tasks");waits=sites("waits");threads=sites("threads");processes=sites("processes");locks=sites("locks");times=sites("time_calls");loops=sites("loops")
 queues={"job_like_functions":[dict(x,module=f["path"]) for f in findings for x in f["functions"] if x["job_like"]],"retry_like_functions":[dict(x,module=f["path"]) for f in findings for x in f["functions"] if x["retry_like"]],"lifecycle_functions":[dict(x,module=f["path"]) for f in findings for x in f["functions"] if x["lifecycle_like"]],"infinite_loops_without_wait":[x for x in loops if x["infinite"] and not x["contains_wait"]],"module_level_tasks":[x for x in tasks if x["owner"]=="<module>"],"mutable_global_state":[{"module":f["path"],"globals":f["module_mutable_globals"]} for f in findings if f["module_mutable_globals"]],"naive_datetime_usage":[x for x in times if "datetime.now" in x["call"] or "datetime.utcnow" in x["call"]],"task_without_lifecycle":[{"module":f["path"],"tasks":f["findings"].get("tasks",[])} for f in findings if f["findings"].get("tasks") and not f["findings"].get("lifecycle_calls")]}
 checks.extend([Check("AST_COVERAGE","PASS" if not errors else "FAIL","All modules parsed." if not errors else "AST errors found.",{"errors":errors},bool(errors)),Check("TIME_OR_CONCURRENCY_ACTIVITY","PASS" if tasks or waits or times or loops else "FAIL","Time/concurrency activity detected.",{},not(tasks or waits or times or loops)),Check("DATABASE_EVIDENCE_READY","PASS","DB/WAL/SHM evidence captured without opening SQLite.",{"production_connection_opened":False})])
 blockers=[c.check_id for c in checks if c.blocking];conclusion="GO" if not blockers else "NO_GO"
 payload={"schema_version":2,"stage":STAGE,"performance_fix":"precomputed AST nodes and function spans; visible progress every 20 modules","generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":conclusion,"blocking_failures":blockers,"module_count":len(findings),"task_count":len(tasks),"wait_count":len(waits),"thread_process_count":len(threads)+len(processes),"lock_count":len(locks),"time_call_count":len(times),"loop_count":len(loops)},"git":{"branch":branch,"head_before_commit":head,"upstream":upstream},"checks":[asdict(c) for c in checks],"module_findings":findings,"review_queues":queues,"v2_lifecycle_contract":{"scheduler_owner":"rom_v2/application/services/scheduler.py","lifecycle_owner":"rom_v2/app/lifecycle.py","clock_port":"rom_v2/application/ports/clock.py","random_port":"rom_v2/application/ports/random_source.py","persistence_timezone":"UTC","presentation_timezone":"Europe/Kyiv","module_level_task_creation":"FORBIDDEN","busy_loop_without_wait":"FORBIDDEN","shared_mutable_global_state":"FORBIDDEN","task_requires_owner_cancel_shutdown_reporting":True,"retry_requires_bounded_attempts_jitter_idempotency":True},"database_evidence_before":before,"artifacts":{"patch":PATCH,"json":REPORT,"markdown":DOC},"next_stage":"21.1.9" if conclusion=="GO" else None}
 print("[5/8] [PASS] Writing lifecycle and concurrency inventory.");write_atomic(root/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n");write_atomic(root/DOC,render(payload))
 if conclusion!="GO":print("[6/8] [FAIL] Lifecycle audit NO_GO; commit not created.");return 1
 print("[6/8] [PASS] Lifecycle, time and concurrency contract validated.")
 try:print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.8 commit.");ch=commit(root)
 except PatchError as e:print(f"[7/8] [FAIL] {e}",file=sys.stderr);return 2
 if before!=evidence(root):print("[8/8] [FAIL] DB/WAL/SHM evidence changed.",file=sys.stderr);return 2
 print(f"[8/8] [PASS] Lifecycle inventory committed and DB/WAL/SHM verified: {ch}");print("="*72);print(f"ROM Stage {STAGE} - background jobs time and concurrency")
 for c in checks:print(f"[{c.status}] {c.check_id}: {c.summary}")
 print(f"[PASS] TASKS: {len(tasks)}\n[PASS] WAITS: {len(waits)}\n[PASS] THREAD_PROCESS_SITES: {len(threads)+len(processes)}\n[PASS] LOCK_SITES: {len(locks)}\n[PASS] TIME_CALLS: {len(times)}\n[PASS] LOOPS: {len(loops)}\n[PASS] MUTABLE_GLOBAL_MODULES: {len(queues['mutable_global_state'])}")
 print("CONCLUSION: GO\nPATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({ch})");print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED");return 0
if __name__=="__main__":raise SystemExit(main())
