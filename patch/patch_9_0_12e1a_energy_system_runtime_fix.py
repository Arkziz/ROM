from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12e1a_energy_system_runtime_fix"
TARGET_RELATIVE_PATH = Path("systems") / "energy_system.py"
MARKER = "# ENERGY SYSTEM RUNTIME FIX 9.0.12e1a"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(f"File not found: {target}")

    original = target.read_text(encoding="utf-8")
    if MARKER in original:
        print("Patch 9.0.12e1a is already applied.")
        return

    backup = make_backup(root, target)

    code = r'''

# ==============================
# ENERGY SYSTEM RUNTIME FIX 9.0.12e1a
# ==============================

def _ensure_energy_column_v2(table, column, column_type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        conn.commit()
    except Exception:
        pass


def init_energy_system(*args, **kwargs):
    """Initialize fatigue columns without legacy facade recursion."""
    _ensure_energy_column_v2("users", "energy", "INTEGER DEFAULT 0")
    _ensure_energy_column_v2("users", "last_energy_update", "TEXT DEFAULT ''")
    _ensure_energy_column_v2("users", "energy_full_notified", "INTEGER DEFAULT 1")
    _ensure_energy_column_v2("users", "daily_hunts", "INTEGER DEFAULT 0")
    _ensure_energy_column_v2("users", "daily_hunts_date", "TEXT DEFAULT ''")
    return True


def _energy_today_v2():
    from datetime import date
    return date.today().isoformat()


def get_today_str():
    db_module = _db()
    legacy = getattr(db_module, "get_today_str", None)
    if callable(legacy):
        try:
            return legacy()
        except Exception:
            pass
    return _energy_today_v2()


def reset_daily_hunts_if_needed(user_id):
    """Reset only the daily hunt counter when the calendar date changes."""
    init_energy_system()
    today = get_today_str()
    row = cursor.execute(
        "SELECT daily_hunts_date FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()
    if not row:
        return False
    stored_date = row[0] or ""
    if stored_date == today:
        return False
    cursor.execute(
        "UPDATE users SET daily_hunts=0, daily_hunts_date=? WHERE user_id=?",
        (today, user_id)
    )
    conn.commit()
    return True


def get_user_energy(user_id, *args, **kwargs):
    """
    Return current fatigue in the established public dict format.

    Scale:
    - 0 = fully rested
    - 40 = fully fatigued
    - every ENERGY_REGEN_MINUTES fatigue decreases by 1
    """
    init_energy_system()
    reset_daily_hunts_if_needed(user_id)

    row = cursor.execute(
        "SELECT energy, last_energy_update FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    if not row:
        return {
            "success": False,
            "energy": 0,
            "max_energy": ENERGY_MAX,
            "next_energy_minutes": ENERGY_REGEN_MINUTES,
        }

    try:
        energy = int(row[0] or 0)
    except Exception:
        energy = 0
    energy = max(0, min(ENERGY_MAX, energy))
    last_update = row[1] or ""
    now = datetime.now()

    if not last_update:
        cursor.execute(
            "UPDATE users SET energy=?, last_energy_update=? WHERE user_id=?",
            (energy, now.isoformat(), user_id)
        )
        conn.commit()
        return {
            "success": True,
            "energy": energy,
            "max_energy": ENERGY_MAX,
            "next_energy_minutes": ENERGY_REGEN_MINUTES,
        }

    try:
        last_dt = datetime.fromisoformat(last_update)
    except Exception:
        last_dt = now

    elapsed_seconds = max(0.0, (now - last_dt).total_seconds())
    tick_seconds = ENERGY_REGEN_MINUTES * 60
    ticks = int(elapsed_seconds // tick_seconds)

    if energy > 0 and ticks > 0:
        new_energy = max(0, energy - ticks)
        consumed_ticks = energy - new_energy
        new_last_dt = last_dt + timedelta(minutes=consumed_ticks * ENERGY_REGEN_MINUTES)
        notified = 1 if new_energy <= 0 else 0
        cursor.execute(
            """
            UPDATE users
            SET energy=?, last_energy_update=?, energy_full_notified=?
            WHERE user_id=?
            """,
            (new_energy, new_last_dt.isoformat(), notified, user_id)
        )
        conn.commit()
        energy = new_energy
        last_dt = new_last_dt
        elapsed_seconds = max(0.0, (now - last_dt).total_seconds())

    if energy <= 0:
        next_minutes = 0
    else:
        remaining_seconds = max(0, tick_seconds - int(elapsed_seconds % tick_seconds))
        next_minutes = max(1, (remaining_seconds + 59) // 60)

    return {
        "success": True,
        "energy": energy,
        "max_energy": ENERGY_MAX,
        "next_energy_minutes": int(next_minutes),
    }
'''

    target.write_text(original.rstrip() + "\n" + code + "\n", encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "Compilation failed after patch; energy_system.py was restored.\n"
            f"Error: {error}"
        )

    print("Patch 9.0.12e1a applied successfully.")
    print(f"Backup: {backup}")
    print("Fixed:")
    print("- removed runtime dependency on undefined _energy_system_v1")
    print("- init_energy_system now uses direct SQL column initialization")
    print("- get_user_energy now uses direct SQL and returns the existing dict contract")
    print("- fatigue scale remains 0=rested and 40=fully fatigued")


if __name__ == "__main__":
    main()
