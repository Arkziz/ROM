from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "8_0_3a_auction_sell_handler_order"
TARGET_REL = Path("handlers") / "auction_house.py"

OLD_BLOCK = '''def register_auction_house_handlers(bot):
    if _auction_base_register_handlers_before_sell_equipment_v1:
        _auction_base_register_handlers_before_sell_equipment_v1(bot)

    _auction_register_sell_equipment_handlers(bot)
'''

NEW_BLOCK = '''def register_auction_house_handlers(bot):
    # Важливо: handler для ➕ Виставити товар має реєструватися ДО placeholder-ів 8.0.2.
    # Інакше старий placeholder перехоплює кнопку раніше за реальний flow 8.0.3.
    _auction_register_sell_equipment_handlers(bot)

    if _auction_base_register_handlers_before_sell_equipment_v1:
        _auction_base_register_handlers_before_sell_equipment_v1(bot)
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
    target = root / TARGET_REL

    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/auction_house.py. Спочатку потрібні патчі 8.0.2 і 8.0.3.")

    original = target.read_text(encoding="utf-8")

    if "handler для ➕ Виставити товар має реєструватися ДО placeholder" in original:
        print("ℹ️ Патч 8.0.3a вже застосовано. Змін не потрібно.")
        py_compile.compile(str(target), doraise=True)
        return

    if OLD_BLOCK not in original:
        # Fallback: replace the last register_auction_house_handlers function if it has the wrong call order.
        pattern = re.compile(
            r"def register_auction_house_handlers\(bot\):\n"
            r"\s+if _auction_base_register_handlers_before_sell_equipment_v1:\n"
            r"\s+_auction_base_register_handlers_before_sell_equipment_v1\(bot\)\n\s*\n"
            r"\s+_auction_register_sell_equipment_handlers\(bot\)\n",
            re.MULTILINE,
        )
        updated, count = pattern.subn(NEW_BLOCK, original, count=1)
        if count == 0:
            raise SystemExit(
                "❌ Не знайдено очікуваний блок register_auction_house_handlers у handlers/auction_house.py.\n"
                "Можливо файл уже сильно змінений. Надішли актуальний handlers/auction_house.py."
            )
    else:
        updated = original.replace(OLD_BLOCK, NEW_BLOCK, 1)

    backup = make_backup(root, target)
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_8_0_3a_auction_sell_handler_order.\n"
            "handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.3a Auction Sell Handler Order застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("\nЩо виправлено:")
    print("- реальний handler ➕ Виставити товар тепер реєструється ДО placeholder-а")
    print("- кнопка ➕ Виставити товар має відкривати вибір категорії, а не текст 'буде реалізовано'")
    print("\nПісля патча:")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
