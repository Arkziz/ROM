from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "7_0_2a_guild_hall_reply_keyboard"
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
)

from keyboards import city_kb


GUILD_RANKING_LIMIT = 10


# ==============================
# REPLY KEYBOARDS
# ==============================

def guild_hall_kb(user_id):
    """
    ReplyKeyboard для Зали Гільдій.

    Важливо:
    у місті ми використовуємо звичайні кнопки основного меню, не inline.
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
    # Import inside function to avoid circular imports at module load.
    from handlers.city import build_city_text

    bot.send_message(
        message.chat.id,
        build_city_text(message.from_user.id),
        reply_markup=city_kb()
    )


# ==============================
# HANDLERS
# ==============================

def register_guild_handlers(bot):
    init_guild_system()

    @bot.message_handler(func=lambda message: message.text == "🏰 Зала Гільдій")
    def guild_hall_message(message):
        open_guild_hall(
            bot=bot,
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )

    @bot.message_handler(func=lambda message: message.text == "🔙 Місто")
    def guild_back_to_city_message(message):
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
        send_guild_section(
            bot,
            message,
            build_guild_placeholder_text("🏗️ Створення гільдії", "7.0.3")
        )

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


def write_guild_handler(root):
    target = root / GUILD_HANDLER_PATH
    target.parent.mkdir(exist_ok=True)
    backup = make_backup(root, target) if target.exists() else None
    target.write_text(GUILD_HANDLER_CODE.strip() + "\n", encoding="utf-8")
    return target, backup, None


def patch_keyboards(root):
    target = root / "keyboards.py"

    if not target.exists():
        raise SystemExit("❌ Не знайдено keyboards.py")

    original = target.read_text(encoding="utf-8")
    text = original
    backup = make_backup(root, target)

    pattern = re.compile(
        r"def\s+city_kb\s*\(\s*\)\s*:\n(?:.*?)(?=\ndef\s+\w+\s*\(|\Z)",
        flags=re.S,
    )

    replacement = r'''def city_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Торговий ряд")
    kb.add("⚒️ Ремісничий квартал")
    kb.add("📜 Гільдія Найманців")
    kb.add("🏰 Зала Гільдій")
    kb.add("🏛️ Ратуша", "🍺 Таверна")
    kb.add("🔙 Мапа")
    return kb

# ✅ GUILD HALL CITY BUTTON REPLY V2
'''

    if not pattern.search(text):
        raise SystemExit("❌ Не знайдено def city_kb() у keyboards.py")

    text = pattern.sub(replacement, text, count=1)
    target.write_text(text, encoding="utf-8")
    return target, backup, original


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [write_guild_handler, patch_keyboards]:
            file_path, backup_path, original = patch_func(root)
            changed_files.append(file_path)
            if backup_path:
                backups.append(backup_path)
            if original is not None:
                originals.append((file_path, original))

        for file_path in changed_files:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            if original is not None:
                file_path.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка під час patch_7_0_2a_guild_hall_reply_keyboard.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.2a Guild Hall Reply Keyboard застосовано успішно.")
    print("")
    print("Змінені файли:")
    for file_path in changed_files:
        print(f"- {file_path}")

    if backups:
        print("")
        print("Backup:")
        for backup in backups:
            print(f"- {backup}")

    print("")
    print("Що змінено:")
    print("- Зала Гільдій більше не використовує inline-кнопки")
    print("- усі дії в Залі Гільдій тепер через звичайні ReplyKeyboard кнопки")
    print("- додано кнопку 🔙 Місто для повернення в місто")
    print("- city_kb() лишається у стилі інших частин міста")
    print("")
    print("Після патча:")
    print("python -m py_compile .\\handlers\\guild.py")
    print("python -m py_compile .\\keyboards.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
