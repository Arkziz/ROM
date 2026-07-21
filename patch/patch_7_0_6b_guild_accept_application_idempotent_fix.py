from pathlib import Path
from datetime import datetime
import py_compile
import sys

PATCH_NAME = "7_0_6b_guild_accept_application_idempotent_fix"
SYSTEM_MARKER = "# ✅ GUILD ACCEPT APPLICATION IDEMPOTENT FIX V1"
DB_MARKER = "# ✅ GUILD ACCEPT APPLICATION IDEMPOTENT FIX DB WRAPPER V1"
HANDLER_MARKER = "# ✅ GUILD ACCEPT APPLICATION UI SAFE FIX V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ GUILD ACCEPT APPLICATION IDEMPOTENT FIX V1
# ==============================

# 7.0.6b
# Fix проблеми:
# - гравець уже додався в guild_members;
# - заявка лишилась pending;
# - повторне натискання ✅ Прийняти заявку падало через UNIQUE constraint
#   guild_applications(guild_id, user_id, status).
#
# Рішення:
# - прийняття заявки стало idempotent;
# - якщо гравець уже в цій гільдії, pending-заявка просто позначається accepted/removes duplicate safely;
# - якщо already є accepted-заявка з таким UNIQUE ключем, pending-заявка видаляється;
# - старі pending-заявки гравця в інші гільдії скасовуються.


def _guild_safe_set_application_status(application_id, status, processed_by=None):
    """
    Безпечно змінює статус заявки з урахуванням UNIQUE(guild_id, user_id, status).

    Якщо запис із таким status уже існує, поточна заявка видаляється,
    щоб не ламати БД і не залишати pending-дублікат.
    """

    app = get_guild_application_by_id(application_id)
    if not app:
        return False

    now = now_iso()

    try:
        cursor.execute("""
        UPDATE guild_applications
        SET status=?, processed_at=?, processed_by=?
        WHERE id=?
        """, (
            status,
            now,
            processed_by,
            application_id,
        ))
        conn.commit()
        return True
    except Exception as error:
        if "UNIQUE constraint failed" not in str(error):
            raise

        # Є інша заявка з таким самим guild_id/user_id/status.
        # Поточний pending-запис більше не потрібен.
        cursor.execute("DELETE FROM guild_applications WHERE id=?", (application_id,))
        conn.commit()
        return True


def _guild_cancel_other_pending_applications(user_id, except_application_id=None, processed_by=None):
    now = now_iso()

    if except_application_id is None:
        cursor.execute("""
        UPDATE guild_applications
        SET status=?, processed_at=?, processed_by=?
        WHERE user_id=? AND status=?
        """, (
            GUILD_APPLICATION_CANCELLED,
            now,
            processed_by,
            user_id,
            GUILD_APPLICATION_PENDING,
        ))
    else:
        cursor.execute("""
        UPDATE guild_applications
        SET status=?, processed_at=?, processed_by=?
        WHERE user_id=? AND status=? AND id != ?
        """, (
            GUILD_APPLICATION_CANCELLED,
            now,
            processed_by,
            user_id,
            GUILD_APPLICATION_PENDING,
            except_application_id,
        ))

    conn.commit()


# FINAL OVERRIDE for 7.0.5 accept_guild_application.
def accept_guild_application(actor_user_id, application_id):
    init_guild_system()

    app = get_guild_application_by_id(application_id)

    if not app:
        return {"success": False, "message": "❌ Заявку не знайдено."}

    guild_id = app["guild_id"]
    applicant_user_id = app["user_id"]

    if app["status"] != GUILD_APPLICATION_PENDING:
        return {"success": False, "message": "❌ Ця заявка вже не очікує розгляду."}

    if not can_manage_guild_applications(actor_user_id, guild_id):
        return {"success": False, "message": "❌ У тебе немає прав для обробки заявок."}

    guild = get_guild_by_id(guild_id)
    if not guild:
        return {"success": False, "message": "❌ Гільдію не знайдено."}

    applicant_name = get_character_name_by_user_id(applicant_user_id)
    existing_member = get_user_guild_member(applicant_user_id)

    # Idempotent recovery: гравець уже в цій гільдії, але pending-заявка висить.
    if existing_member and int(existing_member["guild_id"]) == int(guild_id):
        _guild_safe_set_application_status(
            application_id,
            GUILD_APPLICATION_ACCEPTED,
            processed_by=actor_user_id,
        )
        _guild_cancel_other_pending_applications(
            applicant_user_id,
            except_application_id=application_id,
            processed_by=actor_user_id,
        )
        return {
            "success": True,
            "message": f"✅ {applicant_name} уже перебуває в цій гільдії. Заявку очищено."
        }

    # Якщо гравець уже в іншій гільдії — pending-заявку треба прибрати без падіння.
    if existing_member and int(existing_member["guild_id"]) != int(guild_id):
        _guild_safe_set_application_status(
            application_id,
            GUILD_APPLICATION_REJECTED,
            processed_by=actor_user_id,
        )
        return {"success": False, "message": "❌ Гравець уже перебуває в іншій гільдії. Заявку відхилено."}

    member_count = get_guild_member_count(guild_id)
    member_limit = int(guild["member_limit"] or DEFAULT_GUILD_MEMBER_LIMIT)

    if member_count >= member_limit:
        return {"success": False, "message": "❌ У гільдії немає вільних місць."}

    now = now_iso()

    try:
        cursor.execute("""
        INSERT INTO guild_members (guild_id, user_id, role, joined_at)
        VALUES (?, ?, ?, ?)
        """, (
            guild_id,
            applicant_user_id,
            GUILD_ROLE_MEMBER,
            now,
        ))
        conn.commit()
    except Exception as error:
        # Якщо паралельно/раніше гравець уже був доданий — переводимо в idempotent branch.
        if "UNIQUE constraint failed" not in str(error):
            raise

    _guild_safe_set_application_status(
        application_id,
        GUILD_APPLICATION_ACCEPTED,
        processed_by=actor_user_id,
    )

    _guild_cancel_other_pending_applications(
        applicant_user_id,
        except_application_id=application_id,
        processed_by=actor_user_id,
    )

    try:
        add_guild_log(
            guild_id=guild_id,
            event_type="application_accepted",
            text=f"{applicant_name} вступив до гільдії."
        )
    except Exception:
        pass

    return {"success": True, "message": f"✅ {applicant_name} прийнято до гільдії."}


def cleanup_stale_guild_applications():
    """
    Чистить старі pending-заявки від гравців, які вже є в тій самій гільдії.
    Також прибирає pending-заявки в інші гільдії для гравців, які вже десь перебувають.
    """

    init_guild_system()

    fixed_same_guild = 0
    cancelled_other_guild = 0

    cursor.execute("""
    SELECT ga.id, ga.guild_id, ga.user_id, gm.guild_id AS member_guild_id
    FROM guild_applications ga
    JOIN guild_members gm ON gm.user_id = ga.user_id
    WHERE ga.status=?
    """, (GUILD_APPLICATION_PENDING,))

    rows = cursor.fetchall()

    for row in rows:
        app_id = row["id"]
        app_guild_id = row["guild_id"]
        member_guild_id = row["member_guild_id"]

        if int(app_guild_id) == int(member_guild_id):
            _guild_safe_set_application_status(app_id, GUILD_APPLICATION_ACCEPTED, processed_by=None)
            fixed_same_guild += 1
        else:
            _guild_safe_set_application_status(app_id, GUILD_APPLICATION_CANCELLED, processed_by=None)
            cancelled_other_guild += 1

    return {
        "fixed_same_guild": fixed_same_guild,
        "cancelled_other_guild": cancelled_other_guild,
    }
'''

DB_APPEND = r'''

# ==============================
# ✅ GUILD ACCEPT APPLICATION IDEMPOTENT FIX DB WRAPPER V1
# ==============================

# 7.0.6b wrapper-и для безпечного прийняття заявок.


def cleanup_stale_guild_applications():
    from systems.guild_system import cleanup_stale_guild_applications as _cleanup_stale_guild_applications
    return _cleanup_stale_guild_applications()
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ GUILD ACCEPT APPLICATION UI SAFE FIX V1
# ==============================

# 7.0.6b
# UI safety: якщо прийняття заявки повертає result або виняток,
# бот не має падати і має оновити список заявок.

try:
    from db import cleanup_stale_guild_applications
except Exception as _guild_cleanup_import_error:
    print(f"⚠️ Guild cleanup import failed: {_guild_cleanup_import_error}")


# Override show_guild_applications to clean stale pending apps before display.
def show_guild_applications(bot, message):
    try:
        cleanup_stale_guild_applications()
    except Exception:
        pass

    user_id = message.from_user.id
    text = build_guild_applications_text(user_id)
    kb = guild_applications_kb(user_id)
    bot.send_message(message.chat.id, text, reply_markup=kb)


# Override detailed application review handler with exception safety.
def handle_guild_application_review_message(bot, message):
    user_id = message.from_user.id
    text = (message.text or "").strip()
    state = get_guild_application_review_state(user_id)

    if not state:
        return False

    if text == "🔙 Зала Гільдій":
        reset_guild_application_review_state(user_id)
        open_guild_hall(bot, message.chat.id, user_id)
        return True

    if text in ["📨 Заявки", "🔄 Оновити заявки"]:
        show_guild_applications(bot, message)
        return True

    buttons = state.get("buttons", {})
    if text in buttons:
        show_guild_application_detail(bot, message, buttons[text])
        return True

    if text in ["✅ Прийняти заявку", "❌ Відхилити заявку"]:
        application_id = state.get("selected_application_id")
        if not application_id:
            bot.send_message(message.chat.id, "❌ Спочатку обери заявку зі списку.", reply_markup=guild_applications_kb(user_id))
            return True

        try:
            if text == "✅ Прийняти заявку":
                result = accept_guild_application(user_id, application_id)
            else:
                result = reject_guild_application(user_id, application_id)
        except Exception as error:
            result = {
                "success": False,
                "message": f"❌ Не вдалося обробити заявку. Помилка: {error}"
            }

        bot.send_message(message.chat.id, result.get("message", ""), reply_markup=guild_applications_kb(user_id))
        show_guild_applications(bot, message)
        return True

    return False
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
    backup, original, changed = append_if_missing(root, target, "# ✅ GUILD ACCEPT APPLICATION IDEMPOTENT FIX V1", SYSTEM_APPEND)
    return target, backup, original, changed


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")
    backup, original, changed = append_if_missing(root, target, "# ✅ GUILD ACCEPT APPLICATION IDEMPOTENT FIX DB WRAPPER V1", DB_APPEND)
    return target, backup, original, changed


def patch_handler(root):
    target = root / "handlers" / "guild.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/guild.py")
    backup, original, changed = append_if_missing(root, target, "# ✅ GUILD ACCEPT APPLICATION UI SAFE FIX V1", HANDLER_APPEND)
    return target, backup, original, changed


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_system, patch_db, patch_handler]:
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
        from db import init_guild_system, cleanup_stale_guild_applications
        init_guild_system()
        cleanup_result = cleanup_stale_guild_applications()

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_7_0_6b_guild_accept_application_idempotent_fix.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.6b Guild accept application idempotent fix застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо виправлено:")
    print("- прийняття заявки тепер idempotent і не падає при повторному натисканні")
    print("- якщо гравець уже у цій гільдії, pending-заявка очищається")
    print("- якщо accepted-заявка вже існує, pending-дублікат видаляється")
    print("- старі pending-заявки гравців, які вже у гільдії, очищені")
    print("- UI обробки заявок більше не має валити polling через IntegrityError")

    try:
        print("\nCleanup result:")
        print(f"- fixed same guild pending: {cleanup_result.get('fixed_same_guild', 0)}")
        print(f"- cancelled other guild pending: {cleanup_result.get('cancelled_other_guild', 0)}")
    except Exception:
        pass

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\guild_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
