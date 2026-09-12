#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, hashlib, json, sqlite3, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/"game.db"; REPORT=ROOT/"reports/stage_18_19_2_pve_effect_timeline_production_closure.json"; MD=ROOT/"MD/STAGE_18_19_PVE_EFFECT_TIMELINE_PRODUCTION_CLOSURE.md"
PROD=("handlers/combat.py",)
TESTS=("tools/smoke_test_pve_effect_timeline_18_19_1.py","tools/smoke_test_pve_auto_escape_18_18_1.py","tools/smoke_test_pve_encounter_history_recovery_18_18_1a.py")
COMMITS=("c1b66d53099c211ad6f83992c19901519eb535a5","2ed4ff0023020c7a3b83dec422c9b0ce014c8f2d")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd):
 x=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
 if x.returncode:raise RuntimeError("command failed: "+" ".join(cmd)+"\n"+x.stdout+x.stderr)
 return {"command":cmd,"returncode":0,"stdout":x.stdout[-8000:],"stderr":x.stderr[-8000:]}
def dbcheck():
 before=sha(DB);c=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True)
 try:c.execute("PRAGMA query_only=ON");out={"quick_check":c.execute("PRAGMA quick_check").fetchone()[0],"foreign_key_violations":c.execute("PRAGMA foreign_key_check").fetchall(),"total_changes":c.total_changes}
 finally:c.close()
 out.update(sha256_before=before,sha256_after=sha(DB));out["unchanged"]=out["sha256_before"]==out["sha256_after"];return out
def functions(source):
 tree=ast.parse(source);return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def main():
 for rel in PROD+TESTS:
  p=ROOT/rel
  if not p.is_file():raise RuntimeError("missing "+rel)
  ast.parse(p.read_text(encoding="utf-8-sig"),filename=rel)
 source=(ROOT/"handlers/combat.py").read_text(encoding="utf-8-sig");owners=functions(source)
 required=("add_enemy_effect","process_enemy_turn_start_effects","set_skill_cooldown","tick_skill_cooldowns_at_player_turn","validate_skill_cooldown","roll_skill_stun","process_player_turn_start_effects","apply_player_shield_absorb")
 for name in required:
  if name not in owners:raise RuntimeError("missing canonical owner "+name)
 contracts=("incoming[\"fresh\"] = True","if effect.pop(\"fresh\", False):","incoming.pop(\"fresh\", None)","cooldown_turns + 1","mob[\"stunned_turns\"] = 1")
 for token in contracts:
  if token not in source:raise RuntimeError("missing contract "+token)
 if source.count('if mob.get("stunned_turns", 0) > 0:')!=3 or source.count('mob["stunned_turns"] -= 1')!=3:raise RuntimeError("stun route count mismatch")
 if "systems.pvp_" in source:raise RuntimeError("PvP production imported into PvE combat")
 commands=[run([sys.executable,"-m","py_compile",*[str(ROOT/x) for x in PROD+TESTS]])]
 for rel in TESTS:commands.append(run([sys.executable,str(ROOT/rel)]))
 for commit in COMMITS:
  if subprocess.run(["git","cat-file","-e",commit+"^{commit}"],cwd=ROOT).returncode:raise RuntimeError("missing commit "+commit)
 db=dbcheck()
 if db["quick_check"]!="ok" or db["foreign_key_violations"] or db["total_changes"] or not db["unchanged"]:raise RuntimeError("database closure invariant failed")
 report={"stage":"18.19.2","status":"CLOSED","generated_at_utc":datetime.now(timezone.utc).isoformat(),"production_mutation":False,"manual_acceptance":{"status":"PASS","reported_by_user":True,"evidence":"Manual Telegram combat logs reviewed","verified":["bleed has no application tick and then exactly three ticks","poison has no application tick and then exactly three ticks","stun skips exactly the nearest enemy action","HOT starts on the next player action and runs four ticks","shield applies immediately and absorbs incoming damage","cooldown readiness appears after the configured number of subsequent actions","normal PvE completion and repeated hunting work","no traceback observed"],"not_manually_reproduced_but_automated":["same-key weaker/equal/stronger effect reapplication","lethal DOT victory","elite and boss parity","direct blocked-skill callback resource preservation","PvP battle regression"]},"policy":{"dot_hot_application_tick":False,"fresh_effect_duration_loss":False,"dot_ticks_after_application":3,"same_key_damage_stack":False,"stronger_replaces_weaker":True,"equal_strength_longer_duration_refreshes":True,"cooldown":"N blocks exactly N subsequent owner actions","stun":"nearest enemy action only","shield":"immediate","pvp_mutation":False},"architecture":{"canonical_owner":"handlers/combat.py","changed_functions":["add_enemy_effect","process_enemy_turn_start_effects","set_skill_cooldown"],"pvp_reference_only":True},"verification":{"tests":list(TESTS),"commands":commands,"commits":list(COMMITS)},"database":db,"known_nuances":["Old status text may display duplicated effect emoji because both icon and localized name include an emoji; this is cosmetic and predates closure acceptance.","The fresh marker is transient and removed when the effect becomes active.","Elite and boss encounters share the same canonical PvE effect helpers rather than separate timing implementations."],"next_stage":"18.20 according to the current checklist"}
 REPORT.parent.mkdir(exist_ok=True);MD.parent.mkdir(exist_ok=True);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
 lines=["# Stage 18.19: PvE Effect Timeline Production Closure","","**Status:** CLOSED","**Manual acceptance:** PASS","**Production mutation in closure:** none","","## Authoritative implementation","","- `handlers/combat.py` remains the canonical PvE combat and effect-timeline owner.","- `add_enemy_effect` owns same-key replace and refresh policy.","- `process_enemy_turn_start_effects` skips newly applied effects once, then performs periodic ticks and duration decrement.","- `set_skill_cooldown` stores the internal offset needed for exactly N blocked subsequent player actions.","- Existing immediate stun and shield routes remain canonical.","- PvP production was not modified or imported into PvE.","","## Accepted semantics","","- New DOT and HOT effects do not tick during application.","- New enemy effects do not lose duration during application.","- Bleed and poison tick from the next action and retain all configured ticks.","- Same-key effects do not stack damage; stronger replaces weaker and equal strength may refresh a longer duration.","- Cooldown N blocks exactly N subsequent owner actions.","- Stun skips exactly the nearest enemy action.","- Shields apply immediately.","","## Manual verification","","Telegram combat logs confirmed bleed, poison, stun, HOT, shield, cooldown progression, ordinary PvE completion and repeated hunting. No traceback was observed.","","## Automated verification","","- Stage 18.19.1 deterministic timing smoke: PASS.","- Stage 18.18 auto-escape regression: PASS.","- Stage 18.18 encounter-history regression: PASS.","- Python compilation and owner-aware structural contracts: PASS.","- `quick_check=ok`, FK violations=0, database unchanged.","- WAL/SHM were not manipulated.","","## Accepted limitations","","- Lethal DOT, same-key reapplication and elite/boss parity were accepted from deterministic contracts and shared canonical routing rather than additional manual reproduction.","- A direct press of a disabled cooldown skill cannot be performed through the current Telegram keyboard; cooldown validation remains covered automatically.","","## Final decision","","Stage 18.19 is closed. Further changes require a separately identified runtime defect."]
 MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
 print(json.dumps({"status":"CLOSED","tests":len(TESTS),"manual_acceptance":"PASS","db_unchanged":True,"json":str(REPORT.relative_to(ROOT)),"md":str(MD.relative_to(ROOT))},ensure_ascii=False))
if __name__=="__main__":main()
