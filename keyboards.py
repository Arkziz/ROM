from telebot import types


def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔎 Полювання", "🗺️ Мапа")
    kb.add("🎒 Інвентар", "👤 Профіль")
    return kb


def fight_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⚔️ Атакувати")
    kb.add("🏃 Втекти")
    return kb