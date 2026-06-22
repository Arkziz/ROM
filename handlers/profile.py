from telebot import types

from db import (
    get_player_stats,
    get_attack,
    get_magic_attack,
    get_physical_defense,
    get_magic_defense,
    get_max_hp,
    get_current_hp,
    get_user_progress
)

from keyboards import profile_kb, main_kb
from utils import hp_bar

from systems.combat_system import (
    get_physical_crit_chance,
    get_magical_crit_chance,
    get_dodge_chance
)


def profile_inline_kb():
    kb = types.InlineKeyboardMarkup()

    kb.add(types.InlineKeyboardButton(
        text="📊 Параметри",
        callback_data="profile_params"
    ))

    return kb


def params_inline_kb():
    kb = types.InlineKeyboardMarkup()

    kb.add(types.InlineKeyboardButton(
        text="👤 До профілю",
        callback_data="profile_overview"
    ))

    return kb


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
        f"✨ Досвід: {exp}/{exp_to_next}\n"
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

    # Орієнтовний базовий ухил.
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
        f"🎯 Фіз. крит: {physical_crit}%\n"
        f"🔮 Маг. крит: {magical_crit}%\n"
        f"💨 Базовий ухил: {base_dodge}%\n"
        f"💥 Крит ворога по тобі: {enemy_crit}%\n\n"

        f"ℹ️ Ухил у реальному бою залежить від спритності конкретного ворога."
    )

    return text


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

        # 1) Ставимо нижню клавіатуру профілю
        bot.send_message(
            message.chat.id,
            "👤 Розділ персонажа відкрито",
            reply_markup=profile_kb()
        )

        # 2) Показуємо профіль з inline-кнопкою "Параметри"
        bot.send_message(
            message.chat.id,
            text,
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