from telebot import types


def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔎 Полювання", "🗺️ Мапа")
    kb.add("👤 Профіль")
    return kb


def map_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
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


def city_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Торговець", "🧪 Алхімік")
    kb.add("⚒️ Коваль")
    kb.add("🔙 Мапа")
    return kb


def trader_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🪙 Продати весь хлам")
    kb.add("🔙 Місто")
    return kb


def alchemist_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Місто")
    return kb


def blacksmith_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Місто")
    return kb