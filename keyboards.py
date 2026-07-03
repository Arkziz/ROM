from telebot import types


def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔎 Полювання", "🗺️ Мапа")
    kb.add("👤 Профіль", "👀 Роззирнутися")
    return kb


def map_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌿 Початок Шляху")
    kb.add("🌲 Темний Бір")
    kb.add("🏙️ Місто")
    kb.add("🔙 Назад")
    return kb


def profile_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎒 Інвентар")
    kb.add("🔙 Назад")
    return kb


def fight_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⚔️ Атакувати", "🧪 Зілля")
    kb.add("🏃 Втекти")
    return kb


# ==============================
# 🏙️ CITY DISTRICTS
# ==============================

def city_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Торговий ряд")
    kb.add("⚒️ Ремісничий квартал")
    kb.add("📜 Гільдія Найманців")
    kb.add("🏛️ Ратуша", "🍺 Таверна")
    kb.add("🔙 Мапа")
    return kb


def trader_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🪙 Продати весь хлам")
    kb.add("🧰 Продати спорядження")
    kb.add("⚪ Базове спорядження")
    kb.add("🔙 Місто")
    return kb


def craft_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⚒️ Коваль", "🧪 Алхімік")
    kb.add("🔙 Місто")
    return kb


def blacksmith_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
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