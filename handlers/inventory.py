from telebot import types

from db import (
    get_inventory_detailed,
    get_equipped_inventory_ids,
    get_item_by_inventory_id,
    equip_inventory_item,
    unequip_inventory_item
)

from keyboards import profile_kb
from systems.potion_system import use_potion_from_inventory


# ==============================
# HELPERS
# ==============================

def format_item_bonuses(b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef):
    bonuses = []

    if b_str:
        bonuses.append(f"Сила +{b_str}")
    if b_dex:
        bonuses.append(f"Спритність +{b_dex}")
    if b_int:
        bonuses.append(f"Інтелект +{b_int}")
    if b_wis:
        bonuses.append(f"Мудрість +{b_wis}")
    if b_sta:
        bonuses.append(f"Витривалість +{b_sta}")
    if pdef:
        bonuses.append(f"Фіз. захист +{pdef}")
    if mdef:
        bonuses.append(f"Маг. захист +{mdef}")

    return bonuses


def build_inventory_list(user_id):
    items = get_inventory_detailed(user_id)

    if not items:
        return "🎒 Інвентар порожній", None

    eq_weapon, eq_armor = get_equipped_inventory_ids(user_id)

    kb = types.InlineKeyboardMarkup()

    text = "🎒 Інвентар\n\nОберіть предмет, щоб переглянути деталі:"

    for item in items:
        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            quantity,
            max_stack,
            durability,
            b_str,
            b_dex,
            b_int,
            b_wis,
            b_sta,
            pdef,
            mdef,
            sell_price
        ) = item

        equipped = (
            (type_ == "weapon" and inv_id == eq_weapon) or
            (type_ == "armor" and inv_id == eq_armor)
        )

        label = name

        if max_stack > 1:
            label += f" x{quantity}"

        if equipped:
            label += " ✅"

        kb.add(types.InlineKeyboardButton(
            text=label,
            callback_data=f"item_{inv_id}"
        ))

    return text, kb


def build_item_details(user_id, inventory_id):
    item = get_item_by_inventory_id(inventory_id)

    if not item:
        return "❌ Предмет не знайдено", None

    (
        inv_id,
        item_id,
        name,
        type_,
        rarity,
        category,
        quantity,
        max_stack,
        durability,
        b_str,
        b_dex,
        b_int,
        b_wis,
        b_sta,
        pdef,
        mdef,
        sell_price
    ) = item

    eq_weapon, eq_armor = get_equipped_inventory_ids(user_id)

    equipped = (
        (type_ == "weapon" and inv_id == eq_weapon) or
        (type_ == "armor" and inv_id == eq_armor)
    )

    bonuses = format_item_bonuses(
        b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef
    )

    kb = types.InlineKeyboardMarkup()

    # ==============================
    # TEXT
    # ==============================

    text = f"📦 Предмет\n\n{name}\n\n"

    if category == "trash":
        text += (
            f"🔘 Тип: сірий лут\n"
            f"📦 Кількість: {quantity}/{max_stack}\n"
            f"🪙 Ціна продажу: {sell_price:.2f} золота за шт.\n"
            f"🪙 Усього: {(quantity or 1) * (sell_price or 0):.2f} золота\n\n"
            f"ℹ️ Цей предмет потрібен для продажу торговцю."
        )

    elif category == "potion":
        text += (
            f"🧪 Тип: зілля\n"
            f"📦 Кількість: {quantity}/{max_stack}\n"
            f"🪙 Ціна продажу: {sell_price:.2f} золота за шт.\n\n"
        )

        if type_ == "potion_hp":
            text += "❤️ Ефект: відновлює 50 HP\n"
        elif type_ == "potion_hp_medium":
            text += "❤️ Ефект: відновлює 120 HP\n"
        elif type_ == "potion_mp":
            text += "🔵 Ефект: відновлює 40 MP\n"
        elif type_ == "potion_mp_medium":
            text += "🔵 Ефект: відновлює 100 MP\n"

        text += "\nℹ️ Поза боєм зілля використовується миттєво."

        kb.add(types.InlineKeyboardButton(
            text="🧪 Використати",
            callback_data=f"use_potion_{inv_id}"
        ))

    elif category == "equipment":
        text += "🧰 Тип: спорядження\n"

        if type_ == "weapon":
            text += "⚔️ Слот: зброя\n"
        elif type_ == "armor":
            text += "🛡 Слот: обладунок\n"

        if durability is not None:
            text += f"🧱 Міцність: {durability}/100\n"

        if bonuses:
            text += "\n📊 Бонуси:\n"
            for bonus in bonuses:
                text += f"• {bonus}\n"
        else:
            text += "\n📊 Бонуси: немає\n"

        if equipped:
            text += "\n✅ Зараз вдягнено."
            kb.add(types.InlineKeyboardButton(
                text="❌ Зняти",
                callback_data=f"unequip_{inv_id}"
            ))
        else:
            kb.add(types.InlineKeyboardButton(
                text="✅ Вдягнути",
                callback_data=f"equip_{inv_id}"
            ))

    else:
        text += (
            f"📦 Категорія: {category}\n"
            f"📦 Кількість: {quantity}/{max_stack}\n"
        )

    # ==============================
    # NAVIGATION
    # ==============================

    kb.add(types.InlineKeyboardButton(
        text="⬅️ До інвентаря",
        callback_data="inventory_back"
    ))

    return text, kb


# ==============================
# HANDLERS
# ==============================

def register_inventory_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🎒 Інвентар")
    def show_inventory(message):
        user_id = message.from_user.id

        text, kb = build_inventory_list(user_id)

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb if kb else profile_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "inventory_back")
    def inventory_back(call):
        user_id = call.from_user.id

        text, kb = build_inventory_list(user_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb if kb else profile_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("item_"))
    def show_item_details(call):
        user_id = call.from_user.id
        inventory_id = int(call.data.split("_")[1])

        text, kb = build_item_details(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
    def handle_equip(call):
        user_id = call.from_user.id
        inventory_id = int(call.data.split("_")[1])

        result = equip_inventory_item(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result
        )

        text, kb = build_item_details(user_id, inventory_id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("unequip_"))
    def handle_unequip(call):
        user_id = call.from_user.id
        inventory_id = int(call.data.split("_")[1])

        result = unequip_inventory_item(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result
        )

        text, kb = build_item_details(user_id, inventory_id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("use_potion_"))
    def handle_use_potion(call):
        user_id = call.from_user.id
        inventory_id = int(call.data.split("_")[2])

        result = use_potion_from_inventory(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"]
        )

        text, kb = build_inventory_list(user_id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb if kb else profile_kb()
        )