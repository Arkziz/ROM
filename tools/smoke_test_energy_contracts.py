from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db
uid = int(os.environ.get("ROM_TEST_USER_ID", "243129101"))

for name in ("init_energy_system", "get_user_energy"):
    if not hasattr(db, name):
        raise SystemExit(f"[FAIL] missing energy API: {name}")

db.init_energy_system()
result = db.get_user_energy(uid)
if isinstance(result, dict):
    value = result.get("energy", result.get("fatigue"))
elif isinstance(result, (tuple, list)):
    value = result[0] if result else None
else:
    value = result
try:
    value = int(value)
except Exception as exc:
    raise SystemExit(f"[FAIL] invalid energy result: {result!r}") from exc
if not 0 <= value <= 40:
    raise SystemExit(f"[FAIL] fatigue out of range: {value}")
print("[OK] energy runtime contracts")
print("- result type:", type(result).__name__)
print("- fatigue:", value, "/ 40")
print("- rule: 0=rested, 40=fully fatigued")
