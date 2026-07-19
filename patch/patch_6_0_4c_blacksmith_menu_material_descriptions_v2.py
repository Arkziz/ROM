from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "6_0_4c_blacksmith_menu_material_descriptions_v2"

KEYBOARDS_MARKER = "# ✅ BLACKSMITH MENU V2"
CITY_MARKER = "# ✅ BLACKSMITH MENU TEXT V2"
INVENTORY_MARKER = "# ✅ REFINE MATERIAL DESCRIPTIONS V1"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def patch_keyboards(root):
    target = root / "keyboards.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено keyboards.py")

    original = target.read_text(encoding="utf-8")
    text = original
    backup = make_backup(root, target)

    pattern = re.compile(
        r"def\s+blacksmith_kb\s*\(\s*\)\s*:\n(?:.*?)(?=\ndef\s+\w+\s*\(|\Z)",
        flags=re.S,
    )

    replacement = r'''def blacksmith_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛠️ Ремонт", "✨ Заточка")
    kb.add("🔙 Ремісничий квартал")
    return kb

# ✅ BLACKSMITH MENU V2
'''

    if pattern.search(text):
        text = pattern.sub(replacement, text, count=1)
        print("✅ keyboards.py: blacksmith_kb() замінено на меню з Ремонт / Заточка / Назад.")
    else:
        raise SystemExit("❌ Не знайдено def blacksmith_kb() у keyboards.py")

    target.write_text(text, encoding="utf-8")
    return target, backup, original


def patch_city(root):
    target = root / "handlers" / "city.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/city.py")

    original = target.read_text(encoding="utf-8")
    text = original
    backup = make_backup(root, target)
    changed = False

    if "def build_blacksmith_repair_text(user_id):" not in text:
        if "def build_blacksmith_text(user_id):" in text:
            text = text.replace(
                "def build_blacksmith_text(user_id):",
                "def build_blacksmith_repair_text(user_id):",
                1,
            )
            changed = True
            print("✅ city.py: старий build_blacksmith_text перейменовано в build_blacksmith_repair_text.")
        else:
            print("⚠️ city.py: def build_blacksmith_text(user_id) не знайдено.")

    if CITY_MARKER not in text:
        new_menu_func = r'''
# ==============================
# ✅ BLACKSMITH MENU TEXT V2
# ==============================

def build_blacksmith_text(user_id):
    gold = get_wallet(user_id)

    return (
        "⚒️ Коваль\n\n"
        "Біля розпеченого горна працює досвідчений коваль. "
        "Він може полагодити твоє спорядження або посилити його за допомогою каменів заточки.\n\n"
        "Доступні дії:\n"
        "• 🛠️ Ремонт спорядження\n"
        "• ✨ Заточка спорядження\n\n"
        f"💰 Твоє золото: {gold:.2f} 💰"
    )

'''
        insert_at = text.find("def build_blacksmith_repair_text(user_id):")
        if insert_at != -1:
            text = text[:insert_at] + new_menu_func + text[insert_at:]
            changed = True
            print("✅ city.py: додано новий головний текст Коваля.")
        else:
            text = text.rstrip() + "\n\n" + new_menu_func
            changed = True
            print("✅ city.py: додано новий головний текст Коваля в кінець файлу.")
    else:
        print("ℹ️ city.py: BLACKSMITH MENU TEXT V2 уже є.")

    if 'message.text == "🛠️ Ремонт"' not in text:
        handler = r'''

# ==============================
# ✅ BLACKSMITH REPAIR BUTTON V2
# ==============================

def register_blacksmith_repair_button_v2(bot):
    @bot.message_handler(func=lambda message: message.text == "🛠️ Ремонт")
    def blacksmith_repair_button_v2(message):
        bot.send_message(
            message.chat.id,
            build_blacksmith_repair_text(message.from_user.id),
            reply_markup=blacksmith_kb()
        )
'''
        text = text.rstrip() + handler
        changed = True
        print("✅ city.py: додано register_blacksmith_repair_button_v2().")
    else:
        print("ℹ️ city.py: handler 🛠️ Ремонт уже є.")

    if "register_blacksmith_repair_button_v2(bot)" not in text:
        reg_match = re.search(r"def\s+register_city_handlers\s*\(\s*bot\s*\)\s*:\n", text)
        if reg_match:
            insert_pos = reg_match.end()
            text = text[:insert_pos] + "    register_blacksmith_repair_button_v2(bot)\n" + text[insert_pos:]
            changed = True
            print("✅ city.py: register_blacksmith_repair_button_v2(bot) підключено.")
        else:
            print("⚠️ city.py: register_city_handlers(bot) не знайдено, ремонт-кнопку треба підключити вручну.")

    if changed:
        target.write_text(text, encoding="utf-8")
    else:
        print("ℹ️ city.py: змін не внесено.")

    return target, backup, original


def patch_inventory(root):
    target = root / "handlers" / "inventory.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/inventory.py")

    original = target.read_text(encoding="utf-8")
    text = original
    backup = make_backup(root, target)

    if INVENTORY_MARKER in text:
        print("ℹ️ inventory.py: REFINE MATERIAL DESCRIPTIONS V1 уже є.")
        return target, backup, original

    override = r'''

# ==============================
# ✅ REFINE MATERIAL DESCRIPTIONS V1
# ==============================

# 6.0.4c
# Додає корисний опис для матеріалів заточки в деталях предмета.

try:
    _base_build_item_details_before_refine_material_desc_v1 = build_item_details
except Exception:
    _base_build_item_details_before_refine_material_desc_v1 = None


def get_refine_material_description_text(item_id):
    try:
        item_id = int(item_id)
    except Exception:
        return ""

    if item_id == 401:
        return (
            "\nℹ️ Опис:\n"
            "🪨 Камінь Посилення використовується у Коваля для спроби заточки спорядження.\n\n"
            "Правила:\n"
            "• витрачається при кожній спробі заточки;\n"
            "• потрібен для заточки зброї та броні;\n"
            "• не гарантує успіх;\n"
            "• шанс успіху залежить від поточного рівня заточки.\n"
        )

    if item_id == 402:
        return (
            "\nℹ️ Опис:\n"
            "💎 Руна Успіху — особлива руна для безпечної заточки.\n\n"
            "Ефект:\n"
            "• при використанні шанс успіху стає 100%;\n"
            "• витрачається разом із 🪨 Каменем Посилення;\n"
            "• допомагає уникнути невдалої спроби заточки.\n"
        )

    return ""


def _inject_refine_material_description(text, inventory_id):
    try:
        item = get_item_by_inventory_id_full(inventory_id)
        if not item:
            return text

        item_id = item[1]
        description = get_refine_material_description_text(item_id)

        if not description:
            return text

        if "ℹ️ Опис:" in text:
            return text

        return text + description

    except Exception:
        return text


def build_item_details(user_id, inventory_id, back_category="all", page=0):
    if _base_build_item_details_before_refine_material_desc_v1 is None:
        return "❌ Деталі предмета недоступні.", None

    result = _base_build_item_details_before_refine_material_desc_v1(
        user_id,
        inventory_id,
        back_category,
        page
    )

    if isinstance(result, tuple):
        if len(result) >= 2:
            text = result[0]
            kb = result[1]
            text = _inject_refine_material_description(text, inventory_id)
            return text, kb

        if len(result) == 1:
            text = _inject_refine_material_description(result[0], inventory_id)
            return (text,)

    if isinstance(result, str):
        return _inject_refine_material_description(result, inventory_id)

    return result
'''

    text = text.rstrip() + override + "\n"
    target.write_text(text, encoding="utf-8")
    print("✅ inventory.py: додано описи матеріалів заточки.")
    return target, backup, original


def main():
    root = Path(__file__).resolve().parents[1]
    originals = []
    changed_files = []
    backups = []

    try:
        for patch_func in [patch_keyboards, patch_city, patch_inventory]:
            file_path, backup_path, original = patch_func(root)
            changed_files.append(file_path)
            backups.append(backup_path)
            originals.append((file_path, original))

        for file_path in changed_files:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            if original is not None:
                file_path.write_text(original, encoding="utf-8")

        raise SystemExit(
            "❌ Помилка під час patch_6_0_4c_blacksmith_menu_material_descriptions_v2.\n"
            "Змінені файли відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("\n✅ Патч 6.0.4c v2 застосовано успішно.")
    print("\nЗмінені файли:")
    for file_path in changed_files:
        print(f"- {file_path}")

    print("\nBackup:")
    for backup in backups:
        if backup:
            print(f"- {backup}")

    print("\nЩо має бути в грі:")
    print("- Коваль відкривається як головне меню з кнопками: 🛠️ Ремонт / ✨ Заточка / 🔙 Ремісничий квартал")
    print("- 🛠️ Ремонт відкриває окремий екран ремонту")
    print("- ✨ Заточка відкриває refine UI")
    print("- У деталях 🪨 Каменя і 💎 Руни є опис")


if __name__ == "__main__":
    main()
