from pathlib import Path
from datetime import datetime
import py_compile
import sys

PATCH_NAME = "7_0_5_guild_application_review"
GUILD_SYSTEM_MARKER = "# ✅ GUILD APPLICATION REVIEW CORE V1"
DB_MARKER = "# ✅ GUILD APPLICATION REVIEW DB WRAPPERS V1"
GUILD_HANDLER_MARKER = "# ✅ GUILD APPLICATION REVIEW UI V1"

GUILD_SYSTEM_APPEND = r'''

# ==============================
# ✅ GUILD APPLICATION REVIEW CORE V1
# ==============================

# 7.0.5
# Обробка заявок у гільдію: прийняти / відхилити.


def get_guild_application_by_id(application_id):
    init_guild_system()
    cursor.execute("SELECT * FROM guild_applications WHERE id=?", (application_id,))
    return cursor.fetchone()


def accept_guild_application(actor_user_id, application_id):
    """
    Приймає заявку до гільдії.
    Доступно тільки leader/officer цієї гільдії.
    """

    init_guild_system()

    app = get_guild_application_by_id(application_id)

    if not app:
        return {"success": False, "message": "❌ Заявку не знайдено."}

    if app["status"] != GUILD_APPLICATION_PENDING:
        return {"success": False, "message": "❌ Ця заявка вже не очікує розгляду."}

    guild_id = app["guild_id"]
    applicant_user_id = app["user_id"]

    if not can_manage_guild_applications(actor_user_id, guild_id):
        return {"success": False, "message": "❌ У тебе немає прав для обробки заявок."}

    guild = get_guild_by_id(guild_id)
    if not guild:
        return {"success": False, "message": "❌ Гільдію не знайдено."}

    if is_user_in_guild(applicant_user_id):
        cursor.execute("""
        UPDATE guild_applications
        SET status=?, processed_at=?, processed_by=?
        WHERE id=?
        """, (
            GUILD_APPLICATION_REJECTED,
            now_iso(),
            actor_user_id,
            application_id,
        ))
        conn.commit()
        return {"success": False, "message": "❌ Гравець уже перебуває в іншій гільдії. Заявку відхилено."}

    member_count = get_guild_member_count(guild_id)
    member_limit = int(guild["member_limit"] or DEFAULT_GUILD_MEMBER_LIMIT)

    if member_count >= member_limit:
        return {"success": False, "message": "❌ У гільдії немає вільних місць."}

    now = now_iso()

    cursor.execute("""
    INSERT INTO guild_members (guild_id, user_id, role, joined_at)
    VALUES (?, ?, ?, ?)
    """, (
        guild_id,
        applicant_user_id,
        GUILD_ROLE_MEMBER,
        now,
    ))

    cursor.execute("""
    UPDATE guild_applications
    SET status=?, processed_at=?, processed_by=?
    WHERE id=?
    """, (
        GUILD_APPLICATION_ACCEPTED,
        now,
        actor_user_id,
        application_id,
    ))

    # Інші pending-заявки цього гравця автоматично скасовуємо.
    cursor.execute("""
    UPDATE guild_applications
    SET status=?, processed_at=?, processed_by=?
    WHERE user_id=? AND status=? AND id != ?
    """, (
        GUILD_APPLICATION_CANCELLED,
        now,
        actor_user_id,
        applicant_user_id,
        GUILD_APPLICATION_PENDING,
        application_id,
    ))

    conn.commit()

    applicant_name = f"user_id={applicant_user_id}"
    try:
        cursor.execute("SELECT character_name FROM users WHERE user_id=?", (applicant_user_id,))
        row = cursor.fetchone()
        if row:
            try:
                applicant_name = row["character_name"] or applicant_name
            except Exception:
                applicant_name = row[0] or applicant_name
    except Exception:
        pass

    add_guild_log(
        guild_id=guild_id,
        event_type="application_accepted",
        text=f"{applicant_name} вступив до гільдії."
    )

    return {"success": True, "message": f"✅ {applicant_name} прийнято до гільдії."}


def reject_guild_application(actor_user_id, application_id):
    """
    Відхиляє заявку до гільдії.
    Доступно тільки leader/officer цієї гільдії.
    """

    init_guild_system()

    app = get_guild_application_by_id(application_id)

    if not app:
        return {"success": False, "message": "❌ Заявку не знайдено."}

    if app["status"] != GUILD_APPLICATION_PENDING:
        return {"success": False, "message": "❌ Ця заявка вже не очікує розгляду."}

    guild_id = app["guild_id"]
    applicant_user_id = app["user_id"]

    if not can_manage_guild_applications(actor_user_id, guild_id):
        return {"success": False, "message": "❌ У тебе немає прав для обробки заявок."}

    now = now_iso()

    cursor.execute("""
    UPDATE guild_applications
    SET status=?, processed_at=?, processed_by=?
    WHERE id=?
    """, (
        GUILD_APPLICATION_REJECTED,
        now,
        actor_user_id,
        application_id,
    ))

    conn.commit()

    applicant_name = f"user_id={applicant_user_id}"
    try:
        cursor.execute("SELECT character_name FROM users WHERE user_id=?", (applicant_user_id,))
        row = cursor.fetchone()
        if row:
            try:
                applicant_name = row["character_name"] or applicant_name
            except Exception:
                applicant_name = row[0] or applicant_name
    except Exception:
        pass

    add_guild_log(
        guild_id=guild_id,
        event_type="application_rejected",
        text=f"Заявку від {applicant_name} відхилено."
    )

    return {"success": True, "message": f"✅ Заявку від {applicant_name} відхилено."}
'''

DB_APPEND = r'''

# ==============================
# ✅ GUILD APPLICATION REVIEW DB WRAPPERS V1
# ==============================

# 7.0.5 wrappers для обробки заявок.


def get_guild_application_by_id(application_id):
    from systems.guild_system import get_guild_application_by_id as _get_guild_application_by_id
    return _get_guild_application_by_id(application_id)


def accept_guild_application(actor_user_id, application_id):
    from systems.guild_system import accept_guild_application as _accept_guild_application
    return _accept_guild_application(actor_user_id=actor_user_id, application_id=application_id)


def reject_guild_application(actor_user_id, application_id):
    from systems.guild_system import reject_guild_application as _reject_guild_application
    return _reject_guild_application(actor_user_id=actor_user_id, application_id=application_id)
'''

GUILD_HANDLER_APPEND = r'''

# ==============================
# ✅ GUILD APPLICATION REVIEW UI V1
# ==============================

# 7.0.5
# ReplyKeyboard UI для заявок: список pending-заявок, вибір заявки,
# прийняти / відхилити.

GUILD_APPLICATION_REVIEW_STATE = {}


def reset_guild_application_review_state(user_id):
    GUILD_APPLICATION_REVIEW_STATE.pop(user_id, None)


def get_guild_application_review_state(user_id):
    return GUILD_APPLICATION_REVIEW_STATE.get(user_id)


def _app_row_get(row, key, fallback=None):
    try:
        return row[key]
    except Exception:
        return fallback


def guild_applications_kb(user_id):
    guild = get_user_guild(user_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if not guild:
        kb.add("🔙 Зала Гільдій")
        return kb

    apps = get_guild_applications(guild["id"], "pending")
    buttons = {}

    for app in apps:
        app_id = _app_row_get(app, "id")
        name = _app_row_get(app, "character_name") or f"user_id={_app_row_get(app, 'user_id')}"
        level = _app_row_get(app, "level") or "?"
        label = f"👤 {name} | рівень {level}"
        if len(label) > 60:
            label = label[:57] + "..."
        buttons[label] = app_id
        kb.add(label)

    kb.add("🔄 Оновити заявки")
    kb.add("🔙 Зала Гільдій")

    GUILD_APPLICATION_REVIEW_STATE[user_id] = {
        "guild_id": guild["id"],
        "buttons": buttons,
        "selected_application_id": None,
    }

    return kb


def guild_application_detail_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Прийняти заявку", "❌ Відхилити заявку")
    kb.add("📨 Заявки")
    kb.add("🔙 Зала Гільдій")
    return kb


def build_guild_applications_text(user_id):
    guild = get_user_guild(user_id)

    if not guild:
        return "❌ Ти не перебуваєш у гільдії."

    if not can_manage_guild_applications(user_id, guild["id"]):
        return "❌ Переглядати і обробляти заявки можуть тільки 👑 Голова або 🛡 Заступник."

    apps = get_guild_applications(guild["id"], "pending")
    guild_name = get_guild_display_name(guild)

    if not apps:
        return f"📨 Заявки до гільдії\n\n{guild_name}\n\nАктивних заявок немає."

    text = f"📨 Заявки до гільдії\n\n{guild_name}\n\n"

    for index, app in enumerate(apps, start=1):
        name = _app_row_get(app, "character_name") or f"user_id={_app_row_get(app, 'user_id')}"
        level = _app_row_get(app, "level") or "?"
        created_at = str(_app_row_get(app, "created_at", ""))[:10]
        text += f"{index}. {name}\n   Рівень: {level} | Подано: {created_at}\n"

    text += "\nОбери заявку кнопкою нижче."
    return text.strip()


def build_guild_application_detail_text(user_id, application_id):
    app = get_guild_application_by_id(application_id)

    if not app:
        return "❌ Заявку не знайдено."

    guild = get_user_guild(user_id)

    if not guild or int(guild["id"]) != int(app["guild_id"]):
        return "❌ Ця заявка не належить твоїй гільдії."

    if not can_manage_guild_applications(user_id, guild["id"]):
        return "❌ У тебе немає прав для обробки заявок."

    name = f"user_id={app['user_id']}"
    level = "?"
    try:
        from db import cursor
        cursor.execute("SELECT character_name, level FROM users WHERE user_id=?", (app["user_id"],))
        row = cursor.fetchone()
        if row:
            try:
                name = row["character_name"] or name
                level = row["level"] or "?"
            except Exception:
                name = row[0] or name
                level = row[1] or "?"
    except Exception:
        pass

    return (
        "📨 Заявка до гільдії\n\n"
        f"Гравець: {name}\n"
        f"Рівень: {level}\n"
        f"Статус: {app['status']}\n"
        f"Подано: {str(app['created_at'])[:10]}\n\n"
        "Обери дію: прийняти або відхилити заявку."
    )


def show_guild_applications(bot, message):
    user_id = message.from_user.id
    text = build_guild_applications_text(user_id)
    kb = guild_applications_kb(user_id)
    bot.send_message(message.chat.id, text, reply_markup=kb)


def show_guild_application_detail(bot, message, application_id):
    user_id = message.from_user.id
    state = GUILD_APPLICATION_REVIEW_STATE.setdefault(user_id, {"buttons": {}, "selected_application_id": None})
    state["selected_application_id"] = application_id

    bot.send_message(
        message.chat.id,
        build_guild_application_detail_text(user_id, application_id),
        reply_markup=guild_application_detail_kb()
    )


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

        if text == "✅ Прийняти заявку":
            result = accept_guild_application(user_id, application_id)
        else:
            result = reject_guild_application(user_id, application_id)

        bot.send_message(message.chat.id, result.get("message", ""), reply_markup=guild_applications_kb(user_id))
        show_guild_applications(bot, message)
        return True

    return False


# Patch register_guild_handlers by wrapping the existing function.
try:
    _base_register_guild_handlers_before_application_review_v1 = register_guild_handlers
except Exception:
    _base_register_guild_handlers_before_application_review_v1 = None


def register_guild_handlers(bot):
    if _base_register_guild_handlers_before_application_review_v1 is not None:
        _base_register_guild_handlers_before_application_review_v1(bot)

    @bot.message_handler(func=lambda message: get_guild_application_review_state(message.from_user.id) is not None)
    def guild_application_review_state_message(message):
        handle_guild_application_review_message(bot, message)

    @bot.message_handler(func=lambda message: message.text == "📨 Заявки")
    def guild_applications_message_v2(message):
        show_guild_applications(bot, message)
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


def patch_guild_system(root):
    target = root / "systems" / "guild_system.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено systems/guild_system.py")
    backup, original, changed = append_if_missing(root, target, GUILD_SYSTEM_MARKER, GUILD_SYSTEM_APPEND)
    return target, backup, original, changed


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")
    backup, original, changed = append_if_missing(root, target, DB_MARKER, DB_APPEND)
    return target, backup, original, changed


def patch_guild_handler(root):
    target = root / "handlers" / "guild.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/guild.py")
    backup, original, changed = append_if_missing(root, target, GUILD_HANDLER_MARKER, GUILD_HANDLER_APPEND)
    return target, backup, original, changed


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_guild_system, patch_db, patch_guild_handler]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        for file_path in changed_files:
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
            "❌ Помилка під час patch_7_0_5_guild_application_review.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.5 Guild Application Review застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in changed_files:
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- перегляд pending-заявок у гільдію")
    print("- вибір заявки кнопкою")
    print("- ✅ Прийняти заявку")
    print("- ❌ Відхилити заявку")
    print("- приймати/відхиляти можуть тільки 👑 Голова або 🛡 Заступник")
    print("- після прийняття гравець додається як 👤 Учасник")
    print("- інші pending-заявки прийнятого гравця автоматично скасовуються")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\guild_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
