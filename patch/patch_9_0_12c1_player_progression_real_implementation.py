from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12c1_player_progression_real_implementation"

PLAYER_IMPL = r'''

# ==============================
# ✅ ROM 9.0.12c1 PLAYER PROGRESSION REAL IMPLEMENTATION V1
# ==============================
# Safe first slice. Complex EXP/progress/combat-stat contracts remain legacy.

def _player_direct_db():
    import db
    return db

def _player_direct_fetchone(sql, params=()):
    db = _player_direct_db()
    db.cursor.execute(sql, params)
    return db.cursor.fetchone()

def _player_direct_value(row, key, index=0, default=None):
    if row is None:
        return default
    try:
        return row[key]
    except Exception:
        pass
    try:
        return row[index]
    except Exception:
        return default

def get_player_level(user_id: int):
    row = _player_direct_fetchone("SELECT level FROM users WHERE user_id=?", (int(user_id),))
    try:
        return int(_player_direct_value(row, "level", 0, 1) or 1)
    except Exception:
        return 1

def get_wallet(user_id: int):
    row = _player_direct_fetchone("SELECT gold FROM users WHERE user_id=?", (int(user_id),))
    try:
        return float(_player_direct_value(row, "gold", 0, 0.0) or 0.0)
    except Exception:
        return 0.0

def add_gold(user_id: int, amount):
    db = _player_direct_db()
    try:
        amount = float(amount)
    except Exception:
        amount = 0.0
    db.cursor.execute("UPDATE users SET gold=COALESCE(gold,0)+? WHERE user_id=?", (amount, int(user_id)))
    db.conn.commit()
    return None

def add_kill(user_id: int, amount: int = 1):
    db = _player_direct_db()
    try:
        amount = max(0, int(amount))
    except Exception:
        amount = 1
    if amount:
        db.cursor.execute("UPDATE users SET kills=COALESCE(kills,0)+? WHERE user_id=?", (amount, int(user_id)))
        db.conn.commit()
    return None

def get_current_hp_raw(user_id: int):
    sync = sync_user_max_hp(int(user_id), heal_to_full=False)
    try:
        return int(sync.get("hp", 0) or 0)
    except Exception:
        return 0

def get_current_hp(user_id: int):
    return get_current_hp_raw(int(user_id))

def set_current_hp(user_id: int, hp: int):
    db = _player_direct_db()
    sync = sync_user_max_hp(int(user_id), heal_to_full=False)
    try:
        max_hp = int(sync.get("max_hp", get_max_hp(user_id)) or get_max_hp(user_id))
    except Exception:
        max_hp = int(get_max_hp(user_id) or 1)
    try:
        safe_hp = max(0, min(int(hp), max_hp))
    except Exception:
        safe_hp = 0
    db.cursor.execute("UPDATE users SET hp=? WHERE user_id=?", (safe_hp, int(user_id)))
    db.conn.commit()
    reset = getattr(db, "reset_hp_regen_timers_now", None)
    if callable(reset):
        reset(int(user_id))
    return safe_hp
'''

DB_FACADE = r'''

# ==============================
# ✅ ROM 9.0.12c1 PLAYER PROGRESSION REAL IMPLEMENTATION WRAPPERS V1
# ==============================
# add_exp/get_user_progress/get_player_stats/combat formulas remain legacy.

def _player_system_v2():
    from systems import player_system as _mod
    return _mod

def get_player_level(user_id):
    return _player_system_v2().get_player_level(user_id)

def get_wallet(user_id):
    return _player_system_v2().get_wallet(user_id)

def add_gold(user_id, amount):
    return _player_system_v2().add_gold(user_id, amount)

def add_kill(user_id, amount=1):
    return _player_system_v2().add_kill(user_id, amount)

def get_current_hp_raw(user_id):
    return _player_system_v2().get_current_hp_raw(user_id)

def get_current_hp(user_id):
    return _player_system_v2().get_current_hp(user_id)

def set_current_hp(user_id, hp):
    return _player_system_v2().set_current_hp(user_id, hp)
'''

SMOKE = '''from pathlib import Path
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
'''

def make_backup(root, path):
    out_dir = root / "backup"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(path.relative_to(root)).replace("\\", "_").replace("/", "_")
    out = out_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    out.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return out

def main():
    root = Path(__file__).resolve().parents[1]
    player = root / "systems" / "player_system.py"
    db = root / "db.py"
    smoke = root / "tools" / "smoke_test_player_contracts.py"
    for path in (player, db):
        if not path.exists():
            raise SystemExit(f"❌ Не знайдено: {path}")
    originals = {player: player.read_text(encoding="utf-8"), db: db.read_text(encoding="utf-8")}
    backups = []
    try:
        if "# ✅ ROM 9.0.12c1 PLAYER PROGRESSION REAL IMPLEMENTATION V1" not in originals[player]:
            backups.append(make_backup(root, player))
            player.write_text(originals[player].rstrip() + PLAYER_IMPL + "\n", encoding="utf-8")
        if "# ✅ ROM 9.0.12c1 PLAYER PROGRESSION REAL IMPLEMENTATION WRAPPERS V1" not in originals[db]:
            backups.append(make_backup(root, db))
            db.write_text(originals[db].rstrip() + DB_FACADE + "\n", encoding="utf-8")
        if smoke.exists():
            backups.append(make_backup(root, smoke))
        smoke.write_text(SMOKE, encoding="utf-8")
        for path in (player, db, smoke):
            py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")
        raise SystemExit(f"❌ Патч не застосовано; файли відновлено.\n{exc}")
    print("✅ Патч 9.0.12c1 застосовано успішно.")
    print("Direct SQL: level, wallet/gold, kills, current HP read/write.")
    print("Legacy retained: EXP/progress, player stats, max HP/refine, combat stats.")
    print("Backup:")
    for item in backups:
        print(f"- {item}")
    print("Перевірки:")
    print("python -m py_compile .\\systems\\player_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/smoke_test_player_contracts.py")
    print("python tools/db_cleanup_readiness.py")

if __name__ == "__main__":
    main()
