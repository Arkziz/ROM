from pathlib import Path
from datetime import datetime
import py_compile
import sys

PATCH_NAME = "7_0_8a_guild_journal_names"
SYSTEM_MARKER = "# ✅ GUILD JOURNAL CHARACTER NAMES CORE V1"
HANDLER_MARKER = "# ✅ GUILD JOURNAL CHARACTER NAMES UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ GUILD JOURNAL CHARACTER NAMES CORE V1
# ==============================

# 7.0.8a
# Future logs: заявка до гільдії пише імʼя персонажа, а не user_id.

try:
    _base_create_guild_application_before_journal_names_v1 = create_guild_application
except Exception:
    _base_create_guild_application_before_journal_names_v1 = None


def create_guild_application(user_id, guild_id):
    """
    FINAL OVERRIDE:
    Подача заявки з журналом через character_name замість user_id.
    """

    init_guild_system()

    if is_user_in_guild(user_id):
        return {
            "success": False,
            "message": "❌ Ти вже перебуваєш у гільдії."
        }

    guild = get_guild_by_id(guild_id)

    if not guild:
        return {
            "success": False,
            "message": "❌ Гільдію не знайдено."
        }

    cursor.execute("""
    SELECT * FROM guild_applications
    WHERE guild_id=? AND user_id=? AND status=?
    """, (
        guild_id,
        user_id,
        GUILD_APPLICATION_PENDING,
    ))

    if cursor.fetchone():
        return {
            "success": False,
            "message": "ℹ️ Ти вже подав заявку в цю гільдію."
        }

    cursor.execute("""
    INSERT INTO guild_applications (guild_id, user_id, status, created_at)
    VALUES (?, ?, ?, ?)
    """, (
        guild_id,
        user_id,
        GUILD_APPLICATION_PENDING,
        now_iso(),
    ))

    conn.commit()

    applicant_name = get_character_name_by_user_id(user_id)

    add_guild_log(
        guild_id=guild_id,
        event_type="application_created",
        text=f"Нова заявка до гільдії від {applicant_name}."
    )

    return {
        "success": True,
        "message": "✅ Заявку до гільдії подано."
    }
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ GUILD JOURNAL CHARACTER NAMES UI V1
# ==============================

# 7.0.8a
# Existing logs: під час показу журналу замінюємо user_id=123 на імʼя персонажа.
# Це не змінює старі записи в БД, але показує їх красиво в UI.

import re as _guild_journal_re


def _guild_journal_character_name_by_user_id_v1(user_id):
    try:
        from db import cursor
        cursor.execute("SELECT character_name FROM users WHERE user_id=?", (int(user_id),))
        row = cursor.fetchone()
        if not row:
            return f"user_id={user_id}"
        try:
            return row["character_name"] or f"user_id={user_id}"
        except Exception:
            return row[0] or f"user_id={user_id}"
    except Exception:
        return f"user_id={user_id}"


def _guild_journal_pretty_text_v1(text):
    text = str(text or "")

    def repl(match):
        user_id = match.group(1)
        return _guild_journal_character_name_by_user_id_v1(user_id)

    return _guild_journal_re.sub(r"user_id=(\d+)", repl, text)


# Override build_guild_logs_text to format user_id in log messages as character_name.
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
        log_text = _guild_log_row_get(row, "text", "")
        log_text = _guild_journal_pretty_text_v1(log_text)
        created_at = _guild_log_format_ua_datetime(_guild_log_row_get(row, "created_at", ""))

        text += (
            f"{index}. {created_at}\n"
            f"   {log_text}\n"
        )

    return text.strip()
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


def patch_handler(root):
    target = root / "handlers" / "guild.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/guild.py")
    backup, original, changed = append_if_missing(root, target, HANDLER_MARKER, HANDLER_APPEND)
    return target, backup, original, changed


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_system, patch_handler]:
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
            "❌ Помилка під час patch_7_0_8a_guild_journal_names.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.8a Guild Journal Names застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо виправлено:")
    print("- старі записи журналу з user_id=... відображаються як імʼя персонажа")
    print("- нові записи 'Нова заявка...' одразу пишуть character_name, а не user_id")
    print("- БД старих логів не переписується, виправлення робиться на рівні UI")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\guild_system.py")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
