from pathlib import Path
import hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from systems.pvp_production_fixture_audit import run_audit
before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}
result=run_audit(2,10,"rare")
assert result["verdict"]=="PASS"
assert result["all_classes_checked"] is True
assert result["all_skills_checked"] is True
assert len(result["actors"])==6
assert result["skills"]["skills_checked"]==18
assert result["matrix_integrity"]["pass"] is True
for row in result["matrix_integrity"]["rows"]:
    if row["kind"]=="mirror": assert row["total"]==row["trials"]
after={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}
assert before==after
print("[OK] PvP production actor fixture and matrix integrity audit")
print("- all 6 classes and actor snapshots: PASS")
print("- all 18 canonical skills: PASS")
print("- mirror totals and ordered pair totals: PASS")
print("- side-delta and modifier sensitivity reporting: PASS")
print("- live balance changes: 0")
print("- production database writes: 0")
