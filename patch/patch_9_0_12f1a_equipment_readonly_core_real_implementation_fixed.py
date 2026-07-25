from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12f1a_equipment_readonly_core_real_implementation_fixed"
MARKER = "# ROM 9.0.12f1a EQUIPMENT READ-ONLY CORE REAL IMPLEMENTATION"
EQUIPMENT_CODE = '\n\n# ==============================\n# ROM 9.0.12f1a EQUIPMENT READ-ONLY CORE REAL IMPLEMENTATION\n# ==============================\n\n_EQUIPMENT_SLOT_ORDER_REAL_V1 = (\n    "main_hand", "off_hand", "helmet", "shoulders", "chest",\n    "gloves", "legs", "boots", "necklace", "ring",\n)\n\n\ndef _equipment_real_db_v1():\n    import db as _db_module\n    return _db_module\n\n\ndef ensure_equipment_slots(user_id):\n    db = _equipment_real_db_v1()\n    uid = int(user_id)\n    db.conn.execute(\n        "CREATE TABLE IF NOT EXISTS equipment_slots ("\n        "user_id INTEGER NOT NULL, "\n        "slot_key TEXT NOT NULL, "\n        "inventory_id INTEGER, "\n        "PRIMARY KEY (user_id, slot_key))"\n    )\n    for slot_key in _EQUIPMENT_SLOT_ORDER_REAL_V1:\n        db.conn.execute(\n            "INSERT OR IGNORE INTO equipment_slots "\n            "(user_id, slot_key, inventory_id) VALUES (?, ?, NULL)",\n            (uid, slot_key),\n        )\n    db.conn.commit()\n    return True\n\n\ndef _equipment_slot_rows_real_v1(user_id):\n    ensure_equipment_slots(user_id)\n    db = _equipment_real_db_v1()\n    return db.conn.execute(\n        "SELECT slot_key, inventory_id FROM equipment_slots "\n        "WHERE user_id=? ORDER BY CASE slot_key "\n        "WHEN \'main_hand\' THEN 1 WHEN \'off_hand\' THEN 2 "\n        "WHEN \'helmet\' THEN 3 WHEN \'shoulders\' THEN 4 "\n        "WHEN \'chest\' THEN 5 WHEN \'gloves\' THEN 6 "\n        "WHEN \'legs\' THEN 7 WHEN \'boots\' THEN 8 "\n        "WHEN \'necklace\' THEN 9 WHEN \'ring\' THEN 10 ELSE 99 END",\n        (int(user_id),),\n    ).fetchall()\n\n\ndef get_all_equipped_items(user_id):\n    db = _equipment_real_db_v1()\n    result = []\n    for _slot_key, inventory_id in _equipment_slot_rows_real_v1(user_id):\n        if inventory_id is None:\n            continue\n        item = db.get_item_by_inventory_id_full(int(inventory_id))\n        if item is not None:\n            result.append(item)\n    return result\n\n\ndef _equipment_aggregate_row_real_v1(user_id):\n    db = _equipment_real_db_v1()\n    ensure_equipment_slots(user_id)\n    return db.conn.execute(\n        "SELECT "\n        "COALESCE(SUM(CASE WHEN COALESCE(inv.durability,100)>0 THEN COALESCE(it.bonus_str,0) ELSE 0 END),0), "\n        "COALESCE(SUM(CASE WHEN COALESCE(inv.durability,100)>0 THEN COALESCE(it.bonus_dex,0) ELSE 0 END),0), "\n        "COALESCE(SUM(CASE WHEN COALESCE(inv.durability,100)>0 THEN COALESCE(it.bonus_int,0) ELSE 0 END),0), "\n        "COALESCE(SUM(CASE WHEN COALESCE(inv.durability,100)>0 THEN COALESCE(it.bonus_wis,0) ELSE 0 END),0), "\n        "COALESCE(SUM(CASE WHEN COALESCE(inv.durability,100)>0 THEN COALESCE(it.bonus_sta,0) ELSE 0 END),0), "\n        "COALESCE(SUM(CASE WHEN COALESCE(inv.durability,100)>0 THEN COALESCE(it.pdef,0) ELSE 0 END),0), "\n        "COALESCE(SUM(CASE WHEN COALESCE(inv.durability,100)>0 THEN COALESCE(it.mdef,0) ELSE 0 END),0) "\n        "FROM equipment_slots es "\n        "LEFT JOIN inventory inv ON inv.id=es.inventory_id "\n        "LEFT JOIN items it ON it.id=inv.item_id "\n        "WHERE es.user_id=?",\n        (int(user_id),),\n    ).fetchone()\n\n\ndef get_item_bonuses(user_id):\n    row = _equipment_aggregate_row_real_v1(user_id)\n    if not row:\n        return 0, 0, 0, 0, 0\n    return tuple(int(value or 0) for value in row[:5])\n\n\ndef get_equipped_item_defenses(user_id):\n    row = _equipment_aggregate_row_real_v1(user_id)\n    if not row:\n        return 0, 0\n    return int(row[5] or 0), int(row[6] or 0)\n'
SMOKE_TEST = 'from pathlib import Path\nimport sys\n\nROOT = Path(__file__).resolve().parents[1]\nif str(ROOT) not in sys.path:\n    sys.path.insert(0, str(ROOT))\n\nimport db\n\nrow = db.conn.execute("SELECT user_id FROM users ORDER BY user_id LIMIT 1").fetchone()\nif not row:\n    raise SystemExit("[SKIP] no users")\nuid = int(row[0])\n\nassert db.ensure_equipment_slots(uid) is True\nitems = db.get_all_equipped_items(uid)\nbonuses = db.get_item_bonuses(uid)\ndefenses = db.get_equipped_item_defenses(uid)\nassert isinstance(items, list), type(items)\nassert isinstance(bonuses, tuple) and len(bonuses) == 5, bonuses\nassert all(isinstance(v, int) for v in bonuses), bonuses\nassert isinstance(defenses, tuple) and len(defenses) == 2, defenses\nassert all(isinstance(v, int) for v in defenses), defenses\nprint("[OK] equipment read-only core runtime contracts")\nprint("- equipped count:", len(items))\nprint("- bonuses:", bonuses)\nprint("- defenses:", defenses)\n'


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    path = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def main():
    root = Path(__file__).resolve().parents[1]
    equipment_path = root / "systems" / "equipment_system.py"
    db_path = root / "db.py"
    smoke_path = root / "tools" / "smoke_test_equipment_readonly_core.py"
    if not equipment_path.exists():
        raise SystemExit(f"ERROR: file not found: {equipment_path}")
    if not db_path.exists():
        raise SystemExit(f"ERROR: file not found: {db_path}")

    equipment_original = equipment_path.read_text(encoding="utf-8")
    backups = []
    try:
        if MARKER not in equipment_original:
            backups.append(make_backup(root, equipment_path))
            equipment_path.write_text(equipment_original.rstrip() + "\n" + EQUIPMENT_CODE + "\n", encoding="utf-8")
        else:
            print("INFO: equipment implementation already present")
        smoke_path.parent.mkdir(exist_ok=True)
        if smoke_path.exists():
            backups.append(make_backup(root, smoke_path))
        smoke_path.write_text(SMOKE_TEST, encoding="utf-8")
        py_compile.compile(str(equipment_path), doraise=True)
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(smoke_path), doraise=True)
    except Exception as error:
        equipment_path.write_text(equipment_original, encoding="utf-8")
        raise SystemExit(f"ERROR: patch failed; equipment file restored.\n{error}")

    print("Patch 9.0.12f1a applied successfully.")
    print("Equipment read-only core now has direct SQL implementations.")
    print("Backup:")
    for path in backups:
        print(f"- {path}")
    print("Checks:")
    print(r"python -m py_compile .\systems\equipment_system.py")
    print(r"python -m py_compile .\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/smoke_test_equipment_readonly_core.py")
    print("python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
