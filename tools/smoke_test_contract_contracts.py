from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import db
UID = 243129101
status = db.get_contract_status(UID)
active = db.get_active_contract(UID)
assert isinstance(status, dict), type(status)
assert active is None or isinstance(active, dict), type(active)
assert int(getattr(db, "CONTRACT_TARGET_KILLS", 0)) == 5
for name in ("create_daily_contract", "abandon_active_contract", "process_contract_progress_on_kill", "claim_contract_reward"):
    assert callable(getattr(db, name, None)), name
print("[OK] contract runtime contracts")
print("- target_kills:", db.CONTRACT_TARGET_KILLS)
print("- status keys:", sorted(status.keys()))
print("- active:", active)
