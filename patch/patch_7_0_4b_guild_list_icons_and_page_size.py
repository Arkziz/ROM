from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "7_0_4b_guild_list_icons_and_page_size"
TARGET_RELATIVE_PATH = Path("handlers") / "guild.py"
MARKER = "# ✅ GUILD LIST BUTTON ICONS V1"

APPEND_CODE = r'''

# ==============================
# ✅ GUILD LIST BUTTON ICONS V1
# ==============================

# 7.0.4b
# Виправляє кнопки у списку гільдій:
# - у кнопці показується реальна іконка guild["icon"], а не захардкожений 🏰
# - кількість гільдій на сторінку залишається 8

GUILD_LIST_PAGE_SIZE = 8


def _guild_row_get(row, key, fallback=None):
    try:
        return row[key]
    except Exception:
        return fallback


def guild_list_kb(user_id, page=0):
    rows = get_public_guild_list(
        limit=GUILD_LIST_PAGE_SIZE + 1,
        offset=page * GUILD_LIST_PAGE_SIZE
    )
    shown = rows[:GUILD_LIST_PAGE_SIZE]

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = {}

    for guild in shown:
        guild_id = _guild_row_get(guild, "id")
        icon = _guild_row_get(guild, "icon", "🏰") or "🏰"
        tag = _guild_row_get(guild, "tag", "???") or "???"
        name = _guild_row_get(guild, "name", "Гільдія") or "Гільдія"
        member_limit = _guild_row_get(guild, "member_limit", 30) or 30

        try:
            member_count = guild["member_count"]
        except Exception:
            member_count = get_guild_member_count(guild_id)

        label = f"{icon} [{tag}] {name} ({member_count}/{member_limit})"

        # Telegram reply buttons should not be too long.
        if len(label) > 60:
            label = label[:57] + "..."

        buttons[label] = guild_id
        kb.add(label)

    nav = []
    if page > 0:
        nav.append("⬅️ Попередні гільдії")
    if len(rows) > GUILD_LIST_PAGE_SIZE:
        nav.append("➡️ Наступні гільдії")
    if nav:
        kb.add(*nav)

    kb.add("🔙 Зала Гільдій")

    GUILD_BROWSE_STATE[user_id] = {
        "page": page,
        "buttons": buttons,
        "selected_guild_id": None,
    }

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


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(
            f"❌ Не знайдено файл: {target}\n"
            "Спочатку застосуй 7.0.2/7.0.4 для handlers/guild.py."
        )

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ GUILD LIST BUTTON ICONS V1 уже застосований, пропускаю.")
        return

    backup_path = make_backup(root, target)

    updated = original.rstrip() + "\n" + APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_4b_guild_list_icons_and_page_size.\n"
            "handlers/guild.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.4b Guild List Icons застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ handlers/guild.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- кнопки у списку гільдій тепер показують реальну іконку гільдії")
    print("- замість захардкоженого 🏰 використовується guild['icon']")
    print("- ліміт залишився 8 гільдій на сторінку")
    print("- навігація сторінок і 🔙 Зала Гільдій не змінені")


if __name__ == "__main__":
    main()
