from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "6_0_7b_sell_refine_display_importfix"
TARGET_RELATIVE_PATH = Path("handlers") / "city.py"
MARKER = "# ✅ SELL REFINE DISPLAY V2 IMPORT FIX"

APPEND_CODE = r'''

# ==============================
# ✅ SELL REFINE DISPLAY V2 IMPORT FIX
# ==============================

# 6.0.7b
# Попередній sell refine display міг не спрацювати, якщо city.py не імпортував
# get_inventory_refined_display_name із db.py. Цей override робить локальний import
# всередині helper-а і більш агресивно оновлює назву у row.

try:
    _base_city_get_sellable_equipment_items_before_refine_display_v2 = get_sellable_equipment_items
except Exception:
    _base_city_get_sellable_equipment_items_before_refine_display_v2 = None

try:
    _base_city_get_item_by_inventory_id_full_before_refine_display_v2 = get_item_by_inventory_id_full
except Exception:
    _base_city_get_item_by_inventory_id_full_before_refine_display_v2 = None


def _city_get_refined_name_v2(inventory_id, name):
    try:
        from db import get_inventory_refined_display_name
        return get_inventory_refined_display_name(inventory_id, name)
    except Exception:
        return name


def _city_string_looks_like_item_name_v2(value):
    if not isinstance(value, str):
        return False

    if not value:
        return False

    # Назви спорядження майже завжди мають рівень або rarity emoji.
    if " рівня" in value:
        return True

    item_markers = [
        "⚪", "🟢", "🔵", "🟣",
        "Посох", "Жезл", "Меч", "Кинджал", "Лук", "Арбалет", "Щит",
        "Обладунок", "Шолом", "Поножі", "Рукавиці", "Чоботи", "Каптур", "Капелюх",
        "Амулет", "Кільце", "Талісман"
    ]

    return any(marker in value for marker in item_markers)


def _city_refine_display_for_sell_row_v2(row):
    try:
        if isinstance(row, dict):
            inventory_id = row.get("inventory_id") or row.get("id")

            if not inventory_id:
                return row

            updated = dict(row)

            for key in ["name", "item_name", "display_name", "label"]:
                if key in updated and isinstance(updated[key], str):
                    updated[key] = _city_get_refined_name_v2(inventory_id, updated[key])

            return updated

        if isinstance(row, (tuple, list)):
            if not row:
                return row

            inventory_id = row[0]
            values = list(row)
            changed = False

            # Міняємо всі поля, які схожі на назву предмета.
            # Це безпечніше для різних форматів get_sellable_equipment_items().
            for index, value in enumerate(values):
                if _city_string_looks_like_item_name_v2(value):
                    values[index] = _city_get_refined_name_v2(inventory_id, value)
                    changed = True

            if not changed:
                # Fallback для найчастіших форматів:
                # (inventory_id, name, ...)
                # (inventory_id, item_id, name, ...)
                for index in [1, 2]:
                    if index < len(values) and isinstance(values[index], str):
                        values[index] = _city_get_refined_name_v2(inventory_id, values[index])
                        changed = True
                        break

            if isinstance(row, tuple):
                return tuple(values)

            return values

    except Exception:
        return row

    return row


def get_sellable_equipment_items(user_id):
    """
    FINAL OVERRIDE V2:
    Список продажу спорядження з назвами [+N].
    """

    if _base_city_get_sellable_equipment_items_before_refine_display_v2 is None:
        return []

    rows = _base_city_get_sellable_equipment_items_before_refine_display_v2(user_id)

    if not rows:
        return rows

    return [_city_refine_display_for_sell_row_v2(row) for row in rows]


def get_item_by_inventory_id_full(inventory_id):
    """
    FINAL OVERRIDE V2:
    Підтвердження продажу показує назву з [+N].
    """

    if _base_city_get_item_by_inventory_id_full_before_refine_display_v2 is None:
        return None

    row = _base_city_get_item_by_inventory_id_full_before_refine_display_v2(inventory_id)

    if not row:
        return row

    try:
        if isinstance(row, dict):
            updated = dict(row)
            for key in ["name", "item_name", "display_name", "label"]:
                if key in updated and isinstance(updated[key], str):
                    updated[key] = _city_get_refined_name_v2(inventory_id, updated[key])
            return updated

        if isinstance(row, (tuple, list)):
            values = list(row)

            for index, value in enumerate(values):
                if _city_string_looks_like_item_name_v2(value):
                    values[index] = _city_get_refined_name_v2(inventory_id, value)

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

    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
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
        print("ℹ️ SELL REFINE DISPLAY V2 уже застосований, пропускаю.")
        return

    backup_path = make_backup(root, target)

    updated = original.rstrip() + "\n" + APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_6_0_7b_sell_refine_display_importfix.\n"
            "handlers/city.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 6.0.7b Sell Refine Display Import Fix застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ handlers/city.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- список продажу тепер локально імпортує get_inventory_refined_display_name")
    print("- назви у 🧰 Продати спорядження мають показувати [+N]")
    print("- підтвердження продажу також має показувати [+N]")


if __name__ == "__main__":
    main()
