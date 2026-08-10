from pathlib import Path
import hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from systems.pvp_policy_metrics_audit import audit_policy, simulate_duel
before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}
report=audit_policy("target_aware",2)
assert len(report["matchups"])==36
for row in report["class_summary"].values():
    for key in ("no_valid_skill_rounds","cooldown_blocked_rounds","policy_basic_attack_rounds","resource_restored_skill","stunned_rounds_inflicted"):
        assert key in row
warrior=report["class_summary"]["warrior"]
knight=report["class_summary"]["knight"]
assert warrior["resource_gained_total"] == warrior["resource_gained_attack"] + warrior["resource_gained_damage_taken"] + warrior["resource_gained_skill"]
assert knight["resource_gained_total"] == knight["resource_gained_attack"] + knight["resource_gained_damage_taken"] + knight["resource_gained_skill"]
assert knight["resource_starved_rounds"] <= knight["no_valid_skill_rounds"]
priority=audit_policy("priority",2)["class_summary"]
assert priority["mage"]["resource_restored_skill"] > 0
assert priority["priest"]["resource_restored_skill"] > 0
assert knight["stuns_applied"] >= knight["stunned_rounds_inflicted"] >= 0
_,duel=simulate_duel("knight","warrior","target_aware",146101)
assert duel[1]["stuns_applied"] >= duel[1]["stunned_rounds_inflicted"]
after={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}
assert before==after
print("[OK] PvP resource, stun and starvation metrics")
print("- Rage event accounting without outcome duplication: PASS")
print("- Mage/Priest MP restoration from state delta: PASS")
print("- pending stun source attribution: PASS")
print("- starvation/cooldown/policy basic attack split: PASS")
print("- production database writes: 0")
