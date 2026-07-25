from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12f1d_equipped_items_full_legacy_contract_fix"
TARGET_RELATIVE_PATH = Path("systems") / "equipment_system.py"
SMOKE_RELATIVE_PATH = Path("tools") / "smoke_test_equipment_readonly_core.py"


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
    smoke = root / SMOKE_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(f"ERROR: file not found: {target}")

    original_target = target.read_text(encoding="utf-8")
    original_smoke = smoke.read_text(encoding="utf-8") if smoke.exists() else None
    marker = "# ROM 9.0.12f1d EQUIPPED ITEMS FULL LEGACY CONTRACT FIX"

    if marker in original_target:
        print("Patch already applied. Nothing to do.")
        return

    backups = [make_backup(root, target)]
    if smoke.exists():
        backups.append(make_backup(root, smoke))

    code = r'''

# ==============================
# ROM 9.0.12f1d EQUIPPED ITEMS FULL LEGACY CONTRACT FIX
# ==============================

_EQUIPMENT_SLOT_NAMES_REAL_V2 = {
    "main_hand": "Основна рука",
    "off_hand": "Друга рука",
    "helmet": "Шолом",
    "shoulders": "Наплічники",
    "chest": "Обладунок",
    "gloves": "Рукавиці",
    "legs": "Поножі",
    "boots": "Чоботи",
    "necklace": "Намисто",
    "ring": "Перстень",
}


def _equipment_refined_name_real_v2(db, inventory_id, base_name, refine_level):
    """Return the same display name used by inventory/repair UI."""
    helper = getattr(db, "get_inventory_refined_display_name", None)
    if helper:
        try:
            value = helper(int(inventory_id))
            if value:
                return str(value)
        except TypeError:
            try:
                value = helper(int(inventory_id), base_name)
                if value:
                    return str(value)
            except Exception:
                pass
        except Exception:
            pass

    name = str(base_name or "Предмет")
    level = int(refine_level or 0)
    if level > 0 and f"[+{level}]" not in name:
        name = f"{name} [+{level}]"
    return name


def _equipment_nested_item_tuple_real_v2(row, display_name):
    """Build the exact 19-field tuple expected by the legacy repair formatter."""
    return (
        int(row["inventory_id"]),
        int(row["item_id"]),
        display_name,
        row["item_type"],
        row["rarity"],
        row["category"],
        row["item_slot_key"],
        int(row["weapon_hands"] or 1),
        int(row["quantity"] or 1),
        int(row["max_stack"] or 1),
        int(row["durability"] if row["durability"] is not None else 100),
        int(row["bonus_str"] or 0),
        int(row["bonus_dex"] or 0),
        int(row["bonus_int"] or 0),
        int(row["bonus_wis"] or 0),
        int(row["bonus_sta"] or 0),
        int(row["pdef"] or 0),
        int(row["mdef"] or 0),
        float(row["sell_price"] or 0.0),
    )


def get_all_equipped_items(user_id):
    """
    Return the historical equipment contract used by repair code:

        [{
            "slot_key": str,
            "slot_name": str,
            "inventory_id": int | None,
            "item": tuple(19 fields) | None,
            ...flat aliases...
        }, ...]

    All ten slots are returned, including empty slots. Newer callers can use
    the flat aliases; old repair code can use the nested ``item`` tuple.
    """
    db = _equipment_real_db_v1()
    ensure_equipment_slots(user_id)
    uid = int(user_id)

    rows = db.conn.execute(
        "SELECT "
        "es.slot_key AS equipped_slot_key, es.inventory_id AS equipped_inventory_id, "
        "inv.id AS inventory_id, inv.user_id AS inventory_user_id, "
        "inv.item_id AS item_id, inv.quantity AS quantity, "
        "inv.durability AS durability, COALESCE(inv.refine_level,0) AS refine_level, "
        "it.name AS item_name, it.type AS item_type, it.rarity AS rarity, "
        "it.category AS category, it.slot_key AS item_slot_key, "
        "COALESCE(it.weapon_hands,1) AS weapon_hands, "
        "COALESCE(it.max_stack,1) AS max_stack, COALESCE(it.sell_price,0) AS sell_price, "
        "COALESCE(it.bonus_str,0) AS bonus_str, COALESCE(it.bonus_dex,0) AS bonus_dex, "
        "COALESCE(it.bonus_int,0) AS bonus_int, COALESCE(it.bonus_wis,0) AS bonus_wis, "
        "COALESCE(it.bonus_sta,0) AS bonus_sta, COALESCE(it.pdef,0) AS pdef, "
        "COALESCE(it.mdef,0) AS mdef "
        "FROM equipment_slots es "
        "LEFT JOIN inventory inv ON inv.id=es.inventory_id AND inv.user_id=es.user_id "
        "LEFT JOIN items it ON it.id=inv.item_id "
        "WHERE es.user_id=? "
        "ORDER BY CASE es.slot_key "
        "WHEN 'main_hand' THEN 1 WHEN 'off_hand' THEN 2 "
        "WHEN 'helmet' THEN 3 WHEN 'shoulders' THEN 4 "
        "WHEN 'chest' THEN 5 WHEN 'gloves' THEN 6 "
        "WHEN 'legs' THEN 7 WHEN 'boots' THEN 8 "
        "WHEN 'necklace' THEN 9 WHEN 'ring' THEN 10 ELSE 99 END",
        (uid,),
    ).fetchall()

    result = []
    for raw in rows:
        row = dict(raw) if hasattr(raw, "keys") else None
        if row is None:
            columns = (
                "equipped_slot_key", "equipped_inventory_id", "inventory_id",
                "inventory_user_id", "item_id", "quantity", "durability",
                "refine_level", "item_name", "item_type", "rarity", "category",
                "item_slot_key", "weapon_hands", "max_stack", "sell_price",
                "bonus_str", "bonus_dex", "bonus_int", "bonus_wis", "bonus_sta",
                "pdef", "mdef",
            )
            row = dict(zip(columns, raw))

        slot_key = str(row.get("equipped_slot_key") or "")
        slot_name = _EQUIPMENT_SLOT_NAMES_REAL_V2.get(slot_key, slot_key)
        inventory_id = row.get("inventory_id")

        if inventory_id is None:
            result.append({
                "slot_key": slot_key,
                "slot_name": slot_name,
                "inventory_id": None,
                "item": None,
                "name": None,
                "durability": None,
                "refine_level": 0,
            })
            continue

        display_name = _equipment_refined_name_real_v2(
            db,
            inventory_id,
            row.get("item_name"),
            row.get("refine_level"),
        )
        nested_item = _equipment_nested_item_tuple_real_v2(row, display_name)

        result.append({
            "slot_key": slot_key,
            "slot_name": slot_name,
            "inventory_id": int(inventory_id),
            "item": nested_item,
            "id": int(inventory_id),
            "inv_id": int(inventory_id),
            "user_id": int(row.get("inventory_user_id") or uid),
            "item_id": int(row.get("item_id") or 0),
            "name": display_name,
            "item_name": display_name,
            "type": row.get("item_type"),
            "rarity": row.get("rarity"),
            "category": row.get("category"),
            "item_slot_key": row.get("item_slot_key"),
            "weapon_hands": int(row.get("weapon_hands") or 1),
            "quantity": int(row.get("quantity") or 1),
            "max_stack": int(row.get("max_stack") or 1),
            "durability": int(row.get("durability") if row.get("durability") is not None else 100),
            "refine_level": int(row.get("refine_level") or 0),
            "sell_price": float(row.get("sell_price") or 0.0),
            "bonus_str": int(row.get("bonus_str") or 0),
            "bonus_dex": int(row.get("bonus_dex") or 0),
            "bonus_int": int(row.get("bonus_int") or 0),
            "bonus_wis": int(row.get("bonus_wis") or 0),
            "bonus_sta": int(row.get("bonus_sta") or 0),
            "pdef": int(row.get("pdef") or 0),
            "mdef": int(row.get("mdef") or 0),
        })

    return result
'''

    smoke_code = r'''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

USER_ID = 243129101
items = db.get_all_equipped_items(USER_ID)
assert isinstance(items, list), type(items)
assert len(items) == 10, f"expected 10 equipment slots, got {len(items)}"
for entry in items:
    assert isinstance(entry, dict), type(entry)
    for key in ("slot_key", "slot_name", "inventory_id", "item"):
        assert key in entry, (key, entry)
    if entry["inventory_id"] is not None:
        assert isinstance(entry["item"], tuple), type(entry["item"])
        assert len(entry["item"]) == 19, len(entry["item"])

repair_rows = db.get_equipped_items_for_repair(USER_ID)
assert isinstance(repair_rows, list), type(repair_rows)
assert len(repair_rows) == 10, f"expected 10 repair rows, got {len(repair_rows)}"
for row in repair_rows:
    assert isinstance(row, dict), type(row)
    for key in ("slot", "slot_key", "inventory_id", "name", "durability", "repair_cost", "is_broken"):
        assert key in row, (key, row)

print("[OK] equipment full legacy contract")
print("- equipment slots:", len(items))
print("- repair rows:", len(repair_rows))
print("- repairable:", sum(1 for row in repair_rows if row.get("repair_cost", 0) > 0))
'''

    target.write_text(original_target.rstrip() + "\n" + code + "\n", encoding="utf-8")
    smoke.write_text(smoke_code, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(smoke), doraise=True)
    except Exception as error:
        target.write_text(original_target, encoding="utf-8")
        if original_smoke is None:
            try:
                smoke.unlink()
            except FileNotFoundError:
                pass
        else:
            smoke.write_text(original_smoke, encoding="utf-8")
        raise SystemExit(f"ERROR: compile failed; files restored.\n{error}")

    print("Patch 9.0.12f1d applied successfully.")
    print("get_all_equipped_items now exposes the complete historical repair contract.")
    print("Backup:")
    for path in backups:
        print(f"- {path}")
    print("Checks:")
    print(r"python -m py_compile .\systems\equipment_system.py")
    print(r"python tools\smoke_test_equipment_readonly_core.py")


if __name__ == "__main__":
    main()
