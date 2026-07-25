from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12f1c_equipped_items_slot_name_contract_fix"
TARGET = Path("systems") / "equipment_system.py"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET
    if not target.exists():
        raise SystemExit(f"File not found: {target}")

    original = target.read_text(encoding="utf-8")
    marker = "# HOTFIX 9.0.12f1c: EQUIPPED ITEM SLOT_NAME CONTRACT"
    if marker in original:
        print("Patch already applied.")
        return

    backup_path = make_backup(root, target)

    patch_lines = [
        "",
        "# HOTFIX 9.0.12f1c: EQUIPPED ITEM SLOT_NAME CONTRACT",
        "_SLOT_NAMES_9_0_12F1C = {",
        "    'main_hand': 'Основна рука',",
        "    'off_hand': 'Друга рука',",
        "    'helmet': 'Шолом',",
        "    'shoulders': 'Наплічники',",
        "    'chest': 'Обладунок',",
        "    'gloves': 'Рукавиці',",
        "    'legs': 'Поножі',",
        "    'boots': 'Чоботи',",
        "    'necklace': 'Намисто',",
        "    'ring': 'Перстень',",
        "}",
        "",
        "_get_all_equipped_items_before_slot_name_9_0_12f1c = get_all_equipped_items",
        "",
        "def get_all_equipped_items(user_id):",
        "    rows = _get_all_equipped_items_before_slot_name_9_0_12f1c(user_id)",
        "    normalized = []",
        "    for row in rows or []:",
        "        if isinstance(row, dict):",
        "            item = dict(row)",
        "        elif hasattr(row, 'keys'):",
        "            item = {key: row[key] for key in row.keys()}",
        "        else:",
        "            try:",
        "                item = dict(row)",
        "            except Exception:",
        "                continue",
        "        slot_key = item.get('slot_key') or item.get('equipment_slot') or item.get('slot') or ''",
        "        item['slot_key'] = slot_key",
        "        item['slot_name'] = item.get('slot_name') or _SLOT_NAMES_9_0_12F1C.get(slot_key, slot_key or 'Невідомий слот')",
        "        if 'inventory_id' not in item:",
        "            item['inventory_id'] = item.get('inv_id') or item.get('id')",
        "        if 'durability' not in item:",
        "            item['durability'] = item.get('inv_durability', 100)",
        "        if 'refine_level' not in item:",
        "            item['refine_level'] = item.get('inventory_refine_level', 0)",
        "        if 'name' not in item:",
        "            item['name'] = item.get('item_name') or item.get('raw_name') or 'Предмет'",
        "        normalized.append(item)",
        "    return normalized",
        "",
    ]
    patch = "\n".join(patch_lines)
    target.write_text(original.rstrip() + "\n" + patch, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(f"Compile failed; file restored. Error: {error}")

    print("Patch 9.0.12f1c applied successfully.")
    print(f"Backup: {backup_path}")
    print("Fixed: equipped item rows include slot_name and compatibility aliases.")


if __name__ == "__main__":
    main()
