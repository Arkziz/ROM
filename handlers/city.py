from data.locations import LOCATIONS
from db import get_current_location, sell_all_trash
from keyboards import city_kb, trader_kb, main_kb


def register_city_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🏙️ Місто")
    def show_city(message):
        user_id = message.from_user.id

        location_id = get_current_location(user_id)
        location = LOCATIONS.get(location_id, LOCATIONS["start_path"])

        text = (
            f"🏙️ Місто\n\n"
            f"📍 Регіон:\n"
            f"{location['name']}\n\n"
            f"🏕️ Табір мандрівників\n\n"
            f"Тут можна відпочити, продати лут і підготуватися до наступного полювання.\n\n"
            f"Доступні місця:\n"
            f"• 🛒 Торговець"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=city_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🛒 Торговець")
    def show_trader(message):
        text = (
            f"🛒 Торговець\n\n"
            f"Торговець скуповує сірий лут, здобутий у бою.\n\n"
            f"Доступні дії:\n"
            f"• 🪙 Продати весь хлам"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=trader_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🪙 Продати весь хлам")
    def sell_trash(message):
        user_id = message.from_user.id

        result = sell_all_trash(user_id)

        if result["sold_items_count"] == 0:
            bot.send_message(
                message.chat.id,
                "🪙 У тебе немає сірого луту для продажу.",
                reply_markup=trader_kb()
            )
            return

        text = "🪙 Продаж сірого луту\n\n"

        for line in result["details"]:
            text += f"• {line}\n"

        text += (
            f"\n✅ Отримано золота: {result['gold_earned']:.2f}\n"
            f"🎒 Звільнено слотів: {result['freed_slots']}"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=trader_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Місто")
    def back_to_city(message):
        show_city(message)

    @bot.message_handler(func=lambda m: m.text == "🔙 Назад")
    def back_to_main(message):
        bot.send_message(
            message.chat.id,
            "🔙 Повернення в головне меню",
            reply_markup=main_kb()
        )