from telebot import types

from db import (
    EQUIPMENT_SLOTS,
    SLOT_ORDER,
    get_inventory_detailed,
    get_item_by_inventory_id_full,
    equip_inventory_item,
    unequip_inventory_item,
    get_inventory_used_slots,
    get_bag_capacity,
    is_inventory_item_equipped,
    find_equipped_slot_by_inventory_id,
    get_all_equipped_slots
)

from keyboards import profile_kb
from systems.potion_system import use_potion_from_inventory


ITEMS_PER_PAGE = 10


# ==============================
# CATEGORY CONFIG
# ==============================

INVENTORY_CATEGORIES = [
    ("main_hand", "🗡️ Зброя"),
    ("off_hand", "🛡️ Друга рука"),
    ("helmet", "🪖 Голова"),
    ("shoulders", "🦾 Плечі"),
    ("chest", "🦹 Тіло"),
    ("gloves", "🧤 Руки"),
    ("legs", "👖 Ноги"),
    ("boots", "👟 Взуття"),
    ("necklace", "📿 Шия"),
    ("ring", "💍 Кільце"),
    ("trash", "🔘 Сірий лут"),
    ("potion", "🧪 Зілля"),
    ("all", "📦 Переглянути все")
]


# ==============================
# HELPERS
# ==============================

def get_slot_label(slot_key):
    if not slot_key:
        return "Немає слота"

    return EQUIPMENT_SLOTS.get(slot_key, slot_key)


def format_item_bonuses(b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef):
    bonuses = []

    if b_str:
        bonuses.append(f"💪 Сила +{b_str}")
    if b_dex:
        bonuses.append(f"🎯 Спритність +{b_dex}")
    if b_int:
        bonuses.append(f"🔮 Інтелект +{b_int}")
    if b_wis:
        bonuses.append(f"🦉 Мудрість +{b_wis}")
    if b_sta:
        bonuses.append(f"🛡 Витривалість +{b_sta}")
    if pdef:
        bonuses.append(f"🛡 Фіз. захист +{pdef}")
    if mdef:
        bonuses.append(f"🔮 Маг. захист +{mdef}")

    return bonuses


def unpack_full_item(item_full):
    return item_full


def get_inventory_full_items(user_id):
    simple_items = get_inventory_detailed(user_id)
    result = []

    for simple_item in simple_items:
        inv_id = simple_item[0]
        full_item = get_item_by_inventory_id_full(inv_id)

        if full_item:
            result.append(full_item)

    return result


def get_category_items(user_id, category_key):
    items = get_inventory_full_items(user_id)

    if category_key == "all":
        return items

    filtered = []

    for item in items:
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
        ) = item

        if category_key in SLOT_ORDER:
            if category == "equipment" and slot_key == category_key:
                filtered.append(item)

        elif category_key == "trash":
            if category == "trash":
                filtered.append(item)

        elif category_key == "potion":
            if category == "potion":
                filtered.append(item)

    return filtered


def get_category_count(user_id, category_key):
    return len(get_category_items(user_id, category_key))


def build_item_button_label(user_id, item):
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
    ) = item

    label = name

    if max_stack and max_stack > 1:
        label += f" x{quantity}"

    if category == "equipment":
        if durability is not None:
            label += f" [{durability}/100]"

        if is_inventory_item_equipped(user_id, inv_id):
            equipped_slot = find_equipped_slot_by_inventory_id(user_id, inv_id)
            label += f" ✅ {get_slot_label(equipped_slot)}"

    return label


def build_inventory_home(user_id):
    used_slots = get_inventory_used_slots(user_id)
    capacity = get_bag_capacity(user_id)
    free_slots = max(0, capacity - used_slots)

    text = (
        f"🎒 Інвентар\n\n"
        f"🎒 Сумка: {used_slots}/{capacity}\n"
        f"✅ Вільно: {free_slots}\n\n"
        f"Оберіть розділ інвентаря:"
    )

    kb = types.InlineKeyboardMarkup(row_width=2)

    row = []

    for category_key, label in INVENTORY_CATEGORIES:
        count = get_category_count(user_id, category_key)

        # Для "Переглянути все" показуємо загальну кількість слотів
        if category_key == "all":
            button_text = f"{label} ({used_slots})"
        else:
            button_text = f"{label} ({count})"

        row.append(types.InlineKeyboardButton(
            text=button_text,
            callback_data=f"invcat:{category_key}:0"
        ))

        if len(row) == 2:
            kb.add(*row)
            row = []

    if row:
        kb.add(*row)

    return text, kb


def build_category_list(user_id, category_key, page=0):
    items = get_category_items(user_id, category_key)

    used_slots = get_inventory_used_slots(user_id)
    capacity = get_bag_capacity(user_id)
    free_slots = max(0, capacity - used_slots)

    category_label = dict(INVENTORY_CATEGORIES).get(category_key, category_key)

    if not items:
        text = (
            f"{category_label}\n\n"
            f"У цьому розділі немає предметів.\n\n"
            f"🎒 Сумка: {used_slots}/{capacity}\n"
            f"✅ Вільно: {free_slots}"
        )

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text="⬅️ До розділів інвентаря",
            callback_data="inv_home"
        ))

        return text, kb

    total_items = len(items)
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    if page < 0:
        page = 0

    if page >= total_pages:
        page = total_pages - 1

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_items = items[start:end]

    text = (
        f"{category_label}\n\n"
        f"🎒 Сумка: {used_slots}/{capacity}\n"
        f"✅ Вільно: {free_slots}\n"
        f"📄 Сторінка: {page + 1}/{total_pages}\n\n"
    )

    if category_key in SLOT_ORDER:
        equipped_slots = get_all_equipped_slots(user_id)
        equipped_inventory_id = equipped_slots.get(category_key)

        if equipped_inventory_id:
            equipped_item = get_item_by_inventory_id_full(equipped_inventory_id)

            if equipped_item:
                text += f"✅ Зараз вдягнено: {equipped_item[2]}\n\n"
        else:
            text += "Слот порожній.\n\n"

    text += "Оберіть предмет:"

    kb = types.InlineKeyboardMarkup()

    for item in page_items:
        inv_id = item[0]
        label = build_item_button_label(user_id, item)

        kb.add(types.InlineKeyboardButton(
            text=label,
            callback_data=f"item:{inv_id}:{category_key}:{page}"
        ))

    nav_buttons = []

    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"invcat:{category_key}:{page - 1}"
        ))

    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton(
            text="➡️ Далі",
            callback_data=f"invcat:{category_key}:{page + 1}"
        ))

    if nav_buttons:
        kb.add(*nav_buttons)

    kb.add(types.InlineKeyboardButton(
        text="⬅️ До розділів інвентаря",
        callback_data="inv_home"
    ))

    return text, kb


def build_item_details(user_id, inventory_id, back_category="all", page=0):
    item = get_item_by_inventory_id_full(inventory_id)

    if not item:
        text = "❌ Предмет не знайдено"

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"invcat:{back_category}:{page}"
        ))

        return text, kb

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
    ) = item

    equipped = is_inventory_item_equipped(user_id, inv_id)
    equipped_slot_key = find_equipped_slot_by_inventory_id(user_id, inv_id)

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
            callback_data=f"usepot:{inv_id}:{back_category}:{page}"
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

        bonuses = format_item_bonuses(
            b_str,
            b_dex,
            b_int,
            b_wis,
            b_sta,
            pdef,
            mdef
        )

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
                callback_data=f"unequip:{inv_id}:{back_category}:{page}"
            ))
        else:
            kb.add(types.InlineKeyboardButton(
                text=f"✅ Вдягнути у слот: {slot_label}",
                callback_data=f"equip:{inv_id}:{back_category}:{page}"
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
        text="⬅️ Назад до розділу",
        callback_data=f"invcat:{back_category}:{page}"
    ))

    kb.add(types.InlineKeyboardButton(
        text="🏠 До розділів інвентаря",
        callback_data="inv_home"
    ))

    return text, kb


# ==============================
# HANDLERS
# ==============================

def register_inventory_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🎒 Інвентар")
    def show_inventory(message):
        user_id = message.from_user.id

        text, kb = build_inventory_home(user_id)

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb if kb else profile_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "inv_home")
    def inventory_home_callback(call):
        user_id = call.from_user.id

        text, kb = build_inventory_home(user_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb if kb else profile_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("invcat:"))
    def inventory_category_callback(call):
        user_id = call.from_user.id

        parts = call.data.split(":")
        category_key = parts[1]
        page = int(parts[2]) if len(parts) > 2 else 0

        text, kb = build_category_list(user_id, category_key, page)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("item:"))
    def item_details_callback(call):
        user_id = call.from_user.id

        parts = call.data.split(":")
        inventory_id = int(parts[1])
        back_category = parts[2] if len(parts) > 2 else "all"
        page = int(parts[3]) if len(parts) > 3 else 0

        text, kb = build_item_details(
            user_id=user_id,
            inventory_id=inventory_id,
            back_category=back_category,
            page=page
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("equip:"))
    def equip_callback(call):
        user_id = call.from_user.id

        parts = call.data.split(":")
        inventory_id = int(parts[1])
        back_category = parts[2] if len(parts) > 2 else "all"
        page = int(parts[3]) if len(parts) > 3 else 0

        result = equip_inventory_item(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result
        )

        text, kb = build_item_details(
            user_id=user_id,
            inventory_id=inventory_id,
            back_category=back_category,
            page=page
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("unequip:"))
    def unequip_callback(call):
        user_id = call.from_user.id

        parts = call.data.split(":")
        inventory_id = int(parts[1])
        back_category = parts[2] if len(parts) > 2 else "all"
        page = int(parts[3]) if len(parts) > 3 else 0

        result = unequip_inventory_item(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result
        )

        text, kb = build_item_details(
            user_id=user_id,
            inventory_id=inventory_id,
            back_category=back_category,
            page=page
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("usepot:"))
    def use_potion_callback(call):
        user_id = call.from_user.id

        parts = call.data.split(":")
        inventory_id = int(parts[1])
        back_category = parts[2] if len(parts) > 2 else "potion"
        page = int(parts[3]) if len(parts) > 3 else 0

        result = use_potion_from_inventory(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"]
        )

        text, kb = build_category_list(user_id, back_category, page)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )