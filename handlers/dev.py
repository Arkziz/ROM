from db import (
    add_item,
    set_player_level_for_test,
    reset_player_level_for_test,
    get_user_progress
)

from keyboards import main_kb


# ==============================
# DEV CONFIG
# ==============================

DEV_MODE = True


def register_dev_handlers(bot):

    # ==============================
    # /give item_id quantity
    # ==============================

    @bot.message_handler(commands=["give"])
    def give_item(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id

        parts = message.text.split()

        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                "❌ Формат: /give item_id [quantity]\nНаприклад: /give 201 5",
                reply_markup=main_kb()
            )
            return

        try:
            item_id = int(parts[1])
            quantity = int(parts[2]) if len(parts) >= 3 else 1
        except Exception:
            bot.send_message(
                message.chat.id,
                "❌ item_id і quantity мають бути числами.",
                reply_markup=main_kb()
            )
            return

        if quantity < 1:
            quantity = 1

        result = add_item(user_id, item_id, quantity)

        if not result.get("success"):
            bot.send_message(
                message.chat.id,
                result.get("message", "❌ Не вдалося видати предмет."),
                reply_markup=main_kb()
            )
            return

        text = (
            f"✅ DEV: предмет видано.\n\n"
            f"📦 {result.get('name', 'Предмет')} x{result.get('added', 0)}\n"
            f"🎒 Сумка: {result.get('used_slots', 0)}/{result.get('capacity', 20)}"
        )

        if result.get("lost", 0) > 0:
            text += f"\n⚠️ Не влізло: x{result.get('lost', 0)}"

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )

    # ==============================
    # /setlevel N
    # /lvl N
    # /level N
    # ==============================

    @bot.message_handler(commands=["setlevel", "lvl", "level"])
    def set_level(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id

        parts = message.text.split()

        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                "❌ Формат: /setlevel 5\nАбо: /lvl 5",
                reply_markup=main_kb()
            )
            return

        target_level = parts[1]

        result = set_player_level_for_test(user_id, target_level)

        bot.send_message(
            message.chat.id,
            result["message"],
            reply_markup=main_kb()
        )

    # ==============================
    # /resetlevel
    # ==============================

    @bot.message_handler(commands=["resetlevel"])
    def reset_level(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id

        result = reset_player_level_for_test(user_id)

        bot.send_message(
            message.chat.id,
            result["message"],
            reply_markup=main_kb()
        )

    # ==============================
    # /progress
    # ==============================

    @bot.message_handler(commands=["progress"])
    def progress(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id

        progress_data = get_user_progress(user_id)

        if not progress_data:
            bot.send_message(
                message.chat.id,
                "❌ Персонажа не знайдено. Натисни /start.",
                reply_markup=main_kb()
            )
            return

        level = progress_data["level"]
        exp = progress_data["exp"]
        exp_to_next = progress_data["exp_to_next"]
        gold = progress_data["gold"]
        kills = progress_data["kills"]

        percent = 0

        if exp_to_next > 0:
            percent = (exp / exp_to_next) * 100

        text = (
            f"📊 DEV Progress\n\n"
            f"🏆 Рівень: {level}\n"
            f"✨ EXP: {exp}/{exp_to_next} ({percent:.2f}%)\n"
            f"🪙 Золото: {gold:.2f}\n"
            f"👹 Вбито мобів: {kills}"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )

    # ==============================
    # /myid
    # ==============================

    @bot.message_handler(commands=["myid"])
    def my_id(message):
        if not DEV_MODE:
            return

        bot.send_message(
            message.chat.id,
            f"🆔 Твій Telegram user_id:\n{message.from_user.id}",
            reply_markup=main_kb()
        )