from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_anti_stall_survivability_candidate_sandbox import run_sandbox
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}
r=run_sandbox(10,14643)
assert r["version"]=="14.6.4c" and len(r["scenarios"])==8
assert all(len(value["rows"])==15 for value in r["scenarios"].values())
assert all(row["max_rounds_observed"]<=15 for name,value in r["scenarios"].items() if name!="baseline_50" for row in value["rows"])
assert r["scenarios"]["anti_stall_moderate"]["config"]["pacing"]=="moderate"
assert r["scenarios"]["moderate_mage85"]["config"]["mage_physical_received"]==0.85
assert r["scenarios"]["balanced_candidate"]["config"]["shield_bash_stun"]==15
assert r["recommendation_status"]=="SANDBOX_ONLY_NOT_APPROVED_FOR_LIVE" and not r["live_balance_changed"] and r["production_database_writes"]==0
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP anti-stall and survivability candidate sandbox")
print("- soft/moderate/strong progressive pacing: PASS")
print("- Mage physical survivability candidates: PASS")
print("- Knight shield/stun candidate: PASS")
print("- 15-round emergency cap: PASS")
print("- live balance changes: 0")
print("- production database writes: 0")
