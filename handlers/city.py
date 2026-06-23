from telebot import types

from data.locations import LOCATIONS
from db import (
    get_current_location,
    sell_all_trash,
    buy_item_for_gold
)

from keyboards import (
    city_kb,
    trader_kb,
    alchemist_kb,
    main_kb
)

from systems.potion_system import (
    POTIONS,
    ALCHEMIST_SHOP,
    get_potion_description
)


# ==============================
# HELPERS
# ==============================

def build_city_text(user_id):
    location_id = get_current_location(user_id)
    location = LOCATIONS.get(location_id, LOCATIONS["start_path"])

    return (
        f"🏙️ Місто\n\n"
        f"📍 Регіон:\n"
        f"{location['name']}\n\n"
        f"🏕️ Табір мандрівників\n\n"
        f"Тут можна продати лут, купити зілля і підготуватися до наступного полювання.\n\n"
        f"Доступні місця:\n"
        f"• 🛒 Торговець\n"
        f"• 🧪 Алхімік"
    )


def build_alchemist_catalog():
    kb = types.InlineKeyboardMarkup()

    text = (
        f"🧪 Алхімік\n\n"
        f"Алхімік продає зілля для виживання в бою.\n\n"
        f"Асортимент:\n\n"
    )

    for item_id in ALCHEMIST_SHOP:
        potion = POTIONS[item_id]

        if potion["type"] == "hp":
            effect = f"+{potion['restore']} HP"
        else:
            effect = f"+{potion['restore']} MP"

        text += (
            f"{potion['name']}\n"
            f"Ефект: {effect}\n"
            f"Ціна: {potion['buy_price']:.2f} золота\n"
            f"Стак: {potion['max_stack']}\n\n"
        )

        kb.add(types.InlineKeyboardButton(
            text=f"Купити: {potion['name']} — {potion['buy_price']:.2f} 🪙",
            callback_data=f"buy_potion_{item_id}"
        ))

    text += (
        f"⚠️ Мана ще не реалізована, тому сині зілля можна купити на майбутнє, "
        f"але використати поки не можна."
    )

    return text, kb


# ==============================
# HANDLERS
# ==============================

def register_city_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🏙️ Місто")
    def show_city(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_city_text(user_id),
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

    @bot.message_handler(func=lambda m: m.text == "🧪 Алхімік")
    def show_alchemist(message):
        # Окремим повідомленням ставимо нижню клавіатуру Алхіміка
        bot.send_message(
            message.chat.id,
            "🧪 Ти підійшов до Алхіміка.",
            reply_markup=alchemist_kb()
        )

        text, kb = build_alchemist_catalog()

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy_potion_"))
    def buy_potion(call):
        user_id = call.from_user.id
        item_id = int(call.data.split("_")[2])

        potion = POTIONS.get(item_id)

        if not potion:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "❌ Такого зілля немає в магазині.",
                reply_markup=alchemist_kb()
            )
            return

        result = buy_item_for_gold(
            user_id=user_id,
            item_id=item_id,
            price=potion["buy_price"],
            quantity=1
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=alchemist_kb()
        )

        # Після покупки знову показуємо каталог
        text, kb = build_alchemist_catalog()

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Місто")
    def back_to_city(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_city_text(user_id),
            reply_markup=city_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Назад")
    def back_to_main(message):
        bot.send_message(
            message.chat.id,
            "🔙 Повернення в головне меню",
            reply_markup=main_kb()
        )