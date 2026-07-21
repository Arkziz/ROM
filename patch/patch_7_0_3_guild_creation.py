from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "7_0_3_guild_creation"
GUILD_HANDLER_PATH = Path("handlers") / "guild.py"

GUILD_HANDLER_CODE = r'''
from telebot import types

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
    get_guild_by_name_or_tag,
)

from keyboards import city_kb


GUILD_RANKING_LIMIT = 10

# module-level state for guild creation wizard
# user_id -> {step, name, tag, icon}
GUILD_CREATE_STATE = {}


# ==============================
# REPLY KEYBOARDS
# ==============================

def guild_hall_kb(user_id):
    """
    ReplyKeyboard для Зали Гільдій.
    """

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


# ==============================
# VALIDATION HELPERS
# ==============================

def normalize_guild_tag_input(value):
    return (value or "").strip().upper()


def validate_guild_name_for_ui(name):
    name = (name or "").strip()

    if len(name) < 3:
        return False, "❌ Назва гільдії має містити мінімум 3 символи."

    if len(name) > 32:
        return False, "❌ Назва гільдії має бути не довша за 32 символи."

    if get_guild_by_name_or_tag(name):
        return False, "❌ Гільдія з такою назвою або абревіатурою вже існує."

    return True, name


def validate_guild_tag_for_ui(tag):
    tag = normalize_guild_tag_input(tag)

    if len(tag) < 2:
        return False, "❌ Абревіатура гільдії має містити мінімум 2 символи."

    if len(tag) > 5:
        return False, "❌ Абревіатура гільдії має бути не довша за 5 символів."

    # keep it simple and readable for ratings/list display
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    if any(ch not in allowed for ch in tag):
        return False, "❌ Абревіатура може містити тільки літери та цифри."

    if get_guild_by_name_or_tag(tag):
        return False, "❌ Гільдія з такою назвою або абревіатурою вже існує."

    return True, tag


def validate_guild_icon_for_ui(icon):
    icon = (icon or "").strip()

    if not icon:
        return True, "🏰"

    # Telegram emoji may be several codepoints, so only prevent very long text.
    if len(icon) > 4:
        return False, "❌ Іконка має бути короткою. Найкраще — один emoji."

    return True, icon


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
        f"• EXP: {guild['monthly_exp']}\n"
        f"• Ресурс: {guild['monthly_resource']}\n"
        f"• Вбивства: {guild['monthly_kills']}\n"
        f"• Контракти: {guild['monthly_contracts']}\n"
        f"• Score: {guild['monthly_score']}\n\n"
        f"За весь час:\n"
        f"• EXP: {guild['total_exp']}\n"
        f"• Ресурс: {guild['total_resource']}\n"
        f"• Score: {guild['total_score']}\n\n"
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

    return (
        f"ℹ️ Інформація про гільдію\n\n"
        f"{guild_name}\n"
        f"Голова user_id: {guild['leader_user_id']}\n"
        f"Рівень: {guild['level']}\n"
        f"Учасники: {member_count}/{guild['member_limit']}\n"
        f"Створено: {guild['created_at']}\n\n"
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
            f"   Рівень: {level} | Score: {score} | Місяць: {monthly_score}\n"
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
            f"   Score: {score} | EXP: {exp} | Ресурс: {resource}\n"
        )

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
        "• назва має бути унікальною.\n\n"
        "Створення гільдії зараз безкоштовне."
    )


def build_guild_create_tag_prompt(name):
    return (
        "🏗️ Створення гільдії\n\n"
        "Крок 2/4 — абревіатура.\n\n"
        f"Назва: {name}\n\n"
        "Введи короткий TAG гільдії.\n"
        "Вимоги:\n"
        "• від 2 до 5 символів;\n"
        "• тільки літери та цифри;\n"
        "• буде показуватись у рейтингах, наприклад [ROM]."
    )


def build_guild_create_icon_prompt(name, tag):
    return (
        "🏗️ Створення гільдії\n\n"
        "Крок 3/4 — іконка.\n\n"
        f"Назва: {name}\n"
        f"TAG: [{tag}]\n\n"
        "Надішли один emoji для іконки гільдії.\n"
        "Наприклад: 🏰, 🐺, 🔥, 🍒\n\n"
        "Якщо хочеш стандартну іконку — надішли 🏰."
    )


def build_guild_create_confirm_text(state):
    name = state.get("name", "")
    tag = state.get("tag", "")
    icon = state.get("icon", "🏰")

    return (
        "🏗️ Створення гільдії\n\n"
        "Крок 4/4 — підтвердження.\n\n"
        f"Майбутня гільдія:\n"
        f"{icon} [{tag}] {name}\n\n"
        "Вартість створення: 0 золота.\n\n"
        "Підтвердити створення?"
    )


# ==============================
# SEND HELPERS
# ==============================

def open_guild_hall(bot, chat_id, user_id):
    bot.send_message(
        chat_id,
        build_guild_hall_text(user_id),
        reply_markup=guild_hall_kb(user_id)
    )


def send_guild_section(bot, message, text):
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=guild_hall_kb(message.from_user.id)
    )


def send_city(bot, message):
    from handlers.city import build_city_text

    bot.send_message(
        message.chat.id,
        build_city_text(message.from_user.id),
        reply_markup=city_kb()
    )


def send_guild_create_prompt(bot, message, text):
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=guild_create_cancel_kb()
    )


# ==============================
# CREATE FLOW
# ==============================

def start_guild_creation(bot, message):
    user_id = message.from_user.id

    init_guild_system()

    if get_user_guild(user_id):
        bot.send_message(
            message.chat.id,
            "❌ Ти вже перебуваєш у гільдії.",
            reply_markup=guild_hall_kb(user_id)
        )
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

        bot.send_message(
            message.chat.id,
            build_guild_create_confirm_text(state),
            reply_markup=guild_create_confirm_kb()
        )
        return True

    if step == "confirm":
        if text != "✅ Створити гільдію":
            bot.send_message(
                message.chat.id,
                "Натисни ✅ Створити гільдію або скасуй створення.",
                reply_markup=guild_create_confirm_kb()
            )
            return True

        result = create_guild(
            user_id=user_id,
            name=state.get("name", ""),
            tag=state.get("tag", ""),
            icon=state.get("icon", "🏰"),
        )

        reset_guild_create_state(user_id)

        if result.get("success"):
            bot.send_message(
                message.chat.id,
                result.get("message", "✅ Гільдію створено."),
                reply_markup=guild_hall_kb(user_id)
            )
            open_guild_hall(bot, message.chat.id, user_id)
        else:
            bot.send_message(
                message.chat.id,
                result.get("message", "❌ Не вдалося створити гільдію."),
                reply_markup=guild_hall_kb(user_id)
            )

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

    @bot.message_handler(func=lambda message: message.text == "🏰 Зала Гільдій")
    def guild_hall_message(message):
        open_guild_hall(
            bot=bot,
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )

    @bot.message_handler(func=lambda message: message.text == "🔙 Місто")
    def guild_back_to_city_message(message):
        reset_guild_create_state(message.from_user.id)
        send_city(bot, message)

    @bot.message_handler(func=lambda message: message.text == "ℹ️ Інформація")
    def guild_info_message(message):
        send_guild_section(
            bot,
            message,
            build_guild_info_text(message.from_user.id)
        )

    @bot.message_handler(func=lambda message: message.text == "👥 Учасники")
    def guild_members_message(message):
        send_guild_section(
            bot,
            message,
            build_guild_members_text(message.from_user.id)
        )

    @bot.message_handler(func=lambda message: message.text == "🏆 Місячний рейтинг")
    def guild_monthly_ranking_message(message):
        send_guild_section(
            bot,
            message,
            build_guild_ranking_text("monthly")
        )

    @bot.message_handler(func=lambda message: message.text == "🏆 Рейтинг за весь час")
    def guild_total_ranking_message(message):
        send_guild_section(
            bot,
            message,
            build_guild_ranking_text("total")
        )

    @bot.message_handler(func=lambda message: message.text == "🏗️ Створити гільдію")
    def guild_create_start_message(message):
        start_guild_creation(bot, message)

    @bot.message_handler(func=lambda message: message.text == "📜 Переглянути гільдії")
    def guild_list_message(message):
        send_guild_section(
            bot,
            message,
            build_guild_placeholder_text("📜 Список гільдій", "7.0.4")
        )

    @bot.message_handler(func=lambda message: message.text == "📨 Мої заявки")
    def guild_my_applications_message(message):
        send_guild_section(
            bot,
            message,
            build_guild_placeholder_text("📨 Мої заявки", "7.0.4")
        )

    @bot.message_handler(func=lambda message: message.text == "📨 Заявки")
    def guild_applications_message(message):
        send_guild_section(
            bot,
            message,
            build_guild_placeholder_text("📨 Заявки до гільдії", "7.0.5")
        )

    @bot.message_handler(func=lambda message: message.text == "📜 Журнал")
    def guild_logs_message(message):
        send_guild_section(
            bot,
            message,
            build_guild_placeholder_text("📜 Журнал гільдії", "7.0.8")
        )
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
    target = root / GUILD_HANDLER_PATH

    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/guild.py. Спочатку застосуй 7.0.2 / 7.0.2a.")

    original = target.read_text(encoding="utf-8")
    backup_path = make_backup(root, target)

    target.write_text(GUILD_HANDLER_CODE.strip() + "\n", encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_3_guild_creation.\n"
            "handlers/guild.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.3 Guild Creation застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ handlers/guild.py пройшов py_compile.")
    print("")
    print("Що додано:")
    print("- створення гільдії через ReplyKeyboard flow")
    print("- крок 1: назва")
    print("- крок 2: TAG / абревіатура")
    print("- крок 3: іконка")
    print("- крок 4: підтвердження")
    print("- створення поки безкоштовне")
    print("- після створення гравець стає 👑 Головою гільдії")
    print("")
    print("Після патча:")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
