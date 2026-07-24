from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_8e_blacksmith_repair_confirm_item_name_fix"
TARGET_RELATIVE = Path("handlers") / "blacksmith_repair_confirm.py"
MARKER = "# ✅ ROM 9.0.8e BLACKSMITH REPAIR CONFIRM ITEM NAME FIX V1"

APPEND_CODE = r'''

# ==============================
# ✅ ROM 9.0.8e BLACKSMITH REPAIR CONFIRM ITEM NAME FIX V1
# ==============================

# Fix reason:
# Confirmation message displayed the whole tuple from get_item_by_inventory_id_full(), e.g.
# [116, 413, '⚪️ Рукавиці 8 рівня', ...]
# instead of only the item name.

try:
    _blacksmith_confirm_base_get_item_name_before_tuple_fix_v1 = _get_item_name
except NameError:
    _blacksmith_confirm_base_get_item_name_before_tuple_fix_v1 = None


def _get_item_name(inventory_id):
    """Return clean item name for blacksmith repair confirmation."""

    item = None

    try:
        from db import get_item_by_inventory_id_full
        item = get_item_by_inventory_id_full(inventory_id)
    except Exception:
        item = None

    name = None

    if isinstance(item, dict):
        name = (
            item.get("name")
            or item.get("item_name")
            or item.get("raw_name")
        )
    elif isinstance(item, (list, tuple)):
        # Common tuple format in this project:
        # (inventory_id, item_id, name, type, rarity, category, slot_key, ...)
        try:
            if len(item) > 2 and isinstance(item[2], str):
                name = item[2]
        except Exception:
            name = None

    if not name:
        try:
            from db import get_item_by_inventory_id
            item = get_item_by_inventory_id(inventory_id)

            if isinstance(item, dict):
                name = item.get("name") or item.get("item_name") or item.get("raw_name")
            elif isinstance(item, (list, tuple)):
                # Usually (inventory_id, item_id, name, ...), but keep safe fallbacks.
                for index in [2, 1, 0]:
                    try:
                        if index < len(item) and isinstance(item[index], str):
                            name = item[index]
                            break
                    except Exception:
                        pass
            elif isinstance(item, str):
                name = item
        except Exception:
            pass

    if not name:
        name = f"Предмет #{inventory_id}"

    try:
        from db import get_inventory_refined_display_name
        return get_inventory_refined_display_name(inventory_id, name)
    except Exception:
        return name
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
    target = root / TARGET_RELATIVE

    if not target.exists():
        raise SystemExit(f"❌ Не знайдено файл: {target}")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч уже застосовано раніше.")
        return

    backup = make_backup(root, target)

    try:
        target.write_text(original.rstrip() + "\n" + APPEND_CODE + "\n", encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_9_0_8e_blacksmith_repair_confirm_item_name_fix.\n"
            "Файл handlers/blacksmith_repair_confirm.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.8e Blacksmith repair confirm item name fix застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/blacksmith_repair_confirm.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- у підтвердженні ремонту більше не показується весь tuple/list предмета")
    print("- показується тільки чиста назва предмета")
    print("- заточка [+N] зберігається, якщо get_inventory_refined_display_name доступна")


if __name__ == "__main__":
    main()
