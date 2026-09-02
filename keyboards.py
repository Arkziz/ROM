# ROM 17.16.1 PVE SKILL BUTTON STATES
# ROM 17.11.1 TRADE DISTRICT TEXT NAVIGATION
from telebot import types


def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔎 Полювання", "🗺️ Мапа")
    kb.add("👤 Профіль", "👀 Роззирнутися")
    kb.add("📋 Меню")
    return kb


def map_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # ROM 12.2.1 MAP REFRESH AND KEYBOARD HOTFIX
    kb.row(types.KeyboardButton("🌿 Початок Шляху"), types.KeyboardButton("🌲 Темний Бір"))
    kb.row(types.KeyboardButton("👥 Гравці локації"), types.KeyboardButton("🏙️ Місто"))
    kb.row(types.KeyboardButton("🔙 Назад"))
    return kb


def profile_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎒 Інвентар", "📜 Історія")
    kb.add("🔙 Назад")
    return kb


def fight_kb(skills=None):
    """
    Стара функція, залишаємо для сумісності — тепер використовуємо build_combat_inline_kb
    """
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⚔️ Атакувати", "✨ Навички")
    kb.add("🧪 Зілля", "🏃 Втекти")
    return kb


# ==============================
# 🏙️ CITY DISTRICTS
# ==============================

def city_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Міські напрямки згруповані по 2 кнопки в ряд.
    # 🗺️ Мапа завжди окремо і останньою кнопкою внизу.
    kb.add("🛒 Торговий ряд", "🏛️ Торговий дім")
    kb.add("⚒️ Ремісничий квартал", "📜 Гільдія Найманців")
    kb.add("🏰 Зала Гільдій", "🏛️ Ратуша")
    kb.add("🍺 Таверна")
    kb.add("🗺️ Мапа")

    return kb

def trader_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🪙 Продати весь мотлох")
    kb.add("🧰 Продати спорядження")
    kb.add("⚪ Базове спорядження")
    kb.add("🔙 Місто")
    return kb


def craft_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⚒️ Коваль", "🧪 Алхімік")
    kb.add("💠 Рунний Майстер")
    kb.add("🔙 Місто")
    return kb


def blacksmith_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛠️ Ремонт", "✨ Заточка")
    kb.add("🔙 Ремісничий квартал")
    return kb

def alchemist_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Ремісничий квартал")
    return kb


def guild_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📜 Контракти")
    kb.add("🔙 Місто")
    return kb


def contracts_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Гільдія Найманців")
    return kb


def townhall_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📆 Щоденне завдання")
    kb.add("🔙 Місто")
    return kb


def tavern_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Місто")
    return kb


# ==============================
# ⚔️ COMBAT KEYBOARDS
# ==============================

def build_combat_inline_kb(user_id, mob):
    """Build the current authoritative PvE inline combat keyboard."""
    from handlers.combat import get_player_class_skills
    from systems.pve_skill_action_state import get_pve_skill_action_state

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("⚔️ Атакувати", callback_data="combat_attack"),
        types.InlineKeyboardButton("🧪 Зілля", callback_data="combat_potion"),
        types.InlineKeyboardButton("🏃 Втекти", callback_data="combat_flee")
    )

    try:
        for skill in get_player_class_skills(user_id) or []:
            state = get_pve_skill_action_state(user_id, mob, skill)
            kb.add(types.InlineKeyboardButton(
                text=state["label"],
                callback_data=state["callback_data"],
            ))
    except Exception:
        pass
    return kb


def combat_placeholder_kb():
    """
    Фальшива клавіатура для заблокування системної клавіатури під час бою.
    Показується перед inline меню.
    """
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    kb.add("⚔️ Бій триває...")
    return kb

# ==============================
# ROM 10.8.1 RUNE MASTER DEDICATED MENU
# ==============================

def rune_master_kb():
    """Dedicated Rune Master menu without Blacksmith/Alchemist buttons."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💠 Вставити руну", "🔄 Переробити руни")
    kb.add("🧰 Екстрактор", "🛒 Крамниця")
    kb.add("🔙 Ремісничий квартал")
    return kb

