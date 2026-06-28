import random

from telebot import types

from data.mobs import LOCATION_1_MOBS

from db import (
    get_contract_status,
    create_daily_contract,
    abandon_active_contract
)

from keyboards import city_kb


# ==============================
# HELPERS
# ==============================

def get_available_contract_mobs(player_level):
    """
    Повертає мобів, які реально доступні гравцю для контракту.

    Базове правило:
    - моб має бути відкритий за min_player_level;
    - рівень моба має бути у діапазоні PlayerLevel ± 1.

    Якщо таких немає — fallback:
    - усі моби, які вже доступні за min_player_level.
    """

    available = []

    for mob in LOCATION_1_MOBS:
        mob_level = int(mob.get("level", 1))
        min_player_level = int(mob.get("min_player_level", 1))

        if min_player_level <= player_level and player_level - 1 <= mob_level <= player_level + 1:
            available.append(mob)

    if available:
        return available

    fallback = []

    for mob in LOCATION_1_MOBS:
        min_player_level = int(mob.get("min_player_level", 1))

        if min_player_level <= player_level:
            fallback.append(mob)

    return fallback


def choose_random_contract_mob(player_level):
    available_mobs = get_available_contract_mobs(player_level)

    if not available_mobs:
        return None

    return random.choice(available_mobs)


def build_contracts_text(user_id):
    status = get_contract_status(user_id)

    if not status["exists"]:
        return status["message"], None

    level = status["level"]
    unlocked = status["unlocked"]
    completed_today = status["completed_today"]
    daily_limit = status["daily_limit"]
    active_contract = status["active_contract"]

    text = (
        f"📜 Гільдія Найманців\n\n"
        f"На старій дошці висять свіжі замовлення від мандрівників, "
        f"торговців і варти табору.\n\n"
        f"📆 Сьогодні виконано: {completed_today}/{daily_limit}\n"
    )

    kb = types.InlineKeyboardMarkup()

    if not unlocked:
        text += (
            f"\n🔒 Контракти відкриються з 5 рівня.\n"
            f"👤 Твій рівень: {level}\n\n"
            f"Поки що варто навчитися основам: полюванню, зіллям, "
            f"екіпіруванню та ремонту спорядження."
        )

        return text, kb

    if active_contract:
        text += (
            f"\n📌 Активний контракт:\n"
            f"🎯 Ціль: {active_contract['target_mob_name']}\n"
            f"🏷 Рівень цілі: {active_contract['target_mob_level']}\n"
            f"📈 Прогрес: "
            f"{active_contract['current_kills']}/{active_contract['target_kills']}\n"
            f"✨ Нагорода: {active_contract['reward_exp']} EXP\n\n"
            f"ℹ️ Прогрес зараховується тільки за вбивство саме цієї істоти."
        )

        kb.add(types.InlineKeyboardButton(
            text="❌ Скасувати контракт",
            callback_data="contract_abandon"
        ))

        return text, kb

    if completed_today >= daily_limit:
        text += (
            f"\n✅ Ліміт контрактів на сьогодні виконано.\n"
            f"Повертайся завтра за новими завданнями."
        )

        return text, kb

    text += (
        f"\n✅ Можна взяти новий контракт.\n"
        f"ℹ️ 1 контракт = досвід за 20 мобів твого рівня.\n"
        f"🎯 Ціль буде обрана випадково серед істот, доступних для твого рівня."
    )

    kb.add(types.InlineKeyboardButton(
        text="📜 Взяти контракт",
        callback_data="contract_take"
    ))

    return text, kb


# ==============================
# HANDLERS
# ==============================

def register_contract_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "📜 Контракти")
    def show_contracts(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            "📜 Ти підійшов до дошки контрактів.",
            reply_markup=city_kb()
        )

        text, kb = build_contracts_text(user_id)

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "contract_take")
    def take_contract(call):
        user_id = call.from_user.id

        status = get_contract_status(user_id)

        if not status["exists"]:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                status["message"],
                reply_markup=city_kb()
            )
            return

        if not status["unlocked"]:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                (
                    f"🔒 Контракти відкриються з 5 рівня.\n"
                    f"👤 Твій рівень: {status['level']}"
                ),
                reply_markup=city_kb()
            )
            return

        chosen_mob = choose_random_contract_mob(status["level"])

        if not chosen_mob:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "❌ Не вдалося знайти доступного моба для контракту.",
                reply_markup=city_kb()
            )
            return

        target_mob_name = chosen_mob.get("name", "Невідома істота")
        target_mob_level = int(chosen_mob.get("level", status["level"]))

        result = create_daily_contract(
            user_id=user_id,
            target_mob_name=target_mob_name,
            target_mob_level=target_mob_level
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=city_kb()
        )

        text, kb = build_contracts_text(user_id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "contract_abandon")
    def abandon_contract(call):
        user_id = call.from_user.id

        result = abandon_active_contract(user_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=city_kb()
        )

        text, kb = build_contracts_text(user_id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )