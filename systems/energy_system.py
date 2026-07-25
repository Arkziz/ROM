"""Energy/fatigue domain implementation extracted from db.py.

Fatigue scale: 0 = fully rested, 40 = fully fatigued.
db.py remains a compatibility facade.
"""
from datetime import datetime, timedelta
from importlib import import_module

ENERGY_MAX = 40
ENERGY_REGEN_MINUTES = 5

def _db():
    return import_module("db")

class _ConnProxy:
    def __getattr__(self, name):
        return getattr(_db().conn, name)

class _CursorProxy:
    def __getattr__(self, name):
        return getattr(_db().cursor, name)

conn = _ConnProxy()
cursor = _CursorProxy()

def init_energy_system(*args, **kwargs):
    return _energy_system_v1().init_energy_system(*args, **kwargs)

def get_user_energy(*args, **kwargs):
    return _energy_system_v1().get_user_energy(*args, **kwargs)

def consume_energy_for_hunt(user_id):
    from datetime import datetime

    reset_daily_hunts_if_needed(user_id)
    energy_data = get_user_energy(user_id)
    energy = energy_data["energy"]

    if energy >= ENERGY_MAX:
        return {
            "success": False,
            "energy": ENERGY_MAX,
            "max_energy": ENERGY_MAX,
            "message": (
                "😴 Герой дуже втомлений і не може полювати.\n\n"
                "Потрібно відпочити та дочекатися зниження втоми.\n"
                f"⏳ Наступне зменшення втоми приблизно через: "
                f"{energy_data['next_energy_minutes']} хв."
            )
        }

    new_energy = energy + 1

    cursor.execute("""
    UPDATE users
    SET energy=?,
        last_energy_update=?,
        energy_full_notified=0,
        daily_hunts=daily_hunts + 1,
        daily_hunts_date=?
    WHERE user_id=?
    """, (
        new_energy,
        datetime.now().isoformat(),
        get_today_str(),
        user_id
    ))

    conn.commit()

    return {
        "success": True,
        "energy": new_energy,
        "max_energy": ENERGY_MAX,
        "message": None
    }

def restore_energy_for_test(user_id, amount=0):
    from datetime import datetime

    init_energy_system()

    try:
        amount = int(amount)
    except Exception:
        amount = 0

    amount = max(0, min(ENERGY_MAX, amount))
    notified = 0

    cursor.execute("""
    UPDATE users
    SET energy=?,
        last_energy_update=?,
        energy_full_notified=?
    WHERE user_id=?
    """, (amount, datetime.now().isoformat(), notified, user_id))

    conn.commit()

    return {
        "success": True,
        "energy": amount,
        "max_energy": ENERGY_MAX,
        "message": f"✅ DEV: втому встановлено {amount}/{ENERGY_MAX}"
    }

def get_users_for_energy_full_notification():
    init_energy_system()

    cursor.execute("""
    SELECT user_id
    FROM users
    """)

    users = cursor.fetchall()
    notify_users = []

    for row in users:
        user_id = row[0]

        energy_data = get_user_energy(user_id)
        energy = energy_data["energy"]
        max_energy = energy_data["max_energy"]

        cursor.execute("""
        SELECT energy_full_notified
        FROM users
        WHERE user_id=?
        """, (user_id,))

        notified_row = cursor.fetchone()
        notified = notified_row[0] if notified_row else 0

        if energy <= 0 and not notified:
            notify_users.append(user_id)

            cursor.execute("""
            UPDATE users
            SET energy_full_notified=1
            WHERE user_id=?
            """, (user_id,))

        elif energy > 0 and notified:
            cursor.execute("""
            UPDATE users
            SET energy_full_notified=0
            WHERE user_id=?
            """, (user_id,))

    conn.commit()

    return notify_users

def get_energy_contract_snapshot(user_id):
    result = get_user_energy(user_id)
    return {"result": result, "result_type": type(result).__name__}


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

