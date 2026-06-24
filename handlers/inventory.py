from telebot import types

from db import (
    EQUIPMENT_SLOTS,
    get_inventory_detailed,
    get_equipped_inventory_ids,
    get_item_by_inventory_id,
    get_item_by_inventory_id_full,
    equip_inventory_item,
    unequip_inventory_item,
    get_inventory_used_slots,
    get_bag_capacity,
    is_inventory_item_equipped,
    find_equipped_slot_by_inventory_id
)

from keyboards import profile_kb
from systems.potion_system import use_potion_from_inventory


ITEMS_PER_PAGE = 10


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


def get_slot_label(slot_key):
    if not slot_key:
        return "Немає слота"

    return EQUIPMENT_SLOTS.get(slot_key, slot_key)


def build_inventory_list(user_id, page=0):
    items = get_inventory_detailed(user_id)

    used_slots = get_inventory_used_slots(user_id)
    capacity = get_bag_capacity(user_id)
    free_slots = max(0, capacity - used_slots)

    if not items:
        text = (
            f"🎒 Інвентар порожній\n\n"
            f"🎒 Сумка: {used_slots}/{capacity}\n"
            f"✅ Вільно: {free_slots}"
        )
        return text, None

    total_items = len(items)
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    if page < 0:
        page = 0
    if page >= total_pages:
        page = total_pages - 1

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_items = items[start:end]

    kb = types.InlineKeyboardMarkup()

    text = (
        f"🎒 Інвентар\n\n"
        f"🎒 Сумка: {used_slots}/{capacity}\n"
        f"✅ Вільно: {free_slots}\n"
        f"📄 Сторінка: {page + 1}/{total_pages}\n\n"
        f"Оберіть предмет:"
    )

    for item in page_items:
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

        equipped = is_inventory_item_equipped(user_id, inv_id)

        label = name

        if max_stack and max_stack > 1:
            label += f" x{quantity}"

        if equipped:
            slot_key = find_equipped_slot_by_inventory_id(user_id, inv_id)
            slot_label = get_slot_label(slot_key)
            label += f" ✅ {slot_label}"

        kb.add(types.InlineKeyboardButton(
            text=label,
            callback_data=f"item_{inv_id}_{page}"
        ))

    nav_buttons = []

    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"inv_page_{page - 1}"
        ))

    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton(
            text="➡️ Далі",
            callback_data=f"inv_page_{page + 1}"
        ))

    if nav_buttons:
        kb.add(*nav_buttons)

    return text, kb


def build_item_details(user_id, inventory_id, page=0):
    item_full = get_item_by_inventory_id_full(inventory_id)

    if not item_full:
        return "❌ Предмет не знайдено", None

    (
        inv_id,
        item_id,
        name,
        type_,
        rarity,
        category,
        slot_key,
        weapon_hands,
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
    ) = item_full

    equipped = is_inventory_item_equipped(user_id, inv_id)
    equipped_slot_key = find_equipped_slot_by_inventory_id(user_id, inv_id)

    bonuses = format_item_bonuses(
        b_str,
        b_dex,
        b_int,
        b_wis,
        b_sta,
        pdef,
        mdef
    )

    kb = types.InlineKeyboardMarkup()

    text = f"📦 Предмет\n\n{name}\n\n"

    # ==============================
    # TRASH
    # ==============================

    if category == "trash":
        total_price = (quantity or 1) * (sell_price or 0)

        text += (
            f"🔘 Тип: сірий лут\n"
            f"📦 Кількість: {quantity}/{max_stack}\n"
            f"🪙 Ціна продажу: {sell_price:.2f} золота за шт.\n"
            f"🪙 Усього: {total_price:.2f} золота\n\n"
            f"ℹ️ Цей предмет можна продати торговцю в місті."
        )

    # ==============================
    # POTION
    # ==============================

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
            callback_data=f"use_potion_{inv_id}_{page}"
        ))

    # ==============================
    # EQUIPMENT
    # ==============================

    elif category == "equipment":
        slot_label = get_slot_label(slot_key)

        text += (
            f"🧰 Тип: спорядження\n"
            f"🎯 Слот: {slot_label}\n"
        )

        if slot_key == "main_hand":
            if weapon_hands == 2:
                text += "👐 Тип зброї: дворучна\n"
                text += "⚠️ Дворучна зброя блокує другу руку.\n"
            else:
                text += "✋ Тип зброї: одноручна\n"

        if durability is not None:
            broken_text = " ⚠️ [ЗЛАМАНО]" if durability <= 0 else ""
            text += f"🧱 Міцність: {durability}/100{broken_text}\n"

        if bonuses:
            text += "\n📊 Бонуси:\n"

            for bonus in bonuses:
                text += f"• {bonus}\n"
        else:
            text += "\n📊 Бонуси: немає\n"

        if durability is not None and durability <= 0:
            text += "\n⚠️ Предмет зламаний і не дає бонусів до ремонту.\n"

        if equipped:
            equipped_slot_label = get_slot_label(equipped_slot_key)
            text += f"\n✅ Зараз вдягнено у слот: {equipped_slot_label}"

            kb.add(types.InlineKeyboardButton(
                text="❌ Зняти",
                callback_data=f"unequip_{inv_id}_{page}"
            ))
        else:
            kb.add(types.InlineKeyboardButton(
                text=f"✅ Вдягнути у слот: {slot_label}",
                callback_data=f"equip_{inv_id}_{page}"
            ))

    # ==============================
    # OTHER
    # ==============================

    else:
        text += (
            f"📦 Категорія: {category}\n"
            f"📦 Кількість: {quantity}/{max_stack}\n"
        )

    kb.add(types.InlineKeyboardButton(
        text="⬅️ До інвентаря",
        callback_data=f"inv_page_{page}"
    ))

    return text, kb


# ==============================
# HANDLERS
# ==============================

def register_inventory_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🎒 Інвентар")
    def show_inventory(message):
        user_id = message.from_user.id

        text, kb = build_inventory_list(user_id, page=0)

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb if kb else profile_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("inv_page_"))
    def inventory_page(call):
        user_id = call.from_user.id
        page = int(call.data.split("_")[2])

        text, kb = build_inventory_list(user_id, page=page)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb if kb else profile_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("item_"))
    def show_item_details(call):
        user_id = call.from_user.id

        parts = call.data.split("_")
        inventory_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        text, kb = build_item_details(user_id, inventory_id, page)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
    def handle_equip(call):
        user_id = call.from_user.id

        parts = call.data.split("_")
        inventory_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        result = equip_inventory_item(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result
        )

        text, kb = build_item_details(user_id, inventory_id, page)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("unequip_"))
    def handle_unequip(call):
        user_id = call.from_user.id

        parts = call.data.split("_")
        inventory_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        result = unequip_inventory_item(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result
        )

        text, kb = build_item_details(user_id, inventory_id, page)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("use_potion_"))
    def handle_use_potion(call):
        user_id = call.from_user.id

        parts = call.data.split("_")
        inventory_id = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0

        result = use_potion_from_inventory(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"]
        )

        text, kb = build_inventory_list(user_id, page)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb if kb else profile_kb()
        )