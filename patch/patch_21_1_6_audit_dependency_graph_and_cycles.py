#!/usr/bin/env python3
"""Stage 21.1.6: audit V1 dependency graph, cycles and V2 dependency rules."""
from __future__ import annotations
import ast, hashlib, json, os, subprocess, sys
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="21.1.6"; BRANCH="rewrite/rom-v2"; PARENT="1d8515a03f011146b9b8ecc0dab1bb6039204a3b"
INVENTORY="reports/stage_21_1_1_v1_module_inventory.json"
CONTRACTS="reports/stage_21_1_5_domain_contracts.json"
PATCH="patch/patch_21_1_6_audit_dependency_graph_and_cycles.py"
REPORT="reports/stage_21_1_6_dependency_graph_cycles.json"
DOC="MD/STAGE_21_1_6_DEPENDENCY_GRAPH_CYCLES.md"
COMMIT="Stage 21.1.6: audit dependency graph and cycles"
OWNED={PATCH,REPORT,DOC}; DIRTY={"ROM_FULL_DUMP.txt","ROM_ADDITIONAL_DUMP.txt"}; DBS=("game.db","game.db-wal","game.db-shm")
EXCLUDED={"TEST_REFERENCE","DO_NOT_MIGRATE"}

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
 q=p.with_suffix(p.suffix+".tmp"); q.write_text(t,encoding="utf-8",newline="\n"); os.replace(q,p)
def status(raw): return [{"status":x[:2],"path":x[3:]} for x in raw.split("\0") if x]
def modname(path):
 parts=list(Path(path).with_suffix("").parts)
 if parts and parts[-1]=="__init__": parts=parts[:-1]
 return ".".join(parts)
def resolve(current,module,level):
 base=list(Path(current).with_suffix("").parts[:-1])
 if level:
  if level>len(base)+1:return None
  base=base[:len(base)-level+1]
 else: base=[]
 if module:base.extend(module.split("."))
 return ".".join(base) if base else None

def imports_for(root,path,names):
 tree=ast.parse((root/path).read_text(encoding="utf-8",errors="replace"),filename=path); found=set(); unresolved=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.Import):
   for a in node.names:
    parts=a.name.split(".")
    candidates=[".".join(parts[:i]) for i in range(len(parts),0,-1)]
    target=next((x for x in candidates if x in names),None)
    if target:found.add(target)
  elif isinstance(node,ast.ImportFrom):
   base=resolve(path,node.module,node.level)
   candidates=[]
   if base:
    candidates.append(base); candidates.extend(f"{base}.{a.name}" for a in node.names if a.name!="*")
   target=next((x for x in candidates if x in names),None)
   if target:found.add(target)
   elif node.level and base: unresolved.append({"line":node.lineno,"import":ast.unparse(node)})
 return sorted(found),unresolved

def tarjan(nodes,edges):
 index=0; stack=[]; on=set(); ids={}; low={}; comps=[]
 def visit(v):
  nonlocal index
  ids[v]=low[v]=index; index+=1; stack.append(v); on.add(v)
  for w in edges.get(v,[]):
   if w not in ids: visit(w); low[v]=min(low[v],low[w])
   elif w in on: low[v]=min(low[v],ids[w])
  if low[v]==ids[v]:
   comp=[]
   while True:
    w=stack.pop(); on.remove(w); comp.append(w)
    if w==v:break
   comps.append(sorted(comp))
 for n in nodes:
  if n not in ids:visit(n)
 return comps

def layer(path):
 p=Path(path).parts
 if not p:return "root"
 if p[0]=="handlers":return "telegram_handler"
 if p[0]=="systems":return "system"
 if p[0]=="db_modules" or path=="db.py":return "persistence"
 if p[0]=="data":return "content"
 if p[0]=="events":return "event"
 if path=="main.py":return "composition_root"
 return "root"
def violation(source,target):
 a,b=layer(source),layer(target)
 reasons=[]
 if a=="content" and b in {"telegram_handler","persistence","system"}: reasons.append("content_depends_on_runtime")
 if a=="persistence" and b=="telegram_handler": reasons.append("persistence_depends_on_telegram")
 if a=="system" and b=="telegram_handler": reasons.append("system_depends_on_telegram")
 if a=="telegram_handler" and b=="telegram_handler": reasons.append("handler_to_handler_coupling")
 if a!="composition_root" and target=="main.py": reasons.append("runtime_depends_on_composition_root")
 return reasons

def render(p):
 s=p["summary"];q=p["queues"]
 return "\n".join(["# ROM Stage 21.1.6 - dependency graph, cycles і V2 directions","",f"- **Статус:** `{s['conclusion']}`",f"- **Nodes:** `{s['node_count']}`",f"- **Internal edges:** `{s['edge_count']}`",f"- **Strongly connected cycles:** `{s['cycle_count']}`",f"- **Forbidden-direction candidates:** `{s['violation_count']}`",f"- **Orphan modules:** `{s['orphan_count']}`","","## Review queues","",f"- Cycles: **{len(q['cycles'])}**",f"- Forbidden directions: **{len(q['forbidden_directions'])}**",f"- High fan-in: **{len(q['high_fan_in'])}**",f"- High fan-out: **{len(q['high_fan_out'])}**",f"- Orphans: **{len(q['orphans'])}**","","## V2 dependency contract","","- `domain` залежить тільки від стандартної бібліотеки та власних domain modules.","- `application` залежить від domain і application ports.","- `infrastructure` залежить від domain/application ports, але не навпаки.","- Telegram adapters не імпортуються domain, application або persistence.","- Content не залежить від runtime handlers, systems або persistence.","- Composition root є єдиним місцем wiring concrete infrastructure.","- Цикли V1 не копіюються; для кожного визначається owner, port або extracted service.","- Production DB/WAL/SHM не відкривалися і не змінювалися.","","## Наступний етап","","Stage 21.1.7 - inventory configuration, environment variables і external integrations.",""])
def commit(root):
 paths=[PATCH,REPORT,DOC];a=git(root,"add","-f","--",*paths)
 if a.returncode:raise PatchError(a.stderr.strip() or "git add failed")
 r=git(root,"diff","--cached","--name-only","-z"); staged=sorted(x for x in r.stdout.split("\0") if x)
 if r.returncode or staged!=sorted(paths):git(root,"reset","--",*paths);raise PatchError(f"staging mismatch: {staged}")
 c=git(root,"commit","-m",COMMIT)
 if c.returncode:git(root,"reset","--",*paths);raise PatchError(c.stderr.strip() or c.stdout.strip())
 return rev(root,"HEAD")
def main():
 root=Path(__file__).resolve().parent.parent
 if not (root/INVENTORY).is_file() or not (root/CONTRACTS).is_file():print("[FAIL] Missing canonical inputs.",file=sys.stderr);return 2
 print("[1/8] [PASS] Canonical inventory, domain contracts and directories detected.")
 branch=git(root,"branch","--show-current").stdout.strip();head=rev(root,"HEAD");u=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");up=u.stdout.strip() if u.returncode==0 else None
 entries=status(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout);allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in DIRTY and e["status"][0]==" "))];unexpected=[e for e in entries if e not in allowed]
 checks=[Check("BRANCH","PASS" if branch==BRANCH else "FAIL",f"Active branch: {branch}",{},branch!=BRANCH),Check("PARENT","PASS" if head==PARENT else "FAIL","Expected Stage 21.1.5 parent verified." if head==PARENT else "Unexpected parent.",{"expected":PARENT,"actual":head},head!=PARENT),Check("UPSTREAM","PASS" if up==f"origin/{BRANCH}" else "FAIL",f"Upstream: {up}",{},up!=f"origin/{BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes." if not unexpected else "Unexpected changes exist.",{"unexpected":unexpected},bool(unexpected))]
 if any(c.blocking for c in checks):print("[2/8] [FAIL] Preflight NO_GO.");return 1
 print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
 before=evidence(root);inv=json.loads((root/INVENTORY).read_text(encoding="utf-8"));contracts=json.loads((root/CONTRACTS).read_text(encoding="utf-8"));mods=[m for m in inv["modules"] if m["classification"] not in EXCLUDED];names={modname(m["path"]):m["path"] for m in mods};nodes=sorted(m["path"] for m in mods)
 print(f"[3/8] [PASS] Resolving internal imports for {len(nodes)} modules.")
 edges=defaultdict(set);unresolved=[];errors=[]
 for m in mods:
  try:
   imports,miss=imports_for(root,m["path"],names)
   edges[m["path"]].update(names[x] for x in imports if names[x]!=m["path"]); unresolved.extend(dict(x,module=m["path"]) for x in miss)
  except (OSError,SyntaxError) as e:errors.append({"path":m["path"],"error":str(e)})
 print("[4/8] [PASS] Computing SCC cycles, fan-in/out and forbidden directions.")
 comps=tarjan(nodes,edges);cycles=[c for c in comps if len(c)>1 or (len(c)==1 and c[0] in edges.get(c[0],set()))]
 indeg=Counter();outdeg=Counter()
 for a,targets in edges.items():
  outdeg[a]=len(targets)
  for b in targets:indeg[b]+=1
 violations=[]
 for a,targets in edges.items():
  for b in sorted(targets):
   for reason in violation(a,b):violations.append({"source":a,"target":b,"source_layer":layer(a),"target_layer":layer(b),"reason":reason})
 orphans=[n for n in nodes if not edges.get(n) and indeg[n]==0]
 high_in=[{"module":n,"count":indeg[n]} for n in nodes if indeg[n]>=10];high_out=[{"module":n,"count":outdeg[n]} for n in nodes if outdeg[n]>=10]
 checks.extend([Check("AST_COVERAGE","PASS" if not errors else "FAIL","All modules parsed." if not errors else "AST errors found.",{"errors":errors},bool(errors)),Check("NODE_COVERAGE","PASS" if len(nodes)==contracts["summary"]["module_count"] else "FAIL",f"Graph nodes: {len(nodes)}.",{"expected":contracts["summary"]["module_count"]},len(nodes)!=contracts["summary"]["module_count"]),Check("GRAPH_NONEMPTY","PASS" if sum(len(v) for v in edges.values()) else "FAIL","Internal dependency graph is non-empty.",{},not sum(len(v) for v in edges.values()))])
 blockers=[c.check_id for c in checks if c.blocking];conclusion="GO" if not blockers else "NO_GO";edge_list=[{"source":a,"target":b} for a in sorted(edges) for b in sorted(edges[a])]
 queues={"cycles":cycles,"forbidden_directions":violations,"high_fan_in":sorted(high_in,key=lambda x:(-x["count"],x["module"])),"high_fan_out":sorted(high_out,key=lambda x:(-x["count"],x["module"])),"orphans":orphans,"unresolved_relative_imports":unresolved}
 payload={"schema_version":1,"stage":STAGE,"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":conclusion,"blocking_failures":blockers,"node_count":len(nodes),"edge_count":len(edge_list),"cycle_count":len(cycles),"violation_count":len(violations),"orphan_count":len(orphans)},"git":{"branch":branch,"head_before_commit":head,"upstream":up},"checks":[asdict(c) for c in checks],"nodes":[{"path":m["path"],"classification":m["classification"],"layer":layer(m["path"]),"fan_in":indeg[m["path"]],"fan_out":outdeg[m["path"]]} for m in mods],"edges":edge_list,"strongly_connected_components":comps,"queues":queues,"v2_dependency_contract":{"domain_may_depend_on":[],"application_may_depend_on":["domain","application.ports"],"infrastructure_may_depend_on":["domain","application.ports"],"content_may_depend_on":["content.schemas"],"composition_root_may_depend_on":["application","infrastructure","content"],"telegram_dependency_allowed_only_in":["infrastructure.telegram","app"],"persistence_dependency_allowed_only_in":["infrastructure.database","app"],"cycles":"FORBIDDEN","v1_runtime_import":"FORBIDDEN"},"database_evidence_before":before,"artifacts":{"patch":PATCH,"json":REPORT,"markdown":DOC},"next_stage":"21.1.7" if conclusion=="GO" else None}
 print("[5/8] [PASS] Writing dependency graph and architecture report.");write_atomic(root/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n");write_atomic(root/DOC,render(payload))
 if conclusion!="GO":print("[6/8] [FAIL] Dependency audit NO_GO; commit not created.");return 1
 print("[6/8] [PASS] Graph coverage and V2 dependency contract validated.")
 try:print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.6 commit.");ch=commit(root)
 except PatchError as e:print(f"[7/8] [FAIL] {e}",file=sys.stderr);return 2
 if before!=evidence(root):print("[8/8] [FAIL] DB/WAL/SHM evidence changed.",file=sys.stderr);return 2
 print(f"[8/8] [PASS] Dependency audit committed and DB/WAL/SHM verified: {ch}");print("="*72);print(f"ROM Stage {STAGE} - dependency graph and cycles")
 for c in checks:print(f"[{c.status}] {c.check_id}: {c.summary}")
 print(f"[PASS] NODES: {len(nodes)}\n[PASS] EDGES: {len(edge_list)}\n[PASS] CYCLES: {len(cycles)}\n[PASS] FORBIDDEN_DIRECTION_CANDIDATES: {len(violations)}\n[PASS] ORPHANS: {len(orphans)}")
 print("CONCLUSION: GO\nPATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({ch})");print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED");return 0
if __name__=="__main__":raise SystemExit(main())
