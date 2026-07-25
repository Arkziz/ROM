from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12f1b_equipped_items_dict_contract_fix"
TARGET = Path("systems") / "equipment_system.py"


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
    target = root / TARGET
    if not target.exists():
        raise SystemExit(f"File not found: {target}")
    original = target.read_text(encoding="utf-8")
    marker = "# ROM 9.0.12f1b EQUIPPED ITEMS DICT CONTRACT FIX"
    if marker in original:
        print("Patch already applied.")
        return
    backup_path = make_backup(root, target)
    block = r'''

# ==============================
# ROM 9.0.12f1b EQUIPPED ITEMS DICT CONTRACT FIX
# ==============================

def _equipment_item_dict_real_v2(slot_key, inventory_id):
    """Return one equipped item using the historical dict contract."""
    db = _equipment_real_db_v1()
    cursor = db.conn.execute(
        "SELECT inv.id AS inventory_id, inv.user_id, inv.item_id, "
        "COALESCE(inv.quantity,1) AS quantity, COALESCE(inv.durability,100) AS durability, "
        "COALESCE(inv.refine_level,0) AS refine_level, it.name, it.type, it.rarity, "
        "it.category, it.slot_key AS item_slot_key, COALESCE(it.weapon_hands,1) AS weapon_hands, "
        "COALESCE(it.max_stack,1) AS max_stack, COALESCE(it.sell_price,0) AS sell_price, "
        "COALESCE(it.bonus_str,0) AS bonus_str, COALESCE(it.bonus_dex,0) AS bonus_dex, "
        "COALESCE(it.bonus_int,0) AS bonus_int, COALESCE(it.bonus_wis,0) AS bonus_wis, "
        "COALESCE(it.bonus_sta,0) AS bonus_sta, COALESCE(it.pdef,0) AS pdef, "
        "COALESCE(it.mdef,0) AS mdef, COALESCE(it.item_level,0) AS item_level, "
        "COALESCE(it.item_subtype,'') AS item_subtype, COALESCE(it.armor_type,'') AS armor_type, "
        "COALESCE(it.weapon_min_damage,0) AS weapon_min_damage, "
        "COALESCE(it.weapon_max_damage,0) AS weapon_max_damage, "
        "COALESCE(it.weapon_min_magic_damage,0) AS weapon_min_magic_damage, "
        "COALESCE(it.weapon_max_magic_damage,0) AS weapon_max_magic_damage, "
        "COALESCE(it.weapon_attack_type,'') AS weapon_attack_type "
        "FROM inventory inv JOIN items it ON it.id=inv.item_id WHERE inv.id=?",
        (int(inventory_id),),
    )
    row = cursor.fetchone()
    if not row:
        return None
    columns = [col[0] for col in cursor.description]
    item = dict(zip(columns, row))
    item["slot_key"] = slot_key
    item["equipped_slot"] = slot_key
    item["id"] = item["inventory_id"]
    item["inv_id"] = item["inventory_id"]
    item["item_name"] = item["name"]
    item["level"] = item["item_level"]
    item["b_str"] = item["bonus_str"]
    item["b_dex"] = item["bonus_dex"]
    item["b_int"] = item["bonus_int"]
    item["b_wis"] = item["bonus_wis"]
    item["b_sta"] = item["bonus_sta"]
    try:
        display_name = db.get_inventory_refined_display_name(int(inventory_id))
        if display_name:
            item["name"] = display_name
            item["item_name"] = display_name
    except Exception:
        pass
    return item


def get_all_equipped_items(user_id):
    """Return list[dict], matching the legacy public contract."""
    result = []
    for slot_key, inventory_id in _equipment_slot_rows_real_v1(user_id):
        if inventory_id is None:
            continue
        item = _equipment_item_dict_real_v2(slot_key, inventory_id)
        if item is not None:
            result.append(item)
    return result
'''
    target.write_text(original.rstrip() + block + "\n", encoding="utf-8")
    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as exc:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(f"Compilation failed; original restored.\n{exc}")
    print("Patch 9.0.12f1b applied successfully.")
    print("get_all_equipped_items now returns list[dict] with legacy-compatible keys.")
    print(f"Backup: {backup_path}")


if __name__ == "__main__":
    main()
