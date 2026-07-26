from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12f2_inventory_refine_readonly_real_implementation"
TARGET_RELATIVE_PATH = Path("systems") / "equipment_system.py"
SMOKE_RELATIVE_PATH = Path("tools") / "smoke_test_inventory_refine_contracts.py"
MARKER = "# ROM 9.0.12f2 INVENTORY REFINE READ-ONLY REAL IMPLEMENTATION"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def build_equipment_code():
    return r'''

# ==============================
# ROM 9.0.12f2 INVENTORY REFINE READ-ONLY REAL IMPLEMENTATION
# ==============================

import re as _inventory_refine_re_v3


def _inventory_refine_db_v3():
    import db as _db_module
    return _db_module


def _inventory_refine_level_v3(inventory_id):
    db = _inventory_refine_db_v3()
    row = db.conn.execute(
        "SELECT COALESCE(refine_level, 0) FROM inventory WHERE id=?",
        (int(inventory_id),),
    ).fetchone()
    if not row:
        return 0
    try:
        return max(0, int(row[0] or 0))
    except Exception:
        return 0


def strip_refine_suffix_from_name(name):
    value = str(name or "").strip()
    return _inventory_refine_re_v3.sub(r"\s*\[\+\d+\]\s*$", "", value).strip()


def format_refined_item_name(name, refine_level):
    base_name = strip_refine_suffix_from_name(name)
    try:
        level = max(0, int(refine_level or 0))
    except Exception:
        level = 0
    return base_name if level <= 0 else f"{base_name} [+{level}]"


def get_inventory_refine_level(inventory_id):
    return _inventory_refine_level_v3(inventory_id)


def get_inventory_refined_display_name(inventory_id, name=None):
    db = _inventory_refine_db_v3()
    if name is None:
        row = db.conn.execute(
            "SELECT it.name FROM inventory inv JOIN items it ON it.id=inv.item_id WHERE inv.id=?",
            (int(inventory_id),),
        ).fetchone()
        if not row:
            return ""
        name = row[0]
    return format_refined_item_name(name, _inventory_refine_level_v3(inventory_id))


def _inventory_read_rows_v3(user_id=None, inventory_id=None, full=False, short=False):
    db = _inventory_refine_db_v3()

    if short:
        select_sql = (
            "SELECT inv.id, inv.item_id, it.name, it.type, it.category, "
            "COALESCE(inv.quantity,1), COALESCE(inv.refine_level,0) "
        )
    elif full:
        select_sql = (
            "SELECT inv.id, inv.item_id, it.name, it.type, it.rarity, it.category, "
            "it.slot_key, COALESCE(it.weapon_hands,1), COALESCE(inv.quantity,1), "
            "COALESCE(it.max_stack,1), COALESCE(inv.durability,100), "
            "COALESCE(it.bonus_str,0), COALESCE(it.bonus_dex,0), "
            "COALESCE(it.bonus_int,0), COALESCE(it.bonus_wis,0), "
            "COALESCE(it.bonus_sta,0), COALESCE(it.pdef,0), COALESCE(it.mdef,0), "
            "COALESCE(it.sell_price,0), COALESCE(inv.refine_level,0) "
        )
    else:
        select_sql = (
            "SELECT inv.id, inv.item_id, it.name, it.type, it.rarity, it.category, "
            "COALESCE(inv.quantity,1), COALESCE(it.max_stack,1), "
            "COALESCE(inv.durability,100), COALESCE(it.bonus_str,0), "
            "COALESCE(it.bonus_dex,0), COALESCE(it.bonus_int,0), "
            "COALESCE(it.bonus_wis,0), COALESCE(it.bonus_sta,0), "
            "COALESCE(it.pdef,0), COALESCE(it.mdef,0), COALESCE(it.sell_price,0), "
            "COALESCE(inv.refine_level,0) "
        )

    sql = select_sql + "FROM inventory inv JOIN items it ON it.id=inv.item_id "
    params = []
    where = []
    if user_id is not None:
        where.append("inv.user_id=?")
        params.append(int(user_id))
    if inventory_id is not None:
        where.append("inv.id=?")
        params.append(int(inventory_id))
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "ORDER BY inv.id ASC"
    return db.conn.execute(sql, tuple(params)).fetchall()


def _apply_refine_name_to_row_v3(row, name_index=2, refine_index=-1):
    if row is None:
        return None
    values = list(row)
    values[name_index] = format_refined_item_name(values[name_index], values[refine_index])
    del values[refine_index]
    return tuple(values)


def get_inventory_detailed(user_id):
    """Return the historical 17-field inventory tuple list with refined names."""
    rows = _inventory_read_rows_v3(user_id=user_id, full=False, short=False)
    return [_apply_refine_name_to_row_v3(row) for row in rows]


def get_item_by_inventory_id(inventory_id):
    """Return the historical 17-field inventory tuple with refined name."""
    rows = _inventory_read_rows_v3(inventory_id=inventory_id, full=False, short=False)
    return _apply_refine_name_to_row_v3(rows[0]) if rows else None


def get_item_by_inventory_id_full(inventory_id):
    """Return the historical 19-field full item tuple with refined name."""
    rows = _inventory_read_rows_v3(inventory_id=inventory_id, full=True, short=False)
    return _apply_refine_name_to_row_v3(rows[0]) if rows else None


def get_inventory_entry(user_id, inventory_id):
    """Return the historical 6-field short inventory tuple with refined name."""
    rows = _inventory_read_rows_v3(
        user_id=user_id,
        inventory_id=inventory_id,
        full=False,
        short=True,
    )
    return _apply_refine_name_to_row_v3(rows[0]) if rows else None
'''


def build_smoke_test():
    return r'''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

USER_ID = 243129101


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    inventory = db.get_inventory_detailed(USER_ID)
    require(isinstance(inventory, list), "get_inventory_detailed must return list")

    print("[OK] inventory/refine read-only runtime contracts")
    print("- inventory rows:", len(inventory))

    if not inventory:
        print("- no inventory rows available for deeper contract checks")
        return 0

    row = inventory[0]
    require(isinstance(row, tuple), "inventory row must be tuple")
    require(len(row) == 17, f"inventory row must have 17 fields, got {len(row)}")

    inventory_id = row[0]
    item = db.get_item_by_inventory_id(inventory_id)
    full = db.get_item_by_inventory_id_full(inventory_id)
    entry = db.get_inventory_entry(USER_ID, inventory_id)

    require(isinstance(item, tuple) and len(item) == 17, "get_item_by_inventory_id contract mismatch")
    require(isinstance(full, tuple) and len(full) == 19, "get_item_by_inventory_id_full contract mismatch")
    require(isinstance(entry, tuple) and len(entry) == 6, "get_inventory_entry contract mismatch")

    refine_level = db.get_inventory_refine_level(inventory_id)
    display_name = db.get_inventory_refined_display_name(inventory_id)
    require(isinstance(refine_level, int), "refine level must be int")
    require(isinstance(display_name, str), "refined display name must be str")

    if refine_level > 0:
        require(f"[+{refine_level}]" in display_name, "refine suffix missing from display name")
        require(f"[+{refine_level}]" in str(item[2]), "refine suffix missing from item tuple")
        require(f"[+{refine_level}]" in str(full[2]), "refine suffix missing from full tuple")
        require(f"[+{refine_level}]" in str(entry[2]), "refine suffix missing from entry tuple")

    print("- sample inventory_id:", inventory_id)
    print("- sample name:", display_name)
    print("- refine level:", refine_level)
    print("- tuple lengths: detailed=17 item=17 full=19 entry=6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH
    smoke = root / SMOKE_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(f"Missing file: {target}")

    original = target.read_text(encoding="utf-8")
    if MARKER in original:
        print("Patch 9.0.12f2 already applied. Skipping.")
        return

    backup = make_backup(root, target)
    smoke_backup = make_backup(root, smoke) if smoke.exists() else None

    try:
        target.write_text(original.rstrip() + "\n" + build_equipment_code() + "\n", encoding="utf-8")
        smoke.parent.mkdir(exist_ok=True)
        smoke.write_text(build_smoke_test(), encoding="utf-8")

        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(smoke), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        if smoke_backup:
            smoke.write_text(smoke_backup.read_text(encoding="utf-8"), encoding="utf-8")
        elif smoke.exists():
            smoke.unlink()
        raise SystemExit(f"Patch failed; files restored. Error: {error}")

    print("Patch 9.0.12f2 applied successfully.")
    print("Inventory/refine display read-only logic now lives in systems/equipment_system.py.")
    print(f"Backup: {backup}")
    if smoke_backup:
        print(f"Smoke backup: {smoke_backup}")
    print("Checks:")
    print(r"python -m py_compile .\systems\equipment_system.py")
    print(r"python -m py_compile .\db.py")
    print(r"python tools/check_imports.py")
    print(r"python tools/smoke_test_rom_core.py")
    print(r"python tools/smoke_test_equipment_readonly_core.py")
    print(r"python tools/smoke_test_inventory_refine_contracts.py")
    print(r"python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
