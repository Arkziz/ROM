from telebot import types

from db import (
    EQUIPMENT_SLOTS,
    SLOT_ORDER,
    get_player_stats,
    get_attack,
    get_magic_attack,
    get_physical_defense,
    get_magic_defense,
    get_max_hp,
    get_current_hp,
    get_user_progress,
    get_all_equipped_items
)

from keyboards import profile_kb, main_kb
from utils import hp_bar

from systems.combat_system import (
    get_physical_crit_chance,
    get_magical_crit_chance,
    get_dodge_chance
)


# ==============================
# INLINE KEYBOARDS
# ==============================

def profile_inline_kb():
    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            text="📊 Параметри",
            callback_data="profile_params"
        ),
        types.InlineKeyboardButton(
            text="🧰 Екіпірування",
            callback_data="profile_equipment"
        )
    )

    return kb


def params_inline_kb():
    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            text="👤 До профілю",
            callback_data="profile_overview"
        ),
        types.InlineKeyboardButton(
            text="🧰 Екіпірування",
            callback_data="profile_equipment"
        )
    )

    return kb


def equipment_inline_kb():
    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            text="👤 До профілю",
            callback_data="profile_overview"
        ),
        types.InlineKeyboardButton(
            text="📊 Параметри",
            callback_data="profile_params"
        )
    )

    return kb


# ==============================
# FORMAT HELPERS
# ==============================

def format_item_bonuses(b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef):
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
# TEXT BUILDERS
# ==============================

def build_profile_text(user_id):
    stats = get_player_stats(user_id)
    progress = get_user_progress(user_id)

    if not stats or not progress:
        return None

    str_, dex_, int_, wis_, sta_, lvl = stats

    current_hp = get_current_hp(user_id)
    max_hp = get_max_hp(user_id)

    exp = progress["exp"]
    exp_to_next = progress["exp_to_next"]
    gold = progress["gold"]
    kills = progress["kills"]

    exp_percent = 0

    if exp_to_next > 0:
        exp_percent = (exp / exp_to_next) * 100

    text = (
        f"👤 Персонаж\n\n"
        f"🏆 Рівень: {lvl}\n\n"

        f"❤️ Здоров’я: {current_hp}/{max_hp}\n"
        f"{hp_bar(current_hp, max_hp)}\n\n"

        f"— Характеристики —\n"
        f"💪 Сила: {str_}\n"
        f"🎯 Спритність: {dex_}\n"
        f"🔮 Інтелект: {int_}\n"
        f"🦉 Мудрість: {wis_}\n"
        f"🛡 Витривалість: {sta_}\n\n"

        f"— Прогрес —\n"
        f"✨ Досвід: {exp}/{exp_to_next} ({exp_percent:.1f}%)\n"
        f"👹 Вбито мобів: {kills}\n\n"

        f"— Гаманець —\n"
        f"🪙 Золото: {gold:.2f}"
    )

    return text


def build_params_text(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return None

    str_, dex_, int_, wis_, sta_, lvl = stats

    physical_attack = get_attack(user_id)
    magical_attack = get_magic_attack(user_id)

    pdef = get_physical_defense(user_id)
    mdef = get_magic_defense(user_id)

    physical_crit = get_physical_crit_chance(dex_, lvl)
    magical_crit = get_magical_crit_chance(wis_, lvl)

    # Базовий орієнтир.
    # У реальному бою ухил залежить від DEX конкретного ворога.
    base_dodge = get_dodge_chance(
        player_dex=dex_,
        mob_dex=dex_,
        level=lvl
    )

    enemy_crit = max(0, 10 - (sta_ // 25))

    text = (
        f"📊 Параметри персонажа\n\n"

        f"— Атака —\n"
        f"⚔️ Фізична атака: {physical_attack}\n"
        f"🔮 Магічна атака: {magical_attack}\n\n"

        f"— Захист —\n"
        f"🛡 Фіз. захист: {pdef}\n"
        f"🔮 Маг. захист: {mdef}\n\n"

        f"— Шанси —\n"
        f"🎯 Фіз. крит: {physical_crit:.2f}%\n"
        f"🔮 Маг. крит: {magical_crit:.2f}%\n"
        f"💨 Базовий ухил: {base_dodge:.2f}%\n"
        f"💥 Крит ворога по тобі: {enemy_crit:.2f}%\n\n"

        f"ℹ️ Ухил у реальному бою залежить від спритності конкретного ворога."
    )

    return text


def build_equipment_text(user_id):
    equipped_items = get_all_equipped_items(user_id)

    main_hand_two_handed = False

    for equipped in equipped_items:
        if equipped["slot_key"] != "main_hand":
            continue

        item = equipped["item"]

        if not item:
            continue

        weapon_hands = item[7]

        if weapon_hands == 2:
            main_hand_two_handed = True

    text = (
        f"🧰 Екіпірування персонажа\n\n"
        f"Стан активних слотів:\n\n"
    )

    for equipped in equipped_items:
        slot_key = equipped["slot_key"]
        slot_name = equipped["slot_name"]
        item = equipped["item"]

        if slot_key == "off_hand" and main_hand_two_handed and not item:
            text += (
                f"{slot_name}: 🔒 Заблоковано\n"
                f"ℹ️ Дворучна зброя у слоті 🗡️ Зброя блокує другу руку.\n\n"
            )
            continue

        if not item:
            text += f"{slot_name}: порожньо\n\n"
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

        if durability is None:
            durability = 100

        broken = durability <= 0
        broken_text = " ⚠️ [ЗЛАМАНО]" if broken else ""

        text += (
            f"{slot_name}: {name}\n"
            f"🧱 Міцність: {durability}/100{broken_text}\n"
        )

        if slot_key == "main_hand":
            if weapon_hands == 2:
                text += "👐 Тип зброї: дворучна\n"
            else:
                text += "✋ Тип зброї: одноручна\n"

        bonuses = format_item_bonuses(
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

        if broken:
            text += "⚠️ Предмет зламаний і не дає бонусів до ремонту.\n"

        text += "\n"

    return text


# ==============================
# HANDLERS
# ==============================

def register_profile_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "👤 Профіль")
    def profile(message):
        user_id = message.from_user.id

        text = build_profile_text(user_id)

        if not text:
            bot.send_message(
                message.chat.id,
                "❗ Немає персонажа. Натисни /start",
                reply_markup=main_kb()
            )
            return

        bot.send_message(
            message.chat.id,
            "👤 Розділ персонажа відкрито",
            reply_markup=profile_kb()
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=profile_inline_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "profile_overview")
    def profile_overview_callback(call):
        user_id = call.from_user.id

        text = build_profile_text(user_id)

        if not text:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "❗ Немає персонажа. Натисни /start",
                reply_markup=main_kb()
            )
            return

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=profile_inline_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "profile_params")
    def profile_params_callback(call):
        user_id = call.from_user.id

        text = build_params_text(user_id)

        if not text:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "❗ Немає персонажа. Натисни /start",
                reply_markup=main_kb()
            )
            return

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=params_inline_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "profile_equipment")
    def profile_equipment_callback(call):
        user_id = call.from_user.id

        text = build_equipment_text(user_id)

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=equipment_inline_kb()
        )