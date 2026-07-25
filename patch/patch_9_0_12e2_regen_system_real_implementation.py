from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12e2_regen_system_real_implementation"

REGEN_MODULE = '"""\nROM Regen System\n================\n\nReal implementation introduced in refactor 9.0.12e2.\n\ndb.py remains the public compatibility facade, while the regeneration logic\nlives here and no longer delegates to _legacy_regen_v1_* references.\n\nImportant rules preserved:\n- dynamic max HP from equipment/refine is respected;\n- equipping or refining armor does not heal immediately;\n- passive regeneration heals only after a completed tick;\n- current HP is clamped if max HP decreases;\n- notification worker remains self-contained in systems/notifications.py;\n- 0/40 fatigue logic belongs to systems/energy_system.py and is not changed.\n"""\n\nfrom datetime import datetime, timedelta\n\nHP_REGEN_PERCENT = 0.10\nHP_REGEN_MINUTES = 1\n\n\ndef _db():\n    import db\n    return db\n\n\ndef _table_columns(table_name):\n    db = _db()\n    try:\n        rows = db.conn.execute(f"PRAGMA table_info({table_name})").fetchall()\n        return {row[1] for row in rows}\n    except Exception:\n        return set()\n\n\ndef _parse_datetime(value):\n    if not value:\n        return None\n    try:\n        return datetime.fromisoformat(str(value))\n    except Exception:\n        return None\n\n\ndef _dynamic_max_hp(user_id):\n    db = _db()\n    try:\n        return max(1, int(db.get_max_hp(user_id) or 1))\n    except Exception:\n        row = db.conn.execute(\n            "SELECT max_hp FROM users WHERE user_id=?",\n            (user_id,),\n        ).fetchone()\n        return max(1, int((row[0] if row else 1) or 1))\n\n\ndef _sync_max_hp(user_id):\n    db = _db()\n    sync = getattr(db, "sync_user_max_hp", None)\n    if sync:\n        try:\n            return sync(user_id, heal_to_full=False)\n        except TypeError:\n            return sync(user_id)\n        except Exception:\n            pass\n\n    max_hp = _dynamic_max_hp(user_id)\n    row = db.conn.execute(\n        "SELECT hp FROM users WHERE user_id=?",\n        (user_id,),\n    ).fetchone()\n    if not row:\n        return {"success": False, "hp": 0, "max_hp": max_hp}\n\n    current_hp = int(row[0] or 0)\n    clamped_hp = min(current_hp, max_hp)\n    db.conn.execute(\n        "UPDATE users SET hp=?, max_hp=? WHERE user_id=?",\n        (clamped_hp, max_hp, user_id),\n    )\n    db.conn.commit()\n    return {\n        "success": True,\n        "hp": clamped_hp,\n        "max_hp": max_hp,\n        "changed": clamped_hp != current_hp,\n    }\n\n\ndef init_hp_regen_system():\n    db = _db()\n    migrations = [\n        ("users", "last_hp_regen_update", "TEXT DEFAULT \'\'"),\n        ("users", "hp_full_notified", "INTEGER DEFAULT 1"),\n        ("users", "daily_hunts", "INTEGER DEFAULT 0"),\n        ("users", "daily_hunts_date", "TEXT DEFAULT \'\'"),\n    ]\n\n    columns = _table_columns("users")\n    for table, column, column_type in migrations:\n        if column in columns:\n            continue\n        try:\n            db.conn.execute(\n                f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"\n            )\n        except Exception:\n            pass\n    db.conn.commit()\n    return True\n\n\ndef init_passive_regen_system():\n    db = _db()\n    columns = _table_columns("users")\n    if "last_regen_at" not in columns:\n        try:\n            db.conn.execute(\n                "ALTER TABLE users ADD COLUMN last_regen_at TEXT DEFAULT \'\'"\n            )\n        except Exception:\n            pass\n    db.conn.commit()\n    return True\n\n\ndef reset_hp_regen_timers_now(user_id):\n    db = _db()\n    init_hp_regen_system()\n    init_passive_regen_system()\n    now_iso = datetime.now().isoformat()\n    columns = _table_columns("users")\n\n    assignments = []\n    params = []\n    if "last_hp_regen_update" in columns:\n        assignments.append("last_hp_regen_update=?")\n        params.append(now_iso)\n    if "last_regen_at" in columns:\n        assignments.append("last_regen_at=?")\n        params.append(now_iso)\n\n    if assignments:\n        params.append(user_id)\n        db.conn.execute(\n            f"UPDATE users SET {\', \'.join(assignments)} WHERE user_id=?",\n            tuple(params),\n        )\n        db.conn.commit()\n\n    _sync_max_hp(user_id)\n    return True\n\n\ndef apply_passive_hp_regen(user_id):\n    """Apply the historical 10% max-HP regeneration tick contract."""\n    db = _db()\n    init_hp_regen_system()\n    _sync_max_hp(user_id)\n\n    row = db.conn.execute(\n        "SELECT hp, last_hp_regen_update FROM users WHERE user_id=?",\n        (user_id,),\n    ).fetchone()\n    if not row:\n        return 0\n\n    max_hp = _dynamic_max_hp(user_id)\n    hp = max_hp if row[0] is None else int(row[0] or 0)\n    hp = min(hp, max_hp)\n    last_update = row[1]\n    now = datetime.now()\n\n    last_dt = _parse_datetime(last_update)\n    if last_dt is None:\n        db.conn.execute(\n            "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=? "\n            "WHERE user_id=?",\n            (hp, max_hp, now.isoformat(), user_id),\n        )\n        db.conn.commit()\n        return hp\n\n    if hp >= max_hp:\n        db.conn.execute(\n            "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=?, "\n            "hp_full_notified=1 WHERE user_id=?",\n            (max_hp, max_hp, now.isoformat(), user_id),\n        )\n        db.conn.commit()\n        return max_hp\n\n    diff_seconds = max(0.0, (now - last_dt).total_seconds())\n    ticks = int(diff_seconds // (HP_REGEN_MINUTES * 60))\n    if ticks <= 0:\n        db.conn.execute(\n            "UPDATE users SET max_hp=? WHERE user_id=?",\n            (max_hp, user_id),\n        )\n        db.conn.commit()\n        return hp\n\n    heal_per_tick = max(1, int(max_hp * HP_REGEN_PERCENT))\n    new_hp = min(max_hp, hp + heal_per_tick * ticks)\n    new_update = last_dt + timedelta(minutes=ticks * HP_REGEN_MINUTES)\n\n    # Keep 0 when the player just reached full HP so the notification worker\n    # can send the single full-health notification and then mark it as sent.\n    notified = 0\n    db.conn.execute(\n        "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=?, "\n        "hp_full_notified=? WHERE user_id=?",\n        (new_hp, max_hp, new_update.isoformat(), notified, user_id),\n    )\n    db.conn.commit()\n    return new_hp\n\n\ndef process_passive_regeneration(user_id):\n    """\n    Dynamic-max-HP-safe passive regeneration contract used by existing code.\n\n    This preserves the final runtime behavior that existed before extraction:\n    HP regeneration is processed from last_hp_regen_update and returns a dict.\n    MP is left unchanged here because current combat/class flows manage MP via\n    character_system and the historical final override returned mp_restored=0.\n    """\n    db = _db()\n    init_hp_regen_system()\n    _sync_max_hp(user_id)\n\n    columns = _table_columns("users")\n    select_columns = ["hp"]\n    if "max_hp" in columns:\n        select_columns.append("max_hp")\n    if "last_hp_regen_update" in columns:\n        select_columns.append("last_hp_regen_update")\n\n    row = db.conn.execute(\n        f"SELECT {\', \'.join(select_columns)} FROM users WHERE user_id=?",\n        (user_id,),\n    ).fetchone()\n    if not row:\n        return {\n            "success": False,\n            "minutes": 0,\n            "hp_restored": 0,\n            "mp_restored": 0,\n        }\n\n    index = {name: i for i, name in enumerate(select_columns)}\n    max_hp = _dynamic_max_hp(user_id)\n    current_hp = int(row[index["hp"]] or 0)\n    current_hp = min(current_hp, max_hp)\n    last_value = (\n        row[index["last_hp_regen_update"]]\n        if "last_hp_regen_update" in index\n        else None\n    )\n\n    now = datetime.now()\n    now_iso = now.isoformat()\n    last_dt = _parse_datetime(last_value)\n\n    if last_dt is None:\n        assignments = ["hp=?", "max_hp=?"]\n        params = [current_hp, max_hp]\n        if "last_hp_regen_update" in columns:\n            assignments.append("last_hp_regen_update=?")\n            params.append(now_iso)\n        params.append(user_id)\n        db.conn.execute(\n            f"UPDATE users SET {\', \'.join(assignments)} WHERE user_id=?",\n            tuple(params),\n        )\n        db.conn.commit()\n        return {\n            "success": True,\n            "minutes": 0,\n            "hp_restored": 0,\n            "mp_restored": 0,\n            "hp": current_hp,\n            "max_hp": max_hp,\n        }\n\n    elapsed_seconds = max(0.0, (now - last_dt).total_seconds())\n    elapsed_minutes = int(elapsed_seconds // 60)\n    ticks = elapsed_minutes // HP_REGEN_MINUTES\n    hp_restored = 0\n    new_hp = current_hp\n\n    if current_hp < max_hp and ticks > 0:\n        heal_per_tick = max(1, int(round(max_hp * HP_REGEN_PERCENT)))\n        hp_restored = min(max_hp - current_hp, heal_per_tick * ticks)\n        new_hp = current_hp + hp_restored\n        new_update = last_dt + timedelta(minutes=ticks * HP_REGEN_MINUTES)\n\n        db.conn.execute(\n            "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=?, "\n            "hp_full_notified=0 WHERE user_id=?",\n            (new_hp, max_hp, new_update.isoformat(), user_id),\n        )\n        db.conn.commit()\n\n    elif current_hp >= max_hp:\n        new_hp = max_hp\n        db.conn.execute(\n            "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=? "\n            "WHERE user_id=?",\n            (new_hp, max_hp, now_iso, user_id),\n        )\n        db.conn.commit()\n\n    else:\n        db.conn.execute(\n            "UPDATE users SET hp=?, max_hp=? WHERE user_id=?",\n            (new_hp, max_hp, user_id),\n        )\n        db.conn.commit()\n\n    return {\n        "success": True,\n        "minutes": elapsed_minutes,\n        "hp_restored": hp_restored,\n        "mp_restored": 0,\n        "hp": new_hp,\n        "max_hp": max_hp,\n    }\n\n\ndef apply_passive_mp_regen(user_id, *args, **kwargs):\n    """Compatibility helper; current final runtime does not restore MP here."""\n    result = process_passive_regeneration(user_id)\n    return result.get("mp_restored", 0)\n\n\ndef process_hp_regeneration(user_id, *args, **kwargs):\n    return apply_passive_hp_regen(user_id)\n\n\ndef process_mp_regeneration(user_id, *args, **kwargs):\n    return apply_passive_mp_regen(user_id, *args, **kwargs)\n\n\ndef get_hp_regen_status(user_id):\n    db = _db()\n    init_hp_regen_system()\n    _sync_max_hp(user_id)\n    row = db.conn.execute(\n        "SELECT hp, max_hp, last_hp_regen_update FROM users WHERE user_id=?",\n        (user_id,),\n    ).fetchone()\n    if not row:\n        return {"exists": False, "hp": 0, "max_hp": 0}\n    return {\n        "exists": True,\n        "hp": int(row[0] or 0),\n        "max_hp": int(row[1] or _dynamic_max_hp(user_id)),\n        "last_hp_regen_update": row[2],\n    }\n\n\ndef get_mp_regen_status(user_id):\n    db = _db()\n    mp_data = db.get_user_mp(user_id)\n    if isinstance(mp_data, dict):\n        return dict(mp_data)\n    return {"mp": int(mp_data or 0), "max_mp": int(db.get_max_mp(user_id) or 0)}'

DB_FACADE = '# ==============================\n# ✅ ROM 9.0.12e2 REGEN SYSTEM REAL IMPLEMENTATION WRAPPERS V2\n# ==============================\n\ndef _regen_system_v2():\n    from systems import regen_system as _mod\n    return _mod\n\n\ndef init_hp_regen_system(*args, **kwargs):\n    return _regen_system_v2().init_hp_regen_system(*args, **kwargs)\n\n\ndef init_passive_regen_system(*args, **kwargs):\n    return _regen_system_v2().init_passive_regen_system(*args, **kwargs)\n\n\ndef process_passive_regeneration(*args, **kwargs):\n    return _regen_system_v2().process_passive_regeneration(*args, **kwargs)\n\n\ndef reset_hp_regen_timers_now(*args, **kwargs):\n    return _regen_system_v2().reset_hp_regen_timers_now(*args, **kwargs)\n\n\ndef apply_passive_hp_regen(*args, **kwargs):\n    return _regen_system_v2().apply_passive_hp_regen(*args, **kwargs)'

SMOKE_TEST = 'from pathlib import Path\nimport sys\n\nROOT = Path(__file__).resolve().parents[1]\nif str(ROOT) not in sys.path:\n    sys.path.insert(0, str(ROOT))\n\nimport db\n\nrow = db.conn.execute(\n    "SELECT user_id FROM users ORDER BY user_id LIMIT 1"\n).fetchone()\nif not row:\n    print("[SKIP] no users found for regen contract smoke-test")\n    raise SystemExit(0)\n\nuser_id = int(row[0])\n\nassert db.init_hp_regen_system() in (True, None)\nassert db.init_passive_regen_system() in (True, None)\n\nbefore_hp = db.get_current_hp_raw(user_id)\nmax_hp = db.get_max_hp(user_id)\nresult = db.process_passive_regeneration(user_id)\nafter_hp = db.get_current_hp_raw(user_id)\n\nassert isinstance(before_hp, int), type(before_hp)\nassert isinstance(max_hp, int), type(max_hp)\nassert isinstance(result, dict), type(result)\nassert isinstance(after_hp, int), type(after_hp)\nassert 0 <= after_hp <= max_hp, (after_hp, max_hp)\nfor key in ("success", "minutes", "hp_restored", "mp_restored"):\n    assert key in result, (key, result)\n\nprint("[OK] regen runtime contracts")\nprint("- before:", before_hp, "/", max_hp)\nprint("- after:", after_hp, "/", db.get_max_hp(user_id))\nprint("- result:", result)'

def backup(root, path):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(path.relative_to(root)).replace("\\", "_").replace("/", "_")
    dst = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    dst.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return dst


def replace_between(text, start_marker, end_marker, replacement):
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker)) if start >= 0 else -1
    if start < 0 or end < 0:
        return None
    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]


def main():
    root = Path(__file__).resolve().parents[1]
    db_path = root / "db.py"
    regen_path = root / "systems" / "regen_system.py"
    smoke_path = root / "tools" / "smoke_test_regen_contracts.py"

    for path in (db_path, regen_path):
        if not path.exists():
            raise SystemExit(f"Missing required file: {path}")

    old_db = db_path.read_text(encoding="utf-8")
    old_regen = regen_path.read_text(encoding="utf-8")
    backups = [backup(root, db_path), backup(root, regen_path)]

    start_marker = "# ✅ REFACTOR 9.0.5: REGEN SYSTEM FACADE"
    end_marker = "# ✅ REFACTOR 9.0.6: EQUIPMENT SYSTEM READONLY FACADE"
    new_db = replace_between(old_db, start_marker, end_marker, DB_FACADE)
    if new_db is None:
        raise SystemExit(
            "Could not locate the 9.0.5 regen facade block in db.py. "
            "No files were modified."
        )

    try:
        regen_path.write_text(REGEN_MODULE, encoding="utf-8")
        db_path.write_text(new_db, encoding="utf-8")
        smoke_path.write_text(SMOKE_TEST, encoding="utf-8")

        py_compile.compile(str(regen_path), doraise=True)
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(smoke_path), doraise=True)

        # Import/runtime sanity in a fresh subprocess-like compile scope is
        # performed by the user commands after patching. Here we verify the
        # removed legacy capture names are absent from the new module.
        new_regen_text = regen_path.read_text(encoding="utf-8")
        if "_call_legacy(" in new_regen_text or "getattr(db, legacy_name" in new_regen_text:
            raise RuntimeError("active legacy regen delegation remains in regen_system.py")

    except Exception as exc:
        db_path.write_text(old_db, encoding="utf-8")
        regen_path.write_text(old_regen, encoding="utf-8")
        raise SystemExit(f"Patch failed; source files restored. Error: {exc}")

    print("Patch 9.0.12e2 applied successfully.")
    print("Regen logic now lives in systems/regen_system.py without legacy delegation.")
    print("systems/notifications.py was not modified.")
    print("Backup:")
    for item in backups:
        print(f"- {item}")
    print("Checks:")
    print(r"python -m py_compile .\systems\regen_system.py")
    print(r"python -m py_compile .\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/smoke_test_regen_contracts.py")
    print("python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
