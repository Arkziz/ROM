# ROM 17.10.1 ITEM QUANTITY DISPLAY FORMAT



from data.runes import FIRIUS_TOKENS_PER_DAILY_REWARD

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



    ARMOR_ALLOWED_BY_CLASS,



    MAIN_HAND_ALLOWED_BY_CLASS,



    OFF_HAND_ALLOWED_BY_CLASS,



    CLASS_CONFIGS,







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



    ("material", "🪨 Матеріали"),



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















def build_item_allowed_classes_text(user_id, inventory_id):



    """



    Повертає текст, яким класам підходить предмет.







    Приклади:



    👥 Підходить класам: 🔮 Маг, ⚕️ Жрець



    👥 Підходить класам: ⚔️ Лицар



    👥 Підходить класам: усім класам



    """







    classification = get_item_classification_by_inventory_id(inventory_id)







    if not classification:



        return ""







    if classification.get("category") != "equipment":



        return ""







    slot_key = classification.get("slot_key", "")



    armor_type = classification.get("armor_type", "")



    item_subtype = classification.get("item_subtype", "")







    allowed_class_keys = []







    if is_armor_slot(slot_key):



        if not armor_type:



            return "👥 Підходить класам: усім класам (універсальна броня)\n"







        for class_key, allowed_armor_type in ARMOR_ALLOWED_BY_CLASS.items():



            if allowed_armor_type == armor_type:



                allowed_class_keys.append(class_key)







    elif slot_key == "main_hand":



        if not item_subtype:



            return "👥 Підходить класам: усім класам (універсальна зброя)\n"







        for class_key, allowed_subtypes in MAIN_HAND_ALLOWED_BY_CLASS.items():



            if item_subtype in allowed_subtypes:



                allowed_class_keys.append(class_key)







    elif slot_key == "off_hand":



        if not item_subtype:



            return "👥 Підходить класам: усім класам (універсальний предмет другої руки)\n"







        for class_key, allowed_subtypes in OFF_HAND_ALLOWED_BY_CLASS.items():



            if item_subtype in allowed_subtypes:



                allowed_class_keys.append(class_key)







    else:



        # Прикраси та інші слоти поки не мають класових обмежень.



        return "👥 Підходить класам: усім класам\n"







    if not allowed_class_keys:



        return "👥 Підходить класам: не визначено\n"







    class_names = []







    for class_key in allowed_class_keys:



        config = CLASS_CONFIGS.get(class_key, {})



        class_names.append(config.get("name", class_key))







    return f"👥 Підходить класам: {', '.join(class_names)}\n"







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



        label += f" ×{quantity}"







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



        # ROM 17.6.1 INVENTORY MOBILE MESSAGE WIDTH



        f"Оберіть потрібний розділ вашого інвентаря:"



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







    kb.add(types.InlineKeyboardButton(



        text="🔙 Профіль",



        callback_data="inv_profile"



    ))







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







    text += "Оберіть предмет для перегляду або виконання доступної дії:"







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







        allowed_classes_text = build_item_allowed_classes_text(



            user_id=user_id,



            inventory_id=inv_id



        )







        if allowed_classes_text:



            text += allowed_classes_text







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







    @bot.callback_query_handler(func=lambda call: call.data == "inv_profile")



    def inventory_profile_callback(call):



        from handlers.profile import build_character_text, profile_inline_kb







        bot.answer_callback_query(call.id)



        bot.send_message(



            call.message.chat.id,



            "👤 Розділ персонажа відкрито",



            reply_markup=profile_kb()



        )



        bot.send_message(



            call.message.chat.id,



            build_character_text(call.from_user.id),



            reply_markup=profile_inline_kb(active_tab="character")



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



        # ROM 17.5.1.1 KEEP POTION PREVIEW OPEN



        result = use_potion_from_inventory(user_id, inventory_id)



        result_message = str(result.get("message") or "Не вдалося використати зілля.")







        if result.get("success"):



            bot.answer_callback_query(call.id)



            bot.send_message(call.message.chat.id, result_message)



            canonical_inventory_id = result.get("inventory_id")



            if canonical_inventory_id is not None:



                text, kb = build_item_details(



                    user_id=user_id,



                    inventory_id=int(canonical_inventory_id),



                    back_category=back_category,



                    page=page,



                )



            else:



                text, kb = build_category_list(user_id, back_category, page)



            try:



                bot.edit_message_text(



                    text,



                    chat_id=call.message.chat.id,



                    message_id=call.message.message_id,



                    reply_markup=kb,



                )



            except Exception:



                try:



                    bot.edit_message_reply_markup(



                        chat_id=call.message.chat.id,



                        message_id=call.message.message_id,



                        reply_markup=None,



                    )



                except Exception:



                    pass



                bot.send_message(call.message.chat.id, text, reply_markup=kb)



            return







        stale_inventory = "Предмет не знайдено в інвентарі" in result_message



        if stale_inventory:



            bot.answer_callback_query(call.id, text=result_message, show_alert=True)



            text, kb = build_category_list(user_id, back_category, page)



            try:



                bot.edit_message_text(



                    text,



                    chat_id=call.message.chat.id,



                    message_id=call.message.message_id,



                    reply_markup=kb,



                )



            except Exception:



                try:



                    bot.edit_message_reply_markup(



                        chat_id=call.message.chat.id,



                        message_id=call.message.message_id,



                        reply_markup=None,



                    )



                except Exception:



                    pass



                bot.send_message(call.message.chat.id, text, reply_markup=kb)



            return







        bot.answer_callback_query(call.id, text=result_message, show_alert=True)



        return











# ==============================



# ✅ REFINE MATERIALS INVENTORY CATEGORY V1



# ==============================







# 6.0.4b



# Окрема категорія інвентаря для матеріалів:



# - 401 🪨 Камінь Посилення



# - 402 💎 Руна Успіху







try:



    if ("material", "🪨 Матеріали") not in INVENTORY_CATEGORIES:



        # Вставляємо перед "Переглянути все", якщо можливо.



        insert_index = len(INVENTORY_CATEGORIES)



        for idx, entry in enumerate(INVENTORY_CATEGORIES):



            if entry[0] == "all":



                insert_index = idx



                break



        INVENTORY_CATEGORIES.insert(insert_index, ("material", "🪨 Матеріали"))



except Exception:



    pass







try:



    _base_get_category_items_before_materials_v1 = get_category_items



except Exception:



    _base_get_category_items_before_materials_v1 = None











def get_category_items(user_id, category_key):



    """



    FINAL OVERRIDE:



    Додає коректну підтримку категорії 🪨 Матеріали.



    """







    if category_key != "material":



        if _base_get_category_items_before_materials_v1 is not None:



            return _base_get_category_items_before_materials_v1(user_id, category_key)



        return []







    items = get_inventory_full_items(user_id)



    result = []







    for item in items:



        try:



            item_id = item[1]



            category = item[5]



        except Exception:



            continue







        if category == "material" or item_id in [601, 602]:



            result.append(item)







    return result











def get_category_count(user_id, category_key):



    return len(get_category_items(user_id, category_key))







# ==============================



# ✅ REFINE MATERIAL DESCRIPTIONS V1



# ==============================







# 6.0.4c



# Додає корисний опис для матеріалів заточки в деталях предмета.







try:



    _base_build_item_details_before_refine_material_desc_v1 = build_item_details



except Exception:



    _base_build_item_details_before_refine_material_desc_v1 = None











def get_refine_material_description_text(item_id):



    try:



        item_id = int(item_id)



    except Exception:



        return ""







    if item_id == 601:



        return (



            "\nℹ️ Опис:\n"



            "🪨 Камінь Посилення використовується у Коваля для спроби заточки спорядження.\n\n"



            "Правила:\n"



            "• витрачається при кожній спробі заточки;\n"



            "• потрібен для заточки зброї та броні;\n"



            "• не гарантує успіх;\n"



            "• шанс успіху залежить від поточного рівня заточки.\n"



        )







    if item_id == 602:



        return (



            "\nℹ️ Опис:\n"



            "💎 Руна Успіху — особлива руна для безпечної заточки.\n\n"



            "Ефект:\n"



            "• при використанні шанс успіху стає 100%;\n"



            "• витрачається разом із 🪨 Каменем Посилення;\n"



            "• допомагає уникнути невдалої спроби заточки.\n"



        )











    if item_id == 726:



        return (



            "\nℹ️ Опис:\n"



            "🪙 Жетон Фіріуса — особливий матеріал для переробки рун у Рунного Майстра.\n\n"



            "Призначення:\n"



            "• використовується для створення руни наступного рівня;\n"



            "• одна успішна переробка витрачає 1 жетон;\n"



            "• для переробки також потрібні 3 однакові руни одного типу й рівня;\n"



            "• жетони накопичуються та не зникають наступного дня;\n"



            f"• {FIRIUS_TOKENS_PER_DAILY_REWARD} жетони можна отримати за виконання щоденного завдання.\n"



        )







    return ""











def _inject_refine_material_description(text, inventory_id):



    try:



        item = get_item_by_inventory_id_full(inventory_id)



        if not item:



            return text







        item_id = item[1]



        description = get_refine_material_description_text(item_id)







        if not description:



            return text







        if "ℹ️ Опис:" in text:



            return text







        return text + description







    except Exception:



        return text











def build_item_details(user_id, inventory_id, back_category="all", page=0):



    if _base_build_item_details_before_refine_material_desc_v1 is None:



        return "❌ Деталі предмета недоступні.", None







    result = _base_build_item_details_before_refine_material_desc_v1(



        user_id,



        inventory_id,



        back_category,



        page



    )







    if isinstance(result, tuple):



        if len(result) >= 2:



            text = result[0]



            kb = result[1]



            text = _inject_refine_material_description(text, inventory_id)



            return text, kb







        if len(result) == 1:



            text = _inject_refine_material_description(result[0], inventory_id)



            return (text,)







    if isinstance(result, str):



        return _inject_refine_material_description(result, inventory_id)







    return result







# ==============================



# ROM 10.3.2 MATERIAL CATEGORY UKRAINIAN LABEL



# ==============================







_BASE_INJECT_MATERIAL_DESCRIPTION_10_3_2 = _inject_refine_material_description











def _inject_refine_material_description(text, inventory_id):



    result = _BASE_INJECT_MATERIAL_DESCRIPTION_10_3_2(text, inventory_id)



    try:



        item = get_item_by_inventory_id_full(inventory_id)



        if not item:



            return result



        item_id = int(item[1])



        if item_id in (601, 602, 726):



            result = result.replace("📦 Категорія: material", "📦 Категорія: Матеріали")



    except Exception:



        pass



    return result







# ==============================



# ROM 10.4.0 RUNE INVENTORY UI



# ==============================







try:



    if ("rune", "💠 Руни") not in INVENTORY_CATEGORIES:



        _rune_category_insert_index = len(INVENTORY_CATEGORIES)



        for _rune_category_index, _rune_category_entry in enumerate(INVENTORY_CATEGORIES):



            if _rune_category_entry[0] == "material":



                _rune_category_insert_index = _rune_category_index



                break



            if _rune_category_entry[0] == "all":



                _rune_category_insert_index = _rune_category_index



                break



        INVENTORY_CATEGORIES.insert(



            _rune_category_insert_index,



            ("rune", "💠 Руни"),



        )



except Exception:



    pass







_RUNE_UI_BASE_GET_CATEGORY_ITEMS_10_4_0 = get_category_items



_RUNE_UI_BASE_MATERIAL_DESCRIPTION_10_4_0 = get_refine_material_description_text



_RUNE_UI_BASE_INJECT_DESCRIPTION_10_4_0 = _inject_refine_material_description











def get_category_items(user_id, category_key):



    if category_key != "rune":



        return _RUNE_UI_BASE_GET_CATEGORY_ITEMS_10_4_0(user_id, category_key)



    return [



        item for item in get_inventory_full_items(user_id)



        if len(item) > 5 and item[5] == "rune"



    ]







# ==============================



# ROM 17.7.1 INVENTORY CANONICAL UI SORTING



# ==============================







_STAGE_17_7_1_BASE_GET_CATEGORY_ITEMS = get_category_items



_STAGE_17_7_1_RARITY_PREFIXES = ("⚪️", "⚪", "🟢", "🔵", "🟣")



_STAGE_17_7_1_CATEGORY_ORDER = (



    "main_hand",



    "off_hand",



    "helmet",



    "shoulders",



    "chest",



    "gloves",



    "legs",



    "boots",



    "necklace",



    "ring",



    "trash",



    "rune",



    "material",



    "potion",



)



_STAGE_17_7_1_CATEGORY_RANK = {



    category_key: index



    for index, category_key in enumerate(_STAGE_17_7_1_CATEGORY_ORDER)



}











def _inventory_ui_normalized_name_17_7_1(item):



    """Return case-insensitive item name without a leading rarity marker."""



    try:



        name = str(item[2] or "").strip()



    except Exception:



        name = ""



    for prefix in _STAGE_17_7_1_RARITY_PREFIXES:



        if name.startswith(prefix):



            name = name[len(prefix):].lstrip()



            break



    return name.casefold()











def _inventory_ui_category_key_17_7_1(item):



    """Map one inventory tuple to the approved logical category in the all view."""



    try:



        category = str(item[5] or "").strip().lower()



        slot_key = str(item[6] or "").strip().lower()



    except Exception:



        return ""



    if category == "equipment" and slot_key:



        return slot_key



    return category











def _inventory_ui_sort_key_17_7_1(item, include_category=False):



    """Sort by category rank, normalized name, then newest inventory ID first."""



    try:



        inventory_id = int(item[0])



    except Exception:



        inventory_id = 0



    name_key = _inventory_ui_normalized_name_17_7_1(item)



    if not include_category:



        return (name_key, -inventory_id)



    category_key = _inventory_ui_category_key_17_7_1(item)



    category_rank = _STAGE_17_7_1_CATEGORY_RANK.get(



        category_key,



        len(_STAGE_17_7_1_CATEGORY_ORDER),



    )



    return (category_rank, name_key, -inventory_id)











def get_category_items(user_id, category_key):



    """Return final filtered inventory UI items in canonical Stage 17.7 order."""



    items = list(_STAGE_17_7_1_BASE_GET_CATEGORY_ITEMS(user_id, category_key) or [])



    return sorted(



        items,



        key=lambda item: _inventory_ui_sort_key_17_7_1(



            item,



            include_category=(category_key == "all"),



        ),



    )















def get_category_count(user_id, category_key):



    return len(get_category_items(user_id, category_key))











def _get_rune_inventory_description(item_id):



    from data.runes import (



        FIRIUS_TOKEN_ITEM_ID,



        PERFECT_RUNE_EXTRACTOR_ITEM_ID,



        RUNE_EXTRACTOR_ITEM_ID,



        RUNE_LEVEL_ROMAN,



        RUNE_STAT_NAMES,



        get_rune_definition,



    )







    definition = get_rune_definition(item_id)



    if definition:



        stat_name = RUNE_STAT_NAMES[definition["stat"]]



        level = int(definition["level"])



        level_roman = RUNE_LEVEL_ROMAN[level]



        if level < 5:



            next_roman = RUNE_LEVEL_ROMAN[level + 1]



            upgrade_line = (



                f"• може бути покращена до Руни {stat_name} {next_roman}.\n"



            )



        else:



            upgrade_line = (



                "• має максимальний рівень і не може бути покращена далі.\n"



            )



        return (



            "\nℹ️ Опис:\n"



            f"{definition['name']} — руна характеристики рівня {level_roman}.\n\n"



            "Ефект:\n"



            f"• після вставки у спорядження додає +{definition['bonus']} "



            f"до характеристики {stat_name};\n"



            "• бонус діє лише тоді, коли предмет екіпірований і не зламаний;\n"



            "• для переробки потрібні 3 однакові руни одного типу й рівня;\n"



            "• переробка також витрачає 1 Жетон Фіріуса;\n"



            + upgrade_line



        )







    if int(item_id) == RUNE_EXTRACTOR_ITEM_ID:



        return (
            'ℹ️ Опис:\n'
            '🧰 Екстрактор рун — матеріал для вилучення рун зі спорядження.\n\n'
            '⚙️ Ефект:\n'
            '• повертає 1 випадкову вставлену руну в інвентар;\n'
            '• знищує предмет спорядження;\n'
            '• витрачається під час використання.\n\n'
            '🛒 Придбання:\n'
            '• можна придбати у Рунного Майстра за золото.'
        )







    if int(item_id) == PERFECT_RUNE_EXTRACTOR_ITEM_ID:



        return (
            'ℹ️ Опис:\n'
            '✨ Досконалий Екстрактор рун — матеріал для повного вилучення рун зі спорядження.\n\n'
            '⚙️ Ефект:\n'
            '• повертає всі вставлені руни в інвентар;\n'
            '• знищує предмет спорядження;\n'
            '• витрачається під час використання.\n\n'
            '🛒 Придбання:\n'
            '• можна придбати в Магазині кристалів за 20 кристалів.'
        )







    return ""











def get_refine_material_description_text(item_id):



    description = _RUNE_UI_BASE_MATERIAL_DESCRIPTION_10_4_0(item_id)



    if description:



        return description



    try:



        return _get_rune_inventory_description(int(item_id))



    except Exception:



        return ""











def _inject_refine_material_description(text, inventory_id):



    result = _RUNE_UI_BASE_INJECT_DESCRIPTION_10_4_0(text, inventory_id)



    try:



        item = get_item_by_inventory_id_full(inventory_id)



        if not item:



            return result



        item_id = int(item[1])



        category = str(item[5] or "") if len(item) > 5 else ""



        if category == "rune" or 701 <= item_id <= 725:



            result = result.replace("📦 Категорія: rune", "📦 Категорія: Руни")



        if item_id in (601, 602, 726, 727, 728):



            result = result.replace(



                "📦 Категорія: material",



                "📦 Категорія: Матеріали",



            )



    except Exception:



        pass



    return result







# ==============================



# ROM 10.5.0 EQUIPMENT RUNE SLOT DISPLAY + MOBILE LABELS



# ==============================







_RUNE_SLOT_BASE_BUILD_ITEM_DETAILS_10_5_0 = build_item_details



_RUNE_SLOT_BASE_BUTTON_LABEL_10_5_0 = build_item_button_label











def build_item_button_label(user_id, item):



    """Use × and hide redundant ×1 for rune buttons on narrow mobile screens."""



    label = _RUNE_SLOT_BASE_BUTTON_LABEL_10_5_0(user_id, item)



    try:



        category = str(item[5] or "")



        quantity = int(item[8] or 0)



        if category == "rune":



            label = label.replace(f" ×{quantity}", "")



            label = label.replace(f" ×{quantity}", "")



            if quantity > 1:



                label += f" ×{quantity}"



        else:



            label = label.replace(f" ×{quantity}", f" ×{quantity}")



    except Exception:



        pass



    return label











def build_item_details(user_id, inventory_id, back_category="all", page=0):



    result = _RUNE_SLOT_BASE_BUILD_ITEM_DETAILS_10_5_0(



        user_id,



        inventory_id,



        back_category,



        page,



    )



    try:



        from systems.rune_system import format_equipment_rune_slots_text



        block = format_equipment_rune_slots_text(user_id, inventory_id)



        if not block:



            return result



        if isinstance(result, tuple) and len(result) >= 2:



            text, keyboard = result[0], result[1]



            if "💠 Рунні слоти:" not in text:



                text += block



            return (text, keyboard, *result[2:])



        if isinstance(result, str) and "💠 Рунні слоти:" not in result:



            return result + block



    except Exception:



        return result



    return result







# ==============================



# ROM 10.8.1 RUNE CATEGORY MOBILE WIDTH TEXT



# ==============================







_RUNE_CATEGORY_BASE_BUILD_LIST_10_8_1 = build_category_list











def build_category_list(user_id, category_key, page=0):



    result = _RUNE_CATEGORY_BASE_BUILD_LIST_10_8_1(



        user_id,



        category_key,



        page,



    )



    if category_key != "rune":



        return result



    try:



        if isinstance(result, tuple) and len(result) >= 2:



            text, keyboard = result[0], result[1]



            text = text.replace(



                "Оберіть предмет для перегляду або виконання доступної дії:",



                "Оберіть предмет для ознайомлення:",



                1,



            )



            return (text, keyboard, *result[2:])



        if isinstance(result, str):



            return result.replace(



                "Оберіть предмет для перегляду або виконання доступної дії:",



                "Оберіть предмет для ознайомлення:",



                1,



            )



    except Exception:



        return result



    return result







# ROM 17.28.1.3 NAME RUNE INVENTORY PRESENTATION



_NAME_RUNE_ITEM_ID_17_28_1_3 = 502



_base_build_item_details_before_name_rune_17_28_1_3 = build_item_details







def build_item_details(user_id, inventory_id, back_category="all", page=0):



    text, kb = _base_build_item_details_before_name_rune_17_28_1_3(



        user_id, inventory_id, back_category, page



    )



    try:



        from db_modules.connection import cursor



        row = cursor.execute(



            "SELECT item_id FROM inventory WHERE id=? AND user_id=?",



            (int(inventory_id), int(user_id)),



        ).fetchone()



        if row and int(row[0]) == _NAME_RUNE_ITEM_ID_17_28_1_3:



            from systems.name_rune_system import NAME_RUNE_DESCRIPTION







            text = text.replace("Руна імені", "✍️ Руна імені")



            text = text.replace("📦 Категорія: material", "📦 Категорія: Матеріали")



            if NAME_RUNE_DESCRIPTION not in text:



                text = f"{text.rstrip()}\n\n📖 Опис: {NAME_RUNE_DESCRIPTION}"



            button = types.InlineKeyboardButton(



                text="✍️ Використати Руну імені",



                callback_data=f"name_rune_use:{int(inventory_id)}",



            )



            if getattr(kb, "keyboard", None) is not None:



                kb.keyboard.insert(0, [button])



            else:



                kb.add(button)



    except Exception:



        pass



    return text, kb







# ROM Stage 17.31.1.2 consumables inventory presentation.



if ("consumable", "🧰 Витратні предмети") not in INVENTORY_CATEGORIES:



    INVENTORY_CATEGORIES.append(("consumable", "🧰 Витратні предмети"))



_FATIGUE_ARTIFACT_BASE_DETAILS_17_31_1_1 = build_item_details







def build_item_details(user_id, inventory_id, back_category="all", page=0):



    text, kb = _FATIGUE_ARTIFACT_BASE_DETAILS_17_31_1_1(user_id, inventory_id, back_category, page)



    try:



        from db_modules.connection import cursor



        row = cursor.execute("SELECT item_id FROM inventory WHERE id=? AND user_id=?", (int(inventory_id), int(user_id))).fetchone()



        if row and int(row[0]) == 503:



            from systems.energy_system import get_user_energy



            fatigue = int(get_user_energy(user_id).get("energy", 0))



            text = (f"💠 Артефакт відновлення сил\n\n"



                    f"🧰 Категорія: Витратні предмети\n"



                    f"📦 Одноразовий предмет\n\n"



                    f"Зменшує поточну втому на 5, але не нижче 0.\n\n"



                    f"😴 Поточна втома: {fatigue}/40\n"



                    f"Після одного: {max(0, fatigue-5)}/40")



            button = types.InlineKeyboardButton("💠 Використати", callback_data=f"fa:q:{int(inventory_id)}:1")



            kb.keyboard.insert(0, [button])



    except Exception:



        pass



    return text, kb







# ROM Stage 17.31.1.3 consumables category filter and richer artifact card.



_CONSUMABLE_BASE_GET_CATEGORY_ITEMS_17_31_1_3 = get_category_items







def get_category_items(user_id, category_key):



    if str(category_key) != "consumable":



        return _CONSUMABLE_BASE_GET_CATEGORY_ITEMS_17_31_1_3(user_id, category_key)



    result = []



    for item in get_inventory_full_items(user_id):



        try:



            item_id = int(item[1])



            item_type = str(item[3] or "").strip().lower()



            category = str(item[5] or "").strip().lower()



        except Exception:



            continue



        if item_id == 503 or item_type == "consumable" or category == "consumable":



            result.append(item)



    return sorted(result, key=lambda item: _inventory_ui_sort_key_17_7_1(item, include_category=False))







_CONSUMABLE_BASE_BUILD_ITEM_DETAILS_17_31_1_3 = build_item_details







def build_item_details(user_id, inventory_id, back_category="all", page=0):



    text, kb = _CONSUMABLE_BASE_BUILD_ITEM_DETAILS_17_31_1_3(



        user_id, inventory_id, back_category, page



    )



    try:



        from db_modules.connection import cursor



        row = cursor.execute(



            "SELECT inv.item_id, inv.quantity FROM inventory inv WHERE inv.id=? AND inv.user_id=?",



            (int(inventory_id), int(user_id)),



        ).fetchone()



        if row and int(row[0]) == 503:



            from systems.energy_system import get_user_energy



            fatigue = max(0, int(get_user_energy(user_id).get("energy", 0)))



            quantity = max(1, int(row[1] or 1))



            useful_now = min(quantity, max(1, (fatigue + 4) // 5)) if fatigue > 0 else 0



            text = (



                "💠 Артефакт відновлення сил\n\n"



                "🧰 Категорія: Витратні предмети\n"



                f"📦 У цьому стакі: ×{quantity}/10\n"



                "🔄 Одноразовий предмет\n\n"



                "Стародавній кристалічний артефакт накопичує запас відновлювальної сили. "



                "Після використання зменшує накопичену втому персонажа на 5 за кожен артефакт, "



                "але ніколи не знижує втому нижче 0.\n\n"



                f"😴 Поточна втома: {fatigue}/40\n"



                f"💠 Після одного артефакту: {max(0, fatigue - 5)}/40\n"



                f"✅ Корисно використати зараз: до ×{useful_now}\n\n"



                "ℹ️ Використання недоступне при втомі 0/40 та під час активного бою. "



                "Зайві артефакти не списуються."



            )



    except Exception:



        pass



    return text, kb







# === ROM STAGE 18.11.1 EQUIPMENT RUNE COMPARISON START ===



# Initial item details remain concise. The equipped item is rendered only after



# an ownership-safe, read-only inline callback.



_EQUIPMENT_COMPARISON_BASE_BUILD_ITEM_DETAILS_18_11_1 = build_item_details



_EQUIPMENT_COMPARISON_BASE_REGISTER_HANDLERS_18_11_1 = register_inventory_handlers



_EQUIPMENT_COMPARISON_BASE_TEXT_18_11_1 = build_equipped_comparison_text



_EQUIPMENT_COMPARISON_MARKER_18_11_1 = "⚖️ Зараз вдягнено для порівняння:"



_EQUIPMENT_RUNE_MARKER_18_11_1 = "💠 Рунні слоти:"











def _inventory_comparison_owned_item_18_11_1(user_id, inventory_id):



    """Return the current owned inventory tuple or None; never trusts callback text."""



    try:



        from db_modules.connection import cursor



        row = cursor.execute(



            "SELECT id FROM inventory WHERE id=? AND user_id=? AND COALESCE(quantity,0)>0",



            (int(inventory_id), int(user_id)),



        ).fetchone()



        if not row:



            return None



        return get_item_by_inventory_id_full(int(inventory_id))



    except Exception:



        return None











def _inventory_comparison_target_18_11_1(user_id, inventory_id):



    """Reload the selected row and the currently equipped row for its exact slot."""



    item = _inventory_comparison_owned_item_18_11_1(user_id, inventory_id)



    if not item or len(item) <= 6:



        return None



    slot_key = str(item[6] or "").strip()



    if not slot_key:



        return None



    try:



        equipped_id = get_all_equipped_slots(int(user_id)).get(slot_key)



        if not equipped_id or int(equipped_id) == int(inventory_id):



            return None



        equipped = _inventory_comparison_owned_item_18_11_1(user_id, equipped_id)



        if not equipped:



            return None



        return {



            "selected": item,



            "slot_key": slot_key,



            "equipped_inventory_id": int(equipped_id),



            "equipped": equipped,



        }



    except Exception:



        return None











def _inventory_remove_automatic_comparison_18_11_1(text):



    """Remove the inherited comparison and every ambiguous inherited rune block."""



    value = str(text or "")



    marker = value.find(_EQUIPMENT_COMPARISON_MARKER_18_11_1)



    if marker >= 0:



        value = value[:marker].rstrip()



    rune = value.find(_EQUIPMENT_RUNE_MARKER_18_11_1)



    if rune >= 0:



        value = value[:rune].rstrip()



    return value











def _inventory_selected_rune_block_18_11_2(user_id, inventory_id):



    """Build rune sockets only from the exact selected owned inventory row."""



    if not _inventory_comparison_owned_item_18_11_1(user_id, inventory_id):



        return ""



    try:



        from systems.rune_system import format_equipment_rune_slots_text



        return str(format_equipment_rune_slots_text(



            int(user_id), int(inventory_id)



        ) or "")



    except Exception:



        return ""











def _inventory_insert_compare_button_18_11_1(keyboard, inventory_id, category, page):



    """Insert Compare before navigation without disturbing existing equip actions."""



    if keyboard is None:



        return keyboard



    callback = f"itemcmp:{int(inventory_id)}:{str(category or 'all')}:{int(page or 0)}"



    try:



        rows = getattr(keyboard, "keyboard", None)



        if rows is None:



            return keyboard



        for row in rows:



            for button in row:



                if str(getattr(button, "callback_data", "")) == callback:



                    return keyboard



        button = types.InlineKeyboardButton(text="⚖️ Порівняти", callback_data=callback)



        navigation_prefixes = ("item:", "invcat:", "inv_home", "inventory", "inv_")



        insert_at = len(rows)



        for index, row in enumerate(rows):



            callbacks = [str(getattr(item, "callback_data", "")) for item in row]



            labels = [str(getattr(item, "text", "")) for item in row]



            if any(value.startswith(navigation_prefixes) for value in callbacks) or any("Назад" in label or "До розділів" in label for label in labels):



                insert_at = index



                break



        rows.insert(insert_at, [button])



    except Exception:



        return keyboard



    return keyboard











def build_equipped_comparison_text(user_id, slot_key, current_inventory_id):



    """Existing equipped-item card plus that equipped row's own rune sockets."""



    text = _EQUIPMENT_COMPARISON_BASE_TEXT_18_11_1(user_id, slot_key, current_inventory_id)



    target = _inventory_comparison_target_18_11_1(user_id, current_inventory_id)



    if not text or not target:



        return text



    try:



        from systems.rune_system import format_equipment_rune_slots_text



        rune_block = format_equipment_rune_slots_text(



            int(user_id), target["equipped_inventory_id"]



        )



        if rune_block and _EQUIPMENT_RUNE_MARKER_18_11_1 not in text:



            text = text.rstrip() + "\n" + str(rune_block)



    except Exception:



        pass



    return text











def build_item_details(user_id, inventory_id, back_category="all", page=0):



    """Selected item only; add Compare iff another item is equipped in the slot."""



    result = _EQUIPMENT_COMPARISON_BASE_BUILD_ITEM_DETAILS_18_11_1(



        user_id, inventory_id, back_category, page



    )



    if not isinstance(result, tuple) or len(result) < 2:



        return result



    text, keyboard = result[0], result[1]



    text = _inventory_remove_automatic_comparison_18_11_1(text)



    selected_runes = _inventory_selected_rune_block_18_11_2(user_id, inventory_id)



    if selected_runes:



        text = text.rstrip() + "\n\n" + selected_runes.lstrip()



    if _inventory_comparison_target_18_11_1(user_id, inventory_id):



        keyboard = _inventory_insert_compare_button_18_11_1(



            keyboard, inventory_id, back_category, page



        )



    return (text, keyboard, *result[2:])











def _inventory_comparison_keyboard_18_11_1(keyboard, inventory_id, category, page):



    """Replace Compare with a canonical return to the selected-item card."""



    try:



        rows = getattr(keyboard, "keyboard", None)



        if rows is None:



            return keyboard



        compare_prefix = f"itemcmp:{int(inventory_id)}:"



        replacement = types.InlineKeyboardButton(



            text="⬅️ Назад до предмета",



            callback_data=f"item:{int(inventory_id)}:{str(category or 'all')}:{int(page or 0)}",



        )



        replaced = False



        for index, row in enumerate(rows):



            if any(str(getattr(button, "callback_data", "")).startswith(compare_prefix) for button in row):



                rows[index] = [replacement]



                replaced = True



                break



        if not replaced:



            rows.insert(0, [replacement])



    except Exception:



        pass



    return keyboard











def register_inventory_handlers(bot):



    """Register comparison before legacy inventory callbacks to preserve priority."""



    @bot.callback_query_handler(



        func=lambda call: str(getattr(call, "data", "") or "").startswith("itemcmp:")



    )



    def equipment_comparison_callback_18_11_1(call):



        try:



            parts = str(call.data or "").split(":")



            if len(parts) != 4:



                raise ValueError("invalid callback")



            inventory_id = int(parts[1])



            category = str(parts[2] or "all")



            page = int(parts[3])



        except Exception:



            bot.answer_callback_query(call.id, "Некоректна дія.", show_alert=True)



            return







        user_id = int(call.from_user.id)



        target = _inventory_comparison_target_18_11_1(user_id, inventory_id)



        if not target:



            bot.answer_callback_query(



                call.id,



                "Предмет або спорядження для порівняння більше недоступні.",



                show_alert=True,



            )



            return







        result = build_item_details(user_id, inventory_id, category, page)



        if not isinstance(result, tuple) or len(result) < 2:



            bot.answer_callback_query(call.id, "Предмет більше недоступний.", show_alert=True)



            return



        text, keyboard = result[0], result[1]



        comparison = build_equipped_comparison_text(



            user_id, target["slot_key"], inventory_id



        )



        if not comparison:



            bot.answer_callback_query(



                call.id, "Спорядження для порівняння більше недоступне.", show_alert=True



            )



            return



        keyboard = _inventory_comparison_keyboard_18_11_1(



            keyboard, inventory_id, category, page



        )



        bot.edit_message_text(



            str(text).rstrip() + comparison,



            call.message.chat.id,



            call.message.message_id,



            reply_markup=keyboard,



        )



        bot.answer_callback_query(call.id)







    return _EQUIPMENT_COMPARISON_BASE_REGISTER_HANDLERS_18_11_1(bot)







# === ROM STAGE 18.11.1 EQUIPMENT RUNE COMPARISON END ===





# ROM Stage 18.16.10 Rebirth Sphere inventory UI.


_REBIRTH_SPHERE_ITEM_ID_18_16_10 = 504


_NEW_PATH_SPHERE_ITEM_ID_18_16_10 = 501


_SPHERE_BASE_GET_CATEGORY_ITEMS_18_16_10 = get_category_items


_SPHERE_BASE_BUILD_ITEM_DETAILS_18_16_10 = build_item_details


_SPHERE_BASE_REGISTER_INVENTORY_HANDLERS_18_16_10 = register_inventory_handlers








def get_category_items(user_id, category_key):


    items = _SPHERE_BASE_GET_CATEGORY_ITEMS_18_16_10(user_id, category_key)


    if str(category_key) != "consumable":


        return items


    by_inventory_id = {int(item[0]): item for item in items}


    for item in get_inventory_full_items(user_id):


        try:


            if int(item[1]) in (_NEW_PATH_SPHERE_ITEM_ID_18_16_10, _REBIRTH_SPHERE_ITEM_ID_18_16_10):


                by_inventory_id[int(item[0])] = item


        except Exception:


            continue


    return sorted(by_inventory_id.values(), key=lambda item: _inventory_ui_sort_key_17_7_1(item, include_category=False))








def _sphere_inventory_item_18_16_10(user_id, inventory_id):


    from db_modules.connection import cursor


    return cursor.execute("""SELECT inv.id,inv.item_id,COALESCE(inv.quantity,1),it.name


        FROM inventory inv JOIN items it ON it.id=inv.item_id


        WHERE inv.id=? AND inv.user_id=? AND inv.item_id IN (501,504)""",


        (int(inventory_id),int(user_id))).fetchone()








def build_item_details(user_id, inventory_id, back_category="all", page=0):


    result = _SPHERE_BASE_BUILD_ITEM_DETAILS_18_16_10(user_id, inventory_id, back_category, page)


    if not isinstance(result, tuple) or len(result) < 2:


        return result


    text, keyboard = result[0], result[1]


    row = _sphere_inventory_item_18_16_10(user_id, inventory_id)


    if not row:


        return result


    item_id = int(row[1])


    if item_id == _NEW_PATH_SPHERE_ITEM_ID_18_16_10:


        text = (


            "🔮 Сфера нового шляху\n\n"


            "🧰 Категорія: Витратні предмети\n"


            "📦 Одноразовий premium-предмет\n\n"


            "📖 Опис: Дозволяє обрати інший клас персонажа. "


            "Після підтвердження всі розподілені очки характеристик повертаються, "


            "а несумісне спорядження знімається. Предмет витрачається лише після успішної зміни класу."


        )


    else:


        from systems.attribute_respec_system import get_attribute_respec_preview


        preview = get_attribute_respec_preview(int(user_id))


        text = (


            "♻️ Сфера Переродження\n\n"


            "🧰 Категорія: Витратні предмети\n"


            "📦 Одноразовий premium-предмет\n\n"


            "📖 Опис: Повністю скидає розподілені очки характеристик без зміни класу. "


            "Усі очки повертаються у вільний баланс для повторного розподілу.\n\n"


            f"⭐ Зараз можна повернути: {preview['returned_points']} очок\n"


            f"📌 Вільних після скидання: {preview['free_after']}"


        )


        button = types.InlineKeyboardButton(


            "♻️ Скинути характеристики",


            callback_data=f"rebirth:preview:{int(inventory_id)}:{str(back_category)}:{int(page)}",


        )


        rows = getattr(keyboard, "keyboard", None)


        if rows is not None:


            rows.insert(0, [button])


    return (text, keyboard, *result[2:])








def _rebirth_preview_text_18_16_10(user_id, final=False):


    from systems.attribute_respec_system import get_attribute_respec_preview


    p = get_attribute_respec_preview(int(user_id))


    a = p["allocated"]


    title = "⚠️ Остаточне підтвердження" if final else "♻️ Скидання характеристик"


    lines = [title, "", "Буде повернено:", "",


        f"• Сила: {a['strength']}", f"• Спритність: {a['dexterity']}",


        f"• Інтелект: {a['intelligence']}", f"• Мудрість: {a['wisdom']}",


        f"• Витривалість: {a['stamina']}", "",


        f"⭐ Усього повернеться: {p['returned_points']} очок",


        f"📌 Вільних очок після скидання: {p['free_after']}", "",


        "Клас персонажа не зміниться."]


    if final:


        lines.extend(["Цю дію не можна скасувати після виконання.", "Сфера Переродження буде витрачена."])


    else:


        lines.append("Сфера Переродження буде витрачена лише після підтвердження.")


    return "\n".join(lines), p








def register_inventory_handlers(bot):


    _SPHERE_BASE_REGISTER_INVENTORY_HANDLERS_18_16_10(bot)





    @bot.callback_query_handler(func=lambda call: str(call.data or "").startswith("rebirth:"))


    def rebirth_sphere_callbacks_18_16_10(call):


        parts = str(call.data or "").split(":")


        if len(parts) < 5:


            bot.answer_callback_query(call.id, "Некоректна дія.", show_alert=True); return


        action, inventory_id, category, page = parts[1], int(parts[2]), parts[3], int(parts[4])


        user_id = int(call.from_user.id)


        row = _sphere_inventory_item_18_16_10(user_id, inventory_id)


        if not row or int(row[1]) != _REBIRTH_SPHERE_ITEM_ID_18_16_10:


            bot.answer_callback_query(call.id, "Сфера Переродження більше недоступна.", show_alert=True); return


        try:


            text, preview = _rebirth_preview_text_18_16_10(user_id, final=(action == "final"))


        except Exception as error:


            bot.answer_callback_query(call.id, str(error), show_alert=True); return


        if preview["returned_points"] <= 0:


            bot.answer_callback_query(call.id, "Немає розподілених очок. Сфера не витрачена.", show_alert=True); return


        kb = types.InlineKeyboardMarkup(row_width=1)


        if action == "preview":


            kb.add(types.InlineKeyboardButton("✅ Продовжити", callback_data=f"rebirth:final:{inventory_id}:{category}:{page}"))


        elif action == "final":


            kb.add(types.InlineKeyboardButton("♻️ Підтвердити скидання", callback_data=f"rebirth:confirm:{inventory_id}:{category}:{page}"))


        elif action == "confirm":


            from systems.attribute_respec_system import reset_allocated_attributes, RespecAlreadyProcessed, AttributeRespecError


            from systems.player_system import get_max_hp


            from systems.character_system import get_max_mp


            key = f"telegram:rebirth:{user_id}:{inventory_id}:{call.message.chat.id}:{call.message.message_id}"


            try:


                result = reset_allocated_attributes(user_id, inventory_id, key,


                    operation_type="attribute_respec", expected_item_id=504,


                    max_hp_getter=get_max_hp, max_mp_getter=get_max_mp)


            except RespecAlreadyProcessed:


                bot.answer_callback_query(call.id, "Це підтвердження вже оброблено.", show_alert=True); return


            except AttributeRespecError as error:


                bot.answer_callback_query(call.id, str(error), show_alert=True); return


            bot.answer_callback_query(call.id)


            bot.edit_message_text(


                "✅ Характеристики скинуто\n\n"


                f"⭐ Повернено очок: {result['before']['returned_points']}\n"


                f"📌 Вільних очок: {result['after']['free_before']}\n\n"


                "Повторно розподілити очки можна у профілі: «Характеристики».",


                call.message.chat.id, call.message.message_id)


            return


        kb.add(types.InlineKeyboardButton("❌ Скасувати", callback_data=f"item:{inventory_id}:{category}:{page}"))


        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)


        bot.answer_callback_query(call.id)



# ROM Stage 18.16.10a sphere category exclusivity.

_SPHERE_CATEGORY_BASE_GET_CATEGORY_ITEMS_18_16_10A = get_category_items



def get_category_items(user_id, category_key):

    key = str(category_key or "")

    items = _SPHERE_CATEGORY_BASE_GET_CATEGORY_ITEMS_18_16_10A(user_id, category_key)

    if key == "potion":

        return [item for item in items if int(item[1]) not in (501, 504)]

    if key == "consumable":

        by_inventory_id = {int(item[0]): item for item in items}

        for item in get_inventory_full_items(user_id):

            try:

                if int(item[1]) in (501, 504):

                    by_inventory_id[int(item[0])] = item

            except Exception:

                continue

        return sorted(by_inventory_id.values(), key=lambda item: _inventory_ui_sort_key_17_7_1(item, include_category=False))

    return items

# ROM Stage 18.16.10c unified sphere inventory cards.
_SPHERE_CARD_BASE_BUILD_ITEM_DETAILS_18_16_10C = build_item_details


def build_item_details(user_id, inventory_id, back_category="all", page=0):
    result = _SPHERE_CARD_BASE_BUILD_ITEM_DETAILS_18_16_10C(
        user_id, inventory_id, back_category, page
    )
    if not isinstance(result, tuple) or len(result) < 2:
        return result
    text, keyboard = result[0], result[1]
    row = _sphere_inventory_item_18_16_10(user_id, inventory_id)
    if not row:
        return result
    item_id = int(row[1])
    quantity = max(0, int(row[2] or 0))
    from db_modules.connection import cursor
    item_row = cursor.execute(
        "SELECT COALESCE(max_stack,1) FROM items WHERE id=?", (item_id,)
    ).fetchone()
    max_stack = max(1, int((item_row[0] if item_row else 1) or 1))
    from systems.attribute_respec_system import get_attribute_respec_preview
    preview = get_attribute_respec_preview(int(user_id))
    if item_id == _NEW_PATH_SPHERE_ITEM_ID_18_16_10:
        from systems.character_system import get_character_class_display
        current_class = get_character_class_display(int(user_id))
        text = (
            "🔮 Сфера нового шляху\n\n"
            "🧰 Категорія: Витратні предмети\n"
            f"📦 У цьому стакі: ×{quantity}/{max_stack}\n"
            "🔄 Одноразовий предмет\n\n"
            "Стародавня сфера дозволяє персонажу обрати інший клас. "
            "Після остаточного підтвердження всі розподілені очки характеристик "
            "повертаються у вільний баланс, а несумісне спорядження знімається. "
            "Сфера витрачається лише після успішної зміни класу.\n\n"
            f"🧭 Поточний клас: {current_class}\n"
            f"⭐ Буде повернено очок: {preview['returned_points']}\n"
            f"📌 Вільних після зміни: {preview['free_after']}\n\n"
            "ℹ️ Сфера не передається, не продається та не випадає з мобів."
        )
    else:
        text = (
            "♻️ Сфера Переродження\n\n"
            "🧰 Категорія: Витратні предмети\n"
            f"📦 У цьому стакі: ×{quantity}/{max_stack}\n"
            "🔄 Одноразовий предмет\n\n"
            "Сфера накопичує силу переродження та дозволяє повністю скинути "
            "розподілені очки характеристик без зміни класу. Після використання "
            "всі розподілені очки повертаються у вільний баланс для повторного розподілу.\n\n"
            f"⭐ Зараз можна повернути: {preview['returned_points']} очок\n"
            f"📌 Вільних після скидання: {preview['free_after']}\n\n"
            "ℹ️ Використання недоступне, якщо немає розподілених очок, "
            "та під час активної несумісної взаємодії. Сфера не списується до остаточного підтвердження."
        )
    return (text, keyboard, *result[2:])

