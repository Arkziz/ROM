from pathlib import Path
from datetime import datetime
import py_compile
import shutil


PATCH_NAME = "9_0_8g_rename_blacksmith_handler"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"

    backup_path.write_text(
        target.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    return backup_path


def main():
    root = Path(__file__).resolve().parents[1]

    old_path = root / "handlers" / "blacksmith_repair_hotfix.py"
    new_path = root / "handlers" / "blacksmith.py"
    main_path = root / "main.py"

    if not main_path.exists():
        raise SystemExit("❌ main.py не знайдено.")

    backups = []

    # ==============================
    # 1. Rename handler file
    # ==============================

    if old_path.exists() and new_path.exists():
        raise SystemExit(
            "❌ Знайдено обидва файли:\n"
            f"- {old_path}\n"
            f"- {new_path}\n\n"
            "Щоб не перезаписати код, патч зупинено. "
            "Потрібно вручну перевірити, який файл актуальний."
        )

    if old_path.exists():
        backups.append(make_backup(root, old_path))
        shutil.move(str(old_path), str(new_path))
        print(f"✅ Перейменовано: {old_path.name} → {new_path.name}")

    elif new_path.exists():
        print("ℹ️ handlers/blacksmith.py вже існує. Перейменування не потрібне.")

    else:
        raise SystemExit(
            "❌ Не знайдено ні handlers/blacksmith_repair_hotfix.py, "
            "ні handlers/blacksmith.py."
        )

    # ==============================
    # 2. Update main.py imports/calls
    # ==============================

    main_text = main_path.read_text(encoding="utf-8")
    original_main_text = main_text
    backups.append(make_backup(root, main_path))

    old_import = "from handlers.blacksmith_repair_hotfix import register_blacksmith_repair_hotfix_handlers"
    new_import = "from handlers.blacksmith import register_blacksmith_repair_hotfix_handlers"

    if old_import in main_text:
        main_text = main_text.replace(old_import, new_import)
        print("✅ main.py: import оновлено на handlers.blacksmith")
    elif new_import in main_text:
        print("ℹ️ main.py: import уже оновлений.")
    else:
        print(
            "⚠️ main.py: старий import не знайдено. "
            "Можливо, імпорт уже змінений або має інший формат."
        )

    # Якщо десь у main.py залишились прямі згадки модуля, прибираємо.
    main_text = main_text.replace(
        "handlers.blacksmith_repair_hotfix",
        "handlers.blacksmith"
    )

    main_path.write_text(main_text, encoding="utf-8")

    # ==============================
    # 3. Compile checks
    # ==============================

    try:
        py_compile.compile(str(new_path), doraise=True)
        py_compile.compile(str(main_path), doraise=True)

    except Exception as error:
        # Restore main.py
        main_path.write_text(original_main_text, encoding="utf-8")

        # Try to restore file rename
        if new_path.exists() and not old_path.exists():
            shutil.move(str(new_path), str(old_path))

        raise SystemExit(
            "❌ Помилка компіляції після перейменування.\n"
            "main.py і blacksmith handler відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("")
    print("✅ Патч 9.0.8g застосовано успішно.")
    print(f"✅ Актуальний файл Коваля: {new_path}")
    print("✅ main.py пройшов py_compile.")
    print("✅ handlers/blacksmith.py пройшов py_compile.")
    print("")
    print("Backup:")
    for backup in backups:
        print(f"- {backup}")
    print("")
    print("Після патча запусти:")
    print("python -m py_compile .\\handlers\\blacksmith.py")
    print("python -m py_compile .\\main.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()