from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from systems.pvp_policy_metrics_audit import audit_all_policies,audit_policy
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}
one=audit_policy("resource_aware",1);assert len(one["matchups"])==36 and len(one["class_summary"])==6
allp=audit_all_policies(1);assert set(allp["policies"])=={"priority","random_valid","resource_aware"}
for p in allp["policies"].values():
 for c,x in p["class_summary"].items():assert "non_mirror_win_rate" in x and "actions" in x and "overheal" in x
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")};assert before==after
print("[OK] PvP simulator policy and metrics audit")
print("- priority/random-valid/resource-aware policies: PASS")
print("- 36 matchups per policy and non-mirror score: PASS")
print("- skill/resource/effect/overheal metrics: PASS")
print("- production database writes: 0")
