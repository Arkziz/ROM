from keyboards import blacksmith_kb
from handlers.city import build_blacksmith_repair_text


REPAIR_BUTTON_TEXTS = {
    "🛠️ Ремонт",
    "🛠 Ремонт",
    "🔧 Ремонт",
    "Ремонт",
}


def _normalize_text_kb_result(result, fallback_kb=None):
    if isinstance(result, tuple):
        if len(result) >= 2:
            return result[0], result[1]
        if len(result) == 1:
            return result[0], fallback_kb

    return result, fallback_kb


def register_blacksmith_repair_hotfix_handlers(bot):
    """
    Hotfix для кнопки 🛠️ Ремонт.

    Реєструється ДО city handlers, щоб кнопку не перехоплювали інші широкі обробники.
    """

    @bot.message_handler(func=lambda message: bool(message.text) and message.text.strip() in REPAIR_BUTTON_TEXTS)
    def blacksmith_repair_hotfix(message):
        result = build_blacksmith_repair_text(message.from_user.id)
        text, kb = _normalize_text_kb_result(result, blacksmith_kb())

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )
