from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import db
row = db.cursor.execute("SELECT user_id FROM users ORDER BY user_id LIMIT 1").fetchone()
if not row:
    print("[SKIP] no users")
    raise SystemExit(0)
uid = int(row[0])
checks = {
    "level": db.get_player_level(uid),
    "wallet": db.get_wallet(uid),
    "hp_raw": db.get_current_hp_raw(uid),
    "hp": db.get_current_hp(uid),
    "progress": db.get_user_progress(uid),
    "stats": db.get_player_stats(uid),
}
assert isinstance(checks["level"], int)
assert isinstance(checks["wallet"], (int, float))
assert isinstance(checks["hp_raw"], int)
assert isinstance(checks["hp"], int)
assert checks["progress"] is not None
assert checks["stats"] is not None
print("[OK] player runtime contracts")
for key, value in checks.items():
    print(f"- {key}: {type(value).__name__} {value}")
