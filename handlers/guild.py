# ROM 17.21.3.4 GUILD MEMBER LIST EXPLICIT ACTOR RECOVERY
# ROM 17.21.3.2.3.4 KICK CONFIRMATION DB NEUTRAL SMOKE RECOVERY
# ROM 17.21.3.2.1 KICK CONFIRMATION HANDLER HASH NEWLINE RECOVERY
# ROM 17.11.2 COMPACT TEXT LOCATION DESCRIPTION
# ROM 17.9.1 GLOBAL PAGINATION BUTTON LABELS
from telebot import types
from systems.guild_system import validate_guild_tag_contract, validate_guild_name_contract, validate_guild_icon_contract

from db import (
    init_guild_system,
    get_user_guild,
    get_user_guild_member,
    get_guild_members,
    get_guild_member_count,
    get_guild_ranking,
    get_guild_display_name,
    get_guild_role_label,
    get_current_guild_season_key,
    create_guild,
    get_guild_creation_terms,
    get_guild_by_name_or_tag,
    get_guild_by_id,
    get_public_guild_list,
    create_guild_application,
    get_user_guild_applications,
    has_pending_guild_application,
    get_character_name_by_user_id,
    get_user_guild_role,
    get_guild_member,
    transfer_guild_leadership,
    transfer_guild_leadership_and_leave,
)

from keyboards import city_kb


GUILD_RANKING_LIMIT = 10
GUILD_LIST_PAGE_SIZE = 8

# user_id -> {step, name, tag, icon}
GUILD_CREATE_STATE = {}

# user_id -> {page, buttons: {label: guild_id}, selected_guild_id}
GUILD_BROWSE_STATE = {}


# ==============================
# REPLY KEYBOARDS
# ==============================

def guild_hall_kb(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if get_user_guild(user_id):
        kb.add("ℹ️ Інформація", "👥 Учасники")
        kb.add("📨 Заявки", "📜 Журнал")
        kb.add("🏆 Місячний рейтинг")
        kb.add("🏆 Рейтинг за весь час")
        kb.add("🔙 Місто")
    else:
        kb.add("🏗️ Створити гільдію")
        kb.add("📜 Переглянути гільдії")
        kb.add("🏆 Місячний рейтинг")
        kb.add("🏆 Рейтинг за весь час")
        kb.add("📨 Мої заявки")
        kb.add("🔙 Місто")

    return kb


def guild_create_cancel_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ Скасувати створення")
    kb.add("🔙 Зала Гільдій")
    return kb


def guild_create_confirm_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Створити гільдію")
    kb.add("✏️ Почати заново")
    kb.add("❌ Скасувати створення")
    return kb


def guild_list_kb(user_id, page=0):
    rows = get_public_guild_list(limit=GUILD_LIST_PAGE_SIZE + 1, offset=page * GUILD_LIST_PAGE_SIZE)
    shown = rows[:GUILD_LIST_PAGE_SIZE]

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = {}

    for guild in shown:
        member_count = guild["member_count"] if "member_count" in guild.keys() else get_guild_member_count(guild["id"])
        label = f"🏰 [{guild['tag']}] {guild['name']} ({member_count}/{guild['member_limit']})"
        # Telegram buttons should not be too long.
        if len(label) > 60:
            label = label[:57] + "..."
        buttons[label] = guild["id"]
        kb.add(label)

    nav = []
    if page > 0:
        nav.append("⬅️ Назад")
    if len(rows) > GUILD_LIST_PAGE_SIZE:
        nav.append("➡️ Далі")
    if nav:
        kb.add(*nav)

    kb.add("🔙 Зала Гільдій")

    GUILD_BROWSE_STATE[user_id] = {
        "page": page,
        "buttons": buttons,
        "selected_guild_id": None,
    }

    return kb


def guild_detail_kb(user_id, guild_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if get_user_guild(user_id):
        kb.add("📜 Переглянути гільдії")
    else:
        if has_pending_guild_application(user_id, guild_id):
            kb.add("ℹ️ Заявку вже подано")
        else:
            kb.add("📨 Подати заявку")
        kb.add("📜 Переглянути гільдії")

    kb.add("🔙 Зала Гільдій")
    return kb


# ==============================
# VALIDATION / STATE HELPERS
# ==============================

def normalize_guild_tag_input(value):
    return (value or "").strip().upper()


def reset_guild_browse_state(user_id):
    GUILD_BROWSE_STATE.pop(user_id, None)


def get_guild_browse_state(user_id):
    return GUILD_BROWSE_STATE.get(user_id)


def set_selected_guild(user_id, guild_id):
    state = GUILD_BROWSE_STATE.setdefault(user_id, {"page": 0, "buttons": {}, "selected_guild_id": None})
    state["selected_guild_id"] = guild_id


def validate_guild_name_for_ui(name):
    validation = validate_guild_name_contract(name)
    if not validation["success"]:
        return False, validation["message"]
    name = validation["name"]
    if get_guild_by_name_or_tag(name):
        return False, "❌ Гільдія з такою назвою або абревіатурою вже існує."
    return True, name



def validate_guild_tag_for_ui(tag):
    validation = validate_guild_tag_contract(tag)
    if not validation["success"]:
        return False, validation["message"]
    tag = validation["tag"]
    if get_guild_by_name_or_tag(tag):
        return False, "❌ Гільдія з такою абревіатурою вже існує."
    return True, tag



def reset_guild_create_state(user_id):
    GUILD_CREATE_STATE.pop(user_id, None)


def start_guild_create_state(user_id):
    GUILD_CREATE_STATE[user_id] = {
        "step": "name",
        "name": "",
        "tag": "",
        "icon": "🏰",
    }


def get_guild_create_state(user_id):
    return GUILD_CREATE_STATE.get(user_id)


def format_ua_date(value):
    value = str(value or "").strip()
    if not value:
        return "невідомо"
    try:
        date_part = value.split("T", 1)[0].split(" ", 1)[0]
        year, month, day = date_part.split("-", 2)
        return f"{day}.{month}.{year}"
    except Exception:
        return value


# ==============================
# TEXT BUILDERS
# ==============================

def build_guild_hall_no_guild_text(user_id):
    season_key = get_current_guild_season_key()

    return (
        "🏰 Зала Гільдій\n\n"
        "У просторій залі з кам’яними прапорами герої об’єднуються у гільдії, "
        "подають заявки та змагаються за місце у рейтингу.\n\n"
        "Ти поки не перебуваєш у гільдії.\n\n"
        "Доступні дії:\n"
        "• 🏗️ Створити гільдію\n"
        "• 📜 Переглянути гільдії\n"
        "• 🏆 Місячний рейтинг\n"
        "• 🏆 Рейтинг за весь час\n"
        "• 📨 Мої заявки\n\n"
        f"Поточний рейтинговий сезон: {season_key}"
    )


def build_guild_hall_member_text(user_id):
    guild = get_user_guild(user_id)
    member = get_user_guild_member(user_id)

    if not guild or not member:
        return build_guild_hall_no_guild_text(user_id)

    season_key = get_current_guild_season_key()
    guild_name = get_guild_display_name(guild)
    role_label = get_guild_role_label(member["role"])
    member_count = get_guild_member_count(guild["id"])

    return (
        f"🏰 Гільдія\n\n"
        f"{guild_name}\n"
        f"Твоя роль: {role_label}\n\n"
        f"Рівень гільдії: {guild['level']}\n"
        f"Учасники: {member_count}/{guild['member_limit']}\n\n"
        f"Місячний рейтинг ({season_key}):\n"
        f"• Досвід: {guild['monthly_exp']}\n"
        f"• Ресурс: {guild['monthly_resource']}\n"
        f"• Вбивства: {guild['monthly_kills']}\n"
        f"• Контракти: {guild['monthly_contracts']}\n"
        f"• Бали: {guild['monthly_score']}\n\n"
        f"За весь час:\n"
        f"• Досвід: {guild['total_exp']}\n"
        f"• Ресурс: {guild['total_resource']}\n"
        f"• Бали: {guild['total_score']}\n\n"
        "Доступні дії:\n"
        "• ℹ️ Інформація\n"
        "• 👥 Учасники\n"
        "• 📨 Заявки\n"
        "• 📜 Журнал\n"
        "• 🏆 Місячний рейтинг\n"
        "• 🏆 Рейтинг за весь час"
    )


def build_guild_hall_text(user_id):
    init_guild_system()

    if get_user_guild(user_id):
        return build_guild_hall_member_text(user_id)
    return build_guild_hall_no_guild_text(user_id)


def build_guild_info_text(user_id):
    guild = get_user_guild(user_id)

    if not guild:
        return "❌ Ти не перебуваєш у гільдії."

    guild_name = get_guild_display_name(guild)
    member_count = get_guild_member_count(guild["id"])
    season_key = get_current_guild_season_key()

    # Try to get leader name.
    leader_name = f"user_id={guild['leader_user_id']}"
    try:
        from db import cursor
        cursor.execute("SELECT character_name FROM users WHERE user_id=?", (guild["leader_user_id"],))
        row = cursor.fetchone()
        if row:
            try:
                leader_name = row["character_name"] or leader_name
            except Exception:
                leader_name = row[0] or leader_name
    except Exception:
        pass

    return (
        f"ℹ️ Інформація про гільдію\n\n"
        f"{guild_name}\n"
        f"Голова: {leader_name}\n"
        f"Рівень: {guild['level']}\n"
        f"Учасники: {member_count}/{guild['member_limit']}\n"
        f"Створено: {format_ua_date(guild['created_at'])}\n\n"
        f"Поточний сезон: {season_key}\n"
        f"Місячний score: {guild['monthly_score']}\n"
        f"All-time score: {guild['total_score']}"
    )


def build_guild_members_text(user_id):
    guild = get_user_guild(user_id)

    if not guild:
        return "❌ Ти не перебуваєш у гільдії."

    members = get_guild_members(guild["id"])
    guild_name = get_guild_display_name(guild)

    if not members:
        return f"👥 Учасники\n\n{guild_name}\n\nСписок учасників порожній."

    text = f"👥 Учасники\n\n{guild_name}\n\n"

    for index, member in enumerate(members, start=1):
        character_name = member["character_name"] or f"user_id={member['user_id']}"
        level = member["level"] or "?"
        role_label = get_guild_role_label(member["role"])
        score = member["contribution_score"] or 0
        monthly_score = member["monthly_contribution_score"] or 0
        text += (
            f"{index}. {role_label} {character_name}\n"
            f"   Рівень: {level} | Бали: {score} | Місяць: {monthly_score}\n"
        )

    return text.strip()


def build_guild_ranking_text(scope="monthly"):
    init_guild_system()

    if scope == "total":
        title = "🏆 Рейтинг гільдій за весь час"
    else:
        title = f"🏆 Місячний рейтинг гільдій ({get_current_guild_season_key()})"

    rows = get_guild_ranking(scope=scope, limit=GUILD_RANKING_LIMIT)

    if not rows:
        return f"{title}\n\nПоки немає жодної гільдії."

    text = f"{title}\n\n"
    for index, guild in enumerate(rows, start=1):
        name = get_guild_display_name(guild)
        if scope == "total":
            score = guild["total_score"] or 0
            exp = guild["total_exp"] or 0
            resource = guild["total_resource"] or 0
        else:
            score = guild["monthly_score"] or 0
            exp = guild["monthly_exp"] or 0
            resource = guild["monthly_resource"] or 0
        text += (
            f"{index}. {name}\n"
            f"   Бали: {score} | Досвід: {exp} | Ресурс: {resource}\n"
        )

    return text.strip()


def build_guild_list_text(user_id, page=0):
    rows = get_public_guild_list(limit=GUILD_LIST_PAGE_SIZE + 1, offset=page * GUILD_LIST_PAGE_SIZE)
    shown = rows[:GUILD_LIST_PAGE_SIZE]

    if not shown:
        return (
            "📜 Список гільдій\n\n"
            "Поки немає жодної гільдії.\n\n"
            "Ти можеш створити першу гільдію у Залі Гільдій."
        )

    text = f"📜 Список гільдій\n\nСторінка: {page + 1}\n\n"

    for index, guild in enumerate(shown, start=1 + page * GUILD_LIST_PAGE_SIZE):
        member_count = guild["member_count"] if "member_count" in guild.keys() else get_guild_member_count(guild["id"])
        text += (
            f"{index}. {get_guild_display_name(guild)}\n"
            f"   Рівень: {guild['level']} | Учасники: {member_count}/{guild['member_limit']}\n"
            f"   Місяць score: {guild['monthly_score']} | All-time: {guild['total_score']}\n"
        )

    text += "\nОбери гільдію кнопкою нижче, щоб переглянути деталі або подати заявку."
    return text.strip()


def build_guild_detail_text(user_id, guild_id):
    guild = get_guild_by_id(guild_id)
    if not guild:
        return "❌ Гільдію не знайдено."

    member_count = get_guild_member_count(guild_id)
    pending_text = ""

    if not get_user_guild(user_id) and has_pending_guild_application(user_id, guild_id):
        pending_text = "\n\nℹ️ Ти вже подав заявку в цю гільдію."

    return (
        f"🏰 Гільдія\n\n"
        f"{get_guild_display_name(guild)}\n"
        f"Рівень: {guild['level']}\n"
        f"Учасники: {member_count}/{guild['member_limit']}\n"
        f"Створено: {format_ua_date(guild['created_at'])}\n\n"
        f"Поточний сезон:\n"
        f"• Досвід: {guild['monthly_exp']}\n"
        f"• Ресурс: {guild['monthly_resource']}\n"
        f"• Бали: {guild['monthly_score']}\n\n"
        f"За весь час:\n"
        f"• Досвід: {guild['total_exp']}\n"
        f"• Ресурс: {guild['total_resource']}\n"
        f"• Бали: {guild['total_score']}"
        f"{pending_text}"
    )


def build_my_applications_text(user_id):
    apps = get_user_guild_applications(user_id)

    if not apps:
        return "📨 Мої заявки\n\nУ тебе немає заявок до гільдій."

    status_labels = {
        "pending": "⏳ очікує",
        "accepted": "✅ прийнята",
        "rejected": "❌ відхилена",
        "cancelled": "🚫 скасована",
    }

    text = "📨 Мої заявки\n\n"
    for index, app in enumerate(apps, start=1):
        icon = app["guild_icon"] or "🏰"
        tag = app["guild_tag"] or "???"
        name = app["guild_name"] or "Гільдія"
        status = status_labels.get(app["status"], app["status"])
        text += f"{index}. {icon} [{tag}] {name}\n   Статус: {status}\n"

    return text.strip()


def build_guild_placeholder_text(title, next_stage):
    return (
        f"{title}\n\n"
        f"Цей розділ буде реалізовано на етапі {next_stage}.\n\n"
        "Ядро гільдій уже створене: таблиці, місячний рейтинг, all-time статистика та історія сезонів працюють."
    )


def build_guild_create_name_prompt():
    return (
        "🏗️ Створення гільдії\n\n"
        "Крок 1/4 — назва гільдії.\n\n"
        "Введи назву гільдії.\n"
        "Вимоги:\n"
        "• від 3 до 32 символів;\n"
        "• українські або латинські літери без змішування;\n"
        "• дозволені одинарні пробіли, апостроф і дефіс;\n"
        "• цифри та emoji заборонені;\n"
        "• назва має бути унікальною."
    )



def build_guild_create_tag_prompt(name):
    return (
        "🏗️ Створення гільдії\n\n"
        "Крок 2/4 — абревіатура.\n\n"
        f"Назва: {name}\n\n"
        "Введи TAG гільдії.\n"
        "Вимоги:\n"
        "• рівно 3 літери;\n"
        "• тільки українські або латинські літери;\n"
        "• цифри, пробіли та інші символи заборонені;\n"
        "• буде показуватись у квадратних дужках, наприклад [ROM]."
    )



def build_guild_create_icon_prompt(name, tag):
    return (
        "🏗️ Створення гільдії\n\n"
        "Крок 3/4 — іконка.\n\n"
        f"Назва: {name}\n"
        f"TAG: [{tag}]\n\n"
        "Надішли рівно один emoji для іконки гільдії.\n"
        "Літери, цифри, текст і кілька emoji заборонені.\n"
        "Іконка має бути унікальною.\n"
        "Наприклад: 🏰, 🐺, 🔥, 🍒\n\n"
        "Якщо хочеш стандартну іконку — надішли 🏰."
    )



def build_guild_create_confirm_text(state, user_id=None):
    name = state.get("name", ""); tag = state.get("tag", ""); icon = state.get("icon", "🏰")
    terms = get_guild_creation_terms(user_id) if user_id is not None else {"cost_gold": 100.0, "gold_balance": 0.0, "member_limit": 10}
    return ("🏗️ Створення гільдії\n\nКрок 4/4 — підтвердження.\n\n" f"Майбутня гільдія:\n{icon} [{tag}] {name}\n\n" f"Вартість: {terms['cost_gold']:.2f} 🪙\n" f"Твій баланс: {terms['gold_balance']:.2f} 🪙\n" f"Початковий ліміт: {terms['member_limit']} учасників.\n\n" "Підтвердити створення?")


# ==============================
# SEND HELPERS
# ==============================

def open_guild_hall(bot, chat_id, user_id):
    reset_guild_browse_state(user_id)
    bot.send_message(chat_id, build_guild_hall_text(user_id), reply_markup=guild_hall_kb(user_id))


def send_guild_section(bot, message, text):
    bot.send_message(message.chat.id, text, reply_markup=guild_hall_kb(message.from_user.id))


def send_city(bot, message):
    from handlers.city import build_city_text
    bot.send_message(message.chat.id, build_city_text(message.from_user.id), reply_markup=city_kb())


def send_guild_create_prompt(bot, message, text):
    bot.send_message(message.chat.id, text, reply_markup=guild_create_cancel_kb())


def show_guild_list(bot, message, page=0):
    text = build_guild_list_text(message.from_user.id, page)
    kb = guild_list_kb(message.from_user.id, page)
    bot.send_message(message.chat.id, text, reply_markup=kb)


def show_guild_detail(bot, message, guild_id):
    set_selected_guild(message.from_user.id, guild_id)
    bot.send_message(
        message.chat.id,
        build_guild_detail_text(message.from_user.id, guild_id),
        reply_markup=guild_detail_kb(message.from_user.id, guild_id)
    )


# ==============================
# CREATE FLOW
# ==============================

def start_guild_creation(bot, message):
    user_id = message.from_user.id
    init_guild_system()
    terms = get_guild_creation_terms(user_id)
    if not terms.get("level_allowed"):
        bot.send_message(
            message.chat.id,
            f"❌ Створення гільдії доступне з {terms.get('min_level', 3)} рівня.\nТвій поточний рівень: {terms.get('level', 0)}.",
            reply_markup=guild_hall_kb(user_id),
        )
        return

    if get_user_guild(user_id):
        bot.send_message(message.chat.id, "❌ Ти вже перебуваєш у гільдії.", reply_markup=guild_hall_kb(user_id))
        return

    start_guild_create_state(user_id)
    send_guild_create_prompt(bot, message, build_guild_create_name_prompt())


def handle_guild_creation_message(bot, message):
    user_id = message.from_user.id
    text = (message.text or "").strip()
    state = get_guild_create_state(user_id)

    if not state:
        return False

    if text in ["❌ Скасувати створення", "🔙 Зала Гільдій", "🔙 Місто"]:
        reset_guild_create_state(user_id)
        if text == "🔙 Місто":
            send_city(bot, message)
        else:
            open_guild_hall(bot, message.chat.id, user_id)
        return True

    if text == "✏️ Почати заново":
        start_guild_create_state(user_id)
        send_guild_create_prompt(bot, message, build_guild_create_name_prompt())
        return True

    step = state.get("step")

    if step == "name":
        ok, result = validate_guild_name_for_ui(text)
        if not ok:
            send_guild_create_prompt(bot, message, result + "\n\nСпробуй ввести іншу назву.")
            return True
        state["name"] = result
        state["step"] = "tag"
        send_guild_create_prompt(bot, message, build_guild_create_tag_prompt(state["name"]))
        return True

    if step == "tag":
        ok, result = validate_guild_tag_for_ui(text)
        if not ok:
            send_guild_create_prompt(bot, message, result + "\n\nСпробуй ввести інший TAG.")
            return True
        state["tag"] = result
        state["step"] = "icon"
        send_guild_create_prompt(bot, message, build_guild_create_icon_prompt(state["name"], state["tag"]))
        return True

    if step == "icon":
        ok, result = validate_guild_icon_for_ui(text)
        if not ok:
            send_guild_create_prompt(bot, message, result + "\n\nСпробуй надіслати один emoji.")
            return True
        state["icon"] = result
        state["step"] = "confirm"
        bot.send_message(message.chat.id, build_guild_create_confirm_text(state, user_id), reply_markup=guild_create_confirm_kb())
        return True

    if step == "confirm":
        if text != "✅ Створити гільдію":
            bot.send_message(message.chat.id, "Натисни ✅ Створити гільдію або скасуй створення.", reply_markup=guild_create_confirm_kb())
            return True

        result = create_guild(user_id=user_id, name=state.get("name", ""), tag=state.get("tag", ""), icon=state.get("icon", "🏰"))
        reset_guild_create_state(user_id)

        if result.get("success"):
            bot.send_message(message.chat.id, result.get("message", "✅ Гільдію створено."), reply_markup=guild_hall_kb(user_id))
            open_guild_hall(bot, message.chat.id, user_id)
        else:
            bot.send_message(message.chat.id, result.get("message", "❌ Не вдалося створити гільдію."), reply_markup=guild_hall_kb(user_id))
        return True

    return False


# ==============================
# LIST / APPLICATION FLOW
# ==============================

def handle_guild_list_message(bot, message):
    user_id = message.from_user.id
    text = (message.text or "").strip()
    state = get_guild_browse_state(user_id)

    if not state:
        return False

    if text == "⬅️ Назад":
        show_guild_list(bot, message, max(0, state.get("page", 0) - 1))
        return True

    if text == "➡️ Далі":
        show_guild_list(bot, message, state.get("page", 0) + 1)
        return True

    if text == "📜 Переглянути гільдії":
        show_guild_list(bot, message, state.get("page", 0))
        return True

    if text == "📨 Подати заявку":
        guild_id = state.get("selected_guild_id")
        if not guild_id:
            bot.send_message(message.chat.id, "❌ Спочатку обери гільдію зі списку.", reply_markup=guild_list_kb(user_id, state.get("page", 0)))
            return True

        result = create_guild_application(user_id=user_id, guild_id=guild_id)
        bot.send_message(message.chat.id, result.get("message", ""), reply_markup=guild_detail_kb(user_id, guild_id))
        show_guild_detail(bot, message, guild_id)
        return True

    buttons = state.get("buttons", {})
    if text in buttons:
        show_guild_detail(bot, message, buttons[text])
        return True

    return False


# ==============================
# HANDLERS
# ==============================

def register_guild_handlers(bot):
    init_guild_system()

    @bot.message_handler(func=lambda message: get_guild_create_state(message.from_user.id) is not None)
    def guild_creation_state_message(message):
        handle_guild_creation_message(bot, message)

    @bot.message_handler(func=lambda message: get_guild_browse_state(message.from_user.id) is not None)
    def guild_browse_state_message(message):
        if not handle_guild_list_message(bot, message):
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

    @bot.message_handler(func=lambda message: message.text == "🏰 Зала Гільдій")
    def guild_hall_message(message):
        open_guild_hall(bot=bot, chat_id=message.chat.id, user_id=message.from_user.id)

    @bot.message_handler(func=lambda message: message.text == "🔙 Зала Гільдій")
    def guild_back_to_hall_message(message):
        reset_guild_create_state(message.from_user.id)
        reset_guild_browse_state(message.from_user.id)
        open_guild_hall(bot=bot, chat_id=message.chat.id, user_id=message.from_user.id)

    @bot.message_handler(func=lambda message: message.text == "🔙 Місто")
    def guild_back_to_city_message(message):
        reset_guild_create_state(message.from_user.id)
        reset_guild_browse_state(message.from_user.id)
        send_city(bot, message)

    @bot.message_handler(func=lambda message: message.text == "ℹ️ Інформація")
    def guild_info_message(message):
        send_guild_section(bot, message, build_guild_info_text(message.from_user.id))

    @bot.message_handler(func=lambda message: message.text == "👥 Учасники")
    def guild_members_message(message):
        show_guild_members_manage(bot, message)
        # ✅ GUILD MEMBERS OLD HANDLER REPLACED V1

    @bot.message_handler(func=lambda message: message.text == "🏆 Місячний рейтинг")
    def guild_monthly_ranking_message(message):
        send_guild_section(bot, message, build_guild_ranking_text("monthly"))

    @bot.message_handler(func=lambda message: message.text == "🏆 Рейтинг за весь час")
    def guild_total_ranking_message(message):
        send_guild_section(bot, message, build_guild_ranking_text("total"))

    @bot.message_handler(func=lambda message: message.text == "🏗️ Створити гільдію")
    def guild_create_start_message(message):
        start_guild_creation(bot, message)

    @bot.message_handler(func=lambda message: message.text == "📜 Переглянути гільдії")
    def guild_list_message(message):
        show_guild_list(bot, message, 0)

    @bot.message_handler(func=lambda message: message.text == "📨 Мої заявки")
    def guild_my_applications_message(message):
        send_guild_section(bot, message, build_my_applications_text(message.from_user.id))

    @bot.message_handler(func=lambda message: message.text == "📨 Заявки")
    def guild_applications_message(message):
        show_guild_applications(bot, message)
        # ✅ GUILD APPLICATIONS HANDLER ORDER FIX V1

    @bot.message_handler(func=lambda message: message.text == "📜 Журнал")
    def guild_logs_message(message):
        show_guild_logs(bot, message, 0)
        # ✅ GUILD JOURNAL OLD HANDLER REPLACED V1


# ==============================
# ✅ UNIQUE GUILD ICON UI VALIDATION V1
# ==============================

# 7.0.4a
# Override UI icon validation: іконка гільдії має бути унікальна.


def validate_guild_icon_for_ui(icon):
    validation = validate_guild_icon_contract(icon)
    if not validation["success"]:
        return False, validation["message"]
    icon = validation["icon"]
    from db import is_guild_icon_taken
    if is_guild_icon_taken(icon):
        return False, "❌ Така іконка вже використовується іншою гільдією. Обери іншу іконку."
    return True, icon



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
        nav.append("⬅️ Назад")
    if len(rows) > GUILD_LIST_PAGE_SIZE:
        nav.append("➡️ Далі")
    if nav:
        kb.add(*nav)

    kb.add("🔙 Зала Гільдій")

    GUILD_BROWSE_STATE[user_id] = {
        "page": page,
        "buttons": buttons,
        "selected_guild_id": None,
    }

    return kb


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
        # ✅ GUILD APPLICATION PASS THROUGH MEMBERS V1
        if message.text == "👥 Учасники":
            reset_guild_application_review_state(message.from_user.id)
            show_guild_members_manage(bot, message)
            return
        handle_guild_application_review_message(bot, message)

    @bot.message_handler(func=lambda message: message.text == "📨 Заявки")
    def guild_applications_message_v2(message):
        show_guild_applications(bot, message)


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
            f"   Рівень: {level} | Бали: {score} | Місяць: {monthly_score}\n"
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
def send_guild_members_manage_for_actor_17_21_3_4(bot, chat_id, user_id):
    user_id = int(user_id)
    _guild_safe_reset_other_states_for_members_v2(user_id)
    bot.send_message(
        chat_id,
        build_guild_member_manage_text(user_id),
        reply_markup=guild_members_manage_kb(user_id)
    )


def show_guild_members_manage(bot, message):
    send_guild_members_manage_for_actor_17_21_3_4(
        bot,
        message.chat.id,
        message.from_user.id,
    )


# Override handler to make sure selected member buttons are not swallowed by stale states.
def guild_kick_confirmation_kb_17_21_3_2(target_user_id):
    """Build confirmation controls for the selected guild member."""
    target_user_id = int(target_user_id)
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Виключити", callback_data=f"guild_kick_confirm:{target_user_id}"),
        types.InlineKeyboardButton("❌ Скасувати", callback_data=f"guild_kick_cancel:{target_user_id}")
    )
    return kb


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
        target_name = get_character_name_by_user_id(selected_user_id)
        bot.send_message(
            message.chat.id,
            f"Виключити {target_name} з гільдії?\n\n"
            "Після виключення гравець не зможе вступити до іншої гільдії "
            "або створити власну протягом 24 годин.",
            reply_markup=guild_kick_confirmation_kb_17_21_3_2(selected_user_id)
        )
        return True

    return False


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


# ==============================
# ✅ GUILD PROGRESS CONTRIBUTIONS UI V1
# ==============================

# 7.0.7
# UI для Guild EXP / Resource / внеску учасників.
# Також додає dev-команду для тесту прогресу:
# /guild_add_progress exp resource kills contracts

try:
    from db import (
        get_guild_next_level_info,
        add_user_guild_progress,
        get_guild_contribution_ranking,
        cleanup_recalculate_all_guild_levels,
    )
except Exception as _guild_progress_import_error:
    print(f"⚠️ Guild progress import failed: {_guild_progress_import_error}")


def _guild_progress_bar(percent, width=10):
    try:
        percent = float(percent)
    except Exception:
        percent = 0.0
    filled = int(round(width * max(0.0, min(100.0, percent)) / 100.0))
    return "█" * filled + "░" * (width - filled)


# ROM 17.21.1 GUILD LEAVE COOLDOWN
def guild_hall_kb(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    guild = get_user_guild(user_id)
    role = str(get_user_guild_role(user_id) or "") if guild else ""
    if guild:
        kb.add("ℹ️ Інформація", "👥 Учасники")
        kb.add("📊 Внесок", "🏛 Прогрес гільдії")
        kb.add("📨 Заявки", "📜 Журнал")
        kb.row("🏆 Місячний рейтинг", "🏆 Рейтинг за весь час")
        if role == "leader":
            kb.row("🚪 Покинути гільдію", "👑 Передати керівництво")
        else:
            kb.add("🚪 Покинути гільдію")
        kb.add("🔙 Місто")
    else:
        kb.add("🏗️ Створити гільдію")
        kb.add("📜 Переглянути гільдії")
        kb.row("🏆 Місячний рейтинг", "🏆 Рейтинг за весь час")
        kb.add("📨 Мої заявки")
        kb.add("🔙 Місто")
    return kb


def build_guild_progress_text(user_id):
    guild = get_user_guild(user_id)

    if not guild:
        return "❌ Ти не перебуваєш у гільдії."

    info = get_guild_next_level_info(guild["id"])
    guild = get_user_guild(user_id)  # refresh after possible level recalc

    if not info:
        return "❌ Не вдалося отримати прогрес гільдії."

    bar = _guild_progress_bar(info["progress_percent"])

    return (
        f"🏛 Прогрес гільдії\n\n"
        f"{get_guild_display_name(guild)}\n\n"
        f"Рівень: {guild['level']}\n"
        f"Досвід до наступного рівня:\n"
        f"{bar} {info['progress_percent']:.1f}%\n"
        f"{info['progress_exp']}/{info['needed_exp']} досвіду\n\n"
        f"Поточний сезон:\n"
        f"• Досвід: {guild['monthly_exp']}\n"
        f"• Ресурс: {guild['monthly_resource']}\n"
        f"• Вбивства: {guild['monthly_kills']}\n"
        f"• Контракти: {guild['monthly_contracts']}\n"
        f"• Бали: {guild['monthly_score']}\n\n"
        f"За весь час:\n"
        f"• Досвід: {guild['total_exp']}\n"
        f"• Ресурс: {guild['total_resource']}\n"
        f"• Вбивства: {guild['total_kills']}\n"
        f"• Контракти: {guild['total_contracts']}\n"
        f"• Бали: {guild['total_score']}"
    )


def build_guild_contribution_text(user_id, scope="monthly"):
    guild = get_user_guild(user_id)

    if not guild:
        return "❌ Ти не перебуваєш у гільдії."

    rows = get_guild_contribution_ranking(guild["id"], scope=scope, limit=30)

    if scope == "total":
        title = "📊 Внесок учасників за весь час"
    else:
        title = f"📊 Внесок учасників за місяць ({get_current_guild_season_key()})"

    text = f"{title}\n\n{get_guild_display_name(guild)}\n\n"

    if not rows:
        return text + "Поки немає учасників."

    for index, row in enumerate(rows, start=1):
        name = row["character_name"] or f"user_id={row['user_id']}"
        role_label = get_guild_role_label(row["role"])

        if scope == "total":
            score = row["contribution_score"] or 0
            exp = row["contribution_exp"] or 0
            resource = row["contribution_resource"] or 0
            kills = row["contribution_kills"] or 0
            contracts = row["contribution_contracts"] or 0
        else:
            score = row["monthly_contribution_score"] or 0
            exp = row["monthly_contribution_exp"] or 0
            resource = row["monthly_contribution_resource"] or 0
            kills = row["monthly_contribution_kills"] or 0
            contracts = row["monthly_contribution_contracts"] or 0

        text += (
            f"{index}. {role_label} {name}\n"
            f"   Бали: {score} | Досвід: {exp} | Ресурс: {resource}\n"
            f"   Вбивства: {kills} | Контракти: {contracts}\n"
        )

    return text.strip()


def guild_contribution_kb(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Внесок за місяць")
    kb.add("📊 Внесок за весь час")
    kb.add("🔙 Зала Гільдій")
    return kb


def send_guild_contribution(bot, message, scope="monthly"):
    bot.send_message(
        message.chat.id,
        build_guild_contribution_text(message.from_user.id, scope),
        reply_markup=guild_contribution_kb(message.from_user.id)
    )


def send_guild_progress(bot, message):
    bot.send_message(
        message.chat.id,
        build_guild_progress_text(message.from_user.id),
        reply_markup=guild_hall_kb(message.from_user.id)
    )


try:
    _base_register_guild_handlers_before_progress_v1 = register_guild_handlers
except Exception:
    _base_register_guild_handlers_before_progress_v1 = None


def register_guild_handlers(bot):
    if _base_register_guild_handlers_before_progress_v1 is not None:
        _base_register_guild_handlers_before_progress_v1(bot)

    @bot.message_handler(func=lambda message: message.text == "🏛 Прогрес гільдії")
    def guild_progress_message(message):
        send_guild_progress(bot, message)

    @bot.message_handler(func=lambda message: message.text == "📊 Внесок")
    def guild_contribution_message(message):
        send_guild_contribution(bot, message, "monthly")

    @bot.message_handler(func=lambda message: message.text == "📊 Внесок за місяць")
    def guild_contribution_monthly_message(message):
        send_guild_contribution(bot, message, "monthly")

    @bot.message_handler(func=lambda message: message.text == "📊 Внесок за весь час")
    def guild_contribution_total_message(message):
        send_guild_contribution(bot, message, "total")

    @bot.message_handler(commands=["guild_add_progress", "dev_guild_progress"])
    def guild_add_progress_command(message):
        parts = (message.text or "").split()

        if len(parts) < 5:
            bot.send_message(
                message.chat.id,
                "Формат: /guild_add_progress EXP RESOURCE KILLS CONTRACTS\n"
                "Приклад: /guild_add_progress 100 5 1 0",
                reply_markup=guild_hall_kb(message.from_user.id)
            )
            return

        try:
            exp = int(parts[1])
            resource = int(parts[2])
            kills = int(parts[3])
            contracts = int(parts[4])
        except Exception:
            bot.send_message(message.chat.id, "❌ Значення мають бути цілими числами.", reply_markup=guild_hall_kb(message.from_user.id))
            return

        result = add_user_guild_progress(
            user_id=message.from_user.id,
            exp=exp,
            resource=resource,
            kills=kills,
            contracts=contracts,
            reason=f"DEV progress: +{exp} EXP, +{resource} resource, +{kills} kills, +{contracts} contracts"
        )

        bot.send_message(
            message.chat.id,
            result.get("message", "") + "\n\n" + build_guild_progress_text(message.from_user.id),
            reply_markup=guild_hall_kb(message.from_user.id)
        )


# ==============================
# ✅ GUILD PROGRESS HANDLER ORDER FIX V1
# ==============================

# 7.0.7a
# Fix: кнопки 🏛 Прогрес гільдії / 📊 Внесок і команда /guild_add_progress
# могли "мовчати", якщо був активний старий state-handler:
# - GUILD_BROWSE_STATE
# - GUILD_APPLICATION_REVIEW_STATE
# - GUILD_MEMBER_MANAGE_STATE
#
# Старі state-handler-и зареєстровані раніше і перехоплюють повідомлення першими.
# Тому тут перевизначаємо їхні handle_* функції так, щоб вони пропускали
# глобальні кнопки Зали Гільдій і DEV-команду прогресу.


def _guild_progress_reset_navigation_states_v1(user_id):
    for reset_func_name in [
        "reset_guild_browse_state",
        "reset_guild_application_review_state",
        "reset_guild_member_manage_state",
    ]:
        try:
            globals()[reset_func_name](user_id)
        except Exception:
            pass


def _guild_progress_handle_dev_command_v1(bot, message):
    text = (message.text or "").strip()

    if not (text.startswith("/guild_add_progress") or text.startswith("/dev_guild_progress")):
        return False

    parts = text.split()

    if len(parts) < 5:
        bot.send_message(
            message.chat.id,
            "Формат: /guild_add_progress EXP RESOURCE KILLS CONTRACTS\n"
            "Приклад: /guild_add_progress 100 5 1 0",
            reply_markup=guild_hall_kb(message.from_user.id)
        )
        return True

    try:
        exp = int(parts[1])
        resource = int(parts[2])
        kills = int(parts[3])
        contracts = int(parts[4])
    except Exception:
        bot.send_message(
            message.chat.id,
            "❌ Значення мають бути цілими числами.",
            reply_markup=guild_hall_kb(message.from_user.id)
        )
        return True

    try:
        result = add_user_guild_progress(
            user_id=message.from_user.id,
            exp=exp,
            resource=resource,
            kills=kills,
            contracts=contracts,
            reason=f"DEV progress: +{exp} EXP, +{resource} resource, +{kills} kills, +{contracts} contracts"
        )

        bot.send_message(
            message.chat.id,
            result.get("message", "") + "\n\n" + build_guild_progress_text(message.from_user.id),
            reply_markup=guild_hall_kb(message.from_user.id)
        )
    except Exception as error:
        bot.send_message(
            message.chat.id,
            f"❌ Не вдалося додати прогрес гільдії. Помилка: {error}",
            reply_markup=guild_hall_kb(message.from_user.id)
        )

    return True


def _guild_progress_handle_global_guild_buttons_v1(bot, message):
    user_id = message.from_user.id
    text = (message.text or "").strip()

    if _guild_progress_handle_dev_command_v1(bot, message):
        return True

    if text == "🏛 Прогрес гільдії":
        _guild_progress_reset_navigation_states_v1(user_id)
        send_guild_progress(bot, message)
        return True

    if text in ["📊 Внесок", "📊 Внесок за місяць"]:
        _guild_progress_reset_navigation_states_v1(user_id)
        send_guild_contribution(bot, message, "monthly")
        return True

    if text == "📊 Внесок за весь час":
        _guild_progress_reset_navigation_states_v1(user_id)
        send_guild_contribution(bot, message, "total")
        return True

    # Також даємо можливість вийти зі stale-state без мовчання.
    if text == "🏰 Зала Гільдій":
        _guild_progress_reset_navigation_states_v1(user_id)
        open_guild_hall(bot, message.chat.id, user_id)
        return True

    if text == "👥 Учасники":
        try:
            _guild_progress_reset_navigation_states_v1(user_id)
            show_guild_members_manage(bot, message)
            return True
        except Exception:
            pass

    if text == "📨 Заявки":
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


try:
    _base_handle_guild_list_message_before_progress_order_v1 = handle_guild_list_message
except Exception:
    _base_handle_guild_list_message_before_progress_order_v1 = None


def handle_guild_list_message(bot, message):
    if _guild_progress_handle_global_guild_buttons_v1(bot, message):
        return True

    if _base_handle_guild_list_message_before_progress_order_v1 is not None:
        return _base_handle_guild_list_message_before_progress_order_v1(bot, message)

    return False


try:
    _base_handle_guild_application_review_message_before_progress_order_v1 = handle_guild_application_review_message
except Exception:
    _base_handle_guild_application_review_message_before_progress_order_v1 = None


def handle_guild_application_review_message(bot, message):
    if _guild_progress_handle_global_guild_buttons_v1(bot, message):
        return True

    if _base_handle_guild_application_review_message_before_progress_order_v1 is not None:
        return _base_handle_guild_application_review_message_before_progress_order_v1(bot, message)

    return False


try:
    _base_handle_guild_member_manage_message_before_progress_order_v1 = handle_guild_member_manage_message
except Exception:
    _base_handle_guild_member_manage_message_before_progress_order_v1 = None


def handle_guild_member_manage_message(bot, message):
    if _guild_progress_handle_global_guild_buttons_v1(bot, message):
        return True

    if _base_handle_guild_member_manage_message_before_progress_order_v1 is not None:
        return _base_handle_guild_member_manage_message_before_progress_order_v1(bot, message)

    return False


try:
    _base_handle_guild_creation_message_before_progress_order_v1 = handle_guild_creation_message
except Exception:
    _base_handle_guild_creation_message_before_progress_order_v1 = None


def handle_guild_creation_message(bot, message):
    # Під час створення гільдії не перехоплюємо звичайні кнопки прогресу,
    # але даємо DEV-команді не мовчати, якщо state випадково завис.
    if _guild_progress_handle_dev_command_v1(bot, message):
        return True

    if _base_handle_guild_creation_message_before_progress_order_v1 is not None:
        return _base_handle_guild_creation_message_before_progress_order_v1(bot, message)

    return False


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
        nav.append("⬅️ Назад")
    if page < max_page:
        nav.append("➡️ Далі")
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

    if text == "⬅️ Назад":
        show_guild_logs(bot, message, max(0, page - 1))
        return True

    if text == "➡️ Далі":
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


# ==============================
# ✅ CONTRACTS BUTTON PASS THROUGH FROM GUILD STATES V1
# ==============================

# 7.0.9b
# Fix: після меню гільдій могли залишатися активні guild state-handler-и.
# Вони перехоплювали звичайні кнопки міста/найманців, зокрема 📜 Контракти,
# і тому при натисканні нічого не відбувалося без помилки в логах.
#
# Рішення: глобальний guild-pass-through для кнопок:
# - 📜 Контракти
# - 📜 Гільдія Найманців
# - 🔙 Гільдія Найманців
# - 🏙️ Місто / 🔙 Місто
#
# Старі state-handler-и вже викликають _guild_progress_handle_global_guild_buttons_v1(),
# тому перевизначаємо цю функцію з підтримкою контрактів.

try:
    _base_guild_progress_handle_global_buttons_before_contracts_v1 = _guild_progress_handle_global_guild_buttons_v1
except Exception:
    _base_guild_progress_handle_global_buttons_before_contracts_v1 = None


def _guild_contracts_reset_guild_states_v1(user_id):
    for reset_func_name in [
        "reset_guild_browse_state",
        "reset_guild_application_review_state",
        "reset_guild_member_manage_state",
        "reset_guild_logs_state",
    ]:
        try:
            globals()[reset_func_name](user_id)
        except Exception:
            pass


def _guild_open_contracts_board_v1(bot, message):
    user_id = message.from_user.id
    _guild_contracts_reset_guild_states_v1(user_id)

    try:
        from handlers.contracts import build_contracts_text
        from keyboards import contracts_kb

        bot.send_message(
            message.chat.id,
            "📜 Ти підійшов до дошки контрактів.",
            reply_markup=contracts_kb()
        )

        text, kb = build_contracts_text(user_id)
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )
        return True
    except Exception as error:
        bot.send_message(
            message.chat.id,
            f"❌ Не вдалося відкрити контракти. Помилка: {error}",
            reply_markup=guild_hall_kb(user_id)
        )
        return True


def _guild_open_mercenary_hall_v1(bot, message):
    user_id = message.from_user.id
    _guild_contracts_reset_guild_states_v1(user_id)

    # Найкращий варіант: якщо в handlers.city є готовий builder Гільдії Найманців — використати його.
    try:
        from handlers.city import build_mercenary_guild_text
        from keyboards import mercenary_guild_kb

        bot.send_message(
            message.chat.id,
            build_mercenary_guild_text(user_id),
            reply_markup=mercenary_guild_kb()
        )
        return True
    except Exception:
        pass

    # Fallback: одразу відкрити дошку контрактів, бо саме вона потрібна гравцю.
    return _guild_open_contracts_board_v1(bot, message)


def _guild_open_city_from_stale_state_v1(bot, message):
    user_id = message.from_user.id
    _guild_contracts_reset_guild_states_v1(user_id)

    try:
        from handlers.city import build_city_text
        from keyboards import city_kb
        bot.send_message(
            message.chat.id,
            build_city_text(user_id),
            reply_markup=city_kb()
        )
        return True
    except Exception as error:
        bot.send_message(
            message.chat.id,
            f"❌ Не вдалося повернутися в місто. Помилка: {error}",
            reply_markup=guild_hall_kb(user_id)
        )
        return True


def _guild_progress_handle_global_guild_buttons_v1(bot, message):
    text = (message.text or "").strip()

    if text == "📜 Контракти":
        return _guild_open_contracts_board_v1(bot, message)

    if text in ["📜 Гільдія Найманців", "🔙 Гільдія Найманців"]:
        return _guild_open_mercenary_hall_v1(bot, message)

    if text in ["🏙️ Місто", "🔙 Місто"]:
        return _guild_open_city_from_stale_state_v1(bot, message)

    if _base_guild_progress_handle_global_buttons_before_contracts_v1 is not None:
        return _base_guild_progress_handle_global_buttons_before_contracts_v1(bot, message)

    return False


# ==============================
# ✅ GUILD CLEANUP DIAGNOSTICS UI V1
# ==============================

# 7.0.10
# Stabilization / cleanup / diagnostics:
# - one central state reset;
# - global pass-through for common buttons;
# - /guild_debug;
# - /guild_fix_states.

try:
    from db import get_guild_diagnostics, run_guild_sanity_cleanup
except Exception as _guild_diag_import_error:
    print(f"⚠️ Guild diagnostics import failed: {_guild_diag_import_error}")


def reset_all_guild_ui_states(user_id):
    """
    Central state cleanup for all guild menus.
    Safe to call even if a state does not exist in this build.
    """

    for reset_func_name in [
        "reset_guild_create_state",
        "reset_guild_browse_state",
        "reset_guild_application_review_state",
        "reset_guild_member_manage_state",
        "reset_guild_logs_state",
    ]:
        try:
            globals()[reset_func_name](user_id)
        except Exception:
            pass


def get_active_guild_ui_states(user_id):
    active = []

    state_checks = [
        ("create", "get_guild_create_state"),
        ("browse", "get_guild_browse_state"),
        ("applications", "get_guild_application_review_state"),
        ("members", "get_guild_member_manage_state"),
        ("logs", "get_guild_logs_state"),
    ]

    for label, getter_name in state_checks:
        try:
            getter = globals().get(getter_name)
            if getter and getter(user_id) is not None:
                active.append(label)
        except Exception:
            pass

    return active


def format_guild_debug_text(user_id):
    try:
        diagnostics = get_guild_diagnostics(user_id)
    except Exception as error:
        return f"🧪 Guild Debug\n\n❌ Не вдалося отримати diagnostics: {error}"

    active_states = get_active_guild_ui_states(user_id)
    guild = diagnostics.get("guild")
    member = diagnostics.get("member")
    next_level = diagnostics.get("next_level_info") or {}

    text = "🧪 Guild Debug\n\n"
    text += f"User ID: {diagnostics.get('user_id')}\n"
    text += f"Season: {diagnostics.get('season_key')}\n"
    text += f"Active UI states: {', '.join(active_states) if active_states else 'none'}\n"
    text += f"User pending applications: {diagnostics.get('user_pending_applications', 0)}\n\n"

    if not guild or not member:
        text += "Guild: none\n"
        return text.strip()

    text += f"Guild ID: {guild['id']}\n"
    text += f"Guild: {get_guild_display_name(guild)}\n"
    text += f"Role: {get_guild_role_label(member['role'])}\n"
    text += f"Members: {diagnostics.get('member_count', 0)}/{guild['member_limit']}\n"
    text += f"Officers: {diagnostics.get('officer_count', 0)}\n"
    text += f"Pending applications: {diagnostics.get('pending_applications', 0)}\n\n"

    text += f"Level: {guild['level']}\n"
    if next_level:
        text += f"Прогрес рівня: {next_level.get('progress_exp', 0)}/{next_level.get('needed_exp', 0)} EXP ({next_level.get('progress_percent', 0):.1f}%)\n"

    text += "\nMonthly:\n"
    text += f"Досвід: {guild['monthly_exp']} | Ресурс: {guild['monthly_resource']} | Вбивства: {guild['monthly_kills']} | Контракти: {guild['monthly_contracts']}\n"
    text += f"Бали: {guild['monthly_score']}\n"

    text += "\nTotal:\n"
    text += f"Досвід: {guild['total_exp']} | Ресурс: {guild['total_resource']} | Вбивства: {guild['total_kills']} | Контракти: {guild['total_contracts']}\n"
    text += f"Бали: {guild['total_score']}"

    if diagnostics.get("error"):
        text += f"\n\nError: {diagnostics.get('error')}"

    return text.strip()


def format_guild_cleanup_result_text(result):
    text = "🧹 Guild Cleanup\n\n"
    text += f"Status: {'✅ OK' if result.get('ok') else '⚠️ issues'}\n"

    stale = result.get("stale_applications")
    if isinstance(stale, dict):
        text += f"Stale pending fixed: {stale.get('fixed_same_guild', 0)}\n"
        text += f"Other pending cancelled: {stale.get('cancelled_other_guild', 0)}\n"
    else:
        text += "Stale applications: n/a\n"

    text += f"Levels recalculated: {result.get('levels_recalculated')}\n"
    text += f"Icons checked: {result.get('icons_checked')}\n"

    errors = result.get("errors") or []
    if errors:
        text += "\nErrors:\n"
        for error in errors:
            text += f"- {error}\n"

    return text.strip()


def _guild_global_navigation_passthrough_v2(bot, message):
    """
    Final global pass-through for common buttons that should work even if a guild state is active.
    """

    user_id = message.from_user.id
    text = (message.text or "").strip()

    if text in ["🏰 Зала Гільдій", "🔙 Зала Гільдій"]:
        reset_all_guild_ui_states(user_id)
        open_guild_hall(bot, message.chat.id, user_id)
        return True

    if text in ["🏙️ Місто", "🔙 Місто"]:
        reset_all_guild_ui_states(user_id)
        try:
            send_city(bot, message)
        except Exception:
            try:
                from handlers.city import build_city_text
                from keyboards import city_kb
                bot.send_message(message.chat.id, build_city_text(user_id), reply_markup=city_kb())
            except Exception as error:
                bot.send_message(message.chat.id, f"❌ Не вдалося повернутися в місто: {error}", reply_markup=guild_hall_kb(user_id))
        return True

    if text == "🏛 Прогрес гільдії":
        reset_all_guild_ui_states(user_id)
        send_guild_progress(bot, message)
        return True

    if text in ["📊 Внесок", "📊 Внесок за місяць"]:
        reset_all_guild_ui_states(user_id)
        send_guild_contribution(bot, message, "monthly")
        return True

    if text == "📊 Внесок за весь час":
        reset_all_guild_ui_states(user_id)
        send_guild_contribution(bot, message, "total")
        return True

    if text == "👥 Учасники":
        reset_all_guild_ui_states(user_id)
        show_guild_members_manage(bot, message)
        return True

    if text == "📨 Заявки":
        reset_all_guild_ui_states(user_id)
        show_guild_applications(bot, message)
        return True

    if text == "📜 Журнал":
        reset_all_guild_ui_states(user_id)
        show_guild_logs(bot, message, 0)
        return True

    if text == "📜 Переглянути гільдії":
        reset_all_guild_ui_states(user_id)
        show_guild_list(bot, message, 0)
        return True

    return False


# Chain into the existing 7.0.7a global handler if present.
try:
    _base_guild_progress_handle_global_buttons_before_cleanup_v1 = _guild_progress_handle_global_guild_buttons_v1
except Exception:
    _base_guild_progress_handle_global_buttons_before_cleanup_v1 = None


def _guild_progress_handle_global_guild_buttons_v1(bot, message):
    if _guild_global_navigation_passthrough_v2(bot, message):
        return True

    if _base_guild_progress_handle_global_buttons_before_cleanup_v1 is not None:
        return _base_guild_progress_handle_global_buttons_before_cleanup_v1(bot, message)

    return False


try:
    _base_register_guild_handlers_before_cleanup_diag_v1 = register_guild_handlers
except Exception:
    _base_register_guild_handlers_before_cleanup_diag_v1 = None


# ROM 17.22.1 GUILD LEADERSHIP TRANSFER AND LEADER EXIT
_GUILD_LEADERSHIP_STATE_17_22_1={}
def _guild_leadership_candidates_17_22_1(user_id):
    guild=get_user_guild(user_id)
    return [] if not guild else [r for r in get_guild_members(guild["id"]) if int(_member_row_get(r,"user_id",0) or 0)!=int(user_id)]
def _guild_leadership_select_kb_17_22_1(user_id,mode):
    kb=types.InlineKeyboardMarkup(row_width=1)
    for r in _guild_leadership_candidates_17_22_1(user_id):
        uid=int(_member_row_get(r,"user_id",0) or 0); name=str(_member_row_get(r,"character_name","Гравець") or "Гравець")
        kb.add(types.InlineKeyboardButton(name,callback_data=f"guild_leadership_select:{mode}:{uid}"))
    kb.add(types.InlineKeyboardButton("❌ Скасувати",callback_data="guild_leadership_cancel")); return kb
def _guild_leadership_confirm_kb_17_22_1(mode,target_id):
    kb=types.InlineKeyboardMarkup(row_width=1); kb.add(types.InlineKeyboardButton("✅ Підтвердити",callback_data=f"guild_leadership_confirm:{mode}:{int(target_id)}")); kb.add(types.InlineKeyboardButton("❌ Скасувати",callback_data="guild_leadership_cancel")); return kb

def register_guild_handlers(bot):
    @bot.message_handler(func=lambda message: getattr(message, 'text', None) == '🚪 Покинути гільдію')
    def guild_leave_prompt_17_21_1(message):
        from db import get_user_guild_role
        user_id = int(message.from_user.id)
        guild = get_user_guild(user_id)
        if not guild:
            bot.send_message(message.chat.id, '❌ Ти не перебуваєш у гільдії.', reply_markup=guild_hall_kb(user_id))
            return
        if str(get_user_guild_role(user_id) or '') == 'leader':
            candidates=_guild_leadership_candidates_17_22_1(user_id)
            if not candidates: bot.send_message(message.chat.id,"❌ Голова не може покинути одноосібну гільдію.",reply_markup=guild_hall_kb(user_id)); return
            _GUILD_LEADERSHIP_STATE_17_22_1[user_id]={"mode":"leave"}
            bot.send_message(message.chat.id,"Оберіть нового голову. Після підтвердження ти покинеш гільдію.",reply_markup=_guild_leadership_select_kb_17_22_1(user_id,"leave"))
            return
        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton('✅ Покинути', callback_data='guild_leave:confirm'), types.InlineKeyboardButton('❌ Скасувати', callback_data='guild_leave:cancel'))
        bot.send_message(message.chat.id, f"Покинути гільдію {get_guild_display_name(guild)}?\n\nПісля виходу ти не зможеш вступити до іншої гільдії або створити власну протягом 24 годин.", reply_markup=kb)
    @bot.callback_query_handler(func=lambda call: str(getattr(call, 'data', '')).startswith('guild_leave:'))
    def guild_leave_callback_17_21_1(call):
        from db import leave_guild
        user_id = int(call.from_user.id)
        action = str(call.data).split(':', 1)[1]
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        if action == 'cancel':
            bot.send_message(call.message.chat.id, 'ℹ️ Вихід із гільдії скасовано.', reply_markup=guild_hall_kb(user_id))
            return
        result = leave_guild(user_id)
        bot.send_message(call.message.chat.id, result.get('message', '❌ Не вдалося виконати дію.'), reply_markup=guild_hall_kb(user_id))
    @bot.message_handler(func=lambda m:getattr(m,"text",None)=="👑 Передати керівництво")
    def guild_leadership_start_17_22_1(message):
        uid=int(message.from_user.id); candidates=_guild_leadership_candidates_17_22_1(uid)
        if str(get_user_guild_role(uid) or "")!="leader": bot.send_message(message.chat.id,"❌ Передавати керівництво може тільки голова."); return
        if not candidates: bot.send_message(message.chat.id,"❌ У гільдії немає іншого учасника.",reply_markup=guild_hall_kb(uid)); return
        _GUILD_LEADERSHIP_STATE_17_22_1[uid]={"mode":"transfer"}; bot.send_message(message.chat.id,"Оберіть нового голову:",reply_markup=_guild_leadership_select_kb_17_22_1(uid,"transfer"))
    @bot.callback_query_handler(func=lambda c:str(getattr(c,"data","")).startswith("guild_leadership_"))
    def guild_leadership_callback_17_22_1(call):
        uid=int(call.from_user.id); data=str(call.data)
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        if data=="guild_leadership_cancel": _GUILD_LEADERSHIP_STATE_17_22_1.pop(uid,None); bot.send_message(call.message.chat.id,"❌ Операцію скасовано.",reply_markup=guild_hall_kb(uid)); return
        parts=data.split(":")
        if len(parts)!=3 or parts[0] not in {"guild_leadership_select","guild_leadership_confirm"} or parts[1] not in {"transfer","leave"}: return
        mode,target_id=parts[1],int(parts[2]); guild=get_user_guild(uid); target=get_guild_member(guild["id"],target_id) if guild else None
        if str(get_user_guild_role(uid) or "")!="leader" or not target: _GUILD_LEADERSHIP_STATE_17_22_1.pop(uid,None); bot.send_message(call.message.chat.id,"❌ Склад гільдії змінився. Почніть знову.",reply_markup=guild_hall_kb(uid)); return
        name=get_character_name_by_user_id(target_id)
        if parts[0]=="guild_leadership_select": _GUILD_LEADERSHIP_STATE_17_22_1[uid]={"mode":mode,"target_id":target_id}; bot.send_message(call.message.chat.id,f"Новий голова — {name}. Підтвердити?",reply_markup=_guild_leadership_confirm_kb_17_22_1(mode,target_id)); return
        state=_GUILD_LEADERSHIP_STATE_17_22_1.pop(uid,None)
        if not state or state.get("mode")!=mode or int(state.get("target_id",0))!=target_id: bot.send_message(call.message.chat.id,"❌ Підтвердження застаріло.",reply_markup=guild_hall_kb(uid)); return
        result=transfer_guild_leadership(uid,target_id) if mode=="transfer" else transfer_guild_leadership_and_leave(uid,target_id)
        bot.send_message(call.message.chat.id,result.get("message","❌ Операцію не завершено."),reply_markup=guild_hall_kb(uid))
    if _base_register_guild_handlers_before_cleanup_diag_v1 is not None:
        _base_register_guild_handlers_before_cleanup_diag_v1(bot)

    @bot.message_handler(commands=["guild_debug"])
    def guild_debug_command(message):
        bot.send_message(
            message.chat.id,
            format_guild_debug_text(message.from_user.id),
            reply_markup=guild_hall_kb(message.from_user.id)
        )

    @bot.message_handler(commands=["guild_fix_states", "guild_cleanup"])
    def guild_fix_states_command(message):
        reset_all_guild_ui_states(message.from_user.id)
        try:
            result = run_guild_sanity_cleanup()
        except Exception as error:
            result = {"ok": False, "errors": [str(error)]}

        bot.send_message(
            message.chat.id,
            format_guild_cleanup_result_text(result),
            reply_markup=guild_hall_kb(message.from_user.id)
        )


    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith(("guild_kick_confirm:", "guild_kick_cancel:")))
    def guild_kick_confirmation_callback_17_21_3_2(call):
        user_id = int(call.from_user.id)
        data = str(getattr(call, "data", ""))
        try:
            action, target_raw = data.split(":", 1)
            target_user_id = int(target_raw)
        except (TypeError, ValueError):
            try:
                bot.answer_callback_query(call.id, "Некоректна дія.", show_alert=True)
            except Exception:
                pass
            return
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        if action == "guild_kick_cancel":
            bot.send_message(
                call.message.chat.id,
                "ℹ️ Виключення учасника скасовано.",
                reply_markup=guild_member_detail_kb(user_id, target_user_id)
            )
            return
        result = kick_guild_member(user_id, target_user_id)
        bot.send_message(
            call.message.chat.id,
            result.get("message", "❌ Не вдалося виконати дію."),
            reply_markup=guild_members_manage_kb(user_id)
        )
        send_guild_members_manage_for_actor_17_21_3_4(bot, call.message.chat.id, user_id)
    # ROM 17.22.1 GUILD LEADERSHIP TRANSFER AND LEADER EXIT



# Stage 17.11.2 compact Guild text wrappers.
def _compact_guild_actions_17_11_2(text, stop_marker=None):
    marker = "\n\nДоступні дії:\n"
    if marker not in text:
        marker = "Доступні дії:\n"
    if marker not in text:
        return text
    start = text.index(marker)
    if stop_marker and stop_marker in text[start:]:
        end = text.index(stop_marker, start)
        return (text[:start].rstrip() + "\n\n" + text[end:].lstrip()).strip()
    return text[:start].rstrip()

_BASE_GUILD_HALL_NO_GUILD_TEXT_17_11_2 = build_guild_hall_no_guild_text
_BASE_GUILD_HALL_MEMBER_TEXT_17_11_2 = build_guild_hall_member_text
_BASE_GUILD_MEMBER_DETAIL_TEXT_17_11_2 = build_guild_member_detail_text


def build_guild_hall_no_guild_text(*args, **kwargs):
    return _compact_guild_actions_17_11_2(
        _BASE_GUILD_HALL_NO_GUILD_TEXT_17_11_2(*args, **kwargs),
        stop_marker="Поточний рейтинговий сезон:",
    )


def build_guild_hall_member_text(*args, **kwargs):
    return _compact_guild_actions_17_11_2(
        _BASE_GUILD_HALL_MEMBER_TEXT_17_11_2(*args, **kwargs)
    )


def build_guild_member_detail_text(*args, **kwargs):
    text = _BASE_GUILD_MEMBER_DETAIL_TEXT_17_11_2(*args, **kwargs)
    return text.replace("Доступні дії:\n", "Керування:\n")

