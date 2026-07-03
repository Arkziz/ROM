from data.locations import (
    LOCATIONS,
    LOCATION_ORDER,
    get_location,
    is_location_unlocked
)

from data.mobs import get_mobs_for_location

from db import (
    get_current_location,
    set_current_location,
    get_player_stats
)

from keyboards import map_kb, main_kb


# ==============================
# HELPERS
# ==============================

def get_player_level_from_stats(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 1

    _, _, _, _, _, level = stats
    return level or 1


def build_world_map_text(user_id):
    player_level = get_player_level_from_stats(user_id)
    current_location_id = get_current_location(user_id)
    current_location = get_location(current_location_id)

    text = (
        "🗺️ Мапа світу\n\n"
        f"📍 Ти зараз знаходишся:\n"
        f"{current_location['name']}\n\n"
        f"👤 Твій рівень: {player_level}\n\n"
        "Доступні локації:\n"
    )

    for location_id in LOCATION_ORDER:
        location = LOCATIONS[location_id]

        unlocked = is_location_unlocked(location_id, player_level)
        current_marker = " ✅" if location_id == current_location_id else ""

        if unlocked:
            text += (
                f"\n• {location['name']} — рівні "
                f"{location['level_min']}–{location['level_max']}{current_marker}\n"
            )
        else:
            text += (
                f"\n• 🔒 {location['name']} — відкриється з "
                f"{location['unlock_level']} рівня\n"
            )

    text += (
        "\n🏙️ Місто — повернутися до торговця та сервісів\n"
        "🔙 Назад — повернутися до табору"
    )

    return text


def build_location_info_text(location_id, player_level):
    location = get_location(location_id)
    mobs = get_mobs_for_location(location_id)

    text = (
        f"{location['name']}\n\n"
        f"🏷 Рівні зони: {location['level_min']}–{location['level_max']}\n\n"
        f"📖 {location['description']}\n\n"
        f"👹 Моби цієї зони:\n"
    )

    for mob in mobs:
        attack_icon = "⚔️" if mob.get("attack_type") == "physical" else "🔮"

        text += (
            f"• {attack_icon} {mob['name']} — "
            f"рівень {mob['level']}\n"
        )

    text += (
        f"\n👑 Бос зони:\n"
        f"{location.get('boss', 'Невідомо')}\n"
    )

    if player_level < location["unlock_level"]:
        text += (
            f"\n🔒 Локація відкриється з "
            f"{location['unlock_level']} рівня."
        )

    return text


# ==============================
# HANDLERS
# ==============================

def register_map_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🗺️ Мапа")
    def show_map(message):
        user_id = message.from_user.id

        text = build_world_map_text(user_id)

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=map_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Мапа")
    def show_map_from_city(message):
        user_id = message.from_user.id

        text = build_world_map_text(user_id)

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=map_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🌿 Початок Шляху")
    def travel_start_path(message):
        user_id = message.from_user.id
        player_level = get_player_level_from_stats(user_id)
        location_id = "start_path"

        if not is_location_unlocked(location_id, player_level):
            location = get_location(location_id)

            bot.send_message(
                message.chat.id,
                (
                    f"🔒 {location['name']} недоступна.\n"
                    f"Потрібний рівень: {location['unlock_level']}"
                ),
                reply_markup=map_kb()
            )
            return

        set_current_location(user_id, location_id)

        bot.send_message(
            message.chat.id,
            build_location_info_text(location_id, player_level),
            reply_markup=main_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🌲 Темний Бір")
    def travel_dark_forest(message):
        user_id = message.from_user.id
        player_level = get_player_level_from_stats(user_id)
        location_id = "dark_forest"

        if not is_location_unlocked(location_id, player_level):
            location = get_location(location_id)

            bot.send_message(
                message.chat.id,
                (
                    f"🔒 {location['name']} недоступна.\n\n"
                    f"Потрібний рівень: {location['unlock_level']}\n"
                    f"👤 Твій рівень: {player_level}"
                ),
                reply_markup=map_kb()
            )
            return

        set_current_location(user_id, location_id)

        bot.send_message(
            message.chat.id,
            build_location_info_text(location_id, player_level),
            reply_markup=main_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Назад")
    def back_to_main_from_map(message):
        bot.send_message(
            message.chat.id,
            "🏕️ Ти повернувся до табору.",
            reply_markup=main_kb()
        )