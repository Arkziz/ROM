from telebot import types


def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔎 Полювання", "🗺️ Мапа")
    kb.add("🏙️ Місто", "🎒 Інвентар")
    kb.add("👤 Профіль")
    return kb


def fight_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⚔️ Атакувати")
    kb.add("🏃 Втекти")
    return kb


def city_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Торговець")
    kb.add("🔙 Назад")
    return kb


def trader_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🪙 Продати весь хлам")
    kb.add("🔙 Місто")
    return kb