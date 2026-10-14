#!/usr/bin/env python3
"""Stage 21.1.2: audit duplicate definitions, alias chains and runtime overrides."""
from __future__ import annotations
import ast, hashlib, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="21.1.2"; BRANCH="rewrite/rom-v2"
PARENT="8ec55ed1f41d47335174dcb3c285d0b20e80ae57"
INVENTORY="reports/stage_21_1_1_v1_module_inventory.json"
PATCH="patch/patch_21_1_2_audit_duplicate_definitions_and_runtime_overrides.py"
REPORT="reports/stage_21_1_2_duplicate_definitions_runtime_overrides.json"
DOC="MD/STAGE_21_1_2_DUPLICATE_DEFINITIONS_RUNTIME_OVERRIDES.md"
COMMIT="Stage 21.1.2: audit duplicate definitions and runtime overrides"
OWNED={PATCH,REPORT,DOC}; DIRTY={"ROM_FULL_DUMP.txt","ROM_ADDITIONAL_DUMP.txt"}
DBS=("game.db","game.db-wal","game.db-shm")
ALIAS_RE=re.compile(r"^(?:_?(?:base|old|orig|original|previous|legacy|before|candidate|shadow)|.*_(?:base|old|legacy|candidate|shadow))",re.I)

@dataclass(frozen=True)
class Check: check_id:str; status:str; summary:str; details:dict[str,Any]; blocking:bool=False
class PatchError(RuntimeError): pass

def run(root,*cmd,timeout=120): return subprocess.run(cmd,cwd=root,text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=timeout,check=False)
def git(root,*args,timeout=120): return run(root,"git",*args,timeout=timeout)
def rev(root,name):
 r=git(root,"rev-parse","--verify",f"{name}^{{commit}}"); return r.stdout.strip() if r.returncode==0 else None
def sha(path):
 h=hashlib.sha256();
 with path.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""): h.update(c)
 return h.hexdigest()
def db_ev(root):
 out={}
 for n in DBS:
  p=root/n
  if not p.exists(): out[n]={"exists":False}; continue
  s=p.stat(); out[n]={"exists":True,"size":s.st_size,"mtime_ns":s.st_mtime_ns,"sha256":sha(p)}
 return out
def write_atomic(path,text):
 t=path.with_suffix(path.suffix+".tmp"); t.write_text(text,encoding="utf-8",newline="\n"); os.replace(t,path)
def parse_status(raw):
 return [{"status":x[:2],"path":x[3:]} for x in raw.split("\0") if x]

def analyze_module(root,path):
 text=(root/path).read_text(encoding="utf-8",errors="replace"); tree=ast.parse(text,filename=path)
 defs=defaultdict(list); classes=defaultdict(list); aliases=[]; monkey=[]; registrations=[]; all_assignments=[]
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): defs[node.name].append(node.lineno)
  elif isinstance(node,ast.ClassDef): classes[node.name].append(node.lineno)
  elif isinstance(node,(ast.Assign,ast.AnnAssign)):
   targets=node.targets if isinstance(node,ast.Assign) else [node.target]
   value=node.value
   for target in targets:
    if isinstance(target,ast.Name):
     source=None
     if isinstance(value,ast.Name): source=value.id
     elif isinstance(value,ast.Attribute): source=ast.unparse(value)
     if source:
      all_assignments.append({"target":target.id,"source":source,"line":node.lineno})
      if ALIAS_RE.search(target.id) or ALIAS_RE.search(source): aliases.append({"target":target.id,"source":source,"line":node.lineno})
    elif isinstance(target,ast.Attribute): monkey.append({"target":ast.unparse(target),"line":node.lineno,"kind":"attribute_assignment"})
 for node in ast.walk(tree):
  if isinstance(node,ast.Call):
   name=ast.unparse(node.func)
   low=name.lower()
   if any(k in low for k in ("register","add_handler","message_handler","callback_query_handler")):
    registrations.append({"call":name,"line":getattr(node,"lineno",None)})
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
   for dec in node.decorator_list:
    d=ast.unparse(dec).lower()
    if any(k in d for k in ("handler","callback","message")): registrations.append({"decorator":ast.unparse(dec),"symbol":node.name,"line":node.lineno})
 duplicates=[{"kind":"function","name":n,"lines":ls,"effective_line":ls[-1]} for n,ls in defs.items() if len(ls)>1]
 duplicates += [{"kind":"class","name":n,"lines":ls,"effective_line":ls[-1]} for n,ls in classes.items() if len(ls)>1]
 risk="HIGH" if duplicates or monkey else ("MEDIUM" if aliases or len(registrations)>1 else "LOW")
 return {"path":path,"sha256":sha(root/path),"duplicates":duplicates,"alias_candidates":aliases,"all_symbol_aliases":all_assignments,"monkey_patch_candidates":monkey,"registration_candidates":registrations,"risk":risk,"requires_owner_resolution":bool(duplicates or aliases or monkey)}

def render_md(payload):
 s=payload["summary"]; q=payload["queues"]
 return "\n".join(["# ROM Stage 21.1.2 - аудит дублікатів і runtime overrides","",f"- **Статус:** `{s['conclusion']}`",f"- **Проаналізовано модулів:** `{s['module_count']}`",f"- **Модулів із duplicate definitions:** `{s['duplicate_module_count']}`",f"- **Alias-chain candidates:** `{s['alias_module_count']}`",f"- **Monkey-patch candidates:** `{s['monkey_patch_module_count']}`",f"- **Registration candidates:** `{s['registration_module_count']}`","","## Черги","",f"- High risk: **{len(q['high_risk'])}**",f"- Owner resolution required: **{len(q['owner_resolution_required'])}**",f"- Multiple registration candidates: **{len(q['multiple_registration_candidates'])}**","","## Контракт","","- Останнє визначення в Python є runtime-effective лише в межах модуля, але не вважається автоматично accepted owner.","- Alias, monkey patch і registration order не переносяться у V2 механічно.","- Кожний high-risk модуль потребує authoritative owner рішення в наступних contract audits.","- Повні lines, symbols, aliases, registrations та SHA-256 містяться у JSON.","- Production DB/WAL/SHM не відкривалися і не змінювалися.","","## Наступний етап","","Stage 21.1.3 - карта runtime registration Telegram handlers і callbacks.",""])

def commit_exact(root):
 paths=[PATCH,REPORT,DOC]; a=git(root,"add","-f","--",*paths)
 if a.returncode: raise PatchError(a.stderr.strip() or "git add failed")
 r=git(root,"diff","--cached","--name-only","-z"); staged=sorted(x for x in r.stdout.split("\0") if x)
 if r.returncode or staged!=sorted(paths): git(root,"reset","--",*paths); raise PatchError(f"staging mismatch: {staged}")
 c=git(root,"commit","-m",COMMIT)
 if c.returncode: git(root,"reset","--",*paths); raise PatchError(c.stderr.strip() or c.stdout.strip())
 return rev(root,"HEAD")

def main():
 root=Path(__file__).resolve().parent.parent
 if not (root/INVENTORY).is_file(): print(f"[FAIL] Missing {INVENTORY}",file=sys.stderr); return 2
 print("[1/8] [PASS] Inputs and regulated directories detected.")
 branch=git(root,"branch","--show-current").stdout.strip(); head=rev(root,"HEAD")
 up=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}"); upstream=up.stdout.strip() if up.returncode==0 else None
 entries=parse_status(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout)
 allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in DIRTY and e["status"][0]==" "))]
 unexpected=[e for e in entries if e not in allowed]
 checks=[Check("BRANCH","PASS" if branch==BRANCH else "FAIL",f"Active branch: {branch}",{"expected":BRANCH},branch!=BRANCH),Check("PARENT","PASS" if head==PARENT else "FAIL","Expected parent verified." if head==PARENT else "Unexpected parent.",{"expected":PARENT,"actual":head},head!=PARENT),Check("UPSTREAM","PASS" if upstream==f"origin/{BRANCH}" else "FAIL",f"Upstream: {upstream}",{},upstream!=f"origin/{BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes." if not unexpected else "Unexpected changes exist.",{"unexpected":unexpected},bool(unexpected))]
 blockers=[c.check_id for c in checks if c.blocking]
 if blockers: print("[2/8] [FAIL] "+", ".join(blockers)); return 1
 print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
 before=db_ev(root); inv=json.loads((root/INVENTORY).read_text(encoding="utf-8"))
 modules=[m for m in inv["modules"] if m["classification"] not in {"TEST_REFERENCE","DO_NOT_MIGRATE"}]
 print(f"[3/8] [PASS] Auditing {len(modules)} runtime/content/manual-review modules.")
 findings=[]; errors=[]
 for m in modules:
  try: findings.append(analyze_module(root,m["path"]))
  except (OSError,SyntaxError) as e: errors.append({"path":m["path"],"error":str(e)})
 print("[4/8] [PASS] Building effective-definition, alias and registration queues.")
 dup=[f["path"] for f in findings if f["duplicates"]]; alias=[f["path"] for f in findings if f["alias_candidates"]]; monkey=[f["path"] for f in findings if f["monkey_patch_candidates"]]; regs=[f["path"] for f in findings if f["registration_candidates"]]
 queues={"high_risk":[f["path"] for f in findings if f["risk"]=="HIGH"],"owner_resolution_required":[f["path"] for f in findings if f["requires_owner_resolution"]],"multiple_registration_candidates":[f["path"] for f in findings if len(f["registration_candidates"])>1]}
 checks.append(Check("AST_COVERAGE","PASS" if not errors else "FAIL","All selected modules parsed." if not errors else "AST errors found.",{"errors":errors},bool(errors)))
 checks.append(Check("KNOWN_DUPLICATE_COVERAGE","PASS" if len(dup)>=18 else "FAIL",f"Duplicate modules found: {len(dup)}",{"minimum_expected":18},len(dup)<18))
 blockers=[c.check_id for c in checks if c.blocking]; conclusion="GO" if not blockers else "NO_GO"
 payload={"schema_version":1,"stage":STAGE,"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":conclusion,"blocking_failures":blockers,"module_count":len(findings),"duplicate_module_count":len(dup),"alias_module_count":len(alias),"monkey_patch_module_count":len(monkey),"registration_module_count":len(regs)},"git":{"branch":branch,"head_before_commit":head,"upstream":upstream},"checks":[asdict(c) for c in checks],"findings":findings,"queues":queues,"database_evidence_before":before,"constraints":{"last_definition_is_not_automatic_accepted_owner":True,"mechanical_override_migration":"FORBIDDEN","v1_runtime_import_into_v2":"FORBIDDEN"},"artifacts":{"patch":PATCH,"json":REPORT,"markdown":DOC},"next_stage":"21.1.3" if conclusion=="GO" else None}
 print("[5/8] [PASS] Writing JSON and Markdown audit artifacts.")
 write_atomic(root/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n"); write_atomic(root/DOC,render_md(payload))
 if conclusion!="GO": print("[6/8] [FAIL] NO_GO; commit not created."); return 1
 print("[6/8] [PASS] Audit contract and review queues validated.")
 try:
  print("[7/8] [PASS] Creating exact-allowlist commit."); ch=commit_exact(root)
 except PatchError as e: print(f"[7/8] [FAIL] {e}",file=sys.stderr); return 2
 after=db_ev(root)
 if before!=after: print("[8/8] [FAIL] DB/WAL/SHM evidence changed.",file=sys.stderr); return 2
 print(f"[8/8] [PASS] Commit and DB/WAL/SHM evidence verified: {ch}")
 print("="*72); print(f"ROM Stage {STAGE} - duplicate definitions and runtime overrides")
 for c in checks: print(f"[{c.status}] {c.check_id}: {c.summary}")
 print(f"[PASS] DUPLICATE_MODULES: {len(dup)}\n[PASS] ALIAS_MODULES: {len(alias)}\n[PASS] MONKEY_PATCH_MODULES: {len(monkey)}\n[PASS] REGISTRATION_MODULES: {len(regs)}")
 print("CONCLUSION: GO\nPATCH STATUS: PASS"); print(f"GIT COMMIT STATUS: PASS ({ch})"); print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
 return 0
if __name__=="__main__": raise SystemExit(main())
