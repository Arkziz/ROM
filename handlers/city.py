from telebot import types

from data.locations import LOCATIONS
from data.mobs import LOCATION_1_MOBS

from db import (
    get_current_location,
    get_player_stats,
    get_current_hp,
    get_max_hp,
    get_inventory_used_slots,
    get_bag_capacity,
    sell_all_trash,
    buy_item_for_gold,
    get_equipped_items_for_repair,
    get_total_repair_cost,
    repair_all_equipped,
    repair_equipped_item,
    get_wallet,
    get_user_energy
)

from keyboards import (
    city_kb,
    trader_kb,
    alchemist_kb,
    blacksmith_kb,
    main_kb
)

from systems.potion_system import (
    POTIONS,
    ALCHEMIST_SHOP
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
        f"Тут можна продати лут, купити зілля, відремонтувати спорядження "
        f"і підготуватися до наступного полювання.\n\n"
        f"Доступні місця:\n"
        f"• 🛒 Торговець\n"
        f"• 🧪 Алхімік\n"
        f"• ⚒️ Коваль"
    )


def get_nearby_mobs_for_level(player_level):
    available = []

    for mob in LOCATION_1_MOBS:
        mob_level = mob.get("level", 1)
        min_player_level = mob.get("min_player_level", 1)

        if min_player_level <= player_level and player_level - 1 <= mob_level <= player_level + 1:
            available.append(mob)

    if not available:
        for mob in LOCATION_1_MOBS:
            if mob.get("min_player_level", 1) <= player_level:
                available.append(mob)

    return available[:5]


def build_main_menu_text(user_id):
    location_id = get_current_location(user_id)
    location = LOCATIONS.get(location_id, LOCATIONS["start_path"])

    stats = get_player_stats(user_id)

    if stats:
        _, _, _, _, _, lvl = stats
    else:
        lvl = 1

    current_hp = get_current_hp(user_id)
    max_hp = get_max_hp(user_id)
    energy_data = get_user_energy(user_id)
    energy = energy_data["energy"]
    max_energy = energy_data["max_energy"]

    used_slots = get_inventory_used_slots(user_id)
    capacity = get_bag_capacity(user_id)

    nearby_mobs = get_nearby_mobs_for_level(lvl)

    mobs_text = ""

    if nearby_mobs:
        for mob in nearby_mobs:
            mobs_text += f"• {mob['name']} — рівень {mob['level']}\n"
    else:
        mobs_text = "• Навколо поки тихо...\n"

    text = (
        f"🏕️ Табір мандрівників\n\n"
        f"📍 Поточна зона:\n"
        f"{location['name']}\n\n"
        f"📖 {location['description']}\n\n"

        f"Під ногами волога земля, поруч потріскує багаття, "
        f"а за межами табору вже чути рух диких звірів. "
        f"Тут шукачі пригод готуються до наступного полювання.\n\n"

        f"👤 Твій рівень: {lvl}\n"
        f"❤️ Здоров’я: {current_hp}/{max_hp}\n"
        f"🔋 Енергія: {energy}/{max_energy}\n"
        f"🎒 Сумка: {used_slots}/{capacity}\n\n"

        f"👀 Поблизу твого рівня можна зустріти:\n"
        f"{mobs_text}\n"

        f"Доступні дії:\n"
        f"🔎 Полювання — вийти за межі табору\n"
        f"🗺️ Мапа — переглянути напрямки та місто\n"
        f"👤 Профіль — персонаж, інвентар і спорядження"
    )

    return text


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


def build_blacksmith_text(user_id):
    equipped_items = get_equipped_items_for_repair(user_id)
    total_cost = get_total_repair_cost(user_id)
    gold = get_wallet(user_id)

    text = (
        f"⚒️ КОВАЛЬ: РЕМОНТ ТА КУЗНЯ\n\n"
        f"📦 Стан твого спорядження:\n\n"
    )

    kb = types.InlineKeyboardMarkup()

    damaged_count = 0

    for item in equipped_items:
        slot = item["slot"]
        name = item["name"]
        durability = item["durability"]
        repair_cost = item["repair_cost"]
        is_broken = item["is_broken"]
        inventory_id = item["inventory_id"]

        if inventory_id is None:
            text += f"{slot}: порожньо\n\n"
            continue

        broken_text = " ⚠️ [ЗЛАМАНО]" if is_broken else ""

        text += (
            f"{slot}: {name}\n"
            f"🛠️ Міцність: {durability}/100{broken_text}\n"
            f"💰 Ремонт: {repair_cost:.2f} 🪙\n\n"
        )

        if repair_cost > 0:
            damaged_count += 1

            kb.add(types.InlineKeyboardButton(
                text=f"🛠️ Ремонт: {name} — {repair_cost:.2f} 🪙",
                callback_data=f"repair_one_{inventory_id}"
            ))

    text += (
        f"💳 Разом за повний ремонт: {total_cost:.2f} 🪙\n"
        f"💰 Твій баланс: {gold:.2f} 🪙\n\n"
    )

    if damaged_count <= 0:
        text += "✅ Усе спорядження вже в ідеальному стані."
    elif gold < total_cost:
        text += (
            "❌ Недостатньо золота для повного ремонту.\n"
            "ℹ️ Можеш відремонтувати окрему річ, якщо вистачає золота."
        )
    else:
        text += "👇 Можна полагодити все або окрему річ."

    if total_cost > 0:
        kb.add(types.InlineKeyboardButton(
            text=f"🛠️ Полагодити все за {total_cost:.2f} 🪙",
            callback_data="repair_all_equipped"
        ))

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

        text, kb = build_alchemist_catalog()

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.message_handler(func=lambda m: m.text == "⚒️ Коваль")
    def show_blacksmith(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            "⚒️ Ти підійшов до Коваля.",
            reply_markup=blacksmith_kb()
        )

        text, kb = build_blacksmith_text(user_id)

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "repair_all_equipped")
    def repair_all(call):
        user_id = call.from_user.id

        result = repair_all_equipped(user_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=blacksmith_kb()
        )

        text, kb = build_blacksmith_text(user_id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("repair_one_"))
    def repair_one(call):
        user_id = call.from_user.id
        inventory_id = int(call.data.split("_")[2])

        result = repair_equipped_item(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=blacksmith_kb()
        )

        text, kb = build_blacksmith_text(user_id)

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

    @bot.message_handler(func=lambda m: m.text == "👀 Роззирнутися")
    def look_around(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_main_menu_text(user_id),
            reply_markup=main_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Назад")
    def back_to_main(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_main_menu_text(user_id),
            reply_markup=main_kb()
        )