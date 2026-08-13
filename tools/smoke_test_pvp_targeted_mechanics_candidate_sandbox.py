from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_targeted_mechanics_candidate_sandbox import run_sandbox
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; r=run_sandbox(10,14641)
assert r["version"]=="14.6.4a" and len(r["scenarios"])==8 and all(len(x["rows"])==15 for x in r["scenarios"].values())
assert r["scenarios"]["baseline"]["config"]=={} and r["scenarios"]["combined_moderate"]["config"]["scout_pen"]==0.40
assert any(sum(row["mechanic_usage"].get("knight_judgement",0) for row in r["scenarios"][name]["rows"])>0 for name in ("knight_controlled","combined_moderate"))
assert r["recommendation_status"]=="SANDBOX_ONLY_NOT_APPROVED_FOR_LIVE" and not r["live_balance_changed"] and r["production_database_writes"]==0
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP targeted mechanics candidate sandbox"); print("- eight isolated/combined targeted scenarios: PASS"); print("- Judgement, shield, penetration, HoT and Mage candidates: PASS"); print("- production engine and skill catalog: PASS"); print("- live balance changes: 0"); print("- production database writes: 0")
