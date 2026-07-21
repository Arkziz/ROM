from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "7_0_3a_guild_sqlite_row_factory"
TARGET_RELATIVE_PATH = Path("systems") / "guild_system.py"
MARKER = "# ✅ GUILD SQLITE ROW FACTORY FIX V1"

INSERT_CODE = r'''

# ==============================
# ✅ GUILD SQLITE ROW FACTORY FIX V1
# ==============================

# 7.0.3a
# У проєкті sqlite cursor може повертати tuple, а guild_system працює з row["field"].
# sqlite3.Row підтримує обидва формати доступу:
# - row["guild_id"]
# - row[0]
# Тому це безпечний fix для гільдійних таблиць і сумісний зі старим кодом.

import sqlite3 as _guild_sqlite3

try:
    conn.row_factory = _guild_sqlite3.Row
except Exception:
    pass

try:
    cursor.row_factory = _guild_sqlite3.Row
except Exception:
    pass
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
            "Спочатку застосуй patch_7_0_1_guild_core_db.py"
        )

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ GUILD SQLITE ROW FACTORY FIX V1 уже застосований, пропускаю.")
        return

    backup_path = make_backup(root, target)

    anchor = "from db import conn, cursor\n"

    if anchor not in original:
        raise SystemExit("❌ Не знайдено рядок 'from db import conn, cursor' у systems/guild_system.py")

    updated = original.replace(anchor, anchor + INSERT_CODE + "\n", 1)
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_3a_guild_sqlite_row_factory.\n"
            "systems/guild_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    # Runtime sanity check in current DB.
    import sys
    sys.path.insert(0, str(root))

    from systems.guild_system import init_guild_system, get_user_guild_member, get_user_guild

    init_guild_system()

    print("✅ Патч 7.0.3a Guild sqlite Row factory fix застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ systems/guild_system.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- guild_system тепер отримує sqlite rows з доступом row['field']")
    print("- помилка tuple indices must be integers or slices, not str має зникнути")
    print("- створена перед падінням гільдія, ймовірно, вже збережена в БД")
    print("")
    print("Після патча перезапусти бота і зайди в 🏰 Зала Гільдій.")


if __name__ == "__main__":
    main()
