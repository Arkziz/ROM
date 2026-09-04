from telebot import types

from db import (
    get_daily_quest_status,
    claim_daily_quest_reward,
    reset_daily_quest_if_needed
)

from keyboards import townhall_kb


# ==============================
# HELPERS
# ==============================

def build_daily_quest_text(user_id):
    status = get_daily_quest_status(user_id)

    if not status["exists"]:
        return status["message"], None

    progress = status["progress"]
    target_count = status["target_count"]
    completed = status["completed"]
    reward_claimed = status["reward_claimed"]

    text = (
        "📆 Щоденне завдання\n\n"
        "Місцеві жителі потребують допомоги у боротьбі з монстрами.\n\n"
        "🎯 Ціль:\n"
        f"Вбити {target_count} монстрів\n\n"
        "📈 Прогрес:\n"
        f"{progress}/{target_count}\n\n"
        "🎁 Нагорода:\n"
        "🔴 Мале зілля здоров’я ×3\n"
        "🪙 Жетон Фіріуса ×5\n"
        "ℹ️ Жетони накопичуються та не зникають наступного дня.\n"
    )

    kb = types.InlineKeyboardMarkup()

    if reward_claimed:
        text += "\n✅ Нагороду за сьогодні вже отримано."
        return text, kb

    if completed:
        text += "\n✅ Завдання виконано. Можна забрати нагороду."

        kb.add(types.InlineKeyboardButton(
            text="🎁 Отримати нагороду",
            callback_data="daily_claim_reward"
        ))

        return text, kb

    text += "\nℹ️ Прогрес зараховується за перемогу над будь-яким монстром."

    return text, kb


# ==============================
# HANDLERS
# ==============================

def register_daily_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "📆 Щоденне завдання")
    def show_daily_quest(message):
        user_id = message.from_user.id

        reset_daily_quest_if_needed(user_id)
        text, kb = build_daily_quest_text(user_id)

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )

        bot.send_message(
            message.chat.id,
            "🏛️ Ви знаходитесь у Ратуші.",
            reply_markup=townhall_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "daily_claim_reward")
    def claim_daily_reward(call):
        user_id = call.from_user.id

        result = claim_daily_quest_reward(user_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=townhall_kb()
        )

        text, kb = build_daily_quest_text(user_id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )