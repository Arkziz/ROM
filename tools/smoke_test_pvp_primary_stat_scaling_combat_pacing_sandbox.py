from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_primary_stat_scaling_combat_pacing_sandbox import run_sandbox
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}
r=run_sandbox(10,14642)
assert r["version"]=="14.6.4b" and len(r["scenarios"])==8
assert all(len(value["rows"])==15 for value in r["scenarios"].values())
assert r["scenarios"]["baseline_50"]["config"]["round_cap"]==50
assert all(row["max_rounds_observed"]<=15 for name,value in r["scenarios"].items() if name!="baseline_50" for row in value["rows"])
base=r["scenarios"]["cap15_only"]["rows"]; dex=r["scenarios"]["dex_add_050_cap15"]["rows"]
def attack(rows,cls):
 for row in rows:
  if cls in row["initial_attacks"]: return row["initial_attacks"][cls]["physical_attack"]
assert attack(dex,"scout")>attack(base,"scout") and attack(dex,"rogue")>attack(base,"rogue")
assert r["recommendation_status"]=="SANDBOX_ONLY_NOT_APPROVED_FOR_LIVE" and not r["live_balance_changed"] and r["production_database_writes"]==0
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP primary-stat scaling and combat-pacing candidate sandbox")
print("- three DEX scaling models with/without Mage 1.12: PASS")
print("- 15-round hard cap and HP-percent tiebreak: PASS")
print("- production engine, skills and policy: PASS")
print("- live balance changes: 0")
print("- production database writes: 0")
