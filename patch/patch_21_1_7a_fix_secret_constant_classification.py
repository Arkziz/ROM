#!/usr/bin/env python3
"""Stage 21.1.7a: fix secret-like constant classification false positives."""
from __future__ import annotations
import ast, hashlib, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="21.1.7a"; BRANCH="rewrite/rom-v2"; PARENT="86f4f48dff70519255a8e204d3fc5511d0245a5a"
INVENTORY="reports/stage_21_1_1_v1_module_inventory.json"
PATCH="patch/patch_21_1_7a_fix_secret_constant_classification.py"
REPORT="reports/stage_21_1_7_configuration_external_integrations.json"
REMEDIATION="reports/stage_21_1_7a_secret_constant_classification_fix.json"
DOC="MD/STAGE_21_1_7_CONFIGURATION_EXTERNAL_INTEGRATIONS.md"
REMEDIATION_DOC="MD/STAGE_21_1_7A_SECRET_CONSTANT_CLASSIFICATION_FIX.md"
COMMIT="Stage 21.1.7a: fix secret constant classification"
OWNED={PATCH,REPORT,DOC,REMEDIATION,REMEDIATION_DOC}; DIRTY={"ROM_FULL_DUMP.txt","ROM_ADDITIONAL_DUMP.txt"}; DBS=("game.db","game.db-wal","game.db-shm")
EXCLUDED={"TEST_REFERENCE","DO_NOT_MIGRATE"}
SECRET_NAME=re.compile(r"(?i)(^|_)(bot_token|access_token|auth_token|secret|password|passwd|api_key|private_key|credential)(_|$)")
URL_NAME=re.compile(r"(?i)(url|uri|host|endpoint|webhook|channel|chat)")
ENV_CALLS={"os.getenv","os.environ.get"}; NETWORK_ROOTS={"requests","httpx","aiohttp","urllib","telebot","telegram"}

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
  for c in iter(lambda:f.read(1048576),b""):h.update(c)
 return h.hexdigest()
def evidence(root):
 out={}
 for n in DBS:
  p=root/n
  if not p.exists():out[n]={"exists":False};continue
  s=p.stat();out[n]={"exists":True,"size":s.st_size,"mtime_ns":s.st_mtime_ns,"sha256":sha(p)}
 return out
def write_atomic(p,t):
 q=p.with_suffix(p.suffix+".tmp");q.write_text(t,encoding="utf-8",newline="\n");os.replace(q,p)
def status(raw):return [{"status":x[:2],"path":x[3:]} for x in raw.split("\0") if x]
def up(node):
 try:return ast.unparse(node)
 except:return ""
def literal(node):
 try:return ast.literal_eval(node)
 except:return None

def analyze(root,path,classification):
 text=(root/path).read_text(encoding="utf-8",errors="replace");tree=ast.parse(text,filename=path)
 env=[];constants=[];imports=[];network=[];files=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.Import):imports.extend(a.name for a in n.names)
  elif isinstance(n,ast.ImportFrom) and n.module:imports.append(n.module)
  elif isinstance(n,ast.Assign):
   for t in n.targets:
    if isinstance(t,ast.Name) and t.id.isupper():
     value=literal(n.value); constants.append({"name":t.id,"line":n.lineno,"value_type":type(value).__name__ if value is not None else "dynamic","secret_like":bool(SECRET_NAME.search(t.id)),"url_like":bool(URL_NAME.search(t.id)),"has_literal_value":value is not None})
  elif isinstance(n,ast.Call):
   name=up(n.func)
   if name in ENV_CALLS and n.args:
    key=literal(n.args[0]); default=literal(n.args[1]) if len(n.args)>1 else None
    if isinstance(key,str):env.append({"name":key,"line":n.lineno,"access":name,"required":len(n.args)==1,"has_default":len(n.args)>1,"default_type":type(default).__name__ if default is not None else None,"secret_like":bool(SECRET_NAME.search(key)),"url_like":bool(URL_NAME.search(key))})
   elif name.startswith("os.environ[") and n.args:pass
   if any(name==r or name.startswith(r+".") for r in NETWORK_ROOTS):network.append({"line":n.lineno,"call":name})
   if name in {"open","Path.read_text","Path.write_text","Path.open"} or name.endswith((".read_text",".write_text",".open")):files.append({"line":n.lineno,"call":name,"target":up(n.args[0]) if n.args else None})
 return {"path":path,"classification":classification,"sha256":sha(root/path),"imports":sorted(set(imports)),"environment_variables":env,"constants":constants,"network_calls":network,"file_io":files}

def render(p):
 s=p["summary"];q=p["review_queues"]
 return "\n".join(["# ROM Stage 21.1.7 canonical revision 21.1.7a - configuration і external integrations","",f"- **Статус:** `{s['conclusion']}`",f"- **Проаналізовано модулів:** `{s['module_count']}`",f"- **Environment variables:** `{s['environment_variable_count']}`",f"- **Configuration constants:** `{s['constant_count']}`",f"- **Network call sites:** `{s['network_call_count']}`",f"- **File I/O sites:** `{s['file_io_count']}`","","## Review queues","",f"- Secret-like variables: **{len(q['secret_like_variables'])}**",f"- Required variables without defaults: **{len(q['required_without_default'])}**",f"- URL/host variables: **{len(q['url_host_variables'])}**",f"- Network integrations: **{len(q['network_integrations'])}**",f"- Literal secret-like constants: **{len(q['literal_secret_like_constants'])}**","","## V2 configuration contract","","- Один typed settings object завантажується у composition root.","- Domain і application не читають `os.environ` напряму.","- Secret values не зберігаються в repository, reports або logs.","- URL/host settings проходять fail-closed validation.","- Telegram, HTTP, filesystem, clock і scheduler є infrastructure adapters behind ports.","- DEV/test configuration відокремлена від production configuration.","- Production DB/WAL/SHM не відкривалися і не змінювалися.","","## Наступний етап","","Stage 21.1.8 - inventory background jobs, schedulers, time і concurrency boundaries.",""])
def commit(root):
 paths=[PATCH,REPORT,DOC,REMEDIATION,REMEDIATION_DOC];a=git(root,"add","-f","--",*paths)
 if a.returncode:raise PatchError(a.stderr.strip() or "git add failed")
 r=git(root,"diff","--cached","--name-only","-z");staged=sorted(x for x in r.stdout.split("\0") if x)
 if r.returncode or staged!=sorted(paths):git(root,"reset","--",*paths);raise PatchError(f"staging mismatch: {staged}")
 c=git(root,"commit","-m",COMMIT)
 if c.returncode:git(root,"reset","--",*paths);raise PatchError(c.stderr.strip() or c.stdout.strip())
 return rev(root,"HEAD")
def main():
 root=Path(__file__).resolve().parent.parent
 if not (root/INVENTORY).is_file():print(f"[FAIL] Missing {INVENTORY}",file=sys.stderr);return 2
 print("[1/8] [PASS] Canonical inventory and regulated directories detected.")
 branch=git(root,"branch","--show-current").stdout.strip();head=rev(root,"HEAD");u=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");upstream=u.stdout.strip() if u.returncode==0 else None
 entries=status(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout);allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in DIRTY and e["status"][0]==" "))];unexpected=[e for e in entries if e not in allowed]
 checks=[Check("BRANCH","PASS" if branch==BRANCH else "FAIL",f"Active branch: {branch}",{},branch!=BRANCH),Check("PARENT","PASS" if head==PARENT else "FAIL","Expected Stage 21.1.7 parent verified." if head==PARENT else "Unexpected parent.",{"expected":PARENT,"actual":head},head!=PARENT),Check("UPSTREAM","PASS" if upstream==f"origin/{BRANCH}" else "FAIL",f"Upstream: {upstream}",{},upstream!=f"origin/{BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes." if not unexpected else "Unexpected changes exist.",{"unexpected":unexpected},bool(unexpected))]
 if any(c.blocking for c in checks):print("[2/8] [FAIL] Preflight NO_GO.");return 1
 print("[2/8] [PASS] Branch, parent, upstream and worktree verified.")
 before=evidence(root);inv=json.loads((root/INVENTORY).read_text(encoding="utf-8"));mods=[m for m in inv["modules"] if m["classification"] not in EXCLUDED]
 print(f"[3/8] [PASS] Scanning configuration and integrations in {len(mods)} modules.")
 findings=[];errors=[]
 for m in mods:
  try:findings.append(analyze(root,m["path"],m["classification"]))
  except (OSError,SyntaxError) as e:errors.append({"path":m["path"],"error":str(e)})
 print("[4/8] [PASS] Building secret, URL, network and file-I/O review queues.")
 env_by_name=defaultdict(list);constants=[];network=[];file_io=[]
 for f in findings:
  for e in f["environment_variables"]:env_by_name[e["name"]].append(dict(e,module=f["path"]))
  constants.extend(dict(c,module=f["path"]) for c in f["constants"])
  network.extend(dict(c,module=f["path"]) for c in f["network_calls"])
  file_io.extend(dict(c,module=f["path"]) for c in f["file_io"])
 env_registry=[]
 for name,uses in sorted(env_by_name.items()):env_registry.append({"name":name,"uses":uses,"required_anywhere":any(x["required"] for x in uses),"secret_like":any(x["secret_like"] for x in uses),"url_like":any(x["url_like"] for x in uses)})
 queues={"secret_like_variables":[x for x in env_registry if x["secret_like"]],"required_without_default":[x for x in env_registry if x["required_anywhere"]],"url_host_variables":[x for x in env_registry if x["url_like"]],"network_integrations":network,"literal_secret_like_constants":[x for x in constants if x["secret_like"] and x["has_literal_value"]],"file_io":file_io}
 checks.extend([Check("AST_COVERAGE","PASS" if not errors else "FAIL","All modules parsed." if not errors else "AST errors found.",{"errors":errors},bool(errors)),Check("CONFIG_ACTIVITY_FOUND","PASS" if env_registry or constants else "FAIL",f"Found {len(env_registry)} environment variables and {len(constants)} constants.",{},not(env_registry or constants)),Check("NO_SECRET_VALUES_EXPORTED","PASS","Reports contain names and metadata only; environment values are never read.",{"environment_values_read":False})])
 blockers=[c.check_id for c in checks if c.blocking];conclusion="GO" if not blockers else "NO_GO"
 payload={"schema_version":1,"stage":STAGE,"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":conclusion,"blocking_failures":blockers,"module_count":len(findings),"environment_variable_count":len(env_registry),"constant_count":len(constants),"network_call_count":len(network),"file_io_count":len(file_io)},"git":{"branch":branch,"head_before_commit":head,"upstream":upstream},"checks":[asdict(c) for c in checks],"environment_registry":env_registry,"module_findings":findings,"review_queues":queues,"v2_configuration_contract":{"settings_owner":"rom_v2/app/settings.py","load_at_composition_root_only":True,"direct_environment_access_outside_settings":"FORBIDDEN","secret_values_in_repository_or_reports":"FORBIDDEN","url_validation":"HTTPS_FAIL_CLOSED","external_integrations_behind_ports":True,"dev_production_separation":True},"database_evidence_before":before,"artifacts":{"patch":PATCH,"json":REPORT,"markdown":DOC,"remediation_json":REMEDIATION,"remediation_markdown":REMEDIATION_DOC},"next_stage":"21.1.8" if conclusion=="GO" else None}
 print("[5/8] [PASS] Writing configuration and integration inventory.");write_atomic(root/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n");write_atomic(root/DOC,render(payload))
 remediation={"schema_version":1,"stage":STAGE,"generated_at_utc":payload["generated_at_utc"],"summary":{"conclusion":conclusion,"secret_like_constants_before":6,"secret_like_constants_after":len(queues["literal_secret_like_constants"]),"false_positives_removed":6-len(queues["literal_secret_like_constants"])},"root_cause":"The broad token substring matched gameplay currency/item constants such as FIRIUS_TOKEN, not credential secrets.","classification_rule":"Only credential-oriented identifiers such as BOT_TOKEN, ACCESS_TOKEN, AUTH_TOKEN, SECRET, PASSWORD, API_KEY, PRIVATE_KEY and CREDENTIAL are secret-like.","canonical_artifacts_updated":[REPORT,DOC],"database_evidence_before":before,"next_stage":"21.1.8" if conclusion=="GO" else None}
 write_atomic(root/REMEDIATION,json.dumps(remediation,ensure_ascii=False,indent=2)+"\n")
 write_atomic(root/REMEDIATION_DOC,"\n".join(["# ROM Stage 21.1.7a - secret constant classification fix","",f"- **Статус:** `{conclusion}`",f"- **Secret-like constants before:** `6`",f"- **Secret-like constants after:** `{len(queues['literal_secret_like_constants'])}`",f"- **False positives removed:** `{6-len(queues['literal_secret_like_constants'])}`","","## Root cause","","Gameplay identifiers containing `TOKEN` were incorrectly treated as credential secrets.","","## Corrected rule","","Only credential-oriented names such as `BOT_TOKEN`, `ACCESS_TOKEN`, `AUTH_TOKEN`, `SECRET`, `PASSWORD`, `API_KEY`, `PRIVATE_KEY` and `CREDENTIAL` are classified as secret-like.","","Production DB/WAL/SHM were not opened or modified.",""]))
 if conclusion!="GO":print("[6/8] [FAIL] Configuration audit NO_GO; commit not created.");return 1
 print("[6/8] [PASS] Configuration and integration contract validated.")
 try:print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.7a commit.");ch=commit(root)
 except PatchError as e:print(f"[7/8] [FAIL] {e}",file=sys.stderr);return 2
 if before!=evidence(root):print("[8/8] [FAIL] DB/WAL/SHM evidence changed.",file=sys.stderr);return 2
 print(f"[8/8] [PASS] Configuration inventory committed and DB/WAL/SHM verified: {ch}");print("="*72);print(f"ROM Stage {STAGE} - fix secret constant classification")
 for c in checks:print(f"[{c.status}] {c.check_id}: {c.summary}")
 print(f"[PASS] ENVIRONMENT_VARIABLES: {len(env_registry)}\n[PASS] CONSTANTS: {len(constants)}\n[PASS] NETWORK_CALLS: {len(network)}\n[PASS] FILE_IO_SITES: {len(file_io)}\n[PASS] SECRET_LIKE_VARIABLES: {len(queues['secret_like_variables'])}")
 print("CONCLUSION: GO\nPATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({ch})");print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED");return 0
if __name__=="__main__":raise SystemExit(main())
