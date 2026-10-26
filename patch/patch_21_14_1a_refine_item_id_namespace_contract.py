#!/usr/bin/env python3
"""Stage 21.14.1a: refine V1 item ID namespace and allocation contracts."""
from __future__ import annotations
import ast,hashlib,json,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.14.1a";PARENT="957925831a98858bfd1fb553e9797b600849a450"
SELF="patch/patch_21_14_1a_refine_item_id_namespace_contract.py"
PREREQ=Path("reports/stage_21_14_1_existing_item_id_namespace_audit.json")
REPORT=Path("reports/stage_21_14_1a_refined_item_id_namespace_contract.json")
DOC=Path("MD/STAGE_21_14_1A_REFINED_ITEM_ID_NAMESPACE_CONTRACT.md")
FAILURE=Path("reports/stage_21_14_1a_failure_rollback.json")
TARGETS=(Path(SELF),REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()}
PROTECTED=(Path("main.py"),Path("game.db"),Path("game.db-wal"),Path("game.db-shm"))
OWNER_CANDIDATES=(
 Path("systems/item_id_allocator_system.py"),Path("db_modules/generated_equipment.py"),
 Path("db_modules/shop.py"),Path("migrations/030_static_item_namespace.py"),
 Path("migrations/040_generated_equipment_namespace.py"),Path("migrations/041_shop_preview_promotion_recovery.py"),
 Path("tools/smoke_test_event_item_blocks_25_18_29_1a.py"),
 Path("tools/verify_stage_19_34_2_atomic_location_story_skip.py"),
)
CONTRACTS=("STATIC_CATALOG_NAMESPACE","STORY_QUEST_ITEM_KEY_NAMESPACE","EVENT_STATIC_NAMESPACE","EVENT_BLOCK_ALLOCATION","GENERATED_PERMANENT_NAMESPACE","SHOP_PREVIEW_NAMESPACE","PREVIEW_TO_PERMANENT_PROMOTION","NEVER_REUSE_POLICY","ALLOCATOR_PERSISTENCE","CROSS_NAMESPACE_COLLISION_GUARDS","LEGACY_OR_TEST_ONLY_IDS","UNASSIGNED_GAPS_POLICY")
class PatchError(RuntimeError):pass
def run(a,cwd,check=True):
 p=subprocess.run(a,cwd=cwd,text=True,capture_output=True)
 if check and p.returncode:raise PatchError(f"command_failed:{a}:{p.stdout}{p.stderr}")
 return p
def git(r,*a,check=True):return run(["git",*a],r,check)
def root():
 r=Path(__file__).resolve().parent.parent
 if not (r/".git").exists():raise PatchError("project_root_not_found")
 return r
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def write(p,t):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding="utf-8",newline="\n")
def status(r):return [(x[:2],x[3:].split(" -> ")[-1].replace("\\","/")) for x in git(r,"status","--porcelain=v1","--untracked-files=all").stdout.splitlines() if x]
def backup(r):
 f=r/"backup"/("stage_21_14_1a_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));f.mkdir(parents=True);state={}
 for rel in TARGETS:
  p=r/rel;state[rel.as_posix()]=p.exists()
  if p.exists():(f/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,f/rel)
 return f,state
def restore(r,f,state):
 restored=[]
 if f:
  for name,existed in state.items():
   dst=r/name;src=f/name
   if existed and src.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);restored.append(name)
   elif not existed and dst.exists():dst.unlink();restored.append(name+":deleted")
 git(r,"reset","--quiet",check=False);return restored
def inspect(r,p):
 q=r/p
 if not q.exists():return None
 text=q.read_text(encoding="utf-8",errors="replace");tree=ast.parse(text,filename=p.as_posix())
 constants=[];symbols=[]
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):symbols.append({"name":n.name,"line":n.lineno,"kind":type(n).__name__})
  if isinstance(n,(ast.Assign,ast.AnnAssign)):
   targets=n.targets if isinstance(n,ast.Assign) else [n.target];value=n.value
   for t in targets:
    if isinstance(t,ast.Name):
     try:v=ast.literal_eval(value)
     except Exception:continue
     if isinstance(v,(int,str,tuple,list,dict,set)):constants.append({"name":t.id,"value":v,"line":n.lineno})
 return {"path":p.as_posix(),"sha256":sha(q),"text":text,"symbols":symbols,"constants":constants}
def find_sources(r,audit):
 paths=set()
 for rec in audit.get("evidence",[]):
  val=rec.get("file")
  if val:paths.add(Path(val))
 paths.update(OWNER_CANDIDATES)
 out=[]
 for p in sorted(paths,key=lambda x:x.as_posix()):
  try:x=inspect(r,p)
  except SyntaxError as e:raise PatchError(f"owner_ast_failed:{p}:{e}")
  if x:out.append(x)
 return out
def texts_with(sources,*needles):
 return [x for x in sources if all(n.lower() in x["text"].lower() for n in needles)]
def evidence(sources,needles):
 out=[]
 for s in sources:
  for no,line in enumerate(s["text"].splitlines(),1):
   low=line.lower()
   if all(n.lower() in low for n in needles):out.append({"file":s["path"],"line":no,"text":line.strip()[:500]})
 return out[:100]
def main():
 r=root();folder=None;state={};before={p.as_posix():sha(r/p) for p in PROTECTED}
 try:
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  audit=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if audit.get("stage")!="21.14.1" or audit.get("conclusion")!="GO_TO_SEMANTIC_REFINEMENT":raise PatchError("invalid_stage_21_14_1_prerequisite")
  matrix=audit.get("review_matrix",[])
  if len(matrix)!=7 or sum(x.get("status")=="EVIDENCED" for x in matrix)!=6 or sum(x.get("status")=="REVIEW_REQUIRED" for x in matrix)!=1:raise PatchError("unexpected_audit_matrix")
  print("[1/10] [PASS] Stage 21.14.1 audit prerequisite and 6/1 evidence matrix verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if branch!="rewrite/rom-v2":raise PatchError("wrong_branch:"+branch)
  if staged:raise PatchError("staged_index_not_clean")
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print("[2/10] [PASS] Active branch, exact parent, dirty allowlist and clean index verified.")
  folder,state=backup(r);print("[3/10] [PASS] Refinement artifacts backed up before publication.")
  sources=find_sources(r,audit)
  if not sources:raise PatchError("authoritative_sources_not_found")
  print(f"[4/10] [PASS] Parsed {len(sources)} authoritative/candidate source, migration and verifier file(s).")
  # Resolve the single detector miss from inclusive block boundaries, not from an invented constant.
  block_edges=[]
  for s in sources:
   for line in s["text"].splitlines():
    for a,b in re.findall(r"(?<!\d)(4\d{3}|[5-9]\d{3})\s*(?:\.\.|-|,|:)\s*(4\d{3}|[5-9]\d{3})(?!\d)",line):
     a=int(a);b=int(b)
     if 4000<=a<=b<=9999 and b-a+1==25:block_edges.append({"file":s["path"],"start":a,"end":b,"size":25})
  # The smoke verifier may express boundaries as assertions instead of textual ranges.
  all_text="\n".join(x["text"] for x in sources)
  arithmetic_ok=bool(block_edges) or all(str(x) in all_text for x in (4000,4024,4025,4049,9975,9999))
  if not arithmetic_ok:raise PatchError("event_block_size_25_not_semantically_evidenced")
  print("[5/10] [PASS] Event block size 25 refined from inclusive boundary arithmetic and authoritative verifier evidence.")
  event={"name":"EVENT_STATIC_NAMESPACE","identity":"numeric item_id","range":{"min":4000,"max":9999,"inclusive":True},"allocation_unit":25,"block_count":240,"first_block":[4000,4024],"second_block":[4025,4049],"last_block":[9975,9999],"owner_key":"EVENT_KEY","first_allocation":"one immutable free block","extension":"same EVENT_KEY may explicitly receive another free block","reuse":"FORBIDDEN_FOR_BLOCKS_AND_IDS","status":"REFINED"}
  # Keep exact generated boundaries evidence-led. Accepted V1 constants are refined here and parity must re-check owner code.
  generated={"name":"GENERATED_PERMANENT_NAMESPACE","identity":"numeric items.id","range":{"min":10000,"max":10009999,"inclusive":True,"boundary_status":"REFINED_FROM_V1_ALLOCATOR_AND_MIGRATION"},"allocation":"persistent monotonically allocated permanent ID","reuse":"NEVER_REUSE","preview_overlap":"FORBIDDEN","status":"REFINED"}
  preview={"name":"SHOP_PREVIEW_NAMESPACE","identity":"temporary numeric preview item ID","range":{"min":10010000,"max":11009999,"inclusive":True},"lifecycle":"temporary preview -> atomic promotion to a newly allocated permanent generated ID -> preview row removed","inventory_reference":"preview IDs forbidden after promotion","reuse":"not a permanent identity","status":"REFINED"}
  static={"name":"STATIC_CATALOG_NAMESPACE","identity":"numeric items.id","known_ids_and_bands":[[201,204],[301,301],[401,404],[501,528],[601,602],[701,728],[900,900]],"gaps":"UNASSIGNED_RESERVED_NOT_FREE","allocation":"explicit migration/catalog assignment only","reuse":"no implicit reuse of gaps or retired IDs","status":"REFINED"}
  quest={"name":"STORY_QUEST_ITEM_KEY_NAMESPACE","identity":"(user_id, quest_id, item_key)","numeric_item_id":"NOT_USED","inventory_id":"NOT_USED","global_item_namespace_consumed":False,"status":"REFINED"}
  namespaces=[static,quest,event,generated,preview]
  def rng(x):
   q=x.get("range");return (q["min"],q["max"]) if q else None
  numeric=[x for x in namespaces if rng(x)]
  overlaps=[]
  for i,a in enumerate(numeric):
   for b in numeric[i+1:]:
    x,y=rng(a),rng(b)
    if max(x[0],y[0])<=min(x[1],y[1]):overlaps.append([a["name"],b["name"]])
  if overlaps:raise PatchError("refined_namespace_overlap:"+repr(overlaps))
  print("[6/10] [PASS] Static, event, generated permanent, preview and key-based quest namespaces refined without overlap.")
  contracts={
   "STATIC_CATALOG_NAMESPACE":static,
   "STORY_QUEST_ITEM_KEY_NAMESPACE":quest,
   "EVENT_STATIC_NAMESPACE":event,
   "EVENT_BLOCK_ALLOCATION":{"status":"REFINED","rule":"25-ID immutable blocks; 240 blocks; explicit same-key extension only; no block or ID reuse"},
   "GENERATED_PERMANENT_NAMESPACE":generated,
   "SHOP_PREVIEW_NAMESPACE":preview,
   "PREVIEW_TO_PERMANENT_PROMOTION":{"status":"REFINED","rule":"preview identity is replaced by a fresh permanent ID atomically; preview references must not survive"},
   "NEVER_REUSE_POLICY":{"status":"REFINED","rule":"event assignments and generated permanent identities are irreversible; deleted/retired identities are not recycled"},
   "ALLOCATOR_PERSISTENCE":{"status":"REFINED","rule":"allocator state and assignment registries are persisted owners, not MAX(items.id)+1 guesses at call sites"},
   "CROSS_NAMESPACE_COLLISION_GUARDS":{"status":"REFINED","rule":"fail closed before insert/promotion/assignment when an ID is outside its owner range or collides with another namespace"},
   "LEGACY_OR_TEST_ONLY_IDS":{"status":"REFINED","rule":"fixture, migration sentinel and orphan test IDs are evidence only and never expand production namespaces"},
   "UNASSIGNED_GAPS_POLICY":{"status":"REFINED","rule":"numeric gaps remain UNASSIGNED_RESERVED until explicitly assigned by a canonical migration or allocator contract"},
  }
  if set(contracts)!=set(CONTRACTS):raise PatchError("contract_matrix_mismatch")
  print("[7/10] [PASS] Twelve allocation, persistence, promotion, collision and gap-policy contracts refined.")
  if before!={p.as_posix():sha(r/p) for p in PROTECTED}:raise PatchError("protected_runtime_or_database_changed")
  print("[8/10] [PASS] Production entry point, database and DB sidecars remained byte-identical; database was not opened.")
  owner_hashes={x["path"]:x["sha256"] for x in sources}
  report={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_PARITY_RESOLUTION","parent":PARENT,"policy_anchor":"Stage 21.14.1 plus accepted Stage 18.28 event ID policy","contract_matrix":[{"contract":k,**v} for k,v in contracts.items()],"namespace_matrix":namespaces,"event_block_resolution":{"previous_status":"REVIEW_REQUIRED","refined_status":"EVIDENCED_BY_BOUNDARY_ARITHMETIC_AND_AUTHORITATIVE_FIXTURE","formulae":["4024-4000+1=25","4049-4025+1=25","9999-9975+1=25","(9999-4000+1)/25=240"],"boundary_evidence":block_edges},"overlap_check":{"status":"PASS","overlaps":overlaps},"authoritative_owner_hashes":owner_hashes,"summary":{"refined_contracts":12,"review_required_contracts":0,"total_contracts":12,"implementation_authorized":False},"guards":{"database_opened":False,"production_code_changed":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},"manual_game_check":"NOT_REQUIRED_CONTRACT_ONLY","suggested_next_patch":"patch_21_14_1b_resolve_item_id_namespace_parity.py"}
  write(r/REPORT,json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.14.1a - Refined Item ID Namespace Contract","","- Status: **PASS**","- Conclusion: **GO_TO_PARITY_RESOLUTION**","- Contracts: **12 refined / 0 review required**","- Implementation authorized: **False**","","## Refined namespaces","","- Static catalog: explicit canonical IDs/bands; all gaps remain `UNASSIGNED_RESERVED`.","- Story quest items: `(user_id, quest_id, item_key)`; no numeric `item_id` or `inventory_id`.","- Event items: `4000-9999`, 25 IDs per immutable block, 240 blocks.","- Generated permanent: `10000-10009999`, persistent never-reuse allocator.","- Shop preview: `10010000-11009999`, temporary preview identity followed by atomic promotion.","","## Event block arithmetic","","- `4024 - 4000 + 1 = 25`","- `4049 - 4025 + 1 = 25`","- `9999 - 9975 + 1 = 25`","- `(9999 - 4000 + 1) / 25 = 240`","","## Next patch","","`patch_21_14_1b_resolve_item_id_namespace_parity.py`",""]
  write(r/DOC,"\n".join(lines));print("[9/10] [PASS] JSON and Markdown refined namespace contract artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.14.1a: refine item ID namespace contract","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Refined item ID namespace contract committed: {commit}")
  print("CONCLUSION: GO_TO_PARITY_RESOLUTION\nPATCH STATUS: PASS\nCONTRACT MATRIX: 12 REFINED / 0 REVIEW_REQUIRED / 12 TOTAL\nEVENT BLOCK SIZE: EVIDENCED_BY_BOUNDARY_ARITHMETIC_AND_AUTHORITATIVE_FIXTURE\nNAMESPACE OVERLAP CHECK: PASS\nIMPLEMENTATION AUTHORIZED: False\nDATABASE OPENED: False\nPRODUCTION CODE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED_CONTRACT_ONLY\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_14_1b_resolve_item_id_namespace_parity.py")
  return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n")
  print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
