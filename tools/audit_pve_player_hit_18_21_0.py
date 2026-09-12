#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,hashlib,json,sqlite3
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];DB=R/"game.db";REPORT=R/"reports/stage_18_21_0_pve_player_hit_read_only_audit.json";MD=R/"MD/STAGE_18_21_0_PVE_PLAYER_HIT_READ_ONLY_AUDIT.md"
FILES=("handlers/combat.py","systems/combat_system.py","systems/stat_system.py","systems/pvp_round_engine.py","data/mobs.py","data/bosses.py")
TOKENS=("hit","miss","dodge","ухил","промах","dex","critical","crit","calculate_player_attack","damage")
def read(rel):return (R/rel).read_text(encoding="utf-8-sig")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def funcs(rel):
 text=read(rel);tree=ast.parse(text);rows=[]
 for n in ast.walk(tree):
  if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
  seg=ast.get_source_segment(text,n) or "";low=(n.name+" "+seg).lower()
  if not any(t in low for t in TOKENS):continue
  calls=[]
  for x in ast.walk(n):
   if isinstance(x,ast.Call):
    name=ast.get_source_segment(text,x.func) or ""
    if any(t in name.lower() for t in TOKENS):calls.append({"line":x.lineno,"name":name})
  rows.append({"file":rel,"name":n.name,"line":n.lineno,"end":n.end_lineno,"calls":calls,"source":seg})
 return rows
def handlers():
 text=read("handlers/combat.py");tree=ast.parse(text);rows=[]
 for n in ast.walk(tree):
  if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
  decorators=[ast.get_source_segment(text,d) or "" for d in n.decorator_list]
  if any("message_handler" in d or "callback_query_handler" in d for d in decorators):
   seg=ast.get_source_segment(text,n) or "";low=seg.lower()
   if "calculate_player_attack" in seg or "⚔️ атакувати" in low or "skill" in low:
    rows.append({"name":n.name,"line":n.lineno,"decorators":decorators,"uses_player_attack":"calculate_player_attack" in seg,"has_player_miss":any(t in low for t in ("player_miss","промах","mob_dodge","target_dodge")),"has_player_crit":"is_player_crit" in seg,"source":seg})
 return rows
def dbcheck():
 before=sha(DB);c=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True)
 try:c.execute("PRAGMA query_only=ON");out={"quick_check":c.execute("PRAGMA quick_check").fetchone()[0],"foreign_key_violations":c.execute("PRAGMA foreign_key_check").fetchall(),"total_changes":c.total_changes}
 finally:c.close()
 out.update(sha256_before=before,sha256_after=sha(DB));out["unchanged"]=out["sha256_before"]==out["sha256_after"];return out
def inspect_mob_dex():
 rows=[]
 for rel in ("data/mobs.py","data/bosses.py","handlers/combat.py"):
  text=read(rel);tree=ast.parse(text)
  hits=[]
  for n in ast.walk(tree):
   seg=ast.get_source_segment(text,n) or ""
   if any(x in seg.lower() for x in ('"dex"',"'dex'",'"dexterity"',"'dexterity'")):
    if hasattr(n,"lineno"):hits.append({"line":n.lineno,"source":seg[:500]})
  rows.append({"file":rel,"hits":hits[:100],"count":len(hits)})
 return rows
def main():
 for rel in FILES:
  if not (R/rel).is_file():raise RuntimeError("missing "+rel)
  ast.parse(read(rel),filename=rel)
 routes=handlers();all_rows={rel:funcs(rel) for rel in FILES};combat=read("handlers/combat.py").lower();pvp=read("systems/pvp_round_engine.py").lower()
 normal=[x for x in routes if any("атакувати" in d.lower() for d in x["decorators"])]
 skill=[x for x in routes if x not in normal and x["uses_player_attack"]]
 normal_miss=any(x["has_player_miss"] for x in normal);skill_miss=any(x["has_player_miss"] for x in skill)
 findings=[]
 if not normal_miss:findings.append({"severity":"HIGH","code":"PVE_NORMAL_ATTACK_HAS_NO_PLAYER_HIT_ROLL","detail":"Normal player attack reaches calculate_player_attack/crit/damage without an explicit player miss or target dodge branch."})
 if skill and not skill_miss:findings.append({"severity":"INFO","code":"PVE_DAMAGE_SKILLS_ALSO_HAVE_NO_PLAYER_HIT_ROLL","detail":"Damaging PvE skills use calculate_player_attack and damage scaling, but no explicit player miss/target dodge branch was found."})
 mob_dex=inspect_mob_dex();has_mob_dex=any(x["count"] for x in mob_dex)
 if not has_mob_dex:findings.append({"severity":"HIGH","code":"MOB_DEX_SOURCE_NOT_FOUND","detail":"No explicit mob dex/dexterity field was found in audited mob, boss or combat sources."})
 db=dbcheck();status="PASS" if db["quick_check"]=="ok" and not db["foreign_key_violations"] and not db["total_changes"] and db["unchanged"] else "FAIL"
 report={"stage":"18.21.0","status":status,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"read_only":True,"production_mutation":False,"scope_decision":{"mutation_target":"PvE normal player attack only","skills":"audit and document only; no Stage 18.21 mutation without explicit approval","enemy_attacks":"unchanged","pvp":"unchanged"},"route_summary":{"routes":routes,"normal_routes":normal,"skill_routes":skill,"normal_attack_can_miss":normal_miss,"damaging_skills_can_miss":skill_miss,"enemy_attack_can_be_dodged":("is_dodge" in combat or "ухил" in combat),"pvp_has_dodge_model":("dodged" in pvp or "dodge" in pvp)},"mob_dex":mob_dex,"has_explicit_mob_dex":has_mob_dex,"source_map":all_rows,"findings":findings,"database":db,"target_semantics_candidate":{"equal_dex_hit_percent":95,"per_dex_difference_percent":0.5,"minimum_hit_percent":50,"maximum_hit_percent":99,"order":["turn-start effects/resources","player normal-attack hit roll","crit only after hit","damage only after hit","enemy action"],"miss_contract":["mob HP unchanged","no critical roll","no hit-dependent effect","enemy action continues","Stage 18.19 periodic timing unchanged"]},"decision_required_after_audit":["approve or revise hit formula","approve authoritative mob DEX source if absent","confirm skills remain guaranteed-hit for Stage 18.21"]}
 REPORT.parent.mkdir(exist_ok=True);MD.parent.mkdir(exist_ok=True);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
 lines=["# Stage 18.21.0: PvE Player Hit/Miss Read-only Audit","",f"**Status:** {status}","**Production mutation:** none","","## Direct answer","",f"- Normal PvE player attack has an explicit miss branch: `{normal_miss}`.",f"- Damaging PvE skills have an explicit miss branch: `{skill_miss}`.","- Enemy attacks can be dodged by the player independently of both findings.","","## Scope","","Stage 18.21 targets only the player's normal PvE attack. Skills and PvP are audited for comparison but remain unchanged unless separately approved.","","## Findings",""]
 lines += [f"- **{x['severity']} {x['code']}**: {x['detail']}" for x in findings] or ["- No structural gaps found."]
 lines += ["","## Candidate semantics", "","- Hit roll occurs before crit and damage.","- A miss deals zero damage and applies no hit-dependent effects.","- Existing periodic effects and the enemy action continue normally.","- Candidate formula: 95% at equal DEX, ±0.5% per DEX difference, clamped to 50–99%.","","## Database safety", "",f"- quick_check: `{db['quick_check']}`.",f"- FK violations: `{len(db['foreign_key_violations'])}`.",f"- DB unchanged: `{db['unchanged']}`."]
 MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
 if status!="PASS":raise RuntimeError("audit safety invariants failed")
 print(json.dumps({"status":"PASS","normal_attack_can_miss":normal_miss,"damaging_skills_can_miss":skill_miss,"mob_dex_found":has_mob_dex,"routes":len(routes),"findings":len(findings),"db_unchanged":True,"json":str(REPORT.relative_to(R)),"md":str(MD.relative_to(R))},ensure_ascii=False))
if __name__=="__main__":main()
