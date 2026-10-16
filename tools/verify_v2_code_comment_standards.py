#!/usr/bin/env python3
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
