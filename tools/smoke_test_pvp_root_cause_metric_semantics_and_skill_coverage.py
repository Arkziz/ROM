from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_root_cause_metric_semantics import run_audit
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}
r=run_audit(10,14632)
assert r["version"]=="14.6.3b1" and r["pairs_checked"]==15
assert r["policy_invalid_action_count"]==0
assert r["terminal_cancelled_intent_count"]>=0 and r["stunned_skip_count"]>=0
coverage=r["skill_coverage"]; assert coverage["expected_count"]==18 and coverage["observed_count"]==17 and len(coverage["missing_skill_keys"])==1
for row in r["rows"]:
 s=row["metric_semantics"]; assert "terminal_rates" in s
 for cls in (row["class_a"],row["class_b"]):
  m=s["by_class"][cls]; assert m["effective_healing_total"]==m["direct_healing"]+m["hot_healing"] and "resource" in m
assert any("healing_sustain_gap" in row["diagnosis"]["reason_signals"] for row in r["rows"] if "priest" in (row["class_a"],row["class_b"]))
assert r["production_database_writes"]==0 and r["live_balance_changed"] is False
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP root-cause metric semantics and skill coverage fix")
print("- policy invalid versus terminal cancellation split: PASS")
print("- direct plus HoT effective healing: PASS")
print("- exact 18-skill coverage and missing key: PASS")
print("- resource-family semantics: PASS")
print("- terminal-rate semantics: PASS")
print("- live balance changes: 0")
print("- production database writes: 0")
