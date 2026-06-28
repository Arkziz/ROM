from telebot import types

from db import (
    get_contract_status,
    create_daily_contract,
    abandon_active_contract
)

from keyboards import city_kb


# ==============================
# HELPERS
# ==============================

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
        f"Тут можна брати щоденні контракти на знищення небезпечних істот.\n\n"
        f"📆 Сьогодні виконано: {completed_today}/{daily_limit}\n"
    )

    kb = types.InlineKeyboardMarkup()

    if not unlocked:
        text += (
            f"\n🔒 Контракти відкриються з 5 рівня.\n"
            f"👤 Твій рівень: {level}"
        )

        return text, kb

    if active_contract:
        text += (
            f"\n📌 Активний контракт:\n"
            f"🎯 Вбити мобів рівня "
            f"{active_contract['target_min_level']}–{active_contract['target_max_level']}\n"
            f"📈 Прогрес: {active_contract['current_kills']}/{active_contract['target_kills']}\n"
            f"✨ Нагорода: {active_contract['reward_exp']} EXP\n"
        )

        kb.add(types.InlineKeyboardButton(
            text="❌ Скасувати контракт",
            callback_data="contract_abandon"
        ))

        return text, kb

    if completed_today >= daily_limit:
        text += "\n✅ Ліміт контрактів на сьогодні виконано."
        return text, kb

    text += (
        f"\n✅ Можна взяти новий контракт.\n"
        f"ℹ️ 1 контракт = досвід за 20 мобів твого рівня."
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

        result = create_daily_contract(user_id)

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