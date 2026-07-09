from telebot import types

from db import (
    get_player_stats,
    get_current_hp,
    get_max_hp,
    get_user_energy,
    get_user_progress,

    get_physical_defense,
    get_magic_defense,
    get_physical_crit_chance_display,
    get_magical_crit_chance_display,
    get_base_dodge_chance_display,
    get_enemy_crit_chance_against_player,

    get_all_equipped_slots,
    get_item_by_inventory_id_full,
    get_inventory_weapon_damage_display,

    get_character_profile_summary,
    get_character_class
,
    process_passive_regeneration,
    reset_daily_hunts_if_needed,)

from keyboards import profile_kb, main_kb
from utils import hp_bar

# Імпортуємо навички з боєчного модуля, щоб показувати їх у профілі
from handlers.combat import CLASS_SKILLS_V1


# ==============================
# INLINE PROFILE TABS
# ==============================

def profile_inline_kb(active_tab="character"):
    """
    Inline-навігація між вкладками профілю.

    active_tab:
    - character
    - stats
    - equipment
    - skills

    Поточна вкладка НЕ показується як кнопка.
    """

    kb = types.InlineKeyboardMarkup(row_width=2)

    buttons = []

    if active_tab != "character":
        buttons.append(types.InlineKeyboardButton(
            text="👤 Персонаж",
            callback_data="profile_character"
        ))

    if active_tab != "stats":
        buttons.append(types.InlineKeyboardButton(
            text="📊 Параметри",
            callback_data="profile_stats"
        ))

    if active_tab != "equipment":
        buttons.append(types.InlineKeyboardButton(
            text="🧰 Екіпірування",
            callback_data="profile_equipment"
        ))

    if active_tab != "skills":
        buttons.append(types.InlineKeyboardButton(
            text="✨ Навички",
            callback_data="profile_skills"
        ))

    # Розподіл кнопок по рядках
    if len(buttons) == 1:
        kb.add(buttons[0])
    elif len(buttons) == 2:
        kb.add(buttons[0], buttons[1])
    elif len(buttons) == 3:
        kb.add(buttons[0], buttons[1])
        kb.add(buttons[2])
    elif len(buttons) == 4:
        kb.add(buttons[0], buttons[1])
        kb.add(buttons[2], buttons[3])

    return kb


# ==============================
# HELPERS
# ==============================

def format_resource_line(profile_summary):
    resource_type = profile_summary.get("resource_type", "")

    if resource_type == "rage":
        return "🔴 Бойовий ресурс: Лютість\n"

    if resource_type == "combat_energy":
        return "🟡 Бойовий ресурс: Енергія\n"

    if resource_type == "combat_energy_combo":
        return "🟡 Бойовий ресурс: Енергія + комбо\n"

    if resource_type == "mana":
        mp_data = profile_summary.get("mp_data", {})
        mp = mp_data.get("mp", 0)
        max_mp = mp_data.get("max_mp", 0)

        return f"🔵 Мана: {mp}/{max_mp}\n"

    return "Бойовий ресурс: не визначено\n"


def format_equipment_bonuses(b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef):
    bonuses = []

    if b_str:
        bonuses.append(f"💪 Сила +{b_str}")
    if b_dex:
        bonuses.append(f"🎯 Спритність +{b_dex}")
    if b_int:
        bonuses.append(f"🔮 Інтелект +{b_int}")
    if b_wis:
        bonuses.append(f"🦉 Мудрість +{b_wis}")
    if b_sta:
        bonuses.append(f"🛡 Витривалість +{b_sta}")
    if pdef:
        bonuses.append(f"🛡 Фіз. захист +{pdef}")
    if mdef:
        bonuses.append(f"🔮 Маг. захист +{mdef}")

    return bonuses


# ==============================
# PROFILE TEXT
# ==============================

def build_character_text(user_id):
    process_passive_regeneration(user_id)
    reset_daily_hunts_if_needed(user_id)
    stats = get_player_stats(user_id)

    if not stats:
        return "❗ Персонажа не знайдено. Натисни /start."

    str_, dex_, int_, wis_, sta_, lvl = stats

    current_hp = get_current_hp(user_id)
    max_hp = get_max_hp(user_id)

    energy_data = get_user_energy(user_id)
    energy = energy_data["energy"]
    max_energy = energy_data["max_energy"]

    progress = get_user_progress(user_id)

    if progress:
        exp = progress["exp"]
        exp_to_next = progress["exp_to_next"]
        gold = progress["gold"]
        kills = progress["kills"]
        daily_hunts = progress["daily_hunts"]
    else:
        exp = 0
        exp_to_next = 0
        gold = 0
        kills = 0
        daily_hunts = 0

    exp_percent = 0

    if exp_to_next > 0:
        exp_percent = (exp / exp_to_next) * 100

    profile_summary = get_character_profile_summary(user_id)
    character_name = profile_summary.get("name") or "Без імені"
    class_name = profile_summary.get("class_name") or "Не обрано"

    text = (
        f"👤 Персонаж\n\n"
        f"📝 Ім’я: {character_name}\n"
        f"🧭 Клас: {class_name}\n"
        f"{format_resource_line(profile_summary)}\n"

        f"🏆 Рівень: {lvl}\n"
        f"❤️ Здоров’я: {current_hp}/{max_hp}\n"
        f"{hp_bar(current_hp, max_hp)}\n"
        f"😴 Втома: {energy}/{max_energy}\n\n"

        f"— Характеристики —\n"
        f"💪 Сила: {str_}\n"
        f"🎯 Спритність: {dex_}\n"
        f"🔮 Інтелект: {int_}\n"
        f"🦉 Мудрість: {wis_}\n"
        f"🛡 Витривалість: {sta_}\n\n"

        f"— Прогрес —\n"
        f"✨ Досвід: {exp}/{exp_to_next} ({exp_percent:.1f}%)\n"
        f"👹 Вбито мобів: {kills}\n"
        f"🎯 Кількість полювань: {daily_hunts}\n\n"

        f"— Гаманець —\n"
        f"💰 Золото: {gold:.2f}"
    )

    return text


def build_stats_text(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return "❗ Персонажа не знайдено."

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    pdef = get_physical_defense(user_id)
    mdef = get_magic_defense(user_id)

    physical_crit = get_physical_crit_chance_display(user_id)
    magical_crit = get_magical_crit_chance_display(user_id)
    dodge = get_base_dodge_chance_display(user_id)
    enemy_crit = get_enemy_crit_chance_against_player(user_id)

    profile_summary = get_character_profile_summary(user_id)
    character_name = profile_summary.get("name") or "Без імені"
    class_name = profile_summary.get("class_name") or "Не обрано"

    physical_attack = total_str
    magical_attack = total_int

    text = (
        f"📊 Параметри персонажа\n\n"
        f"📝 Ім’я: {character_name}\n"
        f"🧭 Клас: {class_name}\n"
        f"{format_resource_line(profile_summary)}\n"

        f"— Атака —\n"
        f"⚔️ Фізична атака: {physical_attack}\n"
        f"🔮 Магічна атака: {magical_attack}\n\n"

        f"— Захист —\n"
        f"🛡 Фіз. захист: {pdef}\n"
        f"🔮 Маг. захист: {mdef}\n\n"

        f"— Шанси —\n"
        f"🎯 Фіз. крит: {physical_crit:.2f}%\n"
        f"🔮 Маг. крит: {magical_crit:.2f}%\n"
        f"💨 Базовий ухил: {dodge:.2f}%\n"
        f"💥 Крит ворога по тобі: {enemy_crit:.2f}%\n\n"

        f"ℹ️ Ухил у реальному бою залежить від спритності конкретного ворога."
    )

    return text


def build_equipment_text(user_id):
    from db import SLOT_ORDER, EQUIPMENT_SLOTS

    equipped_slots = get_all_equipped_slots(user_id)

    text = (
        f"🧰 Екіпірування персонажа\n\n"
        f"Стан активних слотів:\n\n"
    )

    for slot_key in SLOT_ORDER:
        slot_label = EQUIPMENT_SLOTS.get(slot_key, slot_key)
        inventory_id = equipped_slots.get(slot_key)

        if not inventory_id:
            text += f"{slot_label}: порожньо\n\n"
            continue

        item = get_item_by_inventory_id_full(inventory_id)

        if not item:
            text += f"{slot_label}: помилка предмета\n\n"
            continue

        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            item_slot_key,
            weapon_hands,
            quantity,
            max_stack,
            durability,
            b_str,
            b_dex,
            b_int,
            b_wis,
            b_sta,
            pdef,
            mdef,
            sell_price
        ) = item

        text += f"{slot_label}: {name}\n"

        if durability is not None:
            broken_text = " ⚠️ [ЗЛАМАНО]" if durability <= 0 else ""
            text += f"🧱 Міцність: {durability}/100{broken_text}\n"

        if item_slot_key == "main_hand":
            if weapon_hands == 2:
                text += "👐 Тип зброї: дворучна\n"
            else:
                text += "✋ Тип зброї: одноручна\n"

            weapon_damage_text = get_inventory_weapon_damage_display(inv_id)

            if weapon_damage_text:
                text += f"{weapon_damage_text}\n"

        bonuses = format_equipment_bonuses(
            b_str,
            b_dex,
            b_int,
            b_wis,
            b_sta,
            pdef,
            mdef
        )

        if bonuses:
            text += "📊 Бонуси:\n"

            for bonus in bonuses:
                text += f"• {bonus}\n"
        else:
            text += "📊 Бонуси: немає\n"

        text += "\n"

    return text


def build_skills_text(user_id):
    class_key = get_character_class(user_id)
    skills = CLASS_SKILLS_V1.get(class_key, [])
    profile_summary = get_character_profile_summary(user_id)
    class_name = profile_summary.get("class_name", "Не обрано")
    character_name = profile_summary.get("name") or "Без імені"

    text = f"✨ Навички персонажа\n\n"
    text += f"📝 Ім’я: {character_name}\n"
    text += f"🧭 Клас: {class_name}\n\n"

    if not skills:
        text += "Немає доступних навичок"
    else:
        for i, skill in enumerate(skills):
            text += f"{i+1}. {skill['name']}\n"
            text += f"{skill['description']}\n"
            if skill.get("cost"):
                if skill["cost_type"] == "rage":
                    text += f"💥 Вартість: {skill['cost']} Люті\n"
                elif skill["cost_type"] == "combat_energy" or skill["cost_type"] == "combat_energy_combo":
                    text += f"💥 Вартість: {skill['cost']} Енергії\n"
                elif skill["cost_type"] == "mana":
                    text += f"💧 Вартість: {skill['cost']} Мани\n"
            if skill.get("cooldown", 0) > 0:
                text += f"⏳ Перезарядка: {skill['cooldown']} ходів\n"
            text += "\n"

    return text


# ==============================
# HANDLERS
# ==============================

def register_profile_handlers(bot):

    # ==============================
    # PROFILE ROOT
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "👤 Профіль")
    def profile(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            "👤 Розділ персонажа відкрито",
            reply_markup=profile_kb()
        )

        bot.send_message(
            message.chat.id,
            build_character_text(user_id),
            reply_markup=profile_inline_kb(active_tab="character")
        )

    # ==============================
    # TEXT BUTTONS
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "📊 Параметри")
    def stats(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_stats_text(user_id),
            reply_markup=profile_inline_kb(active_tab="stats")
        )

    @bot.message_handler(func=lambda m: m.text == "🧰 Екіпірування")
    def equipment(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_equipment_text(user_id),
            reply_markup=profile_inline_kb(active_tab="equipment")
        )

    @bot.message_handler(func=lambda m: m.text == "✨ Навички")
    def skills(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_skills_text(user_id),
            reply_markup=profile_inline_kb(active_tab="skills")
        )

    # ==============================
    # INLINE CALLBACKS
    # ==============================

    @bot.callback_query_handler(func=lambda call: call.data == "profile_character")
    def profile_character_callback(call):
        user_id = call.from_user.id

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            build_character_text(user_id),
            reply_markup=profile_inline_kb(active_tab="character")
        )

    @bot.callback_query_handler(func=lambda call: call.data == "profile_stats")
    def profile_stats_callback(call):
        user_id = call.from_user.id

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            build_stats_text(user_id),
            reply_markup=profile_inline_kb(active_tab="stats")
        )

    @bot.callback_query_handler(func=lambda call: call.data == "profile_equipment")
    def profile_equipment_callback(call):
        user_id = call.from_user.id

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            build_equipment_text(user_id),
            reply_markup=profile_inline_kb(active_tab="equipment")
        )

    @bot.callback_query_handler(func=lambda call: call.data == "profile_skills")
    def profile_skills_callback(call):
        user_id = call.from_user.id

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            build_skills_text(user_id),
            reply_markup=profile_inline_kb(active_tab="skills")
        )

    # ==============================
    # BACK
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🔙 Назад")
    def back_from_profile(message):
        bot.send_message(
            message.chat.id,
            "🏕️ Повернення до табору.",
            reply_markup=main_kb()
        )