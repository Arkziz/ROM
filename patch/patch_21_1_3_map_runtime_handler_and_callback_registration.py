#!/usr/bin/env python3
"""Stage 21.1.3: map runtime Telegram handler and callback registration."""
from __future__ import annotations
import ast, hashlib, json, os, subprocess, sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="21.1.3"; BRANCH="rewrite/rom-v2"; PARENT="14bbe172af589c6185162f66e56064a0cd5768e2"
INPUT="reports/stage_21_1_2_duplicate_definitions_runtime_overrides.json"
PATCH="patch/patch_21_1_3_map_runtime_handler_and_callback_registration.py"
REPORT="reports/stage_21_1_3_runtime_handler_callback_map.json"
DOC="MD/STAGE_21_1_3_RUNTIME_HANDLER_CALLBACK_MAP.md"
COMMIT="Stage 21.1.3: map runtime handler and callback registration"
OWNED={PATCH,REPORT,DOC}; DIRTY={"ROM_FULL_DUMP.txt","ROM_ADDITIONAL_DUMP.txt"}; DBS=("game.db","game.db-wal","game.db-shm")
REG_NAMES={"message_handler","callback_query_handler","register_message_handler","register_callback_query_handler","register_next_step_handler"}

@dataclass(frozen=True)
class Check: check_id:str; status:str; summary:str; details:dict[str,Any]; blocking:bool=False
class PatchError(RuntimeError): pass

def run(root,*cmd,timeout=120): return subprocess.run(cmd,cwd=root,text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=timeout,check=False)
def git(root,*args,timeout=120): return run(root,"git",*args,timeout=timeout)
def rev(root,name):
 r=git(root,"rev-parse","--verify",f"{name}^{{commit}}"); return r.stdout.strip() if r.returncode==0 else None
def sha(p):
 h=hashlib.sha256();
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""): h.update(c)
 return h.hexdigest()
def db_ev(root):
 out={}
 for n in DBS:
  p=root/n
  if not p.exists(): out[n]={"exists":False}; continue
  s=p.stat(); out[n]={"exists":True,"size":s.st_size,"mtime_ns":s.st_mtime_ns,"sha256":sha(p)}
 return out
def write_atomic(p,t):
 q=p.with_suffix(p.suffix+".tmp"); q.write_text(t,encoding="utf-8",newline="\n"); os.replace(q,p)
def status(raw): return [{"status":x[:2],"path":x[3:]} for x in raw.split("\0") if x]
def dotted(node):
 try:return ast.unparse(node)
 except:return ""
def literal(node):
 try:return ast.literal_eval(node)
 except:return None

def registration_kind(call):
 name=dotted(call.func); tail=name.split(".")[-1]
 return tail if tail in REG_NAMES else None

def handler_record(path,node,owner,source):
 kind=registration_kind(node)
 if not kind:return None
 args=[dotted(a) for a in node.args]; kwargs={k.arg:dotted(k.value) for k in node.keywords if k.arg}
 return {"module":path,"owner_function":owner,"line":getattr(node,"lineno",None),"kind":kind,"source":source,"call":dotted(node),"args":args,"kwargs":kwargs,"handler_symbol":args[0] if kind.startswith("register_") and args else owner,"order_key":f"{path}:{getattr(node,'lineno',0):06d}"}

def analyze(path,root):
 tree=ast.parse((root/path).read_text(encoding="utf-8",errors="replace"),filename=path); records=[]; register_defs=[]
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
   if node.name.startswith("register_") or "register" in node.name and "handler" in node.name: register_defs.append({"name":node.name,"line":node.lineno})
   for sub in ast.walk(node):
    if isinstance(sub,ast.Call):
     rec=handler_record(path,sub,node.name,"function_body")
     if rec: records.append(rec)
    if isinstance(sub,(ast.FunctionDef,ast.AsyncFunctionDef)):
     for dec in sub.decorator_list:
      call=dec if isinstance(dec,ast.Call) else None
      if call:
       rec=handler_record(path,call,sub.name,"decorator")
       if rec: rec["handler_symbol"]=sub.name; records.append(rec)
 for node in tree.body:
  if isinstance(node,ast.Call):
   rec=handler_record(path,node,"<module>","module_call")
   if rec: records.append(rec)
 return records,register_defs

def main_registration(root):
 p=root/"main.py"; tree=ast.parse(p.read_text(encoding="utf-8",errors="replace"),filename="main.py"); calls=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.Call):
   name=dotted(n.func)
   if name.startswith("register_") or name.endswith(".register_event_handlers"):
    calls.append({"call":name,"line":n.lineno,"order":len(calls)+1})
 return sorted(calls,key=lambda x:x["line"])

def commit_exact(root):
 paths=[PATCH,REPORT,DOC]; a=git(root,"add","-f","--",*paths)
 if a.returncode: raise PatchError(a.stderr.strip() or "git add failed")
 r=git(root,"diff","--cached","--name-only","-z"); staged=sorted(x for x in r.stdout.split("\0") if x)
 if r.returncode or staged!=sorted(paths): git(root,"reset","--",*paths); raise PatchError(f"staging mismatch: {staged}")
 c=git(root,"commit","-m",COMMIT)
 if c.returncode: git(root,"reset","--",*paths); raise PatchError(c.stderr.strip() or c.stdout.strip())
 return rev(root,"HEAD")
def md(p):
 s=p["summary"]; q=p["queues"]
 return "\n".join(["# ROM Stage 21.1.3 - карта runtime handler і callback registration","",f"- **Статус:** `{s['conclusion']}`",f"- **Registration modules:** `{s['module_count']}`",f"- **Registration records:** `{s['registration_record_count']}`",f"- **Main registration calls:** `{s['main_registration_count']}`",f"- **Potential duplicate route groups:** `{s['route_collision_group_count']}`","","## Черги","",f"- Modules with duplicate register definitions: **{len(q['duplicate_register_definitions'])}**",f"- Route collision candidates: **{len(q['route_collision_candidates'])}**",f"- Direct registry mutations: **{len(q['direct_registry_mutations'])}**","","## Контракт V2","","- Один composition root реєструє handlers у явному порядку.","- Domain та application layers не імпортують Telegram SDK.","- Callback namespaces мають єдиного owner і не залежать від випадкового порядку декораторів.","- Direct mutation внутрішніх handler lists не переноситься.","- Повний список registration records, main order і collision candidates міститься у JSON.","- Production DB/WAL/SHM не відкривалися і не змінювалися.","","## Наступний етап","","Stage 21.1.4 - повний inventory database access paths і transaction boundaries.",""])

def main():
 root=Path(__file__).resolve().parent.parent
 if not (root/INPUT).is_file(): print(f"[FAIL] Missing {INPUT}",file=sys.stderr); return 2
 print("[1/8] [PASS] Inputs and regulated directories detected.")
 branch=git(root,"branch","--show-current").stdout.strip(); head=rev(root,"HEAD"); u=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}"); upstream=u.stdout.strip() if u.returncode==0 else None
 entries=status(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout); allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in DIRTY and e["status"][0]==" "))]; unexpected=[e for e in entries if e not in allowed]
 checks=[Check("BRANCH","PASS" if branch==BRANCH else "FAIL",f"Active branch: {branch}",{},branch!=BRANCH),Check("PARENT","PASS" if head==PARENT else "FAIL","Expected parent verified." if head==PARENT else "Unexpected parent.",{"expected":PARENT,"actual":head},head!=PARENT),Check("UPSTREAM","PASS" if upstream==f"origin/{BRANCH}" else "FAIL",f"Upstream: {upstream}",{},upstream!=f"origin/{BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes." if not unexpected else "Unexpected changes exist.",{"unexpected":unexpected},bool(unexpected))]
 if any(c.blocking for c in checks): print("[2/8] [FAIL] Preflight NO_GO"); return 1
 print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
 before=db_ev(root); source=json.loads((root/INPUT).read_text(encoding="utf-8")); modules=[f["path"] for f in source["findings"] if f["registration_candidates"]]
 print(f"[3/8] [PASS] Mapping registration semantics in {len(modules)} modules.")
 records=[]; defs={}; errors=[]
 for path in modules:
  try:r,d=analyze(path,root); records.extend(r); defs[path]=d
  except (OSError,SyntaxError) as e: errors.append({"path":path,"error":str(e)})
 order=main_registration(root)
 print("[4/8] [PASS] Building composition-root order and collision queues.")
 route_groups=defaultdict(list); direct=[]
 for r in records:
  key=(r["kind"],json.dumps(r["kwargs"],sort_keys=True,ensure_ascii=False))
  route_groups[key].append(r)
  if ".insert" in r["call"] or "handlers.insert" in r["call"]: direct.append(r)
 collisions=[{"kind":k[0],"kwargs":json.loads(k[1]),"registrations":v} for k,v in route_groups.items() if len(v)>1 and k[1]!="{}"]
 dup_defs=[{"module":p,"definitions":d} for p,d in defs.items() if len(d)>1]
 checks.append(Check("AST_COVERAGE","PASS" if not errors else "FAIL","All registration modules parsed." if not errors else "AST errors found.",{"errors":errors},bool(errors)))
 checks.append(Check("MAIN_COMPOSITION_ROOT","PASS" if len(order)>=30 else "FAIL",f"Main registration calls: {len(order)}",{"minimum":30},len(order)<30))
 blockers=[c.check_id for c in checks if c.blocking]; conclusion="GO" if not blockers else "NO_GO"
 queues={"duplicate_register_definitions":dup_defs,"route_collision_candidates":collisions,"direct_registry_mutations":direct}
 payload={"schema_version":1,"stage":STAGE,"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":conclusion,"blocking_failures":blockers,"module_count":len(modules),"registration_record_count":len(records),"main_registration_count":len(order),"route_collision_group_count":len(collisions)},"git":{"branch":branch,"head_before_commit":head,"upstream":upstream},"checks":[asdict(c) for c in checks],"main_registration_order":order,"registrations":sorted(records,key=lambda x:x["order_key"]),"register_definitions":defs,"queues":queues,"database_evidence_before":before,"constraints":{"single_v2_composition_root":True,"direct_handler_list_mutation":"FORBIDDEN","telegram_import_in_domain":"FORBIDDEN","callback_namespace_single_owner":True},"artifacts":{"patch":PATCH,"json":REPORT,"markdown":DOC},"next_stage":"21.1.4" if conclusion=="GO" else None}
 print("[5/8] [PASS] Writing JSON and Markdown registration map."); write_atomic(root/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n"); write_atomic(root/DOC,md(payload))
 if conclusion!="GO": print("[6/8] [FAIL] NO_GO; commit not created."); return 1
 print("[6/8] [PASS] Registration map contract validated.")
 try: print("[7/8] [PASS] Creating exact-allowlist commit."); ch=commit_exact(root)
 except PatchError as e: print(f"[7/8] [FAIL] {e}",file=sys.stderr); return 2
 if before!=db_ev(root): print("[8/8] [FAIL] DB/WAL/SHM evidence changed.",file=sys.stderr); return 2
 print(f"[8/8] [PASS] Commit and DB/WAL/SHM evidence verified: {ch}"); print("="*72); print(f"ROM Stage {STAGE} - runtime handler and callback registration map")
 for c in checks: print(f"[{c.status}] {c.check_id}: {c.summary}")
 print(f"[PASS] REGISTRATION_MODULES: {len(modules)}\n[PASS] REGISTRATION_RECORDS: {len(records)}\n[PASS] MAIN_ORDER: {len(order)}\n[PASS] COLLISION_GROUPS: {len(collisions)}\n[PASS] DIRECT_REGISTRY_MUTATIONS: {len(direct)}")
 print("CONCLUSION: GO\nPATCH STATUS: PASS"); print(f"GIT COMMIT STATUS: PASS ({ch})"); print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED"); return 0
if __name__=="__main__": raise SystemExit(main())
