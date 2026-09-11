#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,hashlib,json,sqlite3,sys
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
DYN=R/"systems/dynamic_equipment_system.py";GEN=R/"db_modules/generated_equipment.py";SHOP=R/"db_modules/shop.py";DB=R/"game.db"
REPORT=R/"reports/stage_18_17_4_dynamic_equipment_compatibility_audit.json";MD=R/"MD/STAGE_18_17_4_DYNAMIC_EQUIPMENT_COMPATIBILITY_AUDIT.md"
SCAN_DIRS=("data","systems","handlers","db_modules","tools")
def txt(p):return p.read_text(encoding="utf-8-sig")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def funcs(p):
 t=ast.parse(txt(p));return {n.name:n for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def signature(n):
 a=n.args;return {"posonly":[x.arg for x in a.posonlyargs],"args":[x.arg for x in a.args],"vararg":a.vararg.arg if a.vararg else None,"kwonly":[x.arg for x in a.kwonlyargs],"kwarg":a.kwarg.arg if a.kwarg else None,"defaults":len(a.defaults),"kw_defaults":[x is not None for x in a.kw_defaults]}
def normalized_body(n):
 clone=ast.Module(body=n.body,type_ignores=[]);return ast.dump(clone,annotate_fields=True,include_attributes=False)
def loaded_names(n):return sorted({x.id for x in ast.walk(n) if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Load)})
def imports(tree):
 out=[]
 for n in tree.body:
  if isinstance(n,ast.Import):
   out += [{"kind":"import","module":a.name,"as":a.asname} for a in n.names]
  elif isinstance(n,ast.ImportFrom):
   out += [{"kind":"from","module":n.module,"name":a.name,"as":a.asname,"level":n.level} for a in n.names]
 return out
def scan_refs():
 rows=[]
 for folder in SCAN_DIRS:
  base=R/folder
  if not base.exists():continue
  for p in base.rglob("*.py"):
   if p in (DYN,GEN):continue
   try:t=ast.parse(txt(p))
   except Exception as e:
    rows.append({"file":str(p.relative_to(R)),"parse_error":str(e)});continue
   direct=[];module_aliases=set();package_aliases=set()
   for n in ast.walk(t):
    if isinstance(n,ast.ImportFrom) and n.module=="systems.dynamic_equipment_system":direct += [a.name for a in n.names]
    elif isinstance(n,ast.Import):
     for a in n.names:
      if a.name=="systems.dynamic_equipment_system":module_aliases.add(a.asname or a.name.split(".")[-1])
    elif isinstance(n,ast.ImportFrom) and n.module=="systems":
     for a in n.names:
      if a.name=="dynamic_equipment_system":package_aliases.add(a.asname or a.name)
   attrs=[]
   aliases=module_aliases|package_aliases
   for n in ast.walk(t):
    if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id in aliases:attrs.append(n.attr)
   if direct or attrs or p==SHOP:rows.append({"file":str(p.relative_to(R)),"direct_imports":sorted(set(direct)),"module_attributes":sorted(set(attrs)),"is_shop":p==SHOP})
 return rows
def dbcheck():
 before=sha(DB);c=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True)
 try:c.execute("PRAGMA query_only=ON");o={"quick_check":c.execute("PRAGMA quick_check").fetchone()[0],"foreign_key_violations":c.execute("PRAGMA foreign_key_check").fetchall(),"total_changes":c.total_changes}
 finally:c.close()
 o.update(sha256_before=before,sha256_after=sha(DB));o["unchanged"]=o["sha256_before"]==o["sha256_after"];return o
def main():
 for p in (DYN,GEN,SHOP,DB):
  if not p.exists():raise RuntimeError(f"missing {p.relative_to(R)}")
 dt=ast.parse(txt(DYN));gt=ast.parse(txt(GEN));df=funcs(DYN);gf=funcs(GEN);shared=sorted(set(df)&set(gf))
 refs=scan_refs();used=defaultdict(list)
 for row in refs:
  for name in row.get("direct_imports",[])+row.get("module_attributes",[]):used[name].append(row["file"])
 comparisons=[]
 for name in shared:
  comparisons.append({"name":name,"signature_dynamic":signature(df[name]),"signature_generated":signature(gf[name]),"signature_equal":signature(df[name])==signature(gf[name]),"body_equal":normalized_body(df[name])==normalized_body(gf[name]),"used_by":sorted(set(used.get(name,[]))),"dynamic_loaded_names":loaded_names(df[name]),"generated_loaded_names":loaded_names(gf[name])})
 dyn_public=[]
 for n in dt.body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="__all__" for t in n.targets):dyn_public=ast.literal_eval(n.value)
 missing=[x for x in used if x not in df]
 safe=[x["name"] for x in comparisons if x["signature_equal"] and x["body_equal"]]
 wrappers=[x["name"] for x in comparisons if x["signature_equal"] and not x["body_equal"]]
 blocked=[x["name"] for x in comparisons if not x["signature_equal"]]
 db=dbcheck()
 report={"stage":"18.17.4","status":"PASS","generated_at_utc":datetime.now(timezone.utc).isoformat(),"read_only":True,"production_mutation":False,"sources":{"dynamic":"systems/dynamic_equipment_system.py","generated":"db_modules/generated_equipment.py","shop":"db_modules/shop.py"},"dynamic_public_all":dyn_public,"direct_reference_rows":refs,"used_dynamic_symbols":{k:sorted(set(v)) for k,v in sorted(used.items())},"shared_function_count":len(shared),"shared_functions":shared,"comparisons":comparisons,"classification":{"byte_equivalent_delegate_candidates":safe,"same_signature_non_equivalent_requires_behavior_test":wrappers,"signature_mismatch_blocked":blocked,"referenced_missing_symbols":missing,"consolidation_blockers":[{"kind":"missing_dynamic_symbol","symbol":name,"referenced_by":sorted(set(used.get(name,[])))} for name in missing]},"imports":{"dynamic":imports(dt),"generated":imports(gt)},"database":db,"recommendation":{"target":"systems/dynamic_equipment_system.py becomes a thin compatibility delegate only after behavioral fixtures","preserve_public_symbols":sorted(set(dyn_public)|set(used)),"do_not_delegate_yet":sorted(set(wrappers+blocked)),"next_patch":"18.17.5 legacy class-shop generator route read-only audit/recovery before compatibility consolidation"}}
 if db["quick_check"]!="ok" or db["foreign_key_violations"] or db["total_changes"] or not db["unchanged"] :report["status"]="FAIL"
 REPORT.parent.mkdir(exist_ok=True);MD.parent.mkdir(exist_ok=True);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 lines=["# Stage 18.17.4: Dynamic Equipment Compatibility Read-only Audit","",f"**Status:** {report['status']}","**Production mutation:** none","", "## Import surface","",f"- Shared function names: **{len(shared)}**.",f"- Referenced dynamic symbols: `{sorted(used)}`.",f"- Public `__all__`: `{dyn_public}`.",f"- Missing referenced symbols: `{missing}`.","- Missing symbols are audit findings and consolidation blockers, not audit execution failures.","", "## Consolidation classification","",f"- Byte-equivalent delegate candidates: `{safe}`.",f"- Same-signature but behavior-different functions: `{wrappers}`.",f"- Signature mismatches: `{blocked}`.","", "## Decision","","- Do not remove compatibility functions by name alone.","- Preserve the current public import surface.","- Add behavioral fixtures before replacing non-equivalent implementations with delegates.","- Resolve or retire the legacy `generate_equipment_item` reference before consolidation.","- Item creation remains owned by `db_modules/generated_equipment.py`.","", "## Database safety","",f"- quick_check: `{db['quick_check']}`.",f"- FK violations: `{len(db['foreign_key_violations'])}`.",f"- DB unchanged: `{db['unchanged']}`."]
 MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
 if report["status"]!="PASS":raise RuntimeError(f"audit execution failed: db={db}")
 print(json.dumps({"status":"PASS","shared_functions":len(shared),"referenced_symbols":len(used),"equivalent":len(safe),"behavior_fixtures_needed":len(wrappers),"signature_blockers":len(blocked),"missing_findings":len(missing),"db_unchanged":True,"json":str(REPORT.relative_to(R)),"md":str(MD.relative_to(R))},ensure_ascii=False))
if __name__=="__main__":main()
