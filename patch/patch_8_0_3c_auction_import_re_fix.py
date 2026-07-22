from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_3c_auction_import_re_fix"
TARGET_REL = Path("handlers") / "auction_house.py"


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

    if "import re" in original:
        print("ℹ️ import re вже є в handlers/auction_house.py. Змін не потрібно.")
        py_compile.compile(str(target), doraise=True)
        return

    backup = make_backup(root, target)

    lines = original.splitlines()

    # Insert import re after first standard import block.
    inserted = False
    for idx, line in enumerate(lines):
        if line.strip() == "from telebot import types":
            lines.insert(idx + 1, "import re")
            inserted = True
            break

    if not inserted:
        # Safe fallback: put it at very top.
        lines.insert(0, "import re")

    updated = "\n".join(lines) + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_8_0_3c_auction_import_re_fix.\n"
            "handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.3c Auction import re fix застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("\nЩо виправлено:")
    print("- додано import re у handlers/auction_house.py")
    print("- вибір предмета більше не має падати з NameError: name 're' is not defined")
    print("\nПісля патча:")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
