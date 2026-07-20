from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "6_0_7a_sell_refine_display"
TARGET_RELATIVE_PATH = Path("handlers") / "city.py"
MARKER = "# ✅ SELL REFINE DISPLAY V1"

APPEND_CODE = r'''

# ==============================
# ✅ SELL REFINE DISPLAY V1
# ==============================

# 6.0.7a
# Виправляє UI продажу спорядження: у списку продажу і підтвердженні продажу
# заточені предмети мають показувати [+N].
# Механіку продажу не змінює.

try:
    _base_city_get_sellable_equipment_items_before_refine_display_v1 = get_sellable_equipment_items
except Exception:
    _base_city_get_sellable_equipment_items_before_refine_display_v1 = None

try:
    _base_city_get_item_by_inventory_id_full_before_refine_display_v1 = get_item_by_inventory_id_full
except Exception:
    _base_city_get_item_by_inventory_id_full_before_refine_display_v1 = None


def _city_find_sellable_name_index(row):
    """
    Намагається знайти індекс назви у tuple/list sellable item.
    Різні версії db.py можуть повертати різний формат.
    """

    if not isinstance(row, (tuple, list)):
        return None

    # Найчастіші формати:
    # (inventory_id, name, ...)
    # (inventory_id, item_id, name, ...)
    preferred_indexes = [1, 2]

    for index in preferred_indexes:
        if index < len(row) and isinstance(row[index], str):
            value = row[index]
            if value and value not in ["equipment", "weapon", "armor", "common", "uncommon", "rare", "epic"]:
                return index

    # Fallback: перший рядок, схожий на назву предмета.
    for index, value in enumerate(row):
        if not isinstance(value, str):
            continue

        if " рівня" in value:
            return index

        if any(marker in value for marker in ["⚪", "🟢", "🔵", "🟣", "Посох", "Меч", "Кинджал", "Обладунок", "Шолом", "Поножі", "Рукавиці", "Чоботи"]):
            return index

    return None


def _city_refine_display_for_row(row):
    """
    Додає [+N] у назву row, не змінюючи структуру row.
    """

    try:
        if isinstance(row, dict):
            inventory_id = row.get("inventory_id") or row.get("id")
            name = row.get("name")

            if not inventory_id or not name:
                return row

            updated = dict(row)
            updated["name"] = get_inventory_refined_display_name(inventory_id, name)
            return updated

        if isinstance(row, (tuple, list)):
            if not row:
                return row

            inventory_id = row[0]
            name_index = _city_find_sellable_name_index(row)

            if name_index is None:
                return row

            values = list(row)
            values[name_index] = get_inventory_refined_display_name(inventory_id, values[name_index])

            if isinstance(row, tuple):
                return tuple(values)

            return values

    except Exception:
        return row

    return row


def get_sellable_equipment_items(user_id):
    """
    FINAL OVERRIDE:
    Список продажу спорядження з назвами [+N].
    """

    if _base_city_get_sellable_equipment_items_before_refine_display_v1 is None:
        return []

    rows = _base_city_get_sellable_equipment_items_before_refine_display_v1(user_id)

    if not rows:
        return rows

    return [_city_refine_display_for_row(row) for row in rows]


def get_item_by_inventory_id_full(inventory_id):
    """
    FINAL OVERRIDE:
    Підтвердження продажу та інші city-деталі показують назву з [+N].
    """

    if _base_city_get_item_by_inventory_id_full_before_refine_display_v1 is None:
        return None

    row = _base_city_get_item_by_inventory_id_full_before_refine_display_v1(inventory_id)

    if not row:
        return row

    try:
        if isinstance(row, dict):
            if "name" in row:
                updated = dict(row)
                updated["name"] = get_inventory_refined_display_name(inventory_id, updated.get("name"))
                return updated
            return row

        if isinstance(row, (tuple, list)):
            values = list(row)

            # Для get_item_by_inventory_id_full у проєкті зазвичай:
            # inventory.id, inventory.item_id, items.name, ...
            if len(values) > 2 and isinstance(values[2], str):
                values[2] = get_inventory_refined_display_name(inventory_id, values[2])
            else:
                name_index = _city_find_sellable_name_index(values)
                if name_index is not None:
                    values[name_index] = get_inventory_refined_display_name(inventory_id, values[name_index])

            if isinstance(row, tuple):
                return tuple(values)

            return values

    except Exception:
        return row

    return row
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"

    backup_path.write_text(
        target.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    return backup_path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(
            f"❌ Не знайдено файл: {target}\n"
            "Запускай патч із ROM або з ROM\\patch."
        )

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ SELL REFINE DISPLAY V1 уже застосований, пропускаю.")
        return

    backup_path = make_backup(root, target)

    updated = original.rstrip() + "\n" + APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_6_0_7a_sell_refine_display.\n"
            "handlers/city.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 6.0.7a Sell Refine Display застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ handlers/city.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- 🧰 Продати спорядження показує [+N] у списку")
    print("- підтвердження продажу показує [+N]")
    print("- механіку продажу не змінено")


if __name__ == "__main__":
    main()
