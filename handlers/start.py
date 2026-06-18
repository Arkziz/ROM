from db import create_user
from keyboards import main_kb


def register_start_handlers(bot):

    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id

        create_user(user_id)

        bot.send_message(
            message.chat.id,
            "👤 Персонаж створено ✅",
            reply_markup=main_kb()
        )