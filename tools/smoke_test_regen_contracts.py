from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

row = db.conn.execute(
    "SELECT user_id FROM users ORDER BY user_id LIMIT 1"
).fetchone()
if not row:
    print("[SKIP] no users found for regen contract smoke-test")
    raise SystemExit(0)

user_id = int(row[0])

assert db.init_hp_regen_system() in (True, None)
assert db.init_passive_regen_system() in (True, None)

before_hp = db.get_current_hp_raw(user_id)
max_hp = db.get_max_hp(user_id)
result = db.process_passive_regeneration(user_id)
after_hp = db.get_current_hp_raw(user_id)

assert isinstance(before_hp, int), type(before_hp)
assert isinstance(max_hp, int), type(max_hp)
assert isinstance(result, dict), type(result)
assert isinstance(after_hp, int), type(after_hp)
assert 0 <= after_hp <= max_hp, (after_hp, max_hp)
for key in ("success", "minutes", "hp_restored", "mp_restored"):
    assert key in result, (key, result)

print("[OK] regen runtime contracts")
print("- before:", before_hp, "/", max_hp)
print("- after:", after_hp, "/", db.get_max_hp(user_id))
print("- result:", result)