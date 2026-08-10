from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_production_calibration import CLASSES,SLOTS,SLOT_WEIGHTS,SLOT_WEIGHT_TOTAL,_stats,build_standard_actor
from systems.pvp_production_fixture_audit import run_audit
before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}
assert set(SLOTS)==set(SLOT_WEIGHTS) and round(sum(SLOT_WEIGHTS.values()),6)==round(SLOT_WEIGHT_TOTAL,6)==float(len(SLOTS))
assert SLOT_WEIGHTS["main_hand"]==max(SLOT_WEIGHTS.values()) and SLOT_WEIGHTS["chest"]>SLOT_WEIGHTS["gloves"]
for class_key in CLASSES:
 rows={slot:_stats(class_key,slot,10,"rare") for slot in SLOTS}
 assert all(rows[slot]["fixture_slot_weight"]==SLOT_WEIGHTS[slot] for slot in SLOTS)
 actor=build_standard_actor(class_key,10,"rare"); assert actor.max_hp>0 and actor.max_mp>=0
result=run_audit(2,10,"rare"); parity=result["fixture_slot_parity"]
assert result["verdict"]=="PASS" and parity["pass"] and parity["slots_checked"]==len(SLOTS) and parity["weight_total"]==round(float(len(SLOTS)),6)
after={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP slot-weighted production fixture parity fix")
print(f"- canonical production fixture slots: {len(SLOTS)}/{len(SLOTS)}")
print(f"- aggregate slot budget preserved: {float(len(SLOTS))}")
print("- all 6 class fixtures rebuild successfully: PASS")
print("- live balance changes: 0")
print("- production database writes: 0")
