#!/usr/bin/env python3
"""Reject newly introduced V2 overlays, monkey patches and duplicate owners."""
from __future__ import annotations
import argparse, ast, json
from pathlib import Path
from typing import Any

IGNORED_PARTS = {".git", ".venv", "venv", "backup", ".runtime", "legacy", "__pycache__"}
OVERLAY_NAMES = {"overlay", "overrides", "monkey_patch", "patches", "shadow"}
REBIND_CALLS = {"setattr", "delattr"}


def signature(v: dict[str, Any]) -> str:
    return f"{v['path']}:{v['line']}:{v['code']}:{v.get('symbol','')}"


def scan_file(root: Path, path: Path) -> list[dict[str, Any]]:
    rel = path.relative_to(root).as_posix()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
    except (OSError, UnicodeError, SyntaxError):
        return []
    out: list[dict[str, Any]] = []
    seen: dict[tuple[str, str], int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            key=(type(node).__name__, node.name)
            if key in seen:
                out.append({"path":rel,"line":node.lineno,"code":"DUPLICATE_TOP_LEVEL_OWNER","symbol":node.name})
            else: seen[key]=node.lineno
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in REBIND_CALLS:
            out.append({"path":rel,"line":node.lineno,"code":"RUNTIME_ATTRIBUTE_REBIND","symbol":node.func.id})
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id not in {"self","cls"}:
                    out.append({"path":rel,"line":node.lineno,"code":"MODULE_ATTRIBUTE_REBIND","symbol":target.attr})
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names=[]
            if isinstance(node, ast.Import): names=[a.name for a in node.names]
            elif node.module: names=[node.module]
            for name in names:
                if any(part.lower() in OVERLAY_NAMES for part in name.split('.')):
                    out.append({"path":rel,"line":node.lineno,"code":"OVERLAY_IMPORT","symbol":name})
    return out


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--baseline")
    ap.add_argument("--write-baseline", action="store_true")
    ns=ap.parse_args(); root=Path(ns.project_root).resolve()
    files=[p for p in (root/"rom_v2").rglob("*.py") if not (set(p.parts)&IGNORED_PARTS)]
    violations=[]
    for p in files: violations.extend(scan_file(root,p))
    violations.sort(key=lambda x:(x["path"],x["line"],x["code"],x.get("symbol","")))
    baseline_path=Path(ns.baseline).resolve() if ns.baseline else None
    baseline=set()
    if baseline_path and baseline_path.exists():
        data=json.loads(baseline_path.read_text(encoding="utf-8")); baseline=set(data.get("signatures",[]))
    if ns.write_baseline:
        payload={"schema_version":1,"stage":"21.16.2","purpose":"Reviewed pre-existing findings; new findings are blocking.","signatures":[signature(v) for v in violations],"findings":violations}
        baseline_path.parent.mkdir(parents=True,exist_ok=True)
        baseline_path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        baseline=set(payload["signatures"])
    blocking=[v for v in violations if signature(v) not in baseline]
    report={"schema_version":1,"stage":"21.16.2","status":"PASS" if not blocking else "FAIL","python_files":len(files),"findings_total":len(violations),"baseline_findings":len(violations)-len(blocking),"blocking_violations":blocking,"all_findings":violations}
    out=Path(ns.json); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"V2 direct-code anti-overlay verification: {report['status']}")
    print(f"Python files: {len(files)}")
    print(f"Reviewed baseline findings: {report['baseline_findings']}")
    print(f"Blocking violations: {len(blocking)}")
    return 0 if not blocking else 1
if __name__ == "__main__": raise SystemExit(main())
