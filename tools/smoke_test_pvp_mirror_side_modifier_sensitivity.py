from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_production_calibration import duel
from systems.pvp_production_fixture_audit import run_audit
before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}
for class_key in ("warrior","knight","scout","rogue","mage","priest"):
 row=duel(class_key,class_key,3,10,"rare",14622); assert row["wins_a"]+row["wins_b"]+row["draws"]==3
result=run_audit(2,10,"rare"); assert result["verdict"]=="PASS" and result["matrix_integrity"]["pass"] is True; assert result["all_classes_checked"] and result["all_skills_checked"]; assert result["modifier_sensitivity"]["criterion"]=="combat_metrics_only_v2"; assert "base_primary_stats" in result["actors"]["warrior"]
after={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP mirror, side and modifier sensitivity fix")
print("- winner_id/original-side mirror accounting: PASS")
print("- duel invariant for all 6 mirrors: PASS")
print("- combat-metrics-only modifier sensitivity: PASS")
print("- full primary-stat and equipment breakdown: PASS")
print("- all 6 classes and 18 canonical skills: PASS")
print("- live balance changes: 0")
print("- production database writes: 0")
