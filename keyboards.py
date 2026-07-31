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
    kb.add("🪙 Продати весь хлам")
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
    """
    Будує inline клавіатуру для бою з основними опціями та навичками.
    Навички отримуються напряму з класу гравця.
    """
    from handlers.combat import get_player_class_skills, get_skill_cooldown
    
    kb = types.InlineKeyboardMarkup()
    
    # Основні кнопки
    kb.add(
        types.InlineKeyboardButton("⚔️ Атакувати", callback_data="combat_attack"),
        types.InlineKeyboardButton("🧪 Зілля", callback_data="combat_potion"),
        types.InlineKeyboardButton("🏃 Втекти", callback_data="combat_flee")
    )
    
    # Навички гравця (якщо вони є)
    try:
        skills = get_player_class_skills(user_id)
        if skills:
            for skill in skills:
                cooldown = get_skill_cooldown(mob, skill["key"])
                
                if cooldown > 0:
                    # Навичка в перезарядці
                    kb.add(
                        types.InlineKeyboardButton(
                            f"🔒 {skill['name']} ({cooldown}ч)",
                            callback_data=f"skill_locked:{skill['key']}"
                        )
                    )
                else:
                    # Навичка доступна
                    kb.add(
                        types.InlineKeyboardButton(
                            f"✨ {skill['name']}",
                            callback_data=f"combat_use_skill:{skill['key']}"
                        )
                    )
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
    kb.add("🧰 Екстрактор")
    kb.add("🛒 Крамниця")
    kb.add("🔙 Ремісничий квартал")
    return kb

