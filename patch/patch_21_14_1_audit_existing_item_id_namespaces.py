#!/usr/bin/env python3
"""Stage 21.14.1: read-only audit of V1 item ID namespaces and allocation rules."""
from __future__ import annotations
import ast,hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.14.1";PARENT="1d8e82cc5096a9ba4f9bb3fd4f2cde3dc10042fa"
SELF="patch/patch_21_14_1_audit_existing_item_id_namespaces.py"
REPORT=Path("reports/stage_21_14_1_existing_item_id_namespace_audit.json")
DOC=Path("MD/STAGE_21_14_1_EXISTING_ITEM_ID_NAMESPACE_AUDIT.md")
TARGETS=(Path(SELF),REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt"};PROTECTED=(Path("main.py"),Path("game.db"),Path("game.db-wal"),Path("game.db-shm"))
ROOTS=("data","systems","db_modules","handlers","migrations","tools","tests","tests_v2","rom_v2")
TOKENS=("EVENT_ITEM","EVENT_KEY","event_item","event_key","namespace","item_id","preview","permanent","generated","allocator","never-reuse","never_reuse","4000","9999","10000","10000000","block")
class AuditError(RuntimeError):pass
def run(args,cwd,check=True):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
 if check and p.returncode:raise AuditError(f"command_failed:{args}:{p.stdout}{p.stderr}")
 return p
def git(r,*args,check=True):return run(["git",*args],r,check)
def root():
 r=Path(__file__).resolve().parent.parent
 if not (r/".git").exists():raise AuditError("project_root_not_found")
 return r
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def write(p,text):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf-8",newline="\n")
def status(r):return [(x[:2],x[3:].split(" -> ")[-1].replace("\\","/")) for x in git(r,"status","--porcelain=v1","--untracked-files=all").stdout.splitlines() if x]
def pyfiles(r):
 out=[]
 for name in ROOTS:
  p=r/name
  if p.exists():out.extend(q for q in p.rglob("*.py") if "__pycache__" not in q.parts)
 return sorted(set(out))
def scan_file(r,p):
 rel=p.relative_to(r).as_posix();text=p.read_text(encoding="utf-8",errors="replace")
 hits=[]
 for n,line in enumerate(text.splitlines(),1):
  low=line.lower()
  if any(t.lower() in low for t in TOKENS):hits.append({"line":n,"text":line.strip()[:500]})
 if not hits:return None
 symbols=[]
 try:
  tree=ast.parse(text,filename=rel)
  for node in ast.walk(tree):
   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and any(t.lower() in node.name.lower() for t in ("item","event","alloc","preview","generate","namespace")):
    symbols.append({"name":node.name,"line":node.lineno,"kind":type(node).__name__})
   elif isinstance(node,(ast.Assign,ast.AnnAssign)):
    targets=node.targets if isinstance(node,ast.Assign) else [node.target]
    for target in targets:
     if isinstance(target,ast.Name) and any(t.lower() in target.id.lower() for t in ("item","event","alloc","preview","namespace","id")):
      symbols.append({"name":target.id,"line":node.lineno,"kind":"constant_or_variable"})
 except SyntaxError as e:raise AuditError(f"ast_parse_failed:{rel}:{e}")
 return {"file":rel,"sha256":sha(p),"hits":hits,"symbols":symbols}
def classify(records):
 cats={"event_static_namespace":[],"static_catalog_ids":[],"generated_permanent_ids":[],"preview_ids":[],"quest_item_ids":[],"premium_or_fixed_ids":[],"allocators_and_persistence":[],"tests_and_verifiers":[],"unknown_or_overlap_risk":[]}
 for rec in records:
  blob=(rec["file"]+" "+" ".join(x["text"] for x in rec["hits"])).lower()
  names=[]
  if any(x in blob for x in ("4000","9999","event_key","event item","event_item","event namespace")):names.append("event_static_namespace")
  if "preview" in blob or "10000000" in blob or "10010000" in blob:names.append("preview_ids")
  if any(x in blob for x in ("permanent","never-reuse","never_reuse","next_item_id","allocate_item","generated equipment")):names.append("generated_permanent_ids")
  if "quest" in blob and "item" in blob:names.append("quest_item_ids")
  if any(x in blob for x in ("premium","crystal shop","perfect extractor","sphere","rune of success")):names.append("premium_or_fixed_ids")
  if any(x in blob for x in ("allocator","allocate","sequence","counter","max(item","next_id","registry","block")):names.append("allocators_and_persistence")
  if rec["file"].startswith(("tests/","tests_v2/","tools/")):names.append("tests_and_verifiers")
  if not names:names.append("static_catalog_ids")
  for name in dict.fromkeys(names):cats[name].append(rec["file"])
 return {k:sorted(set(v)) for k,v in cats.items()}
def main():
 r=root();before={p.as_posix():sha(r/p) for p in PROTECTED}
 try:
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise AuditError("wrong_exact_parent")
  branch=git(r,"branch","--show-current").stdout.strip()
  if branch!="rewrite/rom-v2":raise AuditError("wrong_branch:"+branch)
  if git(r,"diff","--cached","--name-only").stdout.strip():raise AuditError("staged_index_not_clean")
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise AuditError("unexpected_dirty:"+repr(bad))
  print("[1/8] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
  files=pyfiles(r);records=[x for p in files if (x:=scan_file(r,p))]
  if not records:raise AuditError("no_item_id_namespace_evidence_found")
  print(f"[2/8] [PASS] Parsed {len(files)} Python file(s); retained {len(records)} item/event ID evidence owner(s).")
  categories=classify(records)
  event_files=categories["event_static_namespace"]
  if not event_files:raise AuditError("event_namespace_4000_9999_not_found")
  print(f"[3/8] [PASS] Event namespace evidence found in {len(event_files)} owner/reference file(s).")
  # Evidence-led audit only: extract every integer near ID/allocation markers, but do not infer undocumented ranges.
  numbers={}
  for rec in records:
   vals=[]
   for hit in rec["hits"]:
    vals.extend(int(x.replace("_","")) for x in re.findall(r"(?<![A-Za-z])\d[\d_]{2,}(?![A-Za-z])",hit["text"]))
   if vals:numbers[rec["file"]]=sorted(set(vals))
  print("[4/8] [PASS] Static, generated, preview, quest, premium/fixed and allocator evidence classified without inventing ranges.")
  decisions=[]
  checks={
   "event_namespace_bounds_evidenced":any(4000 in v and 9999 in v for v in numbers.values()),
   "event_block_size_25_evidenced":any(25 in v for v in numbers.values()),
   "event_key_allocation_evidenced":any("event_key" in " ".join(x["text"] for x in rec["hits"]).lower() for rec in records),
   "generated_permanent_evidence_present":bool(categories["generated_permanent_ids"]),
   "preview_evidence_present":bool(categories["preview_ids"]),
   "quest_item_evidence_present":bool(categories["quest_item_ids"]),
   "allocator_persistence_evidence_present":bool(categories["allocators_and_persistence"]),
  }
  for key,value in checks.items():decisions.append({"contract":key,"status":"EVIDENCED" if value else "REVIEW_REQUIRED"})
  print("[5/8] [PASS] Allocation invariants and unresolved boundaries recorded with fail-closed REVIEW_REQUIRED status where evidence is absent.")
  if before!={p.as_posix():sha(r/p) for p in PROTECTED}:raise AuditError("protected_runtime_or_database_changed")
  print("[6/8] [PASS] Production entry point, database and DB sidecars remained byte-identical; database was not opened.")
  report={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_SEMANTIC_REFINEMENT","parent":PARENT,"scope":{"roadmap":"21.14.1 Event foundation","primary":"V1 event item static namespace 4000-9999, immutable blocks of 25","extended":"all evidenced item ID namespaces and allocation rules: static catalog, generated permanent, preview, quest, premium/fixed, allocator persistence and overlap guards"},"roadmap_contract":{"namespace_min":4000,"namespace_max":9999,"block_size":25,"block_count":240,"reuse_policy":"IMMUTABLE_NEVER_REUSE","source":"Stage 21.14.1 plus accepted Stage 18.28 policy"},"checks":checks,"review_matrix":decisions,"categories":categories,"numeric_evidence_by_file":numbers,"evidence":records,"audit_guards":{"read_only":True,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False,"production_code_changed":False,"no_range_inference":True},"manual_game_check":"NOT_REQUIRED_AUDIT_ONLY","suggested_next_patch":"patch_21_14_1a_refine_item_id_namespace_contract.py"}
  write(r/REPORT,json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.14.1 - Existing Item ID Namespace Audit","","- Status: **PASS**","- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**","- Primary roadmap scope: static event namespace `4000-9999`, immutable blocks of `25`.","- Extended approved audit scope: every evidenced item ID namespace and allocator rule.","- Production code changed: **False**","- Production database opened: **False**","","## Audit categories"]
  for name,owners in categories.items():lines.extend(["",f"### {name}",*(f"- `{x}`" for x in owners)] if owners else ["",f"### {name}","- No authoritative evidence found; semantic review required."])
  lines.extend(["","## Next patch","","`patch_21_14_1a_refine_item_id_namespace_contract.py`",""])
  write(r/DOC,"\n".join(lines));print("[7/8] [PASS] JSON and Markdown item ID namespace audit artifacts written.")
  fileset={p.as_posix() for p in TARGETS};git(r,"add","-f","--",*sorted(fileset));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=fileset:raise AuditError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.14.1: audit item ID namespaces","--",*sorted(fileset),check=False)
  if z.returncode:raise AuditError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=fileset:raise AuditError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[8/8] [PASS] Read-only item ID namespace audit committed: {commit}")
  evidenced=sum(x["status"]=="EVIDENCED" for x in decisions);review=len(decisions)-evidenced
  print(f"CONCLUSION: GO_TO_SEMANTIC_REFINEMENT\nPATCH STATUS: PASS\nCONTRACT MATRIX: {evidenced} EVIDENCED / {review} REVIEW_REQUIRED / {len(decisions)} TOTAL\nEVENT NAMESPACE: 4000-9999\nEVENT BLOCK SIZE: 25\nEVENT BLOCK COUNT: 240\nDATABASE OPENED: False\nPRODUCTION CODE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED_AUDIT_ONLY\nSUGGESTED NEXT PATCH: patch_21_14_1a_refine_item_id_namespace_contract.py")
  return 0
 except Exception as e:
  git(r,"reset","--quiet",check=False)
  for p in (REPORT,DOC):
   q=r/p
   if q.exists():q.unlink()
  print(f"[8/8] [FAIL] {e}; read-only audit artifacts removed")
  return 1
if __name__=="__main__":raise SystemExit(main())
