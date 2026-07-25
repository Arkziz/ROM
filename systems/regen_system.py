"""
ROM Regen System
================

Real implementation introduced in refactor 9.0.12e2.

db.py remains the public compatibility facade, while the regeneration logic
lives here and no longer delegates to _legacy_regen_v1_* references.

Important rules preserved:
- dynamic max HP from equipment/refine is respected;
- equipping or refining armor does not heal immediately;
- passive regeneration heals only after a completed tick;
- current HP is clamped if max HP decreases;
- notification worker remains self-contained in systems/notifications.py;
- 0/40 fatigue logic belongs to systems/energy_system.py and is not changed.
"""

from datetime import datetime, timedelta

HP_REGEN_PERCENT = 0.10
HP_REGEN_MINUTES = 1


def _db():
    import db
    return db


def _table_columns(table_name):
    db = _db()
    try:
        rows = db.conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row[1] for row in rows}
    except Exception:
        return set()


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def _dynamic_max_hp(user_id):
    db = _db()
    try:
        return max(1, int(db.get_max_hp(user_id) or 1))
    except Exception:
        row = db.conn.execute(
            "SELECT max_hp FROM users WHERE user_id=?",
            (user_id,),
        ).fetchone()
        return max(1, int((row[0] if row else 1) or 1))


def _sync_max_hp(user_id):
    db = _db()
    sync = getattr(db, "sync_user_max_hp", None)
    if sync:
        try:
            return sync(user_id, heal_to_full=False)
        except TypeError:
            return sync(user_id)
        except Exception:
            pass

    max_hp = _dynamic_max_hp(user_id)
    row = db.conn.execute(
        "SELECT hp FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    if not row:
        return {"success": False, "hp": 0, "max_hp": max_hp}

    current_hp = int(row[0] or 0)
    clamped_hp = min(current_hp, max_hp)
    db.conn.execute(
        "UPDATE users SET hp=?, max_hp=? WHERE user_id=?",
        (clamped_hp, max_hp, user_id),
    )
    db.conn.commit()
    return {
        "success": True,
        "hp": clamped_hp,
        "max_hp": max_hp,
        "changed": clamped_hp != current_hp,
    }


def init_hp_regen_system():
    db = _db()
    migrations = [
        ("users", "last_hp_regen_update", "TEXT DEFAULT ''"),
        ("users", "hp_full_notified", "INTEGER DEFAULT 1"),
        ("users", "daily_hunts", "INTEGER DEFAULT 0"),
        ("users", "daily_hunts_date", "TEXT DEFAULT ''"),
    ]

    columns = _table_columns("users")
    for table, column, column_type in migrations:
        if column in columns:
            continue
        try:
            db.conn.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"
            )
        except Exception:
            pass
    db.conn.commit()
    return True


def init_passive_regen_system():
    db = _db()
    columns = _table_columns("users")
    if "last_regen_at" not in columns:
        try:
            db.conn.execute(
                "ALTER TABLE users ADD COLUMN last_regen_at TEXT DEFAULT ''"
            )
        except Exception:
            pass
    db.conn.commit()
    return True


def reset_hp_regen_timers_now(user_id):
    db = _db()
    init_hp_regen_system()
    init_passive_regen_system()
    now_iso = datetime.now().isoformat()
    columns = _table_columns("users")

    assignments = []
    params = []
    if "last_hp_regen_update" in columns:
        assignments.append("last_hp_regen_update=?")
        params.append(now_iso)
    if "last_regen_at" in columns:
        assignments.append("last_regen_at=?")
        params.append(now_iso)

    if assignments:
        params.append(user_id)
        db.conn.execute(
            f"UPDATE users SET {', '.join(assignments)} WHERE user_id=?",
            tuple(params),
        )
        db.conn.commit()

    _sync_max_hp(user_id)
    return True


def apply_passive_hp_regen(user_id):
    """Apply the historical 10% max-HP regeneration tick contract."""
    db = _db()
    init_hp_regen_system()
    _sync_max_hp(user_id)

    row = db.conn.execute(
        "SELECT hp, last_hp_regen_update FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    if not row:
        return 0

    max_hp = _dynamic_max_hp(user_id)
    hp = max_hp if row[0] is None else int(row[0] or 0)
    hp = min(hp, max_hp)
    last_update = row[1]
    now = datetime.now()

    last_dt = _parse_datetime(last_update)
    if last_dt is None:
        db.conn.execute(
            "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=? "
            "WHERE user_id=?",
            (hp, max_hp, now.isoformat(), user_id),
        )
        db.conn.commit()
        return hp

    if hp >= max_hp:
        db.conn.execute(
            "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=?, "
            "hp_full_notified=1 WHERE user_id=?",
            (max_hp, max_hp, now.isoformat(), user_id),
        )
        db.conn.commit()
        return max_hp

    diff_seconds = max(0.0, (now - last_dt).total_seconds())
    ticks = int(diff_seconds // (HP_REGEN_MINUTES * 60))
    if ticks <= 0:
        db.conn.execute(
            "UPDATE users SET max_hp=? WHERE user_id=?",
            (max_hp, user_id),
        )
        db.conn.commit()
        return hp

    heal_per_tick = max(1, int(max_hp * HP_REGEN_PERCENT))
    new_hp = min(max_hp, hp + heal_per_tick * ticks)
    new_update = last_dt + timedelta(minutes=ticks * HP_REGEN_MINUTES)

    # Keep 0 when the player just reached full HP so the notification worker
    # can send the single full-health notification and then mark it as sent.
    notified = 0
    db.conn.execute(
        "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=?, "
        "hp_full_notified=? WHERE user_id=?",
        (new_hp, max_hp, new_update.isoformat(), notified, user_id),
    )
    db.conn.commit()
    return new_hp


def process_passive_regeneration(user_id):
    """
    Dynamic-max-HP-safe passive regeneration contract used by existing code.

    This preserves the final runtime behavior that existed before extraction:
    HP regeneration is processed from last_hp_regen_update and returns a dict.
    MP is left unchanged here because current combat/class flows manage MP via
    character_system and the historical final override returned mp_restored=0.
    """
    db = _db()
    init_hp_regen_system()
    _sync_max_hp(user_id)

    columns = _table_columns("users")
    select_columns = ["hp"]
    if "max_hp" in columns:
        select_columns.append("max_hp")
    if "last_hp_regen_update" in columns:
        select_columns.append("last_hp_regen_update")

    row = db.conn.execute(
        f"SELECT {', '.join(select_columns)} FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    if not row:
        return {
            "success": False,
            "minutes": 0,
            "hp_restored": 0,
            "mp_restored": 0,
        }

    index = {name: i for i, name in enumerate(select_columns)}
    max_hp = _dynamic_max_hp(user_id)
    current_hp = int(row[index["hp"]] or 0)
    current_hp = min(current_hp, max_hp)
    last_value = (
        row[index["last_hp_regen_update"]]
        if "last_hp_regen_update" in index
        else None
    )

    now = datetime.now()
    now_iso = now.isoformat()
    last_dt = _parse_datetime(last_value)

    if last_dt is None:
        assignments = ["hp=?", "max_hp=?"]
        params = [current_hp, max_hp]
        if "last_hp_regen_update" in columns:
            assignments.append("last_hp_regen_update=?")
            params.append(now_iso)
        params.append(user_id)
        db.conn.execute(
            f"UPDATE users SET {', '.join(assignments)} WHERE user_id=?",
            tuple(params),
        )
        db.conn.commit()
        return {
            "success": True,
            "minutes": 0,
            "hp_restored": 0,
            "mp_restored": 0,
            "hp": current_hp,
            "max_hp": max_hp,
        }

    elapsed_seconds = max(0.0, (now - last_dt).total_seconds())
    elapsed_minutes = int(elapsed_seconds // 60)
    ticks = elapsed_minutes // HP_REGEN_MINUTES
    hp_restored = 0
    new_hp = current_hp

    if current_hp < max_hp and ticks > 0:
        heal_per_tick = max(1, int(round(max_hp * HP_REGEN_PERCENT)))
        hp_restored = min(max_hp - current_hp, heal_per_tick * ticks)
        new_hp = current_hp + hp_restored
        new_update = last_dt + timedelta(minutes=ticks * HP_REGEN_MINUTES)

        db.conn.execute(
            "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=?, "
            "hp_full_notified=0 WHERE user_id=?",
            (new_hp, max_hp, new_update.isoformat(), user_id),
        )
        db.conn.commit()

    elif current_hp >= max_hp:
        new_hp = max_hp
        db.conn.execute(
            "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=? "
            "WHERE user_id=?",
            (new_hp, max_hp, now_iso, user_id),
        )
        db.conn.commit()

    else:
        db.conn.execute(
            "UPDATE users SET hp=?, max_hp=? WHERE user_id=?",
            (new_hp, max_hp, user_id),
        )
        db.conn.commit()

    return {
        "success": True,
        "minutes": elapsed_minutes,
        "hp_restored": hp_restored,
        "mp_restored": 0,
        "hp": new_hp,
        "max_hp": max_hp,
    }


def apply_passive_mp_regen(user_id, *args, **kwargs):
    """Compatibility helper; current final runtime does not restore MP here."""
    result = process_passive_regeneration(user_id)
    return result.get("mp_restored", 0)


def process_hp_regeneration(user_id, *args, **kwargs):
    return apply_passive_hp_regen(user_id)


def process_mp_regeneration(user_id, *args, **kwargs):
    return apply_passive_mp_regen(user_id, *args, **kwargs)


def get_hp_regen_status(user_id):
    db = _db()
    init_hp_regen_system()
    _sync_max_hp(user_id)
    row = db.conn.execute(
        "SELECT hp, max_hp, last_hp_regen_update FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    if not row:
        return {"exists": False, "hp": 0, "max_hp": 0}
    return {
        "exists": True,
        "hp": int(row[0] or 0),
        "max_hp": int(row[1] or _dynamic_max_hp(user_id)),
        "last_hp_regen_update": row[2],
    }


def get_mp_regen_status(user_id):
    db = _db()
    mp_data = db.get_user_mp(user_id)
    if isinstance(mp_data, dict):
        return dict(mp_data)
    return {"mp": int(mp_data or 0), "max_mp": int(db.get_max_mp(user_id) or 0)}