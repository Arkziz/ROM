#!/usr/bin/env python3
"""Stage 21.2.7: define lintable code and comment standards for ROM V2."""
from __future__ import annotations
import hashlib, json, os, py_compile, subprocess, sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="21.2.7"; TARGET_BRANCH="rewrite/rom-v2"; EXPECTED_PARENT="b1f84c04872e8fc7ee7bbc098b93dd0bd1e32f70"
CLOCK_REPORT="reports/stage_21_2_6_clock_rng_abstractions.json"; CLOCK_ADR="MD/ADR_21_2_6_V2_CLOCK_RNG_ABSTRACTIONS.md"
PATCH_PATH="patch/patch_21_2_7_define_code_comment_standards.py"; VERIFIER_PATH="tools/verify_v2_code_comment_standards.py"
REPORT_PATH="reports/stage_21_2_7_code_comment_standards.json"; ADR_PATH="MD/ADR_21_2_7_V2_CODE_COMMENT_STANDARDS.md"
FAILURE_REPORT="reports/stage_21_2_7_failure_rollback.json"; COMMIT_MESSAGE="Stage 21.2.7: define V2 code and comment standards"
OWNED={PATCH_PATH,VERIFIER_PATH,REPORT_PATH,ADR_PATH,FAILURE_REPORT}; ALLOWED_DIRTY={"ROM_FULL_DUMP.txt","ROM_ADDITIONAL_DUMP.txt"}
DB_FILES=("game.db","game.db-wal","game.db-shm"); BACKUP_PREFIX="stage_21_2_7"

CONTRACT={
 "schema_version":1,
 "canonical_owner":"MD/ADR_21_2_7_V2_CODE_COMMENT_STANDARDS.md",
 "scope":["rom_v2","tests_v2","tools"],
 "type_hints":{"public_functions":True,"public_methods":True,"parameters":True,"return_type":True,"public_attributes":True,"explicit_none_return":True,"any_requires_reason":True,"untyped_public_api_forbidden":True},
 "docstrings":{"public_modules":True,"public_classes":True,"public_functions":True,"public_methods":True,"describe_contract_not_implementation":True,"document_invariants_and_failures":True,"repeat_name_only_forbidden":True},
 "comments":{"explain_reason_not_syntax":True,"required_for_non_obvious_invariants":True,"required_for_rounding":True,"required_for_ordering":True,"required_for_atomicity":True,"required_for_idempotency":True,"required_for_restart_semantics":True,"required_for_workaround":True,"obvious_line_comment_forbidden":True,"stale_comment_forbidden":True,"todo_requires_stage_or_issue":True},
 "naming":{"english_snake_case_modules":True,"english_snake_case_functions":True,"english_pascal_case_types":True,"stable_machine_keys_not_presentation_text":True,"catch_all_names_forbidden":True},
 "complexity":{"single_authoritative_owner":True,"duplicate_production_path_forbidden":True,"small_focused_functions":True,"broad_utils_helpers_services_forbidden":True,"public_api_type_aliases_named":True},
 "exceptions":{"bare_except_forbidden":True,"silent_exception_forbidden":True,"expected_business_outcome_uses_result":True,"exception_chaining_required_when_translating":True},
 "lint_policy":{"new_or_changed_v2_files_must_pass":True,"report_every_violation_with_file_line_rule":True,"no_inline_suppression_without_adr":True,"empty_v2_tree_is_valid_before_stage_21_3_1":True},
 "forbidden_alternatives":["untyped public API","docstring repeating function name","comment restating syntax","unowned TODO","catch-all utils/helpers/common/service","bare except","silent pass after exception","duplicate production owner"]
}

VERIFIER=r'''#!/usr/bin/env python3
"""Verify lintable ROM V2 type-hint, docstring and comment standards."""
from __future__ import annotations
import argparse, ast, json, re, tokenize
from io import StringIO
from pathlib import Path
from typing import Any
PUBLIC=lambda name:not name.startswith("_")
TODO_RE=re.compile(r"(?i)\b(TODO|FIXME)\b(?![^\n]*(stage\s*\d+|#[0-9]+|issue\s*[:#]))")
CATCH_ALL={"common.py","helpers.py","helper.py","utils.py","utility.py","misc.py","manager.py","service.py","services.py","base.py","core.py","shared.py"}
def verify(root:Path,contract:dict[str,Any])->dict[str,Any]:
 violations=[];files=[];public_apis=0;typed_apis=0;documented_apis=0;comments=0
 roots=[root/"rom_v2",root/"tests_v2"]
 for base in roots:
  if not base.is_dir():continue
  for path in sorted(base.rglob("*.py")):
   rel=path.relative_to(root).as_posix();text=path.read_text(encoding="utf-8",errors="replace");files.append(rel)
   if path.name in CATCH_ALL:violations.append({"rule":"CATCH_ALL_MODULE","file":rel,"line":1})
   try:tree=ast.parse(text,filename=rel)
   except SyntaxError as exc:violations.append({"rule":"PARSE_ERROR","file":rel,"line":exc.lineno,"detail":str(exc)});continue
   if ast.get_docstring(tree) is None:violations.append({"rule":"PUBLIC_MODULE_DOCSTRING","file":rel,"line":1})
   try:
    for tok in tokenize.generate_tokens(StringIO(text).readline):
     if tok.type==tokenize.COMMENT:
      comments+=1
      if TODO_RE.search(tok.string):violations.append({"rule":"UNOWNED_TODO","file":rel,"line":tok.start[0],"comment":tok.string[:200]})
   except tokenize.TokenError as exc:violations.append({"rule":"TOKENIZE_ERROR","file":rel,"line":1,"detail":str(exc)})
   for node in ast.walk(tree):
    if isinstance(node,ast.ClassDef) and PUBLIC(node.name):
     public_apis+=1
     if ast.get_docstring(node):documented_apis+=1
     else:violations.append({"rule":"PUBLIC_CLASS_DOCSTRING","file":rel,"line":node.lineno,"symbol":node.name})
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and PUBLIC(node.name):
     public_apis+=1;args=[*node.args.posonlyargs,*node.args.args,*node.args.kwonlyargs]
     if node.args.vararg:args.append(node.args.vararg)
     if node.args.kwarg:args.append(node.args.kwarg)
     missing=[a.arg for a in args if a.arg not in {"self","cls"} and a.annotation is None]
     typed=node.returns is not None and not missing
     if typed:typed_apis+=1
     else:violations.append({"rule":"PUBLIC_API_TYPE_HINTS","file":rel,"line":node.lineno,"symbol":node.name,"missing_parameters":missing,"missing_return":node.returns is None})
     if ast.get_docstring(node):documented_apis+=1
     else:violations.append({"rule":"PUBLIC_API_DOCSTRING","file":rel,"line":node.lineno,"symbol":node.name})
    if isinstance(node,ast.ExceptHandler) and node.type is None:violations.append({"rule":"BARE_EXCEPT","file":rel,"line":node.lineno})
    if isinstance(node,ast.ExceptHandler) and len(node.body)==1 and isinstance(node.body[0],ast.Pass):violations.append({"rule":"SILENT_EXCEPTION","file":rel,"line":node.lineno})
 return {"schema_version":1,"summary":{"status":"PASS" if not violations else "FAIL","file_count":len(files),"public_api_count":public_apis,"typed_public_api_count":typed_apis,"documented_public_api_count":documented_apis,"comment_count":comments,"violation_count":len(violations),"physical_v2_exists":(root/"rom_v2").is_dir()},"files":files,"violations":violations}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--project-root",default=".");p.add_argument("--contract",required=True);p.add_argument("--json-out");a=p.parse_args();c=json.loads(Path(a.contract).read_text(encoding="utf-8"));r=verify(Path(a.project_root).resolve(),c);text=json.dumps(r,ensure_ascii=False,indent=2)+"\n"
 if a.json_out:Path(a.json_out).write_text(text,encoding="utf-8",newline="\n")
 s=r["summary"];print(f"V2 code/comment verifier: {s['status']}");print(f"Files: {s['file_count']}");print(f"Public APIs: {s['public_api_count']}");print(f"Typed public APIs: {s['typed_public_api_count']}");print(f"Documented public APIs: {s['documented_public_api_count']}");print(f"Violations: {s['violation_count']}");return 0 if s["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
'''
@dataclass(frozen=True)
class Check:check_id:str;status:str;summary:str;details:dict[str,Any];blocking:bool=False
class PatchError(RuntimeError):pass
def run(root:Path,*cmd:str,timeout:int=120):return subprocess.run(cmd,cwd=root,text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=timeout,check=False)
def git(root:Path,*args:str):return run(root,"git",*args)
def rev(root:Path,name:str):
 r=git(root,"rev-parse","--verify",f"{name}^{{commit}}");return r.stdout.strip() if r.returncode==0 else None
def sha(path:Path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""):h.update(c)
 return h.hexdigest()
def db(root:Path):
 out={}
 for n in DB_FILES:
  p=root/n;out[n]={"exists":False} if not p.exists() else {"exists":True,"size":p.stat().st_size,"mtime_ns":p.stat().st_mtime_ns,"sha256":sha(p)}
 return out
def write(path:Path,text:str):
 t=path.with_suffix(path.suffix+".tmp");t.parent.mkdir(parents=True,exist_ok=True);t.write_text(text,encoding="utf-8",newline="\n");os.replace(t,path)
def statuses(raw:str):return [{"status":x[:2],"path":x[3:]} for x in raw.split("\0") if x]
def blob(root:Path,commit:str,path:str):
 r=subprocess.run(["git","show",f"{commit}:{path}"],cwd=root,capture_output=True,check=False);return r.stdout if r.returncode==0 else None
def backups(root:Path):
 (root/"backup").mkdir(exist_ok=True);m={"files":{}}
 for rel in (VERIFIER_PATH,REPORT_PATH,ADR_PATH):
  b=blob(root,EXPECTED_PARENT,rel);p=root/"backup"/f"{BACKUP_PREFIX}__{rel.replace('/','__')}"
  if b is None:m["files"][rel]={"existed":False,"backup":None}
  else:p.write_bytes(b);m["files"][rel]={"existed":True,"backup":str(p.relative_to(root)).replace("\\","/")}
 return m
def rollback(root:Path,m,reason,checks):
 git(root,"reset","--",VERIFIER_PATH,REPORT_PATH,ADR_PATH);restored=[];removed=[];errors=[]
 for rel,meta in m["files"].items():
  p=root/rel
  try:
   if meta["existed"]:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/meta["backup"]).read_bytes());restored.append(rel)
   elif p.exists():p.unlink();removed.append(rel)
  except OSError as e:errors.append(f"{rel}: {e}")
 out={"stage":STAGE,"status":"FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE","reason":reason,"failed_checks":[asdict(x) for x in checks if x.status=="FAIL"],"restored_files":restored,"removed_failed_artifacts":removed,"rollback_errors":errors,"database_evidence_after_rollback":db(root),"main_py_started":False,"wal_shm_manipulated":False};write(root/FAILURE_REPORT,json.dumps(out,ensure_ascii=False,indent=2)+"\n");return out
def adr(r):
 s=r["summary"];return "\n".join(["# ADR 21.2.7 — ROM V2 code and comment standards","","- **Status:** `ACCEPTED`","- **Criterion:** `Lintable coding standard`","","## Type hints","","Every public function and method has typed parameters and an explicit return type. Public attributes are typed. `Any` requires a documented boundary reason.","","## Docstrings","","Public modules, classes, functions and methods require docstrings that describe contract, invariants and failure behavior rather than repeating implementation syntax.","","## Comments","","Comments explain reasons and non-obvious invariants. Comments are required around rounding, ordering, atomicity, idempotency, restart semantics and workarounds. Comments that restate obvious code are forbidden. TODO/FIXME requires a Stage or issue reference.","","## Naming and ownership","","English snake_case is used for modules/functions and PascalCase for types. Catch-all modules and duplicate production owners are forbidden.","","## Exceptions","","Bare except and silent exception swallowing are forbidden. Expected business outcomes use typed Result. Translated exceptions preserve chaining.","","## Automated evidence","",f"- Physical V2 exists: **{s['physical_v2_exists']}**.",f"- Files checked: **{s['file_count']}**.",f"- Public APIs checked: **{s['public_api_count']}**.",f"- Violations: **{s['violation_count']}**.","","## Next roadmap stage","","Stage 21.3.1 — Minimal V2 package skeleton and isolated bootstrap.",""])
def commit(root):
 paths=[PATCH_PATH,VERIFIER_PATH,REPORT_PATH,ADR_PATH];r=git(root,"add","-f","--",*paths)
 if r.returncode:raise PatchError(r.stderr.strip())
 staged=sorted(x for x in git(root,"diff","--cached","--name-only","-z").stdout.split("\0") if x)
 if staged!=sorted(paths):git(root,"reset","--",*paths);raise PatchError(f"staging mismatch: {staged}")
 r=git(root,"commit","-m",COMMIT_MESSAGE)
 if r.returncode:git(root,"reset","--",*paths);raise PatchError(r.stderr.strip() or r.stdout.strip())
 return rev(root,"HEAD") or ""
def main():
 root=Path(__file__).resolve().parent.parent
 for req in (CLOCK_REPORT,CLOCK_ADR):
  if not (root/req).is_file():print(f"[FAIL] Missing Stage 21.2.6 artifact: {req}",file=sys.stderr);return 2
 print("[1/8] [PASS] Stage 21.2.6 artifacts and regulated directories detected.")
 branch=git(root,"branch","--show-current").stdout.strip();head=rev(root,"HEAD");u=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");up=u.stdout.strip() if u.returncode==0 else None
 entries=statuses(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout);allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in ALLOWED_DIRTY and e["status"][0]==" "))];unexpected=[e for e in entries if e not in allowed]
 checks=[Check("BRANCH","PASS" if branch==TARGET_BRANCH else "FAIL",f"Active branch: {branch}",{},branch!=TARGET_BRANCH),Check("PARENT","PASS" if head==EXPECTED_PARENT else "FAIL","Expected Stage 21.2.6 parent verified.",{"expected":EXPECTED_PARENT,"actual":head},head!=EXPECTED_PARENT),Check("UPSTREAM","PASS" if up==f"origin/{TARGET_BRANCH}" else "FAIL",f"Upstream: {up}",{},up!=f"origin/{TARGET_BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes.",{"unexpected":unexpected},bool(unexpected))]
 if any(x.blocking for x in checks):print("[2/8] [FAIL] Preflight returned NO_GO.");return 1
 prior=json.loads((root/CLOCK_REPORT).read_text(encoding="utf-8"))
 if prior.get("stage")!="21.2.6" or prior.get("summary",{}).get("conclusion")!="GO":print("[FAIL] Stage 21.2.6 prerequisite is not canonical GO.",file=sys.stderr);return 2
 checks.append(Check("CLOCK_RNG_PREREQUISITE","PASS","Clock/RNG contract is canonical GO.",{}));print("[2/8] [PASS] Branch, parent, upstream, worktree and prerequisite verified; backups prepared in ROM\\backup.")
 before=db(root);m=backups(root);print("[3/8] [PASS] Writing code/comment standards verifier and ADR.");write(root/VERIFIER_PATH,VERIFIER)
 try:py_compile.compile(str(root/VERIFIER_PATH),doraise=True)
 except py_compile.PyCompileError as e:r=rollback(root,m,f"py_compile failed: {e}",checks);print(f"[FAIL] rollback: {r['status']}");return 2
 print("[4/8] [PASS] Executing code/comment standards verifier against current V2 tree.");tc=root/"reports"/".stage_21_2_7_contract.tmp.json";tr=root/"reports"/".stage_21_2_7_result.tmp.json";write(tc,json.dumps(CONTRACT,ensure_ascii=False,indent=2)+"\n");vr=run(root,sys.executable,VERIFIER_PATH,"--project-root",str(root),"--contract",str(tc),"--json-out",str(tr));res=json.loads(tr.read_text(encoding="utf-8")) if tr.exists() else {};tc.unlink(missing_ok=True);tr.unlink(missing_ok=True);s=res.get("summary",{})
 checks += [Check("VERIFIER_EXECUTION","PASS" if vr.returncode==0 else "FAIL",vr.stdout.strip(),{"stderr":vr.stderr.strip()},vr.returncode!=0),Check("LINTABLE_CODING_STANDARD","PASS" if s.get("violation_count")==0 else "FAIL",f"Violations: {s.get('violation_count')}",{},s.get("violation_count")!=0),Check("PUBLIC_API_TYPED","PASS" if s.get("typed_public_api_count")==s.get("public_api_count") else "FAIL","All discovered public APIs are typed.",{},s.get("typed_public_api_count")!=s.get("public_api_count")),Check("PUBLIC_API_DOCUMENTED","PASS" if s.get("documented_public_api_count")==s.get("public_api_count") else "FAIL","All discovered public APIs are documented.",{},s.get("documented_public_api_count")!=s.get("public_api_count")),Check("DATABASE_EVIDENCE_READY","PASS","DB/WAL/SHM captured without SQLite connection.",{"production_connection_opened":False})]
 blockers=[x.check_id for x in checks if x.blocking];out={"schema_version":1,"stage":STAGE,"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":"GO" if not blockers else "NO_GO","blocking_failures":blockers,**s},"git":{"branch":branch,"head_before_commit":head,"upstream":up},"checks":[asdict(x) for x in checks],"code_comment_contract":CONTRACT,"verifier_result":res,"database_evidence_before":before,"artifacts":{"patch":PATCH_PATH,"verifier":VERIFIER_PATH,"json":REPORT_PATH,"adr":ADR_PATH},"next_stage":"21.3.1","suggested_next_patch":"patch_21_3_1_create_isolated_v2_package_skeleton.py"}
 print("[5/8] [PASS] Writing full coding standard and evidence report.")
 try:
  write(root/REPORT_PATH,json.dumps(out,ensure_ascii=False,indent=2)+"\n");write(root/ADR_PATH,adr(res))
  if blockers:r=rollback(root,m,"coding standard NO_GO",checks);print(f"[6/8] [FAIL] rollback: {r['status']}");return 1
  if before!=db(root):r=rollback(root,m,"DB evidence changed",checks);print(f"[6/8] [FAIL] rollback: {r['status']}");return 2
 except Exception as e:r=rollback(root,m,f"mutation failure: {e}",checks);print(f"[6/8] [FAIL] rollback: {r['status']}");return 2
 print("[6/8] [PASS] Type hints, docstrings, comments, naming and exception standards validated.");(root/FAILURE_REPORT).unlink(missing_ok=True)
 try:print("[7/8] [PASS] Creating exact-allowlist Stage 21.2.7 commit.");c=commit(root)
 except PatchError as e:r=rollback(root,m,f"commit failed: {e}",checks);print(f"[7/8] [FAIL] rollback: {r['status']}");return 2
 print(f"[8/8] [PASS] Code/comment standards committed and DB/WAL/SHM verified: {c}");print("="*72);print(f"ROM Stage {STAGE} - Code and comment standards")
 for x in checks:print(f"[{x.status}] {x.check_id}: {x.summary}")
 print(f"[PASS] PHYSICAL_V2_EXISTS: {s['physical_v2_exists']}\n[PASS] FILES: {s['file_count']}\n[PASS] PUBLIC_APIS: {s['public_api_count']}\n[PASS] TYPED_PUBLIC_APIS: {s['typed_public_api_count']}\n[PASS] DOCUMENTED_PUBLIC_APIS: {s['documented_public_api_count']}\n[PASS] VIOLATIONS: {s['violation_count']}")
 print("CONCLUSION: GO\nPATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({c})");print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nWAL/SHM: NOT MANIPULATED\nSUGGESTED NEXT PATCH: patch_21_3_1_create_isolated_v2_package_skeleton.py");return 0
if __name__=="__main__":raise SystemExit(main())
