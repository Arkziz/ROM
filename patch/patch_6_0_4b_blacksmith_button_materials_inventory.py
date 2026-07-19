from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "6_0_4b_blacksmith_button_materials_inventory"

INVENTORY_MARKER = "# ✅ REFINE MATERIALS INVENTORY CATEGORY V1"
KEYBOARDS_MARKER = "# ✅ REFINE BUTTON IN BLACKSMITH KB V1"
CITY_MARKER = "# ✅ REFINE BUTTON CITY FALLBACK V1"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def patch_inventory(root):
    target = root / "handlers" / "inventory.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/inventory.py")

    original = target.read_text(encoding="utf-8")
    text = original
    changed = False

    backup_path = make_backup(root, target)

    # 1) Додаємо категорію 🪨 Матеріали в конфіг категорій.
    if '("material", "🪨 Матеріали")' not in text and "('material', '🪨 Матеріали')" not in text:
        # Найкраще місце — перед зіллям або перед all.
        candidates = [
            '("potion", "🧪 Зілля"),',
            '("all", "📦 Переглянути все")',
            "('potion', '🧪 Зілля'),",
            "('all', '📦 Переглянути все')",
        ]

        inserted = False
        for candidate in candidates:
            if candidate in text:
                text = text.replace(
                    candidate,
                    '("material", "🪨 Матеріали"),\n' + candidate,
                    1
                )
                inserted = True
                changed = True
                print("✅ inventory.py: додано категорію 🪨 Матеріали.")
                break

        if not inserted:
            print("⚠️ inventory.py: не знайшов місце для INVENTORY_CATEGORIES. Додам runtime append нижче.")

    else:
        print("ℹ️ inventory.py: категорія 🪨 Матеріали вже є.")

    # 2) Додаємо override category filtering у кінець файлу.
    if INVENTORY_MARKER not in text:
        override = r'''

# ==============================
# ✅ REFINE MATERIALS INVENTORY CATEGORY V1
# ==============================

# 6.0.4b
# Окрема категорія інвентаря для матеріалів:
# - 401 🪨 Камінь Посилення
# - 402 💎 Руна Успіху

try:
    if ("material", "🪨 Матеріали") not in INVENTORY_CATEGORIES:
        # Вставляємо перед "Переглянути все", якщо можливо.
        insert_index = len(INVENTORY_CATEGORIES)
        for idx, entry in enumerate(INVENTORY_CATEGORIES):
            if entry[0] == "all":
                insert_index = idx
                break
        INVENTORY_CATEGORIES.insert(insert_index, ("material", "🪨 Матеріали"))
except Exception:
    pass

try:
    _base_get_category_items_before_materials_v1 = get_category_items
except Exception:
    _base_get_category_items_before_materials_v1 = None


def get_category_items(user_id, category_key):
    """
    FINAL OVERRIDE:
    Додає коректну підтримку категорії 🪨 Матеріали.
    """

    if category_key != "material":
        if _base_get_category_items_before_materials_v1 is not None:
            return _base_get_category_items_before_materials_v1(user_id, category_key)
        return []

    items = get_inventory_full_items(user_id)
    result = []

    for item in items:
        try:
            item_id = item[1]
            category = item[5]
        except Exception:
            continue

        if category == "material" or item_id in [401, 402]:
            result.append(item)

    return result


def get_category_count(user_id, category_key):
    return len(get_category_items(user_id, category_key))
'''
        text = text.rstrip() + override + "\n"
        changed = True
        print("✅ inventory.py: додано override для категорії 🪨 Матеріали.")
    else:
        print("ℹ️ inventory.py: REFINE MATERIALS INVENTORY CATEGORY V1 вже є.")

    if changed:
        target.write_text(text, encoding="utf-8")
    else:
        print("ℹ️ inventory.py: змін не внесено.")

    return target, backup_path, original


def patch_keyboards(root):
    target = root / "keyboards.py"
    if not target.exists():
        print("⚠️ keyboards.py не знайдено. Пропускаю кнопку Коваля.")
        return None, None, None, False

    original = target.read_text(encoding="utf-8")
    text = original
    changed = False
    backup_path = make_backup(root, target)

    if KEYBOARDS_MARKER in text or "refine_menu" in text:
        print("ℹ️ keyboards.py: кнопка/callback refine_menu вже є.")
        return target, backup_path, original, False

    # Шукаємо blacksmith_kb і додаємо кнопку перед return kb у тілі функції.
    match = re.search(r"def\s+blacksmith_kb\s*\([^)]*\):", text)
    if not match:
        print("⚠️ keyboards.py: def blacksmith_kb(...) не знайдено. Пропускаю.")
        return target, backup_path, original, False

    start = match.start()
    next_def = re.search(r"\ndef\s+\w+\s*\(", text[match.end():])
    end = len(text) if not next_def else match.end() + next_def.start()
    block = text[start:end]

    return_match = re.search(r"(\n\s*)return\s+kb", block)
    if not return_match:
        print("⚠️ keyboards.py: return kb у blacksmith_kb не знайдено. Пропускаю.")
        return target, backup_path, original, False

    indent = return_match.group(1)
    add_code = (
        f'{indent}kb.add(types.InlineKeyboardButton('\
        f'text="✨ Заточка", callback_data="refine_menu"))\n'
        f'{indent}# ✅ REFINE BUTTON IN BLACKSMITH KB V1'
    )

    insert_pos = start + return_match.start(1)
    text = text[:insert_pos] + add_code + text[insert_pos:]
    target.write_text(text, encoding="utf-8")
    changed = True
    print("✅ keyboards.py: додано кнопку ✨ Заточка у blacksmith_kb().")

    return target, backup_path, original, changed


def patch_city_fallback(root):
    """
    Якщо кнопка Коваля виявиться не в keyboards.py, додаємо callback fallback не треба:
    refine_menu вже обробляє handlers/refine.py. Тут лишаємо маркер-коментар.
    """

    target = root / "handlers" / "city.py"
    if not target.exists():
        return None, None, None

    original = target.read_text(encoding="utf-8")
    if CITY_MARKER in original:
        return target, None, original

    backup_path = make_backup(root, target)
    text = original.rstrip() + "\n\n# ✅ REFINE BUTTON CITY FALLBACK V1\n# refine_menu callback is handled by handlers/refine.py\n"
    target.write_text(text, encoding="utf-8")
    return target, backup_path, original


def main():
    root = Path(__file__).resolve().parents[1]

    originals = []
    changed_files = []
    backups = []

    try:
        inv_file, inv_backup, inv_original = patch_inventory(root)
        changed_files.append(inv_file)
        backups.append(inv_backup)
        originals.append((inv_file, inv_original))

        kb_file, kb_backup, kb_original, kb_changed = patch_keyboards(root)
        if kb_file:
            changed_files.append(kb_file)
            backups.append(kb_backup)
            originals.append((kb_file, kb_original))

        city_file, city_backup, city_original = patch_city_fallback(root)
        if city_file:
            changed_files.append(city_file)
            originals.append((city_file, city_original))
        if city_backup:
            backups.append(city_backup)

        # Compile touched Python files.
        for file_path in changed_files:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            if original is not None:
                file_path.write_text(original, encoding="utf-8")

        raise SystemExit(
            "❌ Помилка під час patch_6_0_4b_blacksmith_button_materials_inventory.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("\n✅ Патч 6.0.4b застосовано успішно.")
    print("\nЗмінені файли:")
    for file_path in changed_files:
        print(f"- {file_path}")

    print("\nBackup:")
    for backup in backups:
        if backup:
            print(f"- {backup}")

    print("\nЩо має зʼявитися:")
    print("- в інвентарі категорія 🪨 Матеріали")
    print("- у меню Коваля кнопка ✨ Заточка, якщо blacksmith_kb() у keyboards.py")
    print("\nЯкщо кнопка Коваля не зʼявиться:")
    print("- UI заточки все одно відкривається через /refine")
    print("- надішли keyboards.py, і я дам точний патч під твою клавіатуру")


if __name__ == "__main__":
    main()
