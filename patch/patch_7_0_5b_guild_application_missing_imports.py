from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "7_0_5b_guild_application_missing_imports"
TARGET_RELATIVE_PATH = Path("handlers") / "guild.py"
MARKER = "# ✅ GUILD APPLICATION REVIEW IMPORT FIX V1"

APPEND_CODE = r'''

# ==============================
# ✅ GUILD APPLICATION REVIEW IMPORT FIX V1
# ==============================

# 7.0.5b
# Hotfix: 7.0.5 додав UI для заявок нижче основного import-блоку,
# але частина db-helper-ів не була імпортована у globals handlers/guild.py.
# Python шукає ці імена під час виконання функцій, тому достатньо додати їх тут.

try:
    from db import (
        can_manage_guild_applications,
        get_guild_applications,
        get_guild_application_by_id,
        accept_guild_application,
        reject_guild_application,
    )
except Exception as _guild_application_import_error:
    print(f"⚠️ Guild application import fix failed: {_guild_application_import_error}")
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
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(
            f"❌ Не знайдено файл: {target}\n"
            "Спочатку застосуй 7.0.5 для handlers/guild.py."
        )

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ GUILD APPLICATION REVIEW IMPORT FIX V1 уже застосований, пропускаю.")
        return

    backup_path = make_backup(root, target)
    updated = original.rstrip() + "\n" + APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_5b_guild_application_missing_imports.\n"
            "handlers/guild.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.5b Guild Application Missing Imports застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ handlers/guild.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- can_manage_guild_applications тепер доступний у handlers/guild.py")
    print("- get_guild_applications тепер доступний у handlers/guild.py")
    print("- accept_guild_application / reject_guild_application тепер доступні")
    print("- кнопка 📨 Заявки більше не має падати з NameError")
    print("")
    print("Після патча перезапусти бота.")


if __name__ == "__main__":
    main()
