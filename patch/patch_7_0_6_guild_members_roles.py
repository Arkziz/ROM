from pathlib import Path
from datetime import datetime
import py_compile
import sys
import re

PATCH_NAME = "7_0_6_guild_members_roles"
GUILD_SYSTEM_MARKER = "# ✅ GUILD MEMBERS ROLES CORE V1"
DB_MARKER = "# ✅ GUILD MEMBERS ROLES DB WRAPPERS V1"
GUILD_HANDLER_MARKER = "# ✅ GUILD MEMBERS ROLES UI V1"

GUILD_SYSTEM_APPEND = r'''

# ==============================
# ✅ GUILD MEMBERS ROLES CORE V1
# ==============================

# 7.0.6
# Керування учасниками гільдії:
# - призначити заступника
# - зняти заступника
# - виключити учасника


def get_guild_member(guild_id, user_id):
    init_guild_system()
    cursor.execute(
        "SELECT * FROM guild_members WHERE guild_id=? AND user_id=?",
        (guild_id, user_id)
    )
    return cursor.fetchone()


def get_character_name_by_user_id(user_id):
    try:
        cursor.execute("SELECT character_name FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return f"user_id={user_id}"
        try:
            return row["character_name"] or f"user_id={user_id}"
        except Exception:
            return row[0] or f"user_id={user_id}"
    except Exception:
        return f"user_id={user_id}"


def is_guild_leader(user_id, guild_id):
    member = get_guild_member(guild_id, user_id)
    return bool(member and member["role"] == GUILD_ROLE_LEADER)


def is_guild_officer(user_id, guild_id):
    member = get_guild_member(guild_id, user_id)
    return bool(member and member["role"] == GUILD_ROLE_OFFICER)


def promote_guild_member_to_officer(actor_user_id, target_user_id):
    """
    Призначити заступника.
    Дозволено тільки голові гільдії.
    """

    init_guild_system()
    actor_member = get_user_guild_member(actor_user_id)
    target_member = get_user_guild_member(target_user_id)

    if not actor_member:
        return {"success": False, "message": "❌ Ти не перебуваєш у гільдії."}

    if not target_member or int(target_member["guild_id"]) != int(actor_member["guild_id"]):
        return {"success": False, "message": "❌ Цей гравець не перебуває у твоїй гільдії."}

    guild_id = actor_member["guild_id"]

    if actor_member["role"] != GUILD_ROLE_LEADER:
        return {"success": False, "message": "❌ Призначати заступників може тільки 👑 Голова гільдії."}

    if target_member["role"] == GUILD_ROLE_LEADER:
        return {"success": False, "message": "❌ Голова гільдії вже має найвищу роль."}

    if target_member["role"] == GUILD_ROLE_OFFICER:
        return {"success": False, "message": "ℹ️ Цей гравець уже є 🛡 Заступником."}

    cursor.execute(
        "UPDATE guild_members SET role=? WHERE guild_id=? AND user_id=?",
        (GUILD_ROLE_OFFICER, guild_id, target_user_id)
    )
    conn.commit()

    target_name = get_character_name_by_user_id(target_user_id)
    add_guild_log(
        guild_id=guild_id,
        event_type="member_promoted",
        text=f"{target_name} призначений 🛡 Заступником."
    )

    return {"success": True, "message": f"✅ {target_name} тепер 🛡 Заступник гільдії."}


def demote_guild_officer(actor_user_id, target_user_id):
    """
    Зняти заступника до учасника.
    Дозволено тільки голові гільдії.
    """

    init_guild_system()
    actor_member = get_user_guild_member(actor_user_id)
    target_member = get_user_guild_member(target_user_id)

    if not actor_member:
        return {"success": False, "message": "❌ Ти не перебуваєш у гільдії."}

    if not target_member or int(target_member["guild_id"]) != int(actor_member["guild_id"]):
        return {"success": False, "message": "❌ Цей гравець не перебуває у твоїй гільдії."}

    guild_id = actor_member["guild_id"]

    if actor_member["role"] != GUILD_ROLE_LEADER:
        return {"success": False, "message": "❌ Знімати заступників може тільки 👑 Голова гільдії."}

    if target_member["role"] != GUILD_ROLE_OFFICER:
        return {"success": False, "message": "❌ Цей гравець не є заступником."}

    cursor.execute(
        "UPDATE guild_members SET role=? WHERE guild_id=? AND user_id=?",
        (GUILD_ROLE_MEMBER, guild_id, target_user_id)
    )
    conn.commit()

    target_name = get_character_name_by_user_id(target_user_id)
    add_guild_log(
        guild_id=guild_id,
        event_type="member_demoted",
        text=f"{target_name} більше не є 🛡 Заступником."
    )

    return {"success": True, "message": f"✅ {target_name} тепер 👤 Учасник гільдії."}


def kick_guild_member(actor_user_id, target_user_id):
    """
    Виключити учасника з гільдії.

    Правила:
    - Голова може виключати учасників і заступників, але не себе.
    - Заступник може виключати тільки звичайних учасників.
    - Учасник не може виключати нікого.
    - Голову не можна виключити.
    """

    init_guild_system()
    actor_member = get_user_guild_member(actor_user_id)
    target_member = get_user_guild_member(target_user_id)

    if not actor_member:
        return {"success": False, "message": "❌ Ти не перебуваєш у гільдії."}

    if not target_member or int(target_member["guild_id"]) != int(actor_member["guild_id"]):
        return {"success": False, "message": "❌ Цей гравець не перебуває у твоїй гільдії."}

    guild_id = actor_member["guild_id"]

    if int(actor_user_id) == int(target_user_id):
        return {"success": False, "message": "❌ Не можна виключити самого себе."}

    if target_member["role"] == GUILD_ROLE_LEADER:
        return {"success": False, "message": "❌ Голову гільдії не можна виключити."}

    if actor_member["role"] == GUILD_ROLE_MEMBER:
        return {"success": False, "message": "❌ Учасник не може виключати інших учасників."}

    if actor_member["role"] == GUILD_ROLE_OFFICER and target_member["role"] != GUILD_ROLE_MEMBER:
        return {"success": False, "message": "❌ Заступник може виключати тільки звичайних учасників."}

    cursor.execute(
        "DELETE FROM guild_members WHERE guild_id=? AND user_id=?",
        (guild_id, target_user_id)
    )
    conn.commit()

    target_name = get_character_name_by_user_id(target_user_id)
    add_guild_log(
        guild_id=guild_id,
        event_type="member_kicked",
        text=f"{target_name} виключений з гільдії."
    )

    return {"success": True, "message": f"✅ {target_name} виключений з гільдії."}
'''

DB_APPEND = r'''

# ==============================
# ✅ GUILD MEMBERS ROLES DB WRAPPERS V1
# ==============================

# 7.0.6 wrappers для керування учасниками / ролями.


def get_guild_member(guild_id, user_id):
    from systems.guild_system import get_guild_member as _get_guild_member
    return _get_guild_member(guild_id=guild_id, user_id=user_id)


def get_character_name_by_user_id(user_id):
    from systems.guild_system import get_character_name_by_user_id as _get_character_name_by_user_id
    return _get_character_name_by_user_id(user_id)


def is_guild_leader(user_id, guild_id):
    from systems.guild_system import is_guild_leader as _is_guild_leader
    return _is_guild_leader(user_id=user_id, guild_id=guild_id)


def is_guild_officer(user_id, guild_id):
    from systems.guild_system import is_guild_officer as _is_guild_officer
    return _is_guild_officer(user_id=user_id, guild_id=guild_id)


def promote_guild_member_to_officer(actor_user_id, target_user_id):
    from systems.guild_system import promote_guild_member_to_officer as _promote_guild_member_to_officer
    return _promote_guild_member_to_officer(actor_user_id=actor_user_id, target_user_id=target_user_id)


def demote_guild_officer(actor_user_id, target_user_id):
    from systems.guild_system import demote_guild_officer as _demote_guild_officer
    return _demote_guild_officer(actor_user_id=actor_user_id, target_user_id=target_user_id)


def kick_guild_member(actor_user_id, target_user_id):
    from systems.guild_system import kick_guild_member as _kick_guild_member
    return _kick_guild_member(actor_user_id=actor_user_id, target_user_id=target_user_id)
'''

GUILD_HANDLER_APPEND = r'''

# ==============================
# ✅ GUILD MEMBERS ROLES UI V1
# ==============================

# 7.0.6
# ReplyKeyboard UI для учасників і ролей.

try:
    from db import (
        get_guild_member,
        promote_guild_member_to_officer,
        demote_guild_officer,
        kick_guild_member,
    )
except Exception as _guild_roles_import_error:
    print(f"⚠️ Guild roles import failed: {_guild_roles_import_error}")

GUILD_MEMBER_MANAGE_STATE = {}


def reset_guild_member_manage_state(user_id):
    GUILD_MEMBER_MANAGE_STATE.pop(user_id, None)


def get_guild_member_manage_state(user_id):
    return GUILD_MEMBER_MANAGE_STATE.get(user_id)


def _member_row_get(row, key, fallback=None):
    try:
        return row[key]
    except Exception:
        return fallback


def can_actor_manage_target(actor_user_id, target_user_id):
    actor_member = get_user_guild_member(actor_user_id)
    target_member = get_user_guild_member(target_user_id)

    if not actor_member or not target_member:
        return False

    if int(actor_member["guild_id"]) != int(target_member["guild_id"]):
        return False

    if int(actor_user_id) == int(target_user_id):
        return False

    if actor_member["role"] == "leader":
        return target_member["role"] != "leader"

    if actor_member["role"] == "officer":
        return target_member["role"] == "member"

    return False


def guild_members_manage_kb(user_id):
    guild = get_user_guild(user_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if not guild:
        kb.add("🔙 Зала Гільдій")
        return kb

    members = get_guild_members(guild["id"])
    buttons = {}

    for member in members:
        target_user_id = _member_row_get(member, "user_id")
        name = _member_row_get(member, "character_name") or f"user_id={target_user_id}"
        level = _member_row_get(member, "level") or "?"
        role_label = get_guild_role_label(_member_row_get(member, "role"))
        label = f"👤 {name} | {role_label} | рівень {level}"
        if len(label) > 60:
            label = label[:57] + "..."
        buttons[label] = target_user_id
        kb.add(label)

    kb.add("🔄 Оновити учасників")
    kb.add("🔙 Зала Гільдій")

    GUILD_MEMBER_MANAGE_STATE[user_id] = {
        "guild_id": guild["id"],
        "buttons": buttons,
        "selected_user_id": None,
    }

    return kb


def guild_member_detail_kb(actor_user_id, target_user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actor_member = get_user_guild_member(actor_user_id)
    target_member = get_user_guild_member(target_user_id)

    if actor_member and target_member and int(actor_member["guild_id"]) == int(target_member["guild_id"]):
        if actor_member["role"] == "leader" and int(actor_user_id) != int(target_user_id):
            if target_member["role"] == "member":
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


def build_guild_member_manage_text(user_id):
    guild = get_user_guild(user_id)

    if not guild:
        return "❌ Ти не перебуваєш у гільдії."

    members = get_guild_members(guild["id"])
    guild_name = get_guild_display_name(guild)

    if not members:
        return f"👥 Учасники\n\n{guild_name}\n\nСписок учасників порожній."

    text = f"👥 Учасники\n\n{guild_name}\n\n"

    for index, member in enumerate(members, start=1):
        target_user_id = _member_row_get(member, "user_id")
        name = _member_row_get(member, "character_name") or f"user_id={target_user_id}"
        level = _member_row_get(member, "level") or "?"
        role_label = get_guild_role_label(_member_row_get(member, "role"))
        score = _member_row_get(member, "contribution_score", 0) or 0
        monthly_score = _member_row_get(member, "monthly_contribution_score", 0) or 0
        text += (
            f"{index}. {role_label} {name}\n"
            f"   Рівень: {level} | Score: {score} | Місяць: {monthly_score}\n"
        )

    text += "\nОбери учасника кнопкою нижче, щоб переглянути дії."
    return text.strip()


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
    joined_at = str(target_member["joined_at"] or "")[:10]

    available = []
    if actor_member["role"] == "leader" and int(actor_user_id) != int(target_user_id):
        if target_member["role"] == "member":
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


def show_guild_members_manage(bot, message):
    user_id = message.from_user.id
    bot.send_message(
        message.chat.id,
        build_guild_member_manage_text(user_id),
        reply_markup=guild_members_manage_kb(user_id)
    )


def show_guild_member_detail(bot, message, target_user_id):
    user_id = message.from_user.id
    state = GUILD_MEMBER_MANAGE_STATE.setdefault(user_id, {"buttons": {}, "selected_user_id": None})
    state["selected_user_id"] = target_user_id

    bot.send_message(
        message.chat.id,
        build_guild_member_detail_text(user_id, target_user_id),
        reply_markup=guild_member_detail_kb(user_id, target_user_id)
    )


def refresh_selected_member_or_list(bot, message):
    state = get_guild_member_manage_state(message.from_user.id)
    target_user_id = state.get("selected_user_id") if state else None
    if target_user_id and get_user_guild_member(target_user_id):
        show_guild_member_detail(bot, message, target_user_id)
    else:
        show_guild_members_manage(bot, message)


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


# Patch old 👥 Учасники placeholder/list handler if it exists.
try:
    _base_register_guild_handlers_before_members_roles_v1 = register_guild_handlers
except Exception:
    _base_register_guild_handlers_before_members_roles_v1 = None


def register_guild_handlers(bot):
    if _base_register_guild_handlers_before_members_roles_v1 is not None:
        _base_register_guild_handlers_before_members_roles_v1(bot)

    @bot.message_handler(func=lambda message: get_guild_member_manage_state(message.from_user.id) is not None)
    def guild_member_manage_state_message(message):
        handle_guild_member_manage_message(bot, message)

    @bot.message_handler(func=lambda message: message.text == "👥 Учасники")
    def guild_members_message_v2(message):
        show_guild_members_manage(bot, message)
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


def patch_guild_handler_append(root):
    target = root / "handlers" / "guild.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/guild.py")
    backup, original, changed = append_if_missing(root, target, GUILD_HANDLER_MARKER, GUILD_HANDLER_APPEND)
    return target, backup, original, changed


def patch_old_members_handler(root):
    """
    Старий handler 👥 Учасники був зареєстрований раніше і може перехоплювати кнопку
    до нового wrapper-а. Тому точково міняємо його тіло на show_guild_members_manage().
    """

    target = root / "handlers" / "guild.py"
    original = target.read_text(encoding="utf-8")

    if "# ✅ GUILD MEMBERS OLD HANDLER REPLACED V1" in original:
        return target, None, original, False

    old_block = '''    @bot.message_handler(func=lambda message: message.text == "👥 Учасники")
    def guild_members_message(message):
        send_guild_section(
            bot,
            message,
            build_guild_members_text(message.from_user.id)
        )
'''

    new_block = '''    @bot.message_handler(func=lambda message: message.text == "👥 Учасники")
    def guild_members_message(message):
        show_guild_members_manage(bot, message)
        # ✅ GUILD MEMBERS OLD HANDLER REPLACED V1
'''

    if old_block not in original:
        # Compact version from later generated handlers.
        old_block_2 = '''    @bot.message_handler(func=lambda message: message.text == "👥 Учасники")
    def guild_members_message(message):
        send_guild_section(bot, message, build_guild_members_text(message.from_user.id))
'''
        if old_block_2 not in original:
            return target, None, original, False
        old_block = old_block_2

    backup = make_backup(root, target)
    updated = original.replace(old_block, new_block, 1)
    target.write_text(updated, encoding="utf-8")
    return target, backup, original, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_guild_system, patch_db, patch_guild_handler_append, patch_old_members_handler]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        # Deduplicate changed files for compile.
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
            "❌ Помилка під час patch_7_0_6_guild_members_roles.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.6 Guild Members/Roles застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- перегляд учасників як меню керування")
    print("- вибір учасника кнопкою")
    print("- 🛡 Призначити заступником")
    print("- 👤 Зняти заступника")
    print("- 🚪 Виключити з гільдії")
    print("- Голова може керувати учасниками і заступниками")
    print("- Заступник може виключати тільки звичайних учасників")
    print("- Голову не можна виключити")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\guild_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
