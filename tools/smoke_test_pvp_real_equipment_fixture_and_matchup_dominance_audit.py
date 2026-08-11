from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_real_equipment_fixture_audit import PRODUCTION_REFERENCE,_expected_basic_damage,run_audit
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}
assert len(PRODUCTION_REFERENCE)==6 and PRODUCTION_REFERENCE["mage"]["hp"]==415
assert PRODUCTION_REFERENCE["knight"]["active_slots"]==10 and PRODUCTION_REFERENCE["rogue"]["active_slots"]==10
assert _expected_basic_damage("warrior","priest")>_expected_basic_damage("warrior","knight")
assert _expected_basic_damage("priest","warrior")>_expected_basic_damage("priest","mage")
r=run_audit(10,10,"rare"); assert r["production_reference"]["all_defense_profiles_expected"] is True; assert len(r["matchup_dominance"]["rows"])==15; assert r["production_database_writes"]==0
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP real equipment fixture and matchup dominance audit")
print("- six production references including mage HP 415: PASS")
print("- armor defense profile checks: PASS")
print("- 15 non-mirror matchups: PASS")
print("- DEX attack mapping review: ACTIVE")
print("- live balance changes: 0")
print("- production database writes: 0")
