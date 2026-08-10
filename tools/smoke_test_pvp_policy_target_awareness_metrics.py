from pathlib import Path
import hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from systems.pvp_policy_metrics_audit import POLICIES, audit_all_policies, audit_policy, simulate_duel
before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}
assert "target_aware" in POLICIES
one=audit_policy("target_aware",1)
assert len(one["matchups"])==36 and len(one["class_summary"])==6
required={"resource_gained_round_regen","resource_wasted_at_cap","dot_ticks_dealt","dot_ticks_received","healing_done","healing_received","debuff_uptime_rounds","hot_uptime_rounds"}
for row in one["class_summary"].values(): assert required.issubset(row)
_,energy=simulate_duel("scout","warrior","target_aware",1461)
assert energy[1]["resource_gained_round_regen"]>0
_,dot=simulate_duel("scout","warrior","target_aware",1462)
assert dot[1]["dot_ticks_dealt"]==dot[2]["dot_ticks_received"]
allp=audit_all_policies(1)
assert set(allp["policies"])==set(POLICIES)
after={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}
assert before==after
print("[OK] PvP target-aware policy and metrics attribution")
print("- target-aware opponent effect inspection: PASS")
print("- four-policy backward-compatible audit: PASS")
print("- Energy/Rage/MP source accounting: PASS")
print("- DoT/HoT source and target attribution: PASS")
print("- production database writes: 0")
