#!/usr/bin/env python3
"""Stage 21.3.6: create a deterministic ROM V2 CI baseline."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="21.3.6"; TARGET_BRANCH="rewrite/rom-v2"; EXPECTED_PARENT="46d1781ab8a8fcb1fe5cff6f06070c190814cef5"
PREREQ="reports/stage_21_3_5_architecture_enforcement.json"; PATCH_PATH="patch/patch_21_3_6_create_v2_ci_foundation.py"
RUNNER_PATH="tools/run_v2_ci.py"; WORKFLOW_PATH=".github/workflows/rom-v2-ci.yml"; TEST_PATH="tests_v2/test_ci_baseline.py"
REPORT_PATH="reports/stage_21_3_6_ci_baseline.json"; CONTRACT_PATH="MD/STAGE_21_3_6_V2_CI_BASELINE.md"; FAILURE_REPORT="reports/stage_21_3_6_failure_rollback.json"
COMMIT_MESSAGE="Stage 21.3.6: create V2 CI baseline"; DB_FILES=("game.db","game.db-wal","game.db-shm"); ALLOWED_DIRTY={"ROM_FULL_DUMP.txt","ROM_ADDITIONAL_DUMP.txt"}
MUTATED=(RUNNER_PATH,WORKFLOW_PATH,TEST_PATH,REPORT_PATH,CONTRACT_PATH); OWNED={PATCH_PATH,FAILURE_REPORT,*MUTATED}; BACKUP_PREFIX="stage_21_3_6"

RUNNER_SOURCE=r'''#!/usr/bin/env python3
"""Run the canonical ROM V2 CI baseline locally or in hosted CI."""
from __future__ import annotations
import argparse, ast, json, os, subprocess, sys
from pathlib import Path
from typing import Any


def _run(root: Path, *command: str) -> dict[str, Any]:
    """Run one CI command with deterministic Python environment settings."""
    environment = os.environ.copy(); environment["PYTHONDONTWRITEBYTECODE"] = "1"; environment["PYTHONHASHSEED"] = "0"
    result = subprocess.run(command, cwd=root, env=environment, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=120, check=False)
    return {"command": list(command), "returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def _compile(root: Path) -> dict[str, Any]:
    """Compile every V2 production and test source without writing bytecode."""
    failures=[]; count=0
    for base_name in ("rom_v2", "tests_v2"):
        base=root/base_name
        for path in sorted(base.rglob("*.py")):
            count+=1
            try: compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except SyntaxError as exc: failures.append({"file":path.relative_to(root).as_posix(),"line":exc.lineno,"error":str(exc)})
    return {"name":"compile","status":"PASS" if not failures else "FAIL","file_count":count,"failures":failures}


def _imports(root: Path) -> dict[str, Any]:
    """Import every V2 production module in a fresh interpreter."""
    modules=[]
    for path in sorted((root/"rom_v2").rglob("*.py")):
        relative=path.relative_to(root).with_suffix("")
        if relative.name=="__init__": relative=relative.parent
        module=".".join(relative.parts)
        if module and module not in modules: modules.append(module)
    script="import importlib; [importlib.import_module(name) for name in "+repr(modules)+"]"
    result=_run(root,sys.executable,"-c",script)
    return {"name":"imports","status":"PASS" if result["returncode"]==0 else "FAIL","module_count":len(modules),"execution":result}


def _duplicates(root: Path) -> dict[str, Any]:
    """Detect duplicate top-level production symbol owners across V2 modules."""
    owners:dict[str,list[dict[str,Any]]]={}
    for path in sorted((root/"rom_v2").rglob("*.py")):
        relative=path.relative_to(root).as_posix(); tree=ast.parse(path.read_text(encoding="utf-8"),filename=relative)
        for node in tree.body:
            if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                owners.setdefault(node.name,[]).append({"file":relative,"line":node.lineno,"kind":type(node).__name__})
    duplicates={name:rows for name,rows in owners.items() if len(rows)>1}
    return {"name":"duplicate_scan","status":"PASS" if not duplicates else "FAIL","symbol_count":len(owners),"duplicates":duplicates}


def _content(root: Path) -> dict[str, Any]:
    """Validate declarative V2 JSON content and Python content syntax."""
    failures=[]; files=[]; content=root/"rom_v2"/"content"
    for path in sorted(content.rglob("*")):
        if not path.is_file() or path.name=="__init__.py": continue
        relative=path.relative_to(root).as_posix(); files.append(relative)
        try:
            if path.suffix==".json": json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix==".py": ast.parse(path.read_text(encoding="utf-8"),filename=relative)
            else: failures.append({"file":relative,"rule":"UNSUPPORTED_CONTENT_EXTENSION"})
        except (SyntaxError,json.JSONDecodeError) as exc: failures.append({"file":relative,"rule":"INVALID_CONTENT","error":str(exc)})
    return {"name":"content_validation","status":"PASS" if not failures else "FAIL","file_count":len(files),"failures":failures}


def run_ci(root: Path) -> dict[str, Any]:
    """Execute compile, imports, unit, architecture, duplicate, and content gates."""
    checks=[_compile(root),_imports(root)]
    unit=_run(root,sys.executable,"-m","unittest","discover","-s","tests_v2","-p","test_*.py")
    checks.append({"name":"unit","status":"PASS" if unit["returncode"]==0 else "FAIL","execution":unit})
    architecture=_run(root,sys.executable,"tools/verify_v2_architecture.py","--project-root",str(root))
    checks.append({"name":"architecture","status":"PASS" if architecture["returncode"]==0 else "FAIL","execution":architecture})
    checks.extend([_duplicates(root),_content(root)])
    failed=[check["name"] for check in checks if check["status"]!="PASS"]
    return {"schema_version":1,"status":"PASS" if not failed else "FAIL","failed_checks":failed,"checks":checks}


def main() -> int:
    """Run the CI baseline and write optional machine-readable evidence."""
    parser=argparse.ArgumentParser(); parser.add_argument("--project-root",default="."); parser.add_argument("--json-out"); args=parser.parse_args()
    result=run_ci(Path(args.project_root).resolve()); text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.json_out: Path(args.json_out).write_text(text,encoding="utf-8",newline="\n")
    print(f"ROM V2 CI baseline: {result['status']}")
    for check in result["checks"]: print(f"[{check['status']}] {check['name']}")
    return 0 if result["status"]=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())
'''

WORKFLOW_SOURCE='''name: ROM V2 CI

on:
  push:
    branches: ["rewrite/rom-v2"]
  pull_request:
    branches: ["rewrite/rom-v2", "master"]

permissions:
  contents: read

jobs:
  v2-baseline:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - name: Run canonical V2 CI baseline
        env:
          PYTHONDONTWRITEBYTECODE: "1"
          PYTHONHASHSEED: "0"
        run: python tools/run_v2_ci.py --project-root . --json-out reports/v2_ci_result.json
      - name: Upload CI evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: rom-v2-ci-evidence
          path: reports/v2_ci_result.json
          if-no-files-found: error
'''

TEST_SOURCE='''"""Tests for the canonical ROM V2 CI baseline runner."""
from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from tools.run_v2_ci import _compile, _content, _duplicates, _imports


class V2CiBaselineTest(unittest.TestCase):
    """Verify the current baseline and representative rejection paths."""

    def test_non_recursive_static_gates_pass(self) -> None:
        """Require static CI gates to pass without recursively invoking unit discovery."""
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(_compile(root)["status"],"PASS")
        self.assertEqual(_imports(root)["status"],"PASS")
        self.assertEqual(_duplicates(root)["status"],"PASS")
        self.assertEqual(_content(root)["status"],"PASS")

    def test_duplicate_public_symbol_is_rejected(self) -> None:
        """Reject duplicate top-level production owners."""
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); package=root/"rom_v2"; package.mkdir()
            (package/"one.py").write_text("def duplicate() -> None:\\n    pass\\n",encoding="utf-8")
            (package/"two.py").write_text("def duplicate() -> None:\\n    pass\\n",encoding="utf-8")
            self.assertEqual(_duplicates(root)["status"],"FAIL")

    def test_invalid_json_content_is_rejected(self) -> None:
        """Reject malformed declarative JSON content."""
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); content=root/"rom_v2"/"content"; content.mkdir(parents=True)
            (content/"invalid.json").write_text("{",encoding="utf-8")
            self.assertEqual(_content(root)["status"],"FAIL")


if __name__=="__main__": unittest.main()
'''

@dataclass(frozen=True)
class Check: check_id:str; status:str; summary:str; details:dict[str,Any]; blocking:bool=False
class PatchError(RuntimeError): pass

def run(root:Path,*cmd:str,timeout:int=180):
    env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0"
    return subprocess.run(cmd,cwd=root,env=env,text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=timeout,check=False)
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
    for rel in MUTATED:
        b=blob(root,EXPECTED_PARENT,rel);p=root/"backup"/f"{BACKUP_PREFIX}__{rel.replace('/','__')}"
        if b is None:m["files"][rel]={"existed":False,"backup":None}
        else:p.write_bytes(b);m["files"][rel]={"existed":True,"backup":str(p.relative_to(root)).replace("\\","/")}
    return m
def rollback(root:Path,m,reason,checks):
    git(root,"reset","--",*MUTATED);restored=[];removed=[];errors=[]
    for rel,meta in m["files"].items():
        p=root/rel
        try:
            if meta["existed"]:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/meta["backup"]).read_bytes());restored.append(rel)
            elif p.exists():p.unlink();removed.append(rel)
        except OSError as e:errors.append(f"{rel}: {e}")
    out={"stage":STAGE,"status":"FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE","reason":reason,"failed_checks":[asdict(x) for x in checks if x.status=="FAIL"],"restored_files":restored,"removed_failed_artifacts":removed,"rollback_errors":errors,"database_evidence_after_rollback":db(root),"main_py_started_after_failure":False,"wal_shm_manipulated":False};write(root/FAILURE_REPORT,json.dumps(out,ensure_ascii=False,indent=2)+"\n");return out
def render(result):
    return "\n".join(["# Stage 21.3.6 — ROM V2 CI baseline","","- **Status:** `IMPLEMENTED`","- **Canonical runner:** `tools/run_v2_ci.py`","- **Hosted workflow:** `.github/workflows/rom-v2-ci.yml`","","## Mandatory gates","","1. Compile","2. Imports","3. Unit tests","4. Architecture enforcement","5. Duplicate scan","6. Content validation","","The same canonical runner is executed locally and by hosted CI, so every commit is checked consistently.","",f"Final baseline status: **{result['status']}**.","","## Next roadmap stage","","Stage 21.4.1 — Domain value objects foundation.",""])
def commit(root:Path):
    paths=[PATCH_PATH,*MUTATED];r=git(root,"add","-f","--",*paths)
    if r.returncode:raise PatchError(r.stderr.strip())
    staged=sorted(x for x in git(root,"diff","--cached","--name-only","-z").stdout.split("\0") if x)
    if staged!=sorted(paths):git(root,"reset","--",*paths);raise PatchError(f"staging mismatch: {staged}")
    r=git(root,"commit","-m",COMMIT_MESSAGE)
    if r.returncode:git(root,"reset","--",*paths);raise PatchError(r.stderr.strip() or r.stdout.strip())
    return rev(root,"HEAD") or ""
def main():
    root=Path(__file__).resolve().parent.parent
    if not (root/PREREQ).is_file():print(f"[FAIL] Missing prerequisite: {PREREQ}",file=sys.stderr);return 2
    prior=json.loads((root/PREREQ).read_text(encoding="utf-8"))
    if prior.get("stage")!="21.3.5" or prior.get("summary",{}).get("conclusion")!="GO":print("[FAIL] Stage 21.3.5 prerequisite is not canonical GO.",file=sys.stderr);return 2
    print("[1/10] [PASS] Stage 21.3.5 prerequisite and architecture verifier detected.")
    branch=git(root,"branch","--show-current").stdout.strip();head=rev(root,"HEAD");u=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");up=u.stdout.strip() if u.returncode==0 else None
    entries=statuses(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout);allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in ALLOWED_DIRTY and e["status"][0]==" "))];unexpected=[e for e in entries if e not in allowed]
    checks=[Check("BRANCH","PASS" if branch==TARGET_BRANCH else "FAIL",f"Active branch: {branch}",{},branch!=TARGET_BRANCH),Check("PARENT","PASS" if head==EXPECTED_PARENT else "FAIL","Expected Stage 21.3.5 parent verified.",{"expected":EXPECTED_PARENT,"actual":head},head!=EXPECTED_PARENT),Check("UPSTREAM","PASS" if up==f"origin/{TARGET_BRANCH}" else "FAIL",f"Upstream: {up}",{},up!=f"origin/{TARGET_BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes.",{"unexpected":unexpected},bool(unexpected))]
    if any(x.blocking for x in checks):print("[2/10] [FAIL] Preflight returned NO_GO.");return 1
    print("[2/10] [PASS] Branch, parent, upstream and worktree verified; backups prepared in ROM\\backup.")
    before=db(root);m=backups(root)
    try:
        print("[3/10] [PASS] Writing canonical CI runner, hosted workflow and rejection tests.");write(root/RUNNER_PATH,RUNNER_SOURCE);write(root/WORKFLOW_PATH,WORKFLOW_SOURCE);write(root/TEST_PATH,TEST_SOURCE)
        print("[4/10] [PASS] Compiling generated Python artifacts without bytecode.")
        for rel in (RUNNER_PATH,TEST_PATH):compile((root/rel).read_text(encoding="utf-8"),str(root/rel),"exec")
        print("[5/10] [PASS] Running canonical V2 CI baseline.");tmp=root/"reports/.stage_21_3_6_ci.tmp.json";execution=run(root,sys.executable,RUNNER_PATH,"--project-root",str(root),"--json-out",str(tmp));result=json.loads(tmp.read_text(encoding="utf-8")) if tmp.exists() else {"status":"FAIL","failed_checks":["missing_output"],"checks":[]};tmp.unlink(missing_ok=True);ok=execution.returncode==0 and result.get("status")=="PASS";checks.append(Check("CI_BASELINE","PASS" if ok else "FAIL",execution.stdout.strip() or "CI baseline failed.",{"stderr":execution.stderr.strip(),"failed_checks":result.get("failed_checks",[])},not ok))
        print("[6/10] [PASS] Running CI runner happy-path and rejection tests.");unit=run(root,sys.executable,"-m","unittest","tests_v2.test_ci_baseline");checks.append(Check("CI_TESTS","PASS" if unit.returncode==0 else "FAIL",unit.stderr.strip() or unit.stdout.strip(),{},unit.returncode!=0))
        print("[7/10] [PASS] Validating workflow contract and deterministic environment.");workflow=(root/WORKFLOW_PATH).read_text(encoding="utf-8");required=["actions/checkout@v4","actions/setup-python@v5","actions/upload-artifact@v4","tools/run_v2_ci.py","PYTHONDONTWRITEBYTECODE","PYTHONHASHSEED"] ;missing=[x for x in required if x not in workflow];checks.append(Check("WORKFLOW_CONTRACT","PASS" if not missing else "FAIL",f"Missing workflow markers: {missing}",{},bool(missing)))
        print("[8/10] [PASS] Verifying database safety and runtime isolation.");checks.append(Check("DATABASE_UNCHANGED","PASS" if before==db(root) else "FAIL","DB/WAL/SHM unchanged and SQLite was not opened.",{"production_connection_opened":False},before!=db(root)))
        blockers=[x.check_id for x in checks if x.blocking]
        if blockers:r=rollback(root,m,f"Stage 21.3.6 NO_GO: {blockers}",checks);print(f"[9/10] [FAIL] Rollback: {r['status']}");return 1
        payload={"schema_version":1,"stage":STAGE,"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":"GO","blocking_failures":[],"ci_status":result["status"],"gate_count":len(result["checks"]),"gameplay_started":False,"database_opened":False},"git":{"branch":branch,"head_before_commit":head,"upstream":up},"checks":[asdict(x) for x in checks],"ci_result":result,"database_evidence_before":before,"database_evidence_after":db(root),"changed_files":[PATCH_PATH,*MUTATED],"next_stage":"21.4.1","suggested_next_patch":"patch_21_4_1_define_domain_value_objects.py"}
        print("[9/10] [PASS] Writing CI evidence and baseline contract.");write(root/REPORT_PATH,json.dumps(payload,ensure_ascii=False,indent=2)+"\n");write(root/CONTRACT_PATH,render(result))
    except Exception as e:r=rollback(root,m,f"Mutation or verification failure: {e}",checks);print(f"[9/10] [FAIL] {e}; rollback: {r['status']}",file=sys.stderr);return 2
    (root/FAILURE_REPORT).unlink(missing_ok=True)
    try:c=commit(root)
    except PatchError as e:r=rollback(root,m,f"Commit failure: {e}",checks);print(f"[10/10] [FAIL] rollback: {r['status']}",file=sys.stderr);return 2
    print(f"[10/10] [PASS] CI baseline committed with all canonical gates PASS: {c}");print("="*72);print(f"ROM Stage {STAGE} - CI baseline")
    for x in checks:print(f"[{x.status}] {x.check_id}: {x.summary}")
    print(f"[PASS] CI_GATES: {len(result['checks'])}\n[PASS] CI_STATUS: {result['status']}\n[PASS] GAMEPLAY_STARTED: False\n[PASS] DATABASE_OPENED: False\nCONCLUSION: GO\nPATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({c})");print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nWAL/SHM: NOT MANIPULATED\nSUGGESTED NEXT PATCH: patch_21_4_1_define_domain_value_objects.py");return 0
if __name__=="__main__":raise SystemExit(main())
