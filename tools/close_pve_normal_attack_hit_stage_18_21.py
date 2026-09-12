#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, hashlib, json, sqlite3, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
DB = ROOT / "game.db"
REPORT = ROOT / "reports/stage_18_21_4_pve_normal_attack_hit_production_closure.json"
MD = ROOT / "MD/STAGE_18_21_PVE_NORMAL_ATTACK_HIT_PRODUCTION_CLOSURE.md"
TESTS = (
 "tools/smoke_test_pve_normal_attack_hit_18_21_1.py",
 "tools/smoke_test_pve_physical_normal_attack_scope_18_21_3.py",
 "tools/smoke_test_pve_effect_timeline_18_19_1.py",
 "tools/smoke_test_pve_auto_escape_18_18_1.py",
 "tools/smoke_test_pve_encounter_history_recovery_18_18_1a.py",
)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(rel):
 p=ROOT/rel
 if not p.is_file(): raise RuntimeError("missing maintained test: "+rel)
 x=subprocess.run([sys.executable,str(p)],cwd=ROOT,text=True,capture_output=True)
 if x.returncode: raise RuntimeError(f"test failed: {rel}\n{x.stdout}\n{x.stderr}")
 return {"file":rel,"status":"PASS","stdout":x.stdout.strip()}
def main():
 before=sha(DB)
 handler=(ROOT/"handlers/combat.py").read_text(encoding="utf-8-sig")
 system=(ROOT/"systems/combat_system.py").read_text(encoding="utf-8-sig")
 ht=ast.parse(handler); st=ast.parse(system)
 attacks=[n for n in ast.walk(ht) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="attack"]
 skills=[n for n in ast.walk(ht) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="combat_use_skill_callback"]
 assert len(attacks)==1 and len(skills)==1
 attack=ast.get_source_segment(handler,attacks[0]) or ""
 skill=ast.get_source_segment(handler,skills[0]) or ""
 funcs={n.name:n for n in st.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
 assert {"calculate_player_hit_chance","roll_player_normal_attack_hit"}.issubset(funcs)
 chance=ast.get_source_segment(system,funcs["calculate_player_hit_chance"]) or ""
 assert all(x in chance for x in ("95.0","0.5","50.0","99.0"))
 assert 'normal_attack_uses_hit_roll = attack_profile["attack_type"] == "physical"' in attack
 assert 'player_dex=dex_' in attack and 'mob_dex=mob.get("dex", 0)' in attack
 assert 'player_attack_hit = True' in attack and '💨 ПРОМАХ!' in attack
 assert "roll_player_normal_attack_hit" not in skill
 assert "systems.pvp_" not in attack
 results=[run(t) for t in TESTS]
 con=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True)
 try:
  con.execute("PRAGMA query_only=ON")
  quick=con.execute("PRAGMA quick_check").fetchone()[0]
  fk=con.execute("PRAGMA foreign_key_check").fetchall()
  changes=con.total_changes
 finally: con.close()
 after=sha(DB)
 if quick!="ok" or fk or changes or before!=after: raise RuntimeError("database invariant failed")
 report={
  "stage":"18.21.4","status":"CLOSED","generated_at_utc":datetime.now(timezone.utc).isoformat(),
  "maintained_tests":results,"manual_acceptance":"PASS","db_unchanged":True,
  "policy":{
   "physical_normal_attack":"effective player DEX vs mob DEX; 95 + difference*0.5; clamp 50-99",
   "magical_normal_attack":"guaranteed-hit interim policy until after Stage 18.27",
   "pve_damaging_skills":"guaranteed-hit until separate post-18.27 implementation",
   "support_skills":"no hit roll","pvp":"unchanged","affinity_bonus":False},
  "deferred_dependency":{
   "stage":"18.27","requires":"canonical mob INT/WIS generation and scaling",
   "future_magical_accuracy":"effective player INT vs canonical mob WIS"},
  "database":{"quick_check":quick,"foreign_key_violations":fk,"sha256_before":before,"sha256_after":after}
 }
 REPORT.parent.mkdir(exist_ok=True); MD.parent.mkdir(exist_ok=True)
 REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 lines=[
  "# Stage 18.21: PvE Normal Attack Hit Production Closure","",
  "## Closure status","","**CLOSED**","","Manual acceptance: **PASS**.","",
  "## Final production contract","",
  "- Physical PvE normal attack uses effective player DEX against mob DEX.",
  "- Hit chance is `95 + (player DEX - mob DEX) × 0.5`, clamped to `50–99%`.",
  "- A miss deals zero damage, cannot crit, and does not stop the enemy turn.",
  "- Existing rage, periodic-effect, cooldown, escape, victory and reward contracts remain active.",
  "- Magical normal attacks temporarily remain guaranteed-hit.",
  "- PvE damaging skills temporarily remain guaranteed-hit.",
  "- Support and no-damage skills do not use a hit roll.",
  "- PvP is unchanged.","",
  "## Deferred dependency","",
  "Magical normal-attack accuracy and PvE skill hit/miss are deferred until after Stage 18.27. Stage 18.27 must add canonical mob INT/WIS generation and scaling for normal, elite and boss encounters. The approved future magical axis is effective player INT versus canonical mob WIS.","",
  "## Manual acceptance","",
  "Physical normal-attack misses were observed in live PvE. Mob HP remained unchanged on miss, crit did not occur, the enemy completed the turn, rage behavior remained correct, later attacks and victory worked, and no traceback occurred. Physical and magical class checks after the scope guard passed.","",
  "## Automated verification","",
 ]
 lines += [f"- `{r['file']}`: PASS" for r in results]
 lines += ["","## Database safety","",f"- `quick_check`: `{quick}`.",f"- Foreign-key violations: `{len(fk)}`.","- Production database unchanged: `true`.","- WAL/SHM were not manipulated.",""]
 MD.write_text("\n".join(lines),encoding="utf-8")
 print(json.dumps({"status":"CLOSED","tests":len(results),"manual_acceptance":"PASS","db_unchanged":True,"json":str(REPORT.relative_to(ROOT)),"md":str(MD.relative_to(ROOT))},ensure_ascii=False))
if __name__=="__main__": main()
