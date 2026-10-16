#!/usr/bin/env python3
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
