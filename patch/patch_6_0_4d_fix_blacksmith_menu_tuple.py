from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "6_0_4d_fix_blacksmith_menu_tuple"
CITY_MARKER = "# ✅ BLACKSMITH MENU V2 FINAL TUPLE FIX"
KEYBOARDS_MARKER = "# ✅ BLACKSMITH KB FINAL V2"


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

# ✅ BLACKSMITH KB FINAL V2
'''

    if pattern.search(text):
        text = pattern.sub(replacement, text, count=1)
        target.write_text(text, encoding="utf-8")
        print("✅ keyboards.py: blacksmith_kb() приведено до фінального ReplyKeyboard формату.")
    else:
        raise SystemExit("❌ Не знайдено def blacksmith_kb() у keyboards.py")

    return target, backup, original


def patch_city(root):
    target = root / "handlers" / "city.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/city.py")

    original = target.read_text(encoding="utf-8")
    text = original
    backup = make_backup(root, target)

    if CITY_MARKER in text:
        print("ℹ️ city.py: BLACKSMITH MENU V2 FINAL TUPLE FIX вже є.")
        return target, backup, original

    append_code = r'''

# ==============================
# ✅ BLACKSMITH MENU V2 FINAL TUPLE FIX
# ==============================

# show_blacksmith() у цьому проєкті очікує:
#   text, kb = build_blacksmith_text(user_id)
# Тому build_blacksmith_text() має повертати саме tuple: (text, blacksmith_kb()).


def build_blacksmith_text(user_id):
    gold = get_wallet(user_id)

    text = (
        "⚒️ Коваль\n\n"
        "Біля розпеченого горна працює досвідчений коваль. "
        "Він може полагодити твоє спорядження або посилити його за допомогою каменів заточки.\n\n"
        "Доступні дії:\n"
        "• 🛠️ Ремонт спорядження\n"
        "• ✨ Заточка спорядження\n\n"
        f"💰 Твоє золото: {gold:.2f} 💰"
    )

    return text, blacksmith_kb()


def _normalize_text_kb_result(result, fallback_kb=None):
    """
    Допоміжна функція для старих build_* функцій:
    - якщо функція повертає (text, kb), залишаємо як є;
    - якщо повертає тільки text, додаємо fallback_kb.
    """

    if isinstance(result, tuple):
        if len(result) >= 2:
            return result[0], result[1]
        if len(result) == 1:
            return result[0], fallback_kb

    return result, fallback_kb


def register_blacksmith_repair_button_v2(bot):
    @bot.message_handler(func=lambda message: message.text == "🛠️ Ремонт")
    def blacksmith_repair_button_v2(message):
        result = build_blacksmith_repair_text(message.from_user.id)
        text, kb = _normalize_text_kb_result(result, blacksmith_kb())

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )
'''

    text = text.rstrip() + append_code + "\n"
    target.write_text(text, encoding="utf-8")
    print("✅ city.py: додано final tuple-fix для build_blacksmith_text() і ремонту.")

    return target, backup, original


def main():
    root = Path(__file__).resolve().parents[1]

    originals = []
    changed_files = []
    backups = []

    try:
        for patch_func in [patch_keyboards, patch_city]:
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
            "❌ Помилка під час patch_6_0_4d_fix_blacksmith_menu_tuple.\n"
            "Змінені файли відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("\n✅ Патч 6.0.4d застосовано успішно.")
    print("\nЗмінені файли:")
    for file_path in changed_files:
        print(f"- {file_path}")

    print("\nBackup:")
    for backup in backups:
        print(f"- {backup}")

    print("\nЩо виправлено:")
    print("- build_blacksmith_text(user_id) тепер повертає (text, kb), як очікує show_blacksmith")
    print("- blacksmith_kb() має кнопки: 🛠️ Ремонт / ✨ Заточка / 🔙 Ремісничий квартал")
    print("- кнопка 🛠️ Ремонт коректно обробляє і text, і (text, kb)")


if __name__ == "__main__":
    main()
