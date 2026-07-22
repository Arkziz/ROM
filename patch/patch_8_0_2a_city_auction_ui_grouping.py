from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "8_0_2a_city_auction_ui_grouping"

CITY_KB_CODE = r'''
def city_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Міські напрямки згруповані по 2 кнопки в ряд.
    # 🗺️ Мапа завжди окремо і останньою кнопкою внизу.
    kb.add("🛒 Торговий ряд", "🏛️ Торговий дім")
    kb.add("⚒️ Ремісничий квартал", "📜 Гільдія Найманців")
    kb.add("🏰 Зала Гільдій", "🏛️ Ратуша")
    kb.add("🍺 Таверна")
    kb.add("🗺️ Мапа")

    return kb
'''

AUCTION_KB_CODE = r'''
def auction_house_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Основні дії Торгового Дому згруповані по 2 кнопки в ряд.
    # 🔙 Місто завжди окремо і останньою кнопкою внизу.
    kb.add(AUCTION_BUY_BUTTON, AUCTION_SELL_BUTTON)
    kb.add(AUCTION_MY_LOTS_BUTTON, AUCTION_UNCLAIMED_ITEMS_BUTTON)
    kb.add(AUCTION_SOLD_BUTTON, AUCTION_HISTORY_BUTTON)
    kb.add(AUCTION_BACK_TO_CITY_BUTTON)

    return kb
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def replace_function(text, function_name, new_code):
    pattern = re.compile(rf"^def\s+{re.escape(function_name)}\s*\([^)]*\):\n", re.MULTILINE)
    match = pattern.search(text)

    if not match:
        return text, False

    start = match.start()
    next_match = re.search(r"^def\s+\w+\s*\(|^class\s+\w+\s*[:(]", text[match.end():], re.MULTILINE)

    if next_match:
        end = match.end() + next_match.start()
    else:
        end = len(text)

    updated = text[:start] + new_code.strip() + "\n\n" + text[end:].lstrip("\n")
    return updated, True


def patch_keyboards(root):
    target = root / "keyboards.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено keyboards.py")

    original = target.read_text(encoding="utf-8")
    updated, replaced = replace_function(original, "city_kb", CITY_KB_CODE)

    if not replaced:
        raise SystemExit("❌ Не знайдено def city_kb() у keyboards.py")

    if updated == original:
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(updated, encoding="utf-8")
    return target, backup, original, True


def patch_auction_handler(root):
    target = root / "handlers" / "auction_house.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/auction_house.py. Спочатку потрібен патч 8.0.2.")

    original = target.read_text(encoding="utf-8")
    updated, replaced = replace_function(original, "auction_house_kb", AUCTION_KB_CODE)

    if not replaced:
        raise SystemExit("❌ Не знайдено def auction_house_kb() у handlers/auction_house.py")

    if updated == original:
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(updated, encoding="utf-8")
    return target, backup, original, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_keyboards, patch_auction_handler]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        compile_targets = [root / "keyboards.py", root / "handlers" / "auction_house.py"]
        for file_path in compile_targets:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_8_0_2a_city_auction_ui_grouping.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.2a City/Auction UI grouping застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо змінено:")
    print("- 🏛️ Торговий дім перенесено вище 🗺️ Мапи")
    print("- city_kb() згруповано компактніше")
    print("- 🗺️ Мапа залишилась окремою останньою кнопкою")
    print("- auction_house_kb() згруповано по 2 кнопки в ряд")
    print("- 🔙 Місто залишилось окремою останньою кнопкою")

    print("\nПісля патча:")
    print("python -m py_compile .\\keyboards.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
