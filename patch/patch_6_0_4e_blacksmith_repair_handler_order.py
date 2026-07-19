from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "6_0_4e_blacksmith_repair_handler_order"
HOTFIX_FILE = Path("handlers") / "blacksmith_repair_hotfix.py"

HOTFIX_CODE = r'''
from keyboards import blacksmith_kb
from handlers.city import build_blacksmith_repair_text


REPAIR_BUTTON_TEXTS = {
    "🛠️ Ремонт",
    "🛠 Ремонт",
    "🔧 Ремонт",
    "Ремонт",
}


def _normalize_text_kb_result(result, fallback_kb=None):
    if isinstance(result, tuple):
        if len(result) >= 2:
            return result[0], result[1]
        if len(result) == 1:
            return result[0], fallback_kb

    return result, fallback_kb


def register_blacksmith_repair_hotfix_handlers(bot):
    """
    Hotfix для кнопки 🛠️ Ремонт.

    Реєструється ДО city handlers, щоб кнопку не перехоплювали інші широкі обробники.
    """

    @bot.message_handler(func=lambda message: bool(message.text) and message.text.strip() in REPAIR_BUTTON_TEXTS)
    def blacksmith_repair_hotfix(message):
        result = build_blacksmith_repair_text(message.from_user.id)
        text, kb = _normalize_text_kb_result(result, blacksmith_kb())

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def write_hotfix_file(root):
    target = root / HOTFIX_FILE
    target.parent.mkdir(exist_ok=True)
    backup = make_backup(root, target) if target.exists() else None
    target.write_text(HOTFIX_CODE.strip() + "\n", encoding="utf-8")
    return target, backup, None


def patch_main(root):
    target = root / "main.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено main.py")

    original = target.read_text(encoding="utf-8")
    text = original
    changed = False
    backup = make_backup(root, target)

    import_line = "from handlers.blacksmith_repair_hotfix import register_blacksmith_repair_hotfix_handlers\n"

    if "register_blacksmith_repair_hotfix_handlers" not in text:
        # Вставити import поруч із handler imports.
        matches = list(re.finditer(r"^from handlers\.[^\n]+\n", text, flags=re.M))
        if matches:
            last = matches[-1]
            text = text[:last.end()] + import_line + text[last.end():]
        else:
            text = import_line + text
        changed = True
        print("✅ main.py: додано import register_blacksmith_repair_hotfix_handlers.")
    else:
        print("ℹ️ main.py: import/call hotfix уже згадується.")

    call_line = "register_blacksmith_repair_hotfix_handlers(bot)"

    if call_line not in text:
        # Найкраще місце — прямо перед register_city_handlers(bot), щоб repair handler був раніше широких city handlers.
        city_call = "register_city_handlers(bot)"
        pos = text.find(city_call)
        if pos != -1:
            line_start = text.rfind("\n", 0, pos) + 1
            indent = text[line_start:pos]
            text = text[:line_start] + indent + call_line + "\n" + text[line_start:]
            changed = True
            print("✅ main.py: register_blacksmith_repair_hotfix_handlers(bot) вставлено перед register_city_handlers(bot).")
        else:
            # Fallback: після першого register_*_handlers(bot)
            match = re.search(r"^(\s*)register_[A-Za-z0-9_]+_handlers\(bot\)\s*$", text, flags=re.M)
            if match:
                insert_at = match.end()
                indent = match.group(1)
                text = text[:insert_at] + f"\n{indent}{call_line}" + text[insert_at:]
                changed = True
                print("✅ main.py: register_blacksmith_repair_hotfix_handlers(bot) вставлено після першого register_*_handlers.")
            else:
                raise SystemExit(
                    "❌ Не знайшов місце для register_blacksmith_repair_hotfix_handlers(bot) у main.py."
                )
    else:
        print("ℹ️ main.py: call register_blacksmith_repair_hotfix_handlers(bot) уже є.")

    if changed:
        target.write_text(text, encoding="utf-8")

    return target, backup, original


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
'''

    if pattern.search(text):
        text = pattern.sub(replacement, text, count=1)
        target.write_text(text, encoding="utf-8")
        print("✅ keyboards.py: blacksmith_kb() перевірено/оновлено.")
    else:
        raise SystemExit("❌ Не знайдено def blacksmith_kb() у keyboards.py")

    return target, backup, original


def main():
    root = Path(__file__).resolve().parents[1]

    originals = []
    changed_files = []
    backups = []

    try:
        for patch_func in [write_hotfix_file, patch_keyboards, patch_main]:
            file_path, backup_path, original = patch_func(root)
            changed_files.append(file_path)
            if backup_path:
                backups.append(backup_path)
            if original is not None:
                originals.append((file_path, original))

        for file_path in changed_files:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            if original is not None:
                file_path.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка під час patch_6_0_4e_blacksmith_repair_handler_order.\n"
            "Файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("\n✅ Патч 6.0.4e застосовано успішно.")
    print("\nЗмінені файли:")
    for file_path in changed_files:
        print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо виправлено:")
    print("- створено handlers/blacksmith_repair_hotfix.py")
    print("- repair handler реєструється перед city handlers")
    print("- кнопка 🛠️ Ремонт має відкривати екран ремонту")
    print("\nПісля патча обовʼязково перезапусти бота.")


if __name__ == "__main__":
    main()
