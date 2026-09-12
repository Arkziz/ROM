#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];DB=R/"game.db"
REPORT=R/"reports/stage_18_19_0_pve_effect_timing_read_only_audit.json";MD=R/"MD/STAGE_18_19_0_PVE_EFFECT_TIMING_READ_ONLY_AUDIT.md"
PVE=R/"handlers/combat.py";PVP_FILES=(R/"systems/pvp_round_engine.py",R/"systems/pvp_models.py",R/"systems/pvp_action_validation.py",R/"systems/pvp_combat_log.py",R/"systems/pvp_skill_adapter.py")
TOKENS=("effect","bleed","poison","stun","shield","cooldown","duration","tick","hot","heal_over_time","debuff","buff")
def read(p):return p.read_text(encoding="utf-8-sig")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dotted(n):
 parts=[]
 while isinstance(n,ast.Attribute):parts.append(n.attr);n=n.value
 if isinstance(n,ast.Name):parts.append(n.id);return ".".join(reversed(parts))
 return ""
def functions(path):
 text=read(path);tree=ast.parse(text);rows=[]
 for node in ast.walk(tree):
  if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
  seg=ast.get_source_segment(text,node) or "";low=(node.name+" "+seg).lower()
  if not any(t in low for t in TOKENS):continue
  calls=[];assignments=[]
  for x in ast.walk(node):
   if isinstance(x,ast.Call):
    name=dotted(x.func)
    if name:calls.append({"name":name,"line":x.lineno})
   elif isinstance(x,(ast.Assign,ast.AugAssign)):
    src=ast.get_source_segment(text,x) or ""
    if any(t in src.lower() for t in TOKENS):assignments.append({"line":x.lineno,"source":src[:500]})
  rows.append({"file":str(path.relative_to(R)).replace("\\","/"),"name":node.name,"line":node.lineno,"end":node.end_lineno,"args":[a.arg for a in node.args.args],"calls":sorted(calls,key=lambda z:z["line"]),"effect_assignments":sorted(assignments,key=lambda z:z["line"]),"source":seg})
 return rows
def phase_candidates(rows):
 result=[]
 for row in rows:
  ordered=[]
  for call in row["calls"]:
   low=call["name"].lower()
   if any(t in low for t in TOKENS) or any(t in low for t in ("attack","damage","victory","defeat","death")):ordered.append(call)
  if len(ordered)>=2:result.append({"file":row["file"],"function":row["name"],"line":row["line"],"ordered_calls":ordered})
 return result
def classify(rows,side):
 names={r["name"] for r in rows};src="\n".join(r["source"] for r in rows).lower()
 return {"side":side,"functions":sorted(names),"has_cooldown_tick":any("cooldown" in n and ("tick" in n or "decrement" in n or "project" in n) for n in names),"has_periodic_tick":any("tick" in n and any(k in n for k in ("effect","bleed","poison","periodic")) for n in names) or "periodic" in src,"has_stun_skip":"stunned_skip" in src or ("stun" in src and "skip" in src),"has_shield_absorb":"shield" in src and ("absorb" in src or "remaining_damage" in src),"has_fresh_marker":any(k in src for k in ("fresh","applied_turn","skip_first_tick","starts_next_turn")),"has_duration_decrement":"duration" in src and any(k in src for k in ("-= 1","- 1","decrement")),"has_replace_policy":"replace" in src,"has_stack_policy":"stack" in src}
def dbcheck():
 before=sha(DB);c=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True)
 try:c.execute("PRAGMA query_only=ON");out={"quick_check":c.execute("PRAGMA quick_check").fetchone()[0],"foreign_key_violations":c.execute("PRAGMA foreign_key_check").fetchall(),"total_changes":c.total_changes}
 finally:c.close()
 out.update(sha256_before=before,sha256_after=sha(DB));out["unchanged"]=out["sha256_before"]==out["sha256_after"];return out
def main():
 for p in (PVE,*PVP_FILES,DB):
  if not p.exists():raise RuntimeError(f"missing {p.relative_to(R)}")
 pve=functions(PVE);pvp=[]
 for p in PVP_FILES:pvp.extend(functions(p))
 pvec=classify(pve,"pve");pvpc=classify(pvp,"pvp")
 comparison={key:{"pve":pvec[key],"pvp":pvpc[key],"equal":pvec[key]==pvpc[key]} for key in ("has_cooldown_tick","has_periodic_tick","has_stun_skip","has_shield_absorb","has_fresh_marker","has_duration_decrement","has_replace_policy","has_stack_policy")}
 findings=[]
 if pvpc["has_stun_skip"] and not pvec["has_stun_skip"]:findings.append({"severity":"HIGH","code":"PVE_STUN_TIMELINE_DIFFERS_FROM_PVP","detail":"PvP has explicit stunned-skip semantics while PvE static scan does not show an equivalent phase."})
 if not pvec["has_fresh_marker"]:findings.append({"severity":"HIGH","code":"PVE_NO_FRESH_EFFECT_MARKER","detail":"No explicit fresh/applied_turn marker was found to prevent same-turn tick or duration decrement."})
 if pvec["has_cooldown_tick"] and not pvpc["has_cooldown_tick"]:findings.append({"severity":"INFO","code":"COOLDOWN_OWNERS_DIFFER","detail":"PvE and PvP use separate cooldown ownership; direct code reuse may be unsafe, but semantic parity can be tested."})
 db=dbcheck();status="PASS"
 if db["quick_check"]!="ok" or db["foreign_key_violations"] or db["total_changes"] or not db["unchanged"]:status="FAIL"
 target={"bleed_dot":"new DOT does not tick on application; first tick occurs after the next full turn","stun":"stun applied by player blocks the nearest enemy action; duration 1 skips exactly one action","lethal_periodic":"lethal tick prevents the target's next action and claims terminal completion once","cooldown":"cooldown N blocks N subsequent owner actions; it is ready on the following action","same_dot_reapply":"do not stack damage; refresh only when new duration is longer","buff_debuff":"stronger replaces weaker; equal strength refreshes duration; weaker does not replace stronger","hot":"no immediate heal; first tick after the next turn; clamp to Max HP","shield":"active immediately and may absorb the nearest incoming attack","duration":"new effect is not decremented in its application phase","scope":"PvE mutation only; PvP is behavioral reference unless a shared layer is proven safe"}
 report={"stage":"18.19.0","status":status,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"read_only":True,"production_mutation":False,"approved_target_semantics":target,"pve":pvec,"pvp":pvpc,"semantic_comparison":comparison,"pve_phase_candidates":phase_candidates(pve),"pvp_phase_candidates":phase_candidates(pvp),"findings":findings,"database":db,"recommended_mutation":{"principle":"match proven PvP semantics where behavior agrees, without importing PvP persistence/UI/completion code into PvE","required_components":["formal PvE turn phase owner","fresh/applied_turn metadata for delayed DOT/HOT and duration decrement","explicit nearest-enemy-action stun consumption","owner-action cooldown semantics","single post-tick terminal check","replace/refresh policy helpers","turn-by-turn deterministic fixtures for duration 1/2/3"],"pvp_change_allowed":False},"next_patch":"18.19.1 PvE effect timeline production implementation after reviewing this audit"}
 REPORT.parent.mkdir(exist_ok=True);MD.parent.mkdir(exist_ok=True);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
 lines=["# Stage 18.19.0: PvE Effect Timing Read-only Audit","",f"**Status:** {status}","**Production mutation:** none","", "## Scope","","The audit compares current PvE effect and cooldown ordering with the existing PvP round semantics. PvP is a behavioral reference only and is not modified.","", "## Target semantics",""]
 lines += [f"- **{k}**: {v}." for k,v in target.items()]
 lines += ["", "## Static comparison",""]+[f"- `{k}`: PvE=`{v['pve']}`, PvP=`{v['pvp']}`, equal=`{v['equal']}`." for k,v in comparison.items()]
 lines += ["", "## Findings",""]+([f"- **{x['severity']} {x['code']}**: {x['detail']}" for x in findings] or ["- No semantic blockers found by static analysis."])
 lines += ["", "## Safety decision","","- Do not copy the PvP engine wholesale into PvE.","- Reuse or delegate only pure effect-policy helpers if import direction and behavior are proven safe.","- Keep PvP production unchanged in Stage 18.19.","", "## Database safety","",f"- quick_check: `{db['quick_check']}`.",f"- FK violations: `{len(db['foreign_key_violations'])}`.",f"- DB unchanged: `{db['unchanged']}`."]
 MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
 if status!="PASS":raise RuntimeError("audit execution invariants failed")
 print(json.dumps({"status":"PASS","pve_functions":len(pve),"pvp_functions":len(pvp),"findings":len(findings),"pvp_stun_reference":pvpc["has_stun_skip"],"db_unchanged":True,"json":str(REPORT.relative_to(R)),"md":str(MD.relative_to(R))},ensure_ascii=False))
if __name__=="__main__":main()
