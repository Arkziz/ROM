from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "9_0_12f1_equipment_readonly_core_real_implementation"
TARGET_NAMES = (
    "ensure_equipment_slots",
    "get_all_equipped_items",
    "get_item_bonuses",
    "get_equipped_item_defenses",
)


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    path = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return path


IMPLEMENTATION = r"""

# ==============================
# ROM 9.0.12f1 EQUIPMENT READ-ONLY CORE REAL IMPLEMENTATION V1
# ==============================

_EQUIPMENT_SLOT_ORDER_REAL_V1 = (
    "main_hand", "off_hand", "helmet", "shoulders", "chest",
    "gloves", "legs", "boots", "necklace", "ring",
)


def _equipment_real_db_v1():
    import db as _db_module
    return _db_module


def ensure_equipment_slots(user_id):
    db = _equipment_real_db_v1()
    db.conn.execute(
        """
        CREATE TABLE IF NOT EXISTS equipment_slots (
            user_id INTEGER NOT NULL,
            slot_key TEXT NOT NULL,
            inventory_id INTEGER,
            PRIMARY KEY (user_id, slot_key)
        )
        """
    )
    for slot_key in _EQUIPMENT_SLOT_ORDER_REAL_V1:
        db.conn.execute(
            """
            INSERT OR IGNORE INTO equipment_slots (user_id, slot_key, inventory_id)
            VALUES (?, ?, NULL)
            """,
            (int(user_id), slot_key),
        )
    db.conn.commit()
    return True


def _equipment_slot_rows_real_v1(user_id):
    ensure_equipment_slots(user_id)
    db = _equipment_real_db_v1()
    return db.conn.execute(
        """
        SELECT slot_key, inventory_id
        FROM equipment_slots
        WHERE user_id=?
        ORDER BY CASE slot_key
            WHEN 'main_hand' THEN 1 WHEN 'off_hand' THEN 2
            WHEN 'helmet' THEN 3 WHEN 'shoulders' THEN 4
            WHEN 'chest' THEN 5 WHEN 'gloves' THEN 6
            WHEN 'legs' THEN 7 WHEN 'boots' THEN 8
            WHEN 'necklace' THEN 9 WHEN 'ring' THEN 10
            ELSE 99 END
        """,
        (int(user_id),),
    ).fetchall()


def get_all_equipped_items(user_id):
    db = _equipment_real_db_v1()
    result = []
    for _slot_key, inventory_id in _equipment_slot_rows_real_v1(user_id):
        if inventory_id is None:
            continue
        item = db.get_item_by_inventory_id_full(int(inventory_id))
        if item is not None:
            result.append(item)
    return result


def _equipment_unpack_stats_real_v1(item):
    if isinstance(item, dict):
        return {
            "durability": item.get("durability", item.get("inv_durability", 100)),
            "str": item.get("bonus_str", item.get("item_bonus_str", 0)),
            "dex": item.get("bonus_dex", item.get("item_bonus_dex", 0)),
            "int": item.get("bonus_int", item.get("item_bonus_int", 0)),
            "wis": item.get("bonus_wis", item.get("item_bonus_wis", 0)),
            "sta": item.get("bonus_sta", item.get("item_bonus_sta", 0)),
            "pdef": item.get("pdef", item.get("item_pdef", 0)),
            "mdef": item.get("mdef", item.get("item_mdef", 0)),
        }

    if isinstance(item, (tuple, list)):
        # Current full item contract:
        # 0 inv_id, 1 item_id, 2 name, 3 type, 4 rarity, 5 category,
        # 6 slot, 7 hands, 8 qty, 9 max_stack, 10 durability,
        # 11..15 primary bonuses, 16 pdef, 17 mdef.
        values = list(item)
        def at(index, default=0):
            return values[index] if len(values) > index else default
        return {
            "durability": at(10, 100),
            "str": at(11), "dex": at(12), "int": at(13),
            "wis": at(14), "sta": at(15),
            "pdef": at(16), "mdef": at(17),
        }

    return {
        "durability": 0, "str": 0, "dex": 0, "int": 0,
        "wis": 0, "sta": 0, "pdef": 0, "mdef": 0,
    }


def get_item_bonuses(user_id):
    totals = {"str": 0, "dex": 0, "int": 0, "wis": 0, "sta": 0}
    for item in get_all_equipped_items(user_id):
        stats = _equipment_unpack_stats_real_v1(item)
        try:
            durability = int(stats.get("durability", 100) or 0)
        except Exception:
            durability = 0
        if durability <= 0:
            continue
        for key in totals:
            try:
                totals[key] += int(stats.get(key, 0) or 0)
            except Exception:
                pass
    return totals["str"], totals["dex"], totals["int"], totals["wis"], totals["sta"]


def get_equipped_item_defenses(user_id):
    pdef = 0
    mdef = 0
    for item in get_all_equipped_items(user_id):
        stats = _equipment_unpack_stats_real_v1(item)
        try:
            durability = int(stats.get("durability", 100) or 0)
        except Exception:
            durability = 0
        if durability <= 0:
            continue
        try:
            pdef += int(stats.get("pdef", 0) or 0)
        except Exception:
            pass
        try:
            mdef += int(stats.get("mdef", 0) or 0)
        except Exception:
            pass
    return pdef, mdef
"""


SMOKE_TEST = r"""from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

row = db.conn.execute("SELECT user_id FROM users ORDER BY user_id LIMIT 1").fetchone()
if not row:
    raise SystemExit("[SKIP] no users")
uid = int(row[0])

assert db.ensure_equipment_slots(uid) is True
items = db.get_all_equipped_items(uid)
bonuses = db.get_item_bonuses(uid)
defenses = db.get_equipped_item_defenses(uid)

assert isinstance(items, list), type(items)
assert isinstance(bonuses, tuple) and len(bonuses) == 5, bonuses
assert isinstance(defenses, tuple) and len(defenses) == 2, defenses

print("[OK] equipment read-only core runtime contracts")
print("- equipped count:", len(items))
print("- bonuses:", bonuses)
print("- defenses:", defenses)
"""


def remove_capture(text, name):
    pattern = re.compile(
        r"try:\n"
        rf"\s*_legacy_equipment_ro_v1_{re.escape(name)}\n"
        r"except NameError:\n"
        rf"\s*_legacy_equipment_ro_v1_{re.escape(name)}\s*=\s*{re.escape(name)}\n"
    )
    return pattern.sub("", text)


def main():
    root = Path(__file__).resolve().parents[1]
    db_path = root / "db.py"
    equipment_path = root / "systems" / "equipment_system.py"
    smoke_path = root / "tools" / "smoke_test_equipment_readonly_core.py"

    if not db_path.exists() or not equipment_path.exists():
        raise SystemExit("Missing db.py or systems/equipment_system.py")

    db_original = db_path.read_text(encoding="utf-8")
    equipment_original = equipment_path.read_text(encoding="utf-8")
    backups = [make_backup(root, db_path), make_backup(root, equipment_path)]

    try:
        equipment_new = equipment_original
        if "ROM 9.0.12f1 EQUIPMENT READ-ONLY CORE REAL IMPLEMENTATION V1" not in equipment_new:
            equipment_new = equipment_new.rstrip() + "\n" + IMPLEMENTATION + "\n"

        db_new = db_original
        for name in TARGET_NAMES:
            db_new = remove_capture(db_new, name)

        equipment_path.write_text(equipment_new, encoding="utf-8")
        db_path.write_text(db_new, encoding="utf-8")
        smoke_path.write_text(SMOKE_TEST, encoding="utf-8")

        py_compile.compile(str(equipment_path), doraise=True)
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(smoke_path), doraise=True)
    except Exception as error:
        equipment_path.write_text(equipment_original, encoding="utf-8")
        db_path.write_text(db_original, encoding="utf-8")
        raise SystemExit(f"Patch failed; files restored. Error: {error}")

    print("Patch 9.0.12f1 applied successfully.")
    print("Direct read-only core: slots, equipped items, bonuses, defenses.")
    print("Refine-sensitive inventory display and weapon damage remain legacy for now.")
    print("Backup:")
    for path in backups:
        print("-", path)
    print("Checks:")
    print("python -m py_compile .\systems\equipment_system.py")
    print("python -m py_compile .\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/smoke_test_equipment_readonly_core.py")
    print("python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
