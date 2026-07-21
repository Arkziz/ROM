from pathlib import Path
from datetime import datetime
import py_compile
import sys

PATCH_NAME = "7_0_6a_guild_roles_state_and_date_fix"
SYSTEM_MARKER = "# ✅ GUILD SINGLE OFFICER CORE V1"
DB_MARKER = "# ✅ GUILD SINGLE OFFICER DB WRAPPERS V1"
HANDLER_MARKER = "# ✅ GUILD ROLES STATE DATE FIX V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ GUILD SINGLE OFFICER CORE V1
# ==============================

# 7.0.6a
# У гільдії може бути максимум один 🛡 Заступник.


def get_guild_officer_count(guild_id):
    init_guild_system()
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM guild_members WHERE guild_id=? AND role=?",
        (guild_id, GUILD_ROLE_OFFICER)
    )
    row = cursor.fetchone()
    try:
        return int(row["cnt"] or 0)
    except Exception:
        return int(row[0] or 0) if row else 0


def get_guild_officer_member(guild_id):
    init_guild_system()
    cursor.execute(
        "SELECT * FROM guild_members WHERE guild_id=? AND role=? LIMIT 1",
        (guild_id, GUILD_ROLE_OFFICER)
    )
    return cursor.fetchone()


try:
    _base_promote_guild_member_to_officer_before_single_officer_v1 = promote_guild_member_to_officer
except Exception:
    _base_promote_guild_member_to_officer_before_single_officer_v1 = None


def promote_guild_member_to_officer(actor_user_id, target_user_id):
    """
    FINAL OVERRIDE:
    Призначає заступника, але тільки якщо у гільдії ще немає іншого заступника.
    """

    actor_member = get_user_guild_member(actor_user_id)
    target_member = get_user_guild_member(target_user_id)

    if not actor_member:
        return {"success": False, "message": "❌ Ти не перебуваєш у гільдії."}

    if not target_member or int(target_member["guild_id"]) != int(actor_member["guild_id"]):
        return {"success": False, "message": "❌ Цей гравець не перебуває у твоїй гільдії."}

    guild_id = actor_member["guild_id"]

    if target_member["role"] == GUILD_ROLE_OFFICER:
        return {"success": False, "message": "ℹ️ Цей гравець уже є 🛡 Заступником."}

    officer = get_guild_officer_member(guild_id)

    if officer:
        officer_name = get_character_name_by_user_id(officer["user_id"])
        return {
            "success": False,
            "message": f"❌ У гільдії вже є 🛡 Заступник: {officer_name}. Спочатку зніми його з посади."
        }

    if _base_promote_guild_member_to_officer_before_single_officer_v1 is None:
        return {"success": False, "message": "❌ Функція призначення заступника недоступна."}

    return _base_promote_guild_member_to_officer_before_single_officer_v1(actor_user_id, target_user_id)
'''

DB_APPEND = r'''

# ==============================
# ✅ GUILD SINGLE OFFICER DB WRAPPERS V1
# ==============================

# 7.0.6a wrappers для правила одного заступника.


def get_guild_officer_count(guild_id):
    from systems.guild_system import get_guild_officer_count as _get_guild_officer_count
    return _get_guild_officer_count(guild_id)


def get_guild_officer_member(guild_id):
    from systems.guild_system import get_guild_officer_member as _get_guild_officer_member
    return _get_guild_officer_member(guild_id)
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ GUILD ROLES STATE DATE FIX V1
# ==============================

# 7.0.6a
# Fix-и:
# - дата заявок у форматі DD.MM.YYYY;
# - при переході в 👥 Учасники очищаються стани списку гільдій/заявок, щоб кнопки учасників не ковталися старим state-handler;
# - у UI ховається дія 🛡 Призначити заступником, якщо у гільдії вже є заступник.

try:
    from db import get_guild_officer_member
except Exception as _guild_officer_import_error:
    print(f"⚠️ Guild officer import failed: {_guild_officer_import_error}")


def _guild_format_ua_date_v2(value):
    value = str(value or "").strip()
    if not value:
        return "невідомо"
    try:
        date_part = value.split("T", 1)[0].split(" ", 1)[0]
        year, month, day = date_part.split("-", 2)
        return f"{day}.{month}.{year}"
    except Exception:
        return value


def _guild_safe_reset_other_states_for_members_v2(user_id):
    try:
        reset_guild_browse_state(user_id)
    except Exception:
        pass
    try:
        reset_guild_application_review_state(user_id)
    except Exception:
        pass


def _guild_has_other_officer_v2(guild_id, target_user_id=None):
    try:
        officer = get_guild_officer_member(guild_id)
        if not officer:
            return False
        if target_user_id is None:
            return True
        return int(officer["user_id"]) != int(target_user_id)
    except Exception:
        return False


# Override date display for pending applications.
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
        created_at = _guild_format_ua_date_v2(_app_row_get(app, "created_at", ""))
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
        f"Подано: {_guild_format_ua_date_v2(app['created_at'])}\n\n"
        "Обери дію: прийняти або відхилити заявку."
    )


# Override member detail keyboard to enforce only one officer.
def guild_member_detail_kb(actor_user_id, target_user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actor_member = get_user_guild_member(actor_user_id)
    target_member = get_user_guild_member(target_user_id)

    if actor_member and target_member and int(actor_member["guild_id"]) == int(target_member["guild_id"]):
        guild_id = actor_member["guild_id"]
        has_other_officer = _guild_has_other_officer_v2(guild_id, target_user_id)

        if actor_member["role"] == "leader" and int(actor_user_id) != int(target_user_id):
            if target_member["role"] == "member" and not has_other_officer:
                kb.add("🛡 Призначити заступником")
            elif target_member["role"] == "officer":
                kb.add("👤 Зняти заступника")
            if target_member["role"] != "leader":
                kb.add("🚪 Виключити з гільдії")
        elif actor_member["role"] == "officer" and target_member["role"] == "member":
            kb.add("🚪 Виключити з гільдії")

    kb.add("👥 Учасники")
    kb.add("🔙 Зала Гільдій")
    return kb


# Override member detail text to explain why promote may be unavailable.
def build_guild_member_detail_text(actor_user_id, target_user_id):
    actor_member = get_user_guild_member(actor_user_id)
    target_member = get_user_guild_member(target_user_id)

    if not actor_member or not target_member:
        return "❌ Учасника не знайдено."

    if int(actor_member["guild_id"]) != int(target_member["guild_id"]):
        return "❌ Цей учасник не належить твоїй гільдії."

    guild = get_guild_by_id(target_member["guild_id"])
    name = f"user_id={target_user_id}"
    level = "?"

    try:
        from db import cursor
        cursor.execute("SELECT character_name, level FROM users WHERE user_id=?", (target_user_id,))
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

    role_label = get_guild_role_label(target_member["role"])
    joined_at = _guild_format_ua_date_v2(target_member["joined_at"])

    available = []
    guild_id = target_member["guild_id"]
    has_other_officer = _guild_has_other_officer_v2(guild_id, target_user_id)

    if actor_member["role"] == "leader" and int(actor_user_id) != int(target_user_id):
        if target_member["role"] == "member":
            if has_other_officer:
                try:
                    officer = get_guild_officer_member(guild_id)
                    officer_name = get_character_name_by_user_id(officer["user_id"])
                    available.append(f"• 🛡 Заступник уже є: {officer_name}")
                except Exception:
                    available.append("• 🛡 У гільдії вже є заступник")
            else:
                available.append("• 🛡 Призначити заступником")
        elif target_member["role"] == "officer":
            available.append("• 👤 Зняти заступника")
        if target_member["role"] != "leader":
            available.append("• 🚪 Виключити з гільдії")
    elif actor_member["role"] == "officer" and target_member["role"] == "member":
        available.append("• 🚪 Виключити з гільдії")

    actions_text = "\n".join(available) if available else "Немає доступних дій."

    return (
        f"👤 Учасник гільдії\n\n"
        f"Гільдія: {get_guild_display_name(guild)}\n"
        f"Імʼя: {name}\n"
        f"Рівень: {level}\n"
        f"Роль: {role_label}\n"
        f"Вступив: {joined_at}\n\n"
        f"Внесок за весь час: {target_member['contribution_score']}\n"
        f"Внесок за місяць: {target_member['monthly_contribution_score']}\n\n"
        f"Доступні дії:\n{actions_text}"
    )


# Override entering members menu: clear stale browse/application states.
def show_guild_members_manage(bot, message):
    user_id = message.from_user.id
    _guild_safe_reset_other_states_for_members_v2(user_id)
    bot.send_message(
        message.chat.id,
        build_guild_member_manage_text(user_id),
        reply_markup=guild_members_manage_kb(user_id)
    )


# Override handler to make sure selected member buttons are not swallowed by stale states.
def handle_guild_member_manage_message(bot, message):
    user_id = message.from_user.id
    text = (message.text or "").strip()
    state = get_guild_member_manage_state(user_id)

    if not state:
        return False

    if text == "🔙 Зала Гільдій":
        reset_guild_member_manage_state(user_id)
        open_guild_hall(bot, message.chat.id, user_id)
        return True

    if text in ["👥 Учасники", "🔄 Оновити учасників"]:
        show_guild_members_manage(bot, message)
        return True

    buttons = state.get("buttons", {})
    if text in buttons:
        show_guild_member_detail(bot, message, buttons[text])
        return True

    selected_user_id = state.get("selected_user_id")

    if text == "🛡 Призначити заступником":
        if not selected_user_id:
            bot.send_message(message.chat.id, "❌ Спочатку обери учасника.", reply_markup=guild_members_manage_kb(user_id))
            return True
        result = promote_guild_member_to_officer(user_id, selected_user_id)
        bot.send_message(message.chat.id, result.get("message", ""), reply_markup=guild_members_manage_kb(user_id))
        refresh_selected_member_or_list(bot, message)
        return True

    if text == "👤 Зняти заступника":
        if not selected_user_id:
            bot.send_message(message.chat.id, "❌ Спочатку обери учасника.", reply_markup=guild_members_manage_kb(user_id))
            return True
        result = demote_guild_officer(user_id, selected_user_id)
        bot.send_message(message.chat.id, result.get("message", ""), reply_markup=guild_members_manage_kb(user_id))
        refresh_selected_member_or_list(bot, message)
        return True

    if text == "🚪 Виключити з гільдії":
        if not selected_user_id:
            bot.send_message(message.chat.id, "❌ Спочатку обери учасника.", reply_markup=guild_members_manage_kb(user_id))
            return True
        result = kick_guild_member(user_id, selected_user_id)
        bot.send_message(message.chat.id, result.get("message", ""), reply_markup=guild_members_manage_kb(user_id))
        show_guild_members_manage(bot, message)
        return True

    return False
'''

BROWSE_HANDLER_PATCH_MARKER = "# ✅ GUILD BROWSE PASS THROUGH MEMBERS V1"
APP_HANDLER_PATCH_MARKER = "# ✅ GUILD APPLICATION PASS THROUGH MEMBERS V1"


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
    backup, original, changed = append_if_missing(root, target, SYSTEM_MARKER, SYSTEM_APPEND)
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
    backup, original, changed = append_if_missing(root, target, HANDLER_MARKER, HANDLER_APPEND)
    return target, backup, original, changed


def patch_state_handlers(root):
    target = root / "handlers" / "guild.py"
    original = target.read_text(encoding="utf-8")
    text = original
    changed = False
    backup = None

    if BROWSE_HANDLER_PATCH_MARKER not in text:
        old = '''        if not handle_guild_list_message(bot, message):
            # If browse state cannot handle it, let user return by common buttons.
            if message.text == "🔙 Зала Гільдій":
                reset_guild_browse_state(message.from_user.id)
                open_guild_hall(bot, message.chat.id, message.from_user.id)
'''
        new = '''        if not handle_guild_list_message(bot, message):
            # ✅ GUILD BROWSE PASS THROUGH MEMBERS V1
            if message.text == "👥 Учасники":
                reset_guild_browse_state(message.from_user.id)
                show_guild_members_manage(bot, message)
                return
            if message.text == "📨 Заявки":
                reset_guild_browse_state(message.from_user.id)
                show_guild_applications(bot, message)
                return
            if message.text == "🔙 Зала Гільдій":
                reset_guild_browse_state(message.from_user.id)
                open_guild_hall(bot, message.chat.id, message.from_user.id)
'''
        if old in text:
            text = text.replace(old, new, 1)
            changed = True

    if APP_HANDLER_PATCH_MARKER not in text:
        old = '''    @bot.message_handler(func=lambda message: get_guild_application_review_state(message.from_user.id) is not None)
    def guild_application_review_state_message(message):
        handle_guild_application_review_message(bot, message)
'''
        new = '''    @bot.message_handler(func=lambda message: get_guild_application_review_state(message.from_user.id) is not None)
    def guild_application_review_state_message(message):
        # ✅ GUILD APPLICATION PASS THROUGH MEMBERS V1
        if message.text == "👥 Учасники":
            reset_guild_application_review_state(message.from_user.id)
            show_guild_members_manage(bot, message)
            return
        handle_guild_application_review_message(bot, message)
'''
        if old in text:
            text = text.replace(old, new, 1)
            changed = True

    if changed:
        backup = make_backup(root, target)
        target.write_text(text, encoding="utf-8")

    return target, backup, original, changed


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_guild_system, patch_db, patch_guild_handler, patch_state_handlers]:
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
            "❌ Помилка під час patch_7_0_6a_guild_roles_state_and_date_fix.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.6a Guild roles/state/date fix застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо виправлено:")
    print("- дата у заявках тепер DD.MM.YYYY")
    print("- кнопки учасників більше не мають ковтатися старими state-handler-ами")
    print("- при вході в 👥 Учасники очищаються стани списку гільдій/заявок")
    print("- у гільдії може бути максимум один 🛡 Заступник")
    print("- якщо заступник уже є, кнопка 🛡 Призначити заступником не показується")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\guild_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
