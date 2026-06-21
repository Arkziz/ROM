from data.locations import LOCATIONS
from db import get_current_location, get_player_stats
from keyboards import map_kb


def register_map_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🗺️ Мапа")
    def show_map(message):
        user_id = message.from_user.id

        location_id = get_current_location(user_id)
        location = LOCATIONS.get(location_id, LOCATIONS["start_path"])

        stats = get_player_stats(user_id)

        if stats:
            _, _, _, _, _, lvl = stats
        else:
            lvl = 1

        mobs_text = "\n".join([f"• {mob}" for mob in location["mobs"]])

        text = (
            f"🗺️ Мапа світу\n\n"
            f"📍 Ти зараз знаходишся:\n"
            f"{location['name']}\n\n"

            f"🏷 Рівні зони: {location['level_range']}\n"
            f"📖 {location['description']}\n\n"

            f"👤 Твій рівень: {lvl}\n\n"

            f"👹 Моби цієї зони:\n"
            f"{mobs_text}\n\n"

            f"👑 Бос зони:\n"
            f"{location['boss']}\n\n"

            f"Доступні напрямки:\n"
            f"🏙️ Місто — повернутися до торговця та сервісів\n"
            f"🔒 Інші локації відкриються пізніше"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=map_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Мапа")
    def back_to_map(message):
        show_map(message)