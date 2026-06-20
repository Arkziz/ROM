from data.locations import LOCATIONS
from db import get_current_location
from keyboards import main_kb


def register_map_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🗺️ Мапа")
    def show_map(message):
        user_id = message.from_user.id

        location_id = get_current_location(user_id)
        location = LOCATIONS.get(location_id, LOCATIONS["start_path"])

        mobs_text = "\n".join([f"• {mob}" for mob in location["mobs"]])

        text = (
            f"🗺️ Мапа світу\n\n"
            f"📍 Поточна зона:\n"
            f"{location['name']}\n\n"
            f"🏷 Рівні: {location['level_range']}\n"
            f"📖 {location['description']}\n\n"
            f"👹 Моби цієї зони:\n"
            f"{mobs_text}\n\n"
            f"👑 Бос зони:\n"
            f"{location['boss']}\n\n"
            f"🔒 Інші мапи відкриються пізніше."
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )