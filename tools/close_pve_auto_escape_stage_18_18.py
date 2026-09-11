#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,hashlib,json,sqlite3,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];DB=R/"game.db"
REPORT=R/"reports/stage_18_18_2_pve_auto_escape_production_closure.json";MD=R/"MD/STAGE_18_18_PVE_AUTO_ESCAPE_PRODUCTION_CLOSURE.md"
PROD=("systems/pve_auto_escape_system.py","handlers/combat.py","main.py")
TESTS=("tools/smoke_test_pve_auto_escape_18_18_1.py","tools/smoke_test_pve_encounter_history_recovery_18_18_1a.py")
COMMITS=("b99df86f17ceb8c2d13b4d5f3fc57db21ea813cb","b545e154e5a96c15ddf24325a753990da7233390","ee358f617ddf7b2f61601876e7e80f2ed5dc6969")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd):
 x=subprocess.run(cmd,cwd=R,text=True,capture_output=True)
 if x.returncode:raise RuntimeError("command failed: "+" ".join(cmd)+"\n"+x.stdout+x.stderr)
 return {"command":cmd,"returncode":0,"stdout":x.stdout[-6000:],"stderr":x.stderr[-6000:]}
def dbcheck():
 before=sha(DB);c=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True)
 try:
  c.execute("PRAGMA query_only=ON");idx=c.execute("PRAGMA index_list('pve_encounters')").fetchall();out={"quick_check":c.execute("PRAGMA quick_check").fetchone()[0],"foreign_key_violations":c.execute("PRAGMA foreign_key_check").fetchall(),"history_rows":c.execute("SELECT COUNT(*) FROM pve_encounters").fetchone()[0],"active_rows":c.execute("SELECT COUNT(*) FROM pve_encounters WHERE status='active'").fetchone()[0],"duplicate_active_users":c.execute("SELECT user_id,COUNT(*) FROM pve_encounters WHERE status='active' GROUP BY user_id HAVING COUNT(*)>1").fetchall(),"status_counts":dict(c.execute("SELECT status,COUNT(*) FROM pve_encounters GROUP BY status").fetchall()),"total_changes":c.total_changes,"partial_unique_active":any(str(x[1])=="ux_pve_encounters_one_active_user" and int(x[2])==1 and int(x[4])==1 for x in idx)}
 finally:c.close()
 out.update(sha256_before=before,sha256_after=sha(DB));out["unchanged"]=out["sha256_before"]==out["sha256_after"];return out
def main():
 for rel in PROD+TESTS:
  p=R/rel
  if not p.is_file():raise RuntimeError("missing "+rel)
  ast.parse(p.read_text(encoding="utf-8-sig"),filename=rel)
 system=(R/PROD[0]).read_text(encoding="utf-8-sig");combat=(R/PROD[1]).read_text(encoding="utf-8-sig");main=(R/PROD[2]).read_text(encoding="utf-8-sig")
 for token in ("PVE_AUTO_ESCAPE_TIMEOUT_SECONDS = 300","BEGIN IMMEDIATE","ux_pve_encounters_one_active_user","WHERE status='active'","def begin_pve_encounter(","def claim_pve_terminal(","def expire_pve_encounters_once(","def recover_pve_encounters_after_restart(","deadline_at>?","restored_user_ids"):
  assert token in system,token
 assert "user_id INTEGER NOT NULL UNIQUE" not in system
 assert "claim_pve_terminal(user_id, 'victory'" in combat and "claim_pve_terminal(user_id, 'manual_escape'" in combat and "begin_pve_encounter(" in combat
 assert "recover_pve_encounters_after_restart(bot)" in main and "start_pve_auto_escape_worker(bot)" in main
 commands=[run([sys.executable,"-m","py_compile",*[str(R/x) for x in PROD+TESTS]])]
 for rel in TESTS:commands.append(run([sys.executable,str(R/rel)]))
 for h in COMMITS:
  if subprocess.run(["git","cat-file","-e",h+"^{commit}"],cwd=R).returncode:raise RuntimeError("missing commit "+h)
 db=dbcheck();assert db["quick_check"]=="ok" and not db["foreign_key_violations"] and db["partial_unique_active"] and not db["duplicate_active_users"] and db["total_changes"]==0 and db["unchanged"]
 report={"stage":"18.18.2","status":"CLOSED","generated_at_utc":datetime.now(timezone.utc).isoformat(),"production_mutation":False,"manual_acceptance":{"status":"PASS","reported_by_user":True,"scenarios":["automatic escape after five minutes","no rewards","old combat buttons rejected","repeated hunting after history recovery"]},"policy":{"timeout_seconds":300,"hp_mp":"preserve actual","energy_refund":False,"extra_durability_penalty":False,"death_penalty":False,"rewards_or_progress":False,"normal_elite_boss_same_policy":True,"first_atomic_terminal_completion_wins":True},"architecture":{"owner":"systems/pve_auto_escape_system.py","combat":"handlers/combat.py","startup":"main.py","history":True,"one_active_per_user":True,"restart_before_deadline":"restore original encounter and deadline","restart_after_deadline":"auto_escape"},"verification":{"tests":list(TESTS),"commands":commands,"commits":list(COMMITS)},"database":db,"known_nuances":["Old Telegram inline buttons remain visible but are rejected as stale or not in combat.","Encounter history is retained; only one active row per user is permitted.","The worker notifies only after a successful atomic terminal claim."],"next_stage":"18.19 according to the roadmap"}
 REPORT.parent.mkdir(exist_ok=True);MD.parent.mkdir(exist_ok=True);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
 lines=["# Stage 18.18: PvE Auto-Escape Production Closure","","**Status:** CLOSED","**Manual acceptance:** PASS","**Timeout:** 300 seconds","","## Architecture","","- `systems/pve_auto_escape_system.py` owns persistence, deadlines, atomic terminal claims, recovery and the worker.","- `handlers/combat.py` registers encounters and claims victory/manual escape.","- `main.py` performs restart recovery and starts the worker.","- `pve_encounters` retains history and permits only one active row per user through a partial unique index.","","## Policy","","- Deadline is 300 seconds from authoritative encounter start.","- HP and MP remain actual; energy is not refunded.","- No extra durability or death penalty is applied.","- No EXP, gold, loot, quest, contract, boss or event progress is awarded.","- Normal, elite and boss encounters use the same policy.","- First atomic terminal completion wins.","","## Restart","","Before deadline, runtime mob state is restored without extending the deadline. After deadline, the encounter is completed as auto_escape.","","## Verification","","- Both maintained smoke tests PASS.","- Manual five-minute timeout, no rewards, stale buttons and repeated hunting PASS.","- Partial unique active index exists; duplicate active users: 0.","- quick_check=ok; FK violations=0; closure performs no DB writes.","- WAL/SHM were not manipulated.","","## Final decision","","Stage 18.18 is closed. No further implementation patch is required unless a new runtime defect is discovered."]
 MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
 print(json.dumps({"status":"CLOSED","tests":len(TESTS),"history_rows":db["history_rows"],"active_rows":db["active_rows"],"manual_acceptance":"PASS","db_unchanged":True,"json":str(REPORT.relative_to(R)),"md":str(MD.relative_to(R))},ensure_ascii=False))
if __name__=="__main__":main()
