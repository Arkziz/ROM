from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "6_0_3_refine_display_names"
DB_MARKER = "# ✅ REFINE DISPLAY NAMES V1"

DB_APPEND_CODE = r'''

# ==============================
# ✅ REFINE DISPLAY NAMES V1
# ==============================

# 6.0.3
# Відображення [+N] у назвах inventory-предметів.
# Формат:
#   ⚪ Дворучний посох 8 рівня [+5]
#   ⚪ Обладунок [Тканина] 8 рівня [+6]

import re as _refine_display_re

try:
    _base_get_inventory_detailed_before_refine_display_v1 = get_inventory_detailed
except Exception:
    _base_get_inventory_detailed_before_refine_display_v1 = None

try:
    _base_get_item_by_inventory_id_before_refine_display_v1 = get_item_by_inventory_id
except Exception:
    _base_get_item_by_inventory_id_before_refine_display_v1 = None

try:
    _base_get_item_by_inventory_id_full_before_refine_display_v1 = get_item_by_inventory_id_full
except Exception:
    _base_get_item_by_inventory_id_full_before_refine_display_v1 = None

try:
    _base_get_inventory_entry_before_refine_display_v1 = get_inventory_entry
except Exception:
    _base_get_inventory_entry_before_refine_display_v1 = None

try:
    _base_get_sellable_equipment_items_before_refine_display_v1 = get_sellable_equipment_items
except Exception:
    _base_get_sellable_equipment_items_before_refine_display_v1 = None

try:
    _base_get_equipped_items_for_repair_before_refine_display_v1 = get_equipped_items_for_repair
except Exception:
    _base_get_equipped_items_for_repair_before_refine_display_v1 = None


def strip_refine_suffix_from_name(name):
    """
    Прибирає старий refine suffix, щоб не отримати дублювання:
    Назва [+3] [+4]
    """

    name = name or ""
    return _refine_display_re.sub(r"\s\[\+\d+\]$", "", name).strip()


def format_refined_item_name(name, refine_level):
    """
    Додає suffix [+N] до назви предмета.
    Якщо refine_level <= 0 — повертає назву без suffix.
    """

    name = strip_refine_suffix_from_name(name)

    try:
        refine_level = int(refine_level or 0)
    except Exception:
        refine_level = 0

    if refine_level <= 0:
        return name

    return f"{name} [+{refine_level}]"


def get_inventory_refined_display_name(inventory_id, name=None):
    """
    Повертає назву inventory-предмета з [+N].
    """

    try:
        refine_level = get_inventory_refine_level(inventory_id)
    except Exception:
        refine_level = 0

    if name is None:
        try:
            cursor.execute("""
            SELECT items.name
            FROM inventory
            JOIN items ON inventory.item_id = items.id
            WHERE inventory.id=?
            """, (inventory_id,))
            row = cursor.fetchone()
            name = row[0] if row else "Предмет"
        except Exception:
            name = "Предмет"

    return format_refined_item_name(name, refine_level)


def get_inventory_refine_display_line(inventory_id):
    """
    Текстовий рядок для деталей предмета.
    Поки не всі handlers його використовують, але helper готовий для UI.
    """

    try:
        refine_level = get_inventory_refine_level(inventory_id)
    except Exception:
        refine_level = 0

    try:
        refine_level = int(refine_level or 0)
    except Exception:
        refine_level = 0

    if refine_level <= 0:
        return ""

    return f"✨ Заточка: +{refine_level}\n"


def _replace_tuple_name_by_refine(row, inventory_id_index, name_index):
    if row is None:
        return row

    try:
        values = list(row)
        inventory_id = values[inventory_id_index]
        name = values[name_index]
        values[name_index] = get_inventory_refined_display_name(inventory_id, name)

        if isinstance(row, tuple):
            return tuple(values)

        return values

    except Exception:
        return row


def _replace_dict_name_by_refine(item):
    if not isinstance(item, dict):
        return item

    inventory_id = item.get("inventory_id") or item.get("id")

    if not inventory_id:
        return item

    if "name" not in item:
        return item

    result = dict(item)
    result["name"] = get_inventory_refined_display_name(inventory_id, result.get("name"))
    return result


def get_inventory_detailed(user_id):
    """
    FINAL OVERRIDE:
    Інвентар із назвами, які містять [+N].

    Очікуваний базовий формат row:
    inventory.id, inventory.item_id, items.name, ...
    """

    if _base_get_inventory_detailed_before_refine_display_v1 is None:
        return []

    rows = _base_get_inventory_detailed_before_refine_display_v1(user_id)

    if not rows:
        return rows

    return [
        _replace_tuple_name_by_refine(row, 0, 2)
        for row in rows
    ]


def get_item_by_inventory_id(inventory_id):
    """
    FINAL OVERRIDE:
    Деталі inventory item з назвою [+N].
    """

    if _base_get_item_by_inventory_id_before_refine_display_v1 is None:
        return None

    row = _base_get_item_by_inventory_id_before_refine_display_v1(inventory_id)

    # Формат: inventory.id, inventory.item_id, items.name, ...
    return _replace_tuple_name_by_refine(row, 0, 2)


def get_item_by_inventory_id_full(inventory_id):
    """
    FINAL OVERRIDE:
    Повні деталі inventory item з назвою [+N].
    """

    if _base_get_item_by_inventory_id_full_before_refine_display_v1 is None:
        return None

    row = _base_get_item_by_inventory_id_full_before_refine_display_v1(inventory_id)

    # Формат: inventory.id, inventory.item_id, items.name, ...
    return _replace_tuple_name_by_refine(row, 0, 2)


def get_inventory_entry(user_id, inventory_id):
    """
    FINAL OVERRIDE:
    Короткий inventory entry з назвою [+N].
    """

    if _base_get_inventory_entry_before_refine_display_v1 is None:
        return None

    row = _base_get_inventory_entry_before_refine_display_v1(user_id, inventory_id)

    # Формат: inventory.id, inventory.item_id, items.name, ...
    return _replace_tuple_name_by_refine(row, 0, 2)


def get_sellable_equipment_items(user_id):
    """
    FINAL OVERRIDE:
    Список продажу спорядження з назвами [+N], якщо базова функція існує.
    """

    if _base_get_sellable_equipment_items_before_refine_display_v1 is None:
        return []

    rows = _base_get_sellable_equipment_items_before_refine_display_v1(user_id)

    if not rows:
        return rows

    result = []

    for row in rows:
        if isinstance(row, dict):
            result.append(_replace_dict_name_by_refine(row))
        else:
            # У більшості версій: inventory.id, items.name, ...
            result.append(_replace_tuple_name_by_refine(row, 0, 1))

    return result


def get_equipped_items_for_repair(user_id):
    """
    FINAL OVERRIDE:
    Ремонтний список з назвами [+N], якщо базова функція існує.
    """

    if _base_get_equipped_items_for_repair_before_refine_display_v1 is None:
        return []

    items = _base_get_equipped_items_for_repair_before_refine_display_v1(user_id)

    if not items:
        return items

    result = []

    for item in items:
        if isinstance(item, dict):
            result.append(_replace_dict_name_by_refine(item))
        else:
            # Обережний fallback: якщо перший елемент inventory_id, другий name.
            result.append(_replace_tuple_name_by_refine(item, 0, 1))

    return result
'''


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
    target = root / "db.py"

    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py. Запускай патч з кореня ROM або з ROM\\patch.")

    original = target.read_text(encoding="utf-8")

    if DB_MARKER in original:
        print("ℹ️ db.py: REFINE DISPLAY NAMES V1 уже застосований, пропускаю.")
        return

    backup_path = make_backup(root, target)

    updated = original.rstrip() + "\n" + DB_APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_6_0_3_refine_display_names.\n"
            "db.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 6.0.3 Refine Display Names застосовано успішно.")
    print("✅ db.py пройшов py_compile.")
    print(f"✅ Backup: {backup_path}")
    print("")
    print("Що додано:")
    print("- назви inventory-предметів показують [+N]")
    print("- get_inventory_detailed() показує [+N]")
    print("- get_item_by_inventory_id() показує [+N]")
    print("- get_item_by_inventory_id_full() показує [+N]")
    print("- helper get_inventory_refine_display_line() для майбутнього UI")
    print("")
    print("Формат назв:")
    print("- ⚪ Дворучний посох 8 рівня [+5]")
    print("- ⚪ Обладунок [Тканина] 8 рівня [+6]")


if __name__ == "__main__":
    main()
