from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_4a_auction_potion_button_conflict_fix"
TARGET_REL = Path("handlers") / "auction_house.py"

OLD_BUTTON = 'AUCTION_STACK_CATEGORY_POTION_BUTTON = "🧪 Зілля"'
NEW_BUTTON = 'AUCTION_STACK_CATEGORY_POTION_BUTTON = "🧪 Зілля для продажу"'

REPLACEMENTS = [
    ('• 🧪 Зілля — стекові предмети, можна виставляти частинами.',
     '• 🧪 Зілля для продажу — стекові предмети, можна виставляти частинами.'),
    ('title = "🧪 Виставлення зілля" if category == "potion" else "🪨 Виставлення матеріалів"',
     'title = "🧪 Виставлення зілля" if category == "potion" else "🪨 Виставлення матеріалів"'),
]

MARKER = "# ✅ AUCTION HOUSE POTION BUTTON CONFLICT FIX V1"
MARKER_TEXT = '''\n# ✅ AUCTION HOUSE POTION BUTTON CONFLICT FIX V1\n# Кнопка категорії зілля в Торговому Домі не має збігатися з бойовою кнопкою "🧪 Зілля".\n# Інакше бойовий handler перехоплює кнопку і відповідає: "❗ Ти не в бою".\n'''


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
    target = root / TARGET_REL

    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/auction_house.py. Спочатку потрібен патч 8.0.4.")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч 8.0.4a вже застосовано. Змін не потрібно.")
        py_compile.compile(str(target), doraise=True)
        return

    if OLD_BUTTON not in original:
        raise SystemExit(
            "❌ Не знайдено очікувану кнопку категорії зілля у handlers/auction_house.py:\n"
            f"{OLD_BUTTON}\n\n"
            "Можливо файл уже змінений. Надішли актуальний handlers/auction_house.py."
        )

    backup = make_backup(root, target)
    text = original.replace(OLD_BUTTON, NEW_BUTTON, 1)

    for old, new in REPLACEMENTS:
        if old in text:
            text = text.replace(old, new)

    # Add marker near the top after imports or at end if top location not obvious.
    if "from telebot import types" in text:
        text = text.replace("from telebot import types", "from telebot import types" + MARKER_TEXT, 1)
    else:
        text = text.rstrip() + MARKER_TEXT + "\n"

    target.write_text(text, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_8_0_4a_auction_potion_button_conflict_fix.\n"
            "handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.4a Auction potion button conflict fix застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("\nЩо виправлено:")
    print("- кнопка категорії зілля в Торговому Домі тепер: 🧪 Зілля для продажу")
    print("- вона більше не збігається з бойовою кнопкою 🧪 Зілля")
    print("- бойовий handler більше не має перехоплювати її і писати: ❗ Ти не в бою")
    print("\nПісля патча:")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
