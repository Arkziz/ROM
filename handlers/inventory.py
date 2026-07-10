from telebot import types

from db import (
    EQUIPMENT_SLOTS,
    SLOT_ORDER,
    CLASS_RESET_SPHERE_ITEM_ID,

    get_inventory_detailed,
    get_item_by_inventory_id_full,
    equip_inventory_item,
    unequip_inventory_item,
    get_inventory_used_slots,
    get_bag_capacity,
    is_inventory_item_equipped,
    find_equipped_slot_by_inventory_id,
    get_all_equipped_slots,
    get_player_stats,
    get_item_required_level_by_inventory_id,
    get_inventory_weapon_damage_display,
    get_item_classification_by_inventory_id,
    get_armor_type_label,
    get_item_subtype_label,
    is_armor_slot,

    is_class_reset_sphere_inventory_item,
    use_class_reset_sphere_from_inventory
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
    ("chest", "🥋 Тіло"),
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



def build_item_display_name(user_id, inventory_id, fallback_name):
    """
    Повертає назву предмета для списків інвентаря.

    Для броні додає тип у дужках:
    Чоботи 1 рівня -> Чоботи [Лати] 1 рівня

    Для зброї / off-hand НЕ додає тип у дужках,
    бо назва вже зазвичай містить сам тип:
    Кинджал 1 рівня
    Жезл 1 рівня
    Магічний талісман 1 рівня
    """

    classification = get_item_classification_by_inventory_id(inventory_id)

    if not classification:
        return fallback_name

    slot_key = classification.get("slot_key", "")
    armor_type = classification.get("armor_type", "")

    # Тип у дужках показуємо тільки для броні.
    if not is_armor_slot(slot_key):
        return fallback_name

    if not armor_type:
        return fallback_name

    type_label = get_armor_type_label(armor_type)

    if not type_label:
        return fallback_name

    # Якщо назва вже містить цей тип — не дублюємо.
    if f"[{type_label}]" in fallback_name:
        return fallback_name

    marker = " рівня"

    if marker in fallback_name:
        index = fallback_name.rfind(marker)
        before_level = fallback_name[:index]
        after_level = fallback_name[index:]

        parts = before_level.rsplit(" ", 1)

        if len(parts) == 2 and parts[1].isdigit():
            return f"{parts[0]} [{type_label}] {parts[1]}{after_level}"

    return f"{fallback_name} [{type_label}]"

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


def get_player_level(user_id):
    stats = get_player_stats(user_id)

    if stats:
        _, _, _, _, _, player_level = stats
        return player_level

    return 1


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

    label = build_item_display_name(
        user_id=user_id,
        inventory_id=inv_id,
        fallback_name=name
    )

    if max_stack and max_stack > 1:
        label += f" x{quantity}"

    if category == "equipment":
        if durability is not None:
            label += f" [{durability}/100]"

        if is_inventory_item_equipped(user_id, inv_id):
            equipped_slot = find_equipped_slot_by_inventory_id(user_id, inv_id)
            label += f" ✅ {get_slot_label(equipped_slot)}"

    return label


def build_equipped_comparison_text(user_id, slot_key, current_inventory_id):
    if not slot_key:
        return ""

    equipped_slots = get_all_equipped_slots(user_id)
    equipped_inventory_id = equipped_slots.get(slot_key)

    if not equipped_inventory_id:
        return ""

    if equipped_inventory_id == current_inventory_id:
        return ""

    equipped_item = get_item_by_inventory_id_full(equipped_inventory_id)

    if not equipped_item:
        return ""

    (
        inv_id,
        item_id,
        name,
        type_,
        rarity,
        category,
        item_slot_key,
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
    ) = equipped_item

    display_name = build_item_display_name(
        user_id=user_id,
        inventory_id=inv_id,
        fallback_name=name
    )

    text = "\n\n⚖️ Зараз вдягнено для порівняння:\n"
    text += f"{display_name}\n"

    if item_slot_key == "main_hand":
        if weapon_hands == 2:
            text += "👐 Тип зброї: дворучна\n"
        else:
            text += "✋ Тип зброї: одноручна\n"

        weapon_damage_text = get_inventory_weapon_damage_display(inv_id)

        if weapon_damage_text:
            text += f"{weapon_damage_text}\n"

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
        text += "📊 Бонуси:\n"

        for bonus in bonuses:
            text += f"• {bonus}\n"
    else:
        text += "📊 Бонуси: немає\n"

    return text


# ==============================
# INVENTORY HOME
# ==============================

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


# ==============================
# CATEGORY LIST
# ==============================

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
                equipped_display_name = build_item_display_name(
                    user_id=user_id,
                    inventory_id=equipped_inventory_id,
                    fallback_name=equipped_item[2]
                )

                text += f"✅ Зараз вдягнено: {equipped_display_name}\n\n"
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


# ==============================
# ITEM DETAILS
# ==============================

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

    player_level = get_player_level(user_id)
    required_level = get_item_required_level_by_inventory_id(inv_id)
    level_ok = player_level >= required_level

    equipped = is_inventory_item_equipped(user_id, inv_id)
    equipped_slot_key = find_equipped_slot_by_inventory_id(user_id, inv_id)

    kb = types.InlineKeyboardMarkup()

    display_name = build_item_display_name(
        user_id=user_id,
        inventory_id=inv_id,
        fallback_name=name
    )

    text = f"📦 Предмет\n\n{display_name}\n\n"

    # ==============================
    # TRASH
    # ==============================

    if category == "trash":
        total_price = (quantity or 1) * (sell_price or 0)

        text += (
            f"🔘 Тип: сірий лут\n"
            f"📦 Кількість: {quantity}/{max_stack}\n"
            f"💰 Ціна продажу: {sell_price:.2f} золота за шт.\n"
            f"💰 Усього: {total_price:.2f} золота\n\n"
            f"ℹ️ Цей предмет можна продати торговцю в місті."
        )

    # ==============================
    # POTION / SPECIAL ITEM
    # ==============================

    elif category == "potion":
        text += (
            f"🧪 Тип: зілля / особливий предмет\n"
            f"📦 Кількість: {quantity}/{max_stack}\n"
            f"💰 Ціна продажу: {sell_price:.2f} золота за шт.\n\n"
        )

        if type_ == "potion_hp":
            text += "❤️ Ефект: відновлює 50 HP\n"
        elif type_ == "potion_hp_medium":
            text += "❤️ Ефект: відновлює 120 HP\n"
        elif type_ == "potion_mp":
            text += "🔵 Ефект: відновлює 40 MP\n"
        elif type_ == "potion_mp_medium":
            text += "🔵 Ефект: відновлює 100 MP\n"
        elif type_ == "class_reset" or item_id == CLASS_RESET_SPHERE_ITEM_ID:
            text += (
                "🔮 Ефект: дозволяє змінити клас персонажа.\n"
                "Після використання відкриється вибір нового класу.\n"
            )
        else:
            text += "ℹ️ Ефект предмета поки не описаний.\n"

        text += "\nℹ️ Предмет використовується з інвентаря."

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

        level_text = "✅" if level_ok else "🔒"

        text += (
            f"🏷 Рівень предмета: {required_level} {level_text}\n"
            f"👤 Твій рівень: {player_level}\n"
        )

        if not level_ok:
            text += f"⚠️ Цей предмет можна буде вдягнути з {required_level} рівня.\n"

        if slot_key == "main_hand":
            if weapon_hands == 2:
                text += "👐 Тип зброї: дворучна\n"
                text += "⚠️ Дворучна зброя блокує другу руку.\n"
            else:
                text += "✋ Тип зброї: одноручна\n"

            weapon_damage_text = get_inventory_weapon_damage_display(inv_id)

            if weapon_damage_text:
                text += f"{weapon_damage_text}\n"

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

        comparison_text = build_equipped_comparison_text(
            user_id=user_id,
            slot_key=slot_key,
            current_inventory_id=inv_id
        )

        if comparison_text:
            text += comparison_text

        if equipped:
            equipped_slot_label = get_slot_label(equipped_slot_key)
            text += f"\n✅ Зараз вдягнено у слот: {equipped_slot_label}"

            kb.add(types.InlineKeyboardButton(
                text="❌ Зняти",
                callback_data=f"unequip:{inv_id}:{back_category}:{page}"
            ))
        else:
            if level_ok:
                kb.add(types.InlineKeyboardButton(
                    text=f"✅ Вдягнути у слот: {slot_label}",
                    callback_data=f"equip:{inv_id}:{back_category}:{page}"
                ))
            else:
                text += "\n🔒 Кнопка вдягання недоступна через недостатній рівень.\n"

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

        # 🔮 Сфера нового шляху
        if is_class_reset_sphere_inventory_item(user_id, inventory_id):
            result = use_class_reset_sphere_from_inventory(user_id, inventory_id)

            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                result["message"]
            )

            if result.get("success"):
                from handlers.start import start_class_change_flow

                start_class_change_flow(
                    bot=bot,
                    chat_id=call.message.chat.id,
                    user_id=user_id
                )
                return

            text, kb = build_category_list(user_id, back_category, page)

            bot.send_message(
                call.message.chat.id,
                text,
                reply_markup=kb
            )
            return

        # Звичайні зілля
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