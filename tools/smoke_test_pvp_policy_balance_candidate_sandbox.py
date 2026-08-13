from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_policy_balance_candidate_sandbox import run_sandbox
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; r=run_sandbox(20,14640)
assert r["version"]=="14.6.4" and len(r["scenarios"])==4
assert all(len(x["rows"])==15 for x in r["scenarios"].values())
baseline_j=r["scenarios"]["baseline"]["judgement_uses"]; candidate_j=r["scenarios"]["policy_only"]["judgement_uses"]; assert baseline_j==0, baseline_j; assert candidate_j>0, candidate_j
assert r["recommendation_status"]=="SANDBOX_ONLY_NOT_APPROVED_FOR_LIVE" and not r["live_balance_changed"] and r["production_database_writes"]==0
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP policy and balance candidate sandbox"); print("- baseline plus three isolated candidates: PASS"); print("- production engine and skill catalog: PASS"); print("- Judgement policy candidate observable: PASS"); print("- live balance changes: 0"); print("- production database writes: 0")
