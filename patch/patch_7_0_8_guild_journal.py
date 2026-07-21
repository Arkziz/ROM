from pathlib import Path
from datetime import datetime
import py_compile
import sys

PATCH_NAME = "7_0_8_guild_journal"
SYSTEM_MARKER = "# ✅ GUILD JOURNAL CORE V1"
DB_MARKER = "# ✅ GUILD JOURNAL DB WRAPPERS V1"
HANDLER_MARKER = "# ✅ GUILD JOURNAL UI V1"
OLD_HANDLER_MARKER = "# ✅ GUILD JOURNAL OLD HANDLER REPLACED V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ GUILD JOURNAL CORE V1
# ==============================

# 7.0.8
# Журнал гільдії: перегляд останніх подій.


def get_guild_logs(guild_id, limit=20, offset=0):
    init_guild_system()
    ensure_guild_monthly_season(guild_id)

    try:
        limit = int(limit)
    except Exception:
        limit = 20

    try:
        offset = int(offset)
    except Exception:
        offset = 0

    limit = max(1, min(100, limit))
    offset = max(0, offset)

    cursor.execute("""
    SELECT *
    FROM guild_logs
    WHERE guild_id=?
    ORDER BY id DESC
    LIMIT ? OFFSET ?
    """, (
        guild_id,
        limit,
        offset,
    ))

    return cursor.fetchall()


def get_guild_logs_count(guild_id):
    init_guild_system()
    cursor.execute("SELECT COUNT(*) AS cnt FROM guild_logs WHERE guild_id=?", (guild_id,))
    row = cursor.fetchone()

    try:
        return int(row["cnt"] or 0)
    except Exception:
        return int(row[0] or 0) if row else 0
'''

DB_APPEND = r'''

# ==============================
# ✅ GUILD JOURNAL DB WRAPPERS V1
# ==============================

# 7.0.8 wrappers для журналу гільдії.


def get_guild_logs(guild_id, limit=20, offset=0):
    from systems.guild_system import get_guild_logs as _get_guild_logs
    return _get_guild_logs(guild_id=guild_id, limit=limit, offset=offset)


def get_guild_logs_count(guild_id):
    from systems.guild_system import get_guild_logs_count as _get_guild_logs_count
    return _get_guild_logs_count(guild_id=guild_id)
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ GUILD JOURNAL UI V1
# ==============================

# 7.0.8
# Журнал гільдії через ReplyKeyboard.

try:
    from db import get_guild_logs, get_guild_logs_count
except Exception as _guild_logs_import_error:
    print(f"⚠️ Guild logs import failed: {_guild_logs_import_error}")

GUILD_LOGS_PAGE_SIZE = 10
GUILD_LOGS_STATE = {}


def reset_guild_logs_state(user_id):
    GUILD_LOGS_STATE.pop(user_id, None)


def get_guild_logs_state(user_id):
    return GUILD_LOGS_STATE.get(user_id)


def _guild_log_row_get(row, key, fallback=None):
    try:
        return row[key]
    except Exception:
        return fallback


def _guild_log_format_ua_datetime(value):
    value = str(value or "").strip()
    if not value:
        return "невідомо"

    try:
        date_part, time_part = value.split("T", 1)
        year, month, day = date_part.split("-", 2)
        hour_minute = time_part[:5]
        return f"{day}.{month}.{year} {hour_minute}"
    except Exception:
        try:
            date_part = value.split(" ", 1)[0]
            year, month, day = date_part.split("-", 2)
            return f"{day}.{month}.{year}"
        except Exception:
            return value


def guild_logs_kb(user_id, page=0):
    guild = get_user_guild(user_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if not guild:
        kb.add("🔙 Зала Гільдій")
        return kb

    logs_count = get_guild_logs_count(guild["id"])
    max_page = max(0, (logs_count - 1) // GUILD_LOGS_PAGE_SIZE) if logs_count else 0
    page = max(0, min(page, max_page))

    nav = []
    if page > 0:
        nav.append("⬅️ Попередні записи")
    if page < max_page:
        nav.append("➡️ Наступні записи")
    if nav:
        kb.add(*nav)

    kb.add("🔄 Оновити журнал")
    kb.add("🔙 Зала Гільдій")

    GUILD_LOGS_STATE[user_id] = {
        "guild_id": guild["id"],
        "page": page,
    }

    return kb


def build_guild_logs_text(user_id, page=0):
    guild = get_user_guild(user_id)

    if not guild:
        return "❌ Ти не перебуваєш у гільдії."

    logs_count = get_guild_logs_count(guild["id"])
    max_page = max(0, (logs_count - 1) // GUILD_LOGS_PAGE_SIZE) if logs_count else 0
    page = max(0, min(page, max_page))
    offset = page * GUILD_LOGS_PAGE_SIZE

    rows = get_guild_logs(guild["id"], limit=GUILD_LOGS_PAGE_SIZE, offset=offset)

    text = (
        f"📜 Журнал гільдії\n\n"
        f"{get_guild_display_name(guild)}\n\n"
    )

    if not rows:
        return text + "Подій поки немає."

    text += f"Сторінка: {page + 1}/{max_page + 1}\n\n"

    for index, row in enumerate(rows, start=1 + offset):
        event_type = _guild_log_row_get(row, "event_type", "event")
        log_text = _guild_log_row_get(row, "text", "")
        created_at = _guild_log_format_ua_datetime(_guild_log_row_get(row, "created_at", ""))

        text += (
            f"{index}. {created_at}\n"
            f"   {log_text}\n"
        )

    return text.strip()


def show_guild_logs(bot, message, page=0):
    user_id = message.from_user.id

    # Clear other navigation states so journal buttons are not intercepted.
    for reset_func_name in [
        "reset_guild_browse_state",
        "reset_guild_application_review_state",
        "reset_guild_member_manage_state",
    ]:
        try:
            globals()[reset_func_name](user_id)
        except Exception:
            pass

    bot.send_message(
        message.chat.id,
        build_guild_logs_text(user_id, page),
        reply_markup=guild_logs_kb(user_id, page)
    )


def handle_guild_logs_message(bot, message):
    user_id = message.from_user.id
    text = (message.text or "").strip()
    state = get_guild_logs_state(user_id)

    if not state:
        return False

    page = int(state.get("page", 0) or 0)

    if text == "🔙 Зала Гільдій":
        reset_guild_logs_state(user_id)
        open_guild_hall(bot, message.chat.id, user_id)
        return True

    if text == "🔄 Оновити журнал":
        show_guild_logs(bot, message, page)
        return True

    if text == "⬅️ Попередні записи":
        show_guild_logs(bot, message, max(0, page - 1))
        return True

    if text == "➡️ Наступні записи":
        show_guild_logs(bot, message, page + 1)
        return True

    return False


try:
    _base_register_guild_handlers_before_logs_v1 = register_guild_handlers
except Exception:
    _base_register_guild_handlers_before_logs_v1 = None


def register_guild_handlers(bot):
    if _base_register_guild_handlers_before_logs_v1 is not None:
        _base_register_guild_handlers_before_logs_v1(bot)

    @bot.message_handler(func=lambda message: get_guild_logs_state(message.from_user.id) is not None)
    def guild_logs_state_message(message):
        handle_guild_logs_message(bot, message)

    @bot.message_handler(func=lambda message: message.text == "📜 Журнал")
    def guild_logs_message_v2(message):
        show_guild_logs(bot, message, 0)
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def append_if_missing(root, target, marker, code):
    original = target.read_text(encoding="utf-8")
    if marker in original:
        return None, original, False
    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + code + "\n", encoding="utf-8")
    return backup, original, True


def patch_system(root):
    target = root / "systems" / "guild_system.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено systems/guild_system.py")
    backup, original, changed = append_if_missing(root, target, SYSTEM_MARKER, SYSTEM_APPEND)
    return target, backup, original, changed


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")
    backup, original, changed = append_if_missing(root, target, DB_MARKER, DB_APPEND)
    return target, backup, original, changed


def patch_handler_append(root):
    target = root / "handlers" / "guild.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/guild.py")
    backup, original, changed = append_if_missing(root, target, HANDLER_MARKER, HANDLER_APPEND)
    return target, backup, original, changed


def patch_old_journal_handler(root):
    target = root / "handlers" / "guild.py"
    original = target.read_text(encoding="utf-8")

    if OLD_HANDLER_MARKER in original:
        return target, None, original, False

    old_block = '''    @bot.message_handler(func=lambda message: message.text == "📜 Журнал")
    def guild_logs_message(message):
        send_guild_section(bot, message, build_guild_placeholder_text("📜 Журнал гільдії", "7.0.8"))
'''

    new_block = '''    @bot.message_handler(func=lambda message: message.text == "📜 Журнал")
    def guild_logs_message(message):
        show_guild_logs(bot, message, 0)
        # ✅ GUILD JOURNAL OLD HANDLER REPLACED V1
'''

    if old_block not in original:
        return target, None, original, False

    backup = make_backup(root, target)
    updated = original.replace(old_block, new_block, 1)
    target.write_text(updated, encoding="utf-8")
    return target, backup, original, True


def patch_progress_state_passthrough(root):
    target = root / "handlers" / "guild.py"
    original = target.read_text(encoding="utf-8")
    text = original
    changed = False

    # Extend 7.0.7a global button handler if present.
    anchor = '''    if text == "📨 Заявки":
        try:
            _guild_progress_reset_navigation_states_v1(user_id)
            show_guild_applications(bot, message)
            return True
        except Exception:
            pass

    return False
'''

    replacement = '''    if text == "📨 Заявки":
        try:
            _guild_progress_reset_navigation_states_v1(user_id)
            show_guild_applications(bot, message)
            return True
        except Exception:
            pass

    if text == "📜 Журнал":
        try:
            _guild_progress_reset_navigation_states_v1(user_id)
            show_guild_logs(bot, message, 0)
            return True
        except Exception:
            pass

    return False
'''

    if anchor in text and "show_guild_logs(bot, message, 0)" not in text.split(anchor)[0][-1000:]:
        text = text.replace(anchor, replacement, 1)
        changed = True

    if not changed:
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(text, encoding="utf-8")
    return target, backup, original, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_system, patch_db, patch_handler_append, patch_old_journal_handler, patch_progress_state_passthrough]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        unique_files = []
        for file_path in changed_files:
            if file_path not in unique_files:
                unique_files.append(file_path)

        for file_path in unique_files:
            py_compile.compile(str(file_path), doraise=True)

        sys.path.insert(0, str(root))
        from db import init_guild_system
        init_guild_system()

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_7_0_8_guild_journal.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.8 Guild Journal застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- 📜 Журнал гільдії")
    print("- останні 10 подій на сторінку")
    print("- пагінація журналу: ⬅️ / ➡️")
    print("- дати журналу у форматі DD.MM.YYYY HH:MM")
    print("- журнал використовує існуючу таблицю guild_logs")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\guild_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
