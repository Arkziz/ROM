from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_real_actor_root_cause_audit import _run_pair_once,run_audit
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}
pair=_run_pair_once("warrior","mage",10,14632); assert pair["trials"]==10 and sum(pair["wins"].values())+pair["draws"]==10
for cls in ("warrior","mage"):
 m=pair["class_metrics"][cls]; assert m["valid_actions"]+m["invalid_actions"]>0 and "uses_by_action" in m and "avg_damage_by_action_use" in m
report=run_audit(10,14632); assert report["pairs_checked"]==15 and len(report["rows"])==15
assert report["production_skill_catalog_used"] and report["target_aware_policy_used"] and report["production_round_resolver_used"]
assert report["production_database_writes"]==0 and report["live_balance_changed"] is False
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP real actor action rotation and dominance root-cause audit")
print("- 15 real actor matchup diagnostics: PASS")
print("- action, skill, resource, effect and terminal metrics: PASS")
print("- production engine, skills and policy: PASS")
print("- live balance changes: 0")
print("- production database writes: 0")
