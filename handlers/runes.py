from telebot import types

from db import (
    get_equipment_rune_slot_info,
    get_rune_insertion_preview,
    get_user_inventory_rune_stacks,
    get_user_rune_slot_equipment,
    insert_rune_into_equipment,
)
from keyboards import craft_kb, rune_master_kb

ITEMS_PER_PAGE = 8


def _short_name(value, limit=38):
    value = str(value or "")
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def build_rune_master_home(user_id, page=0):
    equipment = get_user_rune_slot_equipment(user_id)
    available = [item for item in equipment if item["free"] > 0]
    page = max(0, int(page or 0))
    total_pages = max(1, (len(available) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = min(page, total_pages - 1)
    selected = available[page * ITEMS_PER_PAGE:(page + 1) * ITEMS_PER_PAGE]
    text = (
        "💠 Рунний Майстер\n\n"
        "Рунний Майстер вставляє руни характеристик у вільні слоти спорядження.\n\n"
        "⚠️ Після вставки руна закріплюється за предметом. "
        "Для майбутнього вилучення знадобиться Екстрактор рун.\n\n"
        f"📄 Сторінка: {page + 1}/{total_pages}\n"
        # ROM 17.6.1 RUNE MOBILE MESSAGE WIDTH
        "Оберіть предмет спорядження для роботи з рунними слотами:"
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for item in selected:
        keyboard.add(types.InlineKeyboardButton(
            text=_short_name(
                f"{item['name']} [{item['used']}/{item['capacity']}]",
                52,
            ),
            callback_data=f"rm:eq:{item['inventory_id']}:{page}",
        ))
    navigation = []
    if page > 0:
        navigation.append(types.InlineKeyboardButton(
            text="⬅️", callback_data=f"rm:home:{page - 1}"
        ))
    if page + 1 < total_pages:
        navigation.append(types.InlineKeyboardButton(
            text="➡️", callback_data=f"rm:home:{page + 1}"
        ))
    if navigation:
        keyboard.row(*navigation)
    if not available:
        text += "\n\nℹ️ Немає спорядження з вільними рунними слотами."
    return text, keyboard


def build_slot_selection(user_id, equipment_inventory_id, page=0):
    info = get_equipment_rune_slot_info(user_id, equipment_inventory_id)
    if not info.get("success"):
        return info["message"], types.InlineKeyboardMarkup()
    text = (
        "💠 Рунний Майстер\n\n"
        f"⚔️ Спорядження: {info['name']}\n"
        f"📊 Рунні слоти: {info['used']}/{info['capacity']}\n\n"
        "Оберіть порожній слот:"
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for slot in info["slots"]:
        if slot["occupied"]:
            rune = slot["rune"]
            from data.runes import RUNE_LEVEL_ROMAN, RUNE_STAT_NAMES
            stat_name = RUNE_STAT_NAMES.get(rune["stat"], rune["stat"])
            level_name = RUNE_LEVEL_ROMAN.get(int(rune["level"]), str(rune["level"]))
            label = (
                f"🔒 Слот {slot['display_number']}: "
                f"Руна {stat_name} {level_name}"
            )
            keyboard.add(types.InlineKeyboardButton(text=label, callback_data="rm:locked"))
        else:
            keyboard.add(types.InlineKeyboardButton(
                text=f"▫️ Слот {slot['display_number']}: порожній",
                callback_data=(
                    f"rm:slot:{info['inventory_id']}:{slot['slot_index']}:{int(page)}"
                ),
            ))
    keyboard.add(types.InlineKeyboardButton(
        text="⬅️ До списку спорядження",
        callback_data=f"rm:home:{int(page)}",
    ))
    return text, keyboard


def build_rune_selection(user_id, equipment_inventory_id, slot_index, page=0):
    info = get_equipment_rune_slot_info(user_id, equipment_inventory_id)
    if not info.get("success"):
        return info["message"], types.InlineKeyboardMarkup()
    if not 0 <= int(slot_index) < info["capacity"]:
        return "❌ Рунний слот не існує.", types.InlineKeyboardMarkup()
    runes = get_user_inventory_rune_stacks(user_id)
    text = (
        "💠 Вибір руни\n\n"
        f"⚔️ Спорядження: {info['name']}\n"
        f"▫️ Слот: {int(slot_index) + 1}/{info['capacity']}\n\n"
        "Оберіть руну, яку потрібно вставити у вибраний слот:"
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for rune in runes:
        quantity = "" if rune["quantity"] == 1 else f" ×{rune['quantity']}"
        keyboard.add(types.InlineKeyboardButton(
            text=_short_name(f"{rune['name']}{quantity}", 52),
            callback_data=(
                f"rm:rune:{equipment_inventory_id}:{int(slot_index)}:"
                f"{rune['inventory_id']}:{int(page)}"
            ),
        ))
    if not runes:
        text += "\n\nℹ️ В інвентарі немає рун характеристик."
    keyboard.add(types.InlineKeyboardButton(
        text="⬅️ До слотів",
        callback_data=f"rm:eq:{equipment_inventory_id}:{int(page)}",
    ))
    return text, keyboard


def build_insertion_confirmation(user_id, equipment_inventory_id, slot_index, rune_inventory_id, page=0):
    preview = get_rune_insertion_preview(
        user_id, equipment_inventory_id, slot_index, rune_inventory_id
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if not preview.get("success"):
        keyboard.add(types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"rm:eq:{equipment_inventory_id}:{int(page)}",
        ))
        return preview["message"], keyboard
    text = (
        "💠 Підтвердження вставки\n\n"
        f"⚔️ Спорядження: {preview['equipment_name']}\n"
        f"▫️ Рунний слот: {preview['slot_number']}/{preview['capacity']}\n"
        f"💠 Руна: {preview['rune_name']}\n"
        f"📈 Бонус після екіпірування: +{preview['bonus']} до "
        f"{__import__('data.runes', fromlist=['RUNE_STAT_NAMES']).RUNE_STAT_NAMES.get(preview['stat'], preview['stat'])}\n\n"
        "⚠️ Руна буде списана з інвентаря та закріплена за предметом. "
        "Звичайне вилучення або заміна поки недоступні. Бонус діє лише на екіпірованому незламаному предметі."
    )
    keyboard.add(types.InlineKeyboardButton(
        text="✅ Вставити руну",
        callback_data=(
            f"rm:confirm:{equipment_inventory_id}:{int(slot_index)}:"
            f"{rune_inventory_id}:{int(page)}"
        ),
    ))
    keyboard.add(types.InlineKeyboardButton(
        text="❌ Скасувати",
        callback_data=f"rm:eq:{equipment_inventory_id}:{int(page)}",
    ))
    return text, keyboard


def register_rune_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == "💠 Рунний Майстер")
    def show_rune_master(message):
        bot.send_message(
            message.chat.id,
            (
                "💠 Рунний Майстер\n\n"
                "Оберіть потрібну дію:\n"
                "• вставити руну у спорядження;\n"
                "• переробити 3 однакові руни за 1 Жетон Фіріуса."
            ),
            reply_markup=rune_master_kb(),
        )

    @bot.message_handler(func=lambda message: message.text == "💠 Вставити руну")
    def show_rune_insertion(message):
        text, keyboard = build_rune_master_home(message.from_user.id)
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

    @bot.message_handler(func=lambda message: message.text == "🔄 Переробити руни")
    def show_rune_fusion(message):
        text, keyboard = build_rune_fusion_home(message.from_user.id, 0)
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("rm:"))
    def rune_master_callback(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        action = parts[1] if len(parts) > 1 else ""
        bot.answer_callback_query(call.id)
        try:
            if action == "locked":
                bot.answer_callback_query(call.id, "Цей слот уже зайнятий.", show_alert=True)
                return
            if action == "home":
                text, keyboard = build_rune_master_home(user_id, int(parts[2]))
            elif action == "eq":
                text, keyboard = build_slot_selection(user_id, int(parts[2]), int(parts[3]))
            elif action == "slot":
                text, keyboard = build_rune_selection(
                    user_id, int(parts[2]), int(parts[3]), int(parts[4])
                )
            elif action == "rune":
                text, keyboard = build_insertion_confirmation(
                    user_id, int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
                )
            elif action == "confirm":
                result = insert_rune_into_equipment(
                    user_id, int(parts[2]), int(parts[3]), int(parts[4])
                )
                if result.get("success"):
                    text = result["message"]
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton(
                        text="⬅️ До спорядження",
                        callback_data=f"rm:home:{int(parts[5])}",
                    ))
                else:
                    text = result.get("message", "❌ Не вдалося вставити руну.")
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton(
                        text="⬅️ До Рунного Майстра",
                        callback_data="rm:home:0",
                    ))
            else:
                text, keyboard = build_rune_master_home(user_id)
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard,
            )
        except Exception:
            bot.send_message(
                call.message.chat.id,
                "❌ Стан меню змінився. Відкрийте Рунного Майстра ще раз.",
                reply_markup=craft_kb(),
            )

# ==============================
# ROM 10.8.0 RUNE FUSION UI
# ==============================

_RUNE_FUSION_BASE_HOME_10_8_0 = build_rune_master_home


def build_rune_master_home(user_id, page=0):
    """Insertion flow only; fusion is opened from the dedicated reply menu."""
    return _RUNE_FUSION_BASE_HOME_10_8_0(user_id, page)


def build_rune_fusion_home(user_id, page=0):
    from db import get_available_rune_fusion_recipes, get_firius_token_quantity

    recipes = get_available_rune_fusion_recipes(user_id)
    tokens = get_firius_token_quantity(user_id)
    page = max(0, int(page or 0))
    total_pages = max(1, (len(recipes) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = min(page, total_pages - 1)
    selected = recipes[page * ITEMS_PER_PAGE:(page + 1) * ITEMS_PER_PAGE]
    text = (
        "🔄 Переробка рун\n\n"
        f"🪙 Жетони Фіріуса: {tokens}\n\n"
        "Рецепт:\n"
        "3 однакові руни одного типу й рівня + 1 Жетон Фіріуса "
        "→ 1 руна наступного рівня.\n\n"
        "Шанс успіху: 100%.\n"
        f"📄 Сторінка: {page + 1}/{total_pages}\n\n"
        "Оберіть доступний рецепт для переробки рун:"
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for recipe in selected:
        keyboard.add(types.InlineKeyboardButton(
            text=_short_name(
                f"{recipe['source_name']} ×3 → {recipe['result_name']}", 58
            ),
            callback_data=f"rf:preview:{recipe['source_item_id']}:{page}",
        ))
    if not recipes:
        text += "\n\nℹ️ Немає рун, яких зібрано щонайменше 3 однакові."
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton(
            text="⬅️", callback_data=f"rf:home:{page - 1}"
        ))
    if page + 1 < total_pages:
        nav.append(types.InlineKeyboardButton(
            text="➡️", callback_data=f"rf:home:{page + 1}"
        ))
    if nav:
        keyboard.row(*nav)
    return text, keyboard


def build_rune_fusion_confirmation(user_id, source_item_id, page=0):
    from db import get_rune_fusion_preview

    preview = get_rune_fusion_preview(user_id, source_item_id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if not preview.get("success"):
        keyboard.add(types.InlineKeyboardButton(
            text="⬅️ До рецептів", callback_data=f"rf:home:{int(page)}"
        ))
        return preview["message"], keyboard
    text = (
        "🔄 Підтвердження переробки\n\n"
        "Витрачається:\n"
        f"• {preview['source_name']} ×3\n"
        "• 🪙 Жетон Фіріуса ×1\n\n"
        "Результат:\n"
        f"• {preview['result_name']} ×1\n\n"
        "Шанс успіху: 100%."
    )
    keyboard.add(types.InlineKeyboardButton(
        text="✅ Переробити",
        callback_data=f"rf:confirm:{int(source_item_id)}:{int(page)}",
    ))
    keyboard.add(types.InlineKeyboardButton(
        text="❌ Скасувати", callback_data=f"rf:home:{int(page)}"
    ))
    return text, keyboard


def register_rune_fusion_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("rf:"))
    def rune_fusion_callback(call):
        from db import fuse_runes_with_firius_token

        user_id = call.from_user.id
        parts = call.data.split(":")
        action = parts[1] if len(parts) > 1 else "home"
        bot.answer_callback_query(call.id)
        try:
            if action == "home":
                text, keyboard = build_rune_fusion_home(user_id, int(parts[2]))
            elif action == "preview":
                text, keyboard = build_rune_fusion_confirmation(
                    user_id, int(parts[2]), int(parts[3])
                )
            elif action == "confirm":
                result = fuse_runes_with_firius_token(user_id, int(parts[2]))
                text = result.get("message", "❌ Не вдалося переробити руни.")
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(types.InlineKeyboardButton(
                    text="🔄 До переробки", callback_data=f"rf:home:{int(parts[3])}"
                ))
            else:
                text, keyboard = build_rune_fusion_home(user_id, 0)
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard,
            )
        except Exception:
            bot.send_message(
                call.message.chat.id,
                "❌ Стан переробки змінився. Відкрийте Рунного Майстра ще раз.",
                reply_markup=craft_kb(),
            )

# ==============================
# ROM 10.9.0 EQUIPMENT-FIRST EXTRACTOR UI
# ==============================
def build_extractor_home(user_id,page=0):
    from db import get_extractor_equipment,get_extractor_material_counts
    items=get_extractor_equipment(user_id); counts=get_extractor_material_counts(user_id)
    page=max(0,int(page or 0)); pages=max(1,(len(items)+ITEMS_PER_PAGE-1)//ITEMS_PER_PAGE);page=min(page,pages-1)
    text=("🧰 Екстрактор рун\n\nСпочатку оберіть зняте спорядження зі вставленими рунами. "
          "Після цього оберіть тип Екстрактора.\n\nДоступні матеріали:\n"
          f"• 🧰 Простий Екстрактор рун: {counts['simple']}\n"
          f"• ✨ Досконалий Екстрактор рун: {counts['perfect']}\n\n"
          f"📄 Сторінка: {page+1}/{pages}\nОберіть знятий предмет спорядження зі вставленими рунами:")
    kb=types.InlineKeyboardMarkup(row_width=1)
    for item in items[page*ITEMS_PER_PAGE:(page+1)*ITEMS_PER_PAGE]:
        kb.add(types.InlineKeyboardButton(text=_short_name(f"{item['name']} [рун: {item['rune_count']}]",56),
                                          callback_data=f"re:item:{item['inventory_id']}:{page}"))
    if not items:text+="\n\nℹ️ Немає знятого спорядження зі вставленими рунами."
    return text,kb


def build_extractor_type_selection(user_id,equipment_id,page=0):
    from db import get_extractor_preview
    preview=get_extractor_preview(user_id,equipment_id);kb=types.InlineKeyboardMarkup(row_width=1)
    if not preview.get('success'):
        kb.add(types.InlineKeyboardButton(text="⬅️ До спорядження",callback_data=f"re:home:{int(page)}"));return preview['message'],kb
    runes='\n'.join(f"• {r['name']}" for r in preview['runes']);c=preview['materials']
    text=(f"🧰 Вибір Екстрактора\n\nСпорядження:\n• {preview['equipment_name']}\n\nВставлені руни:\n{runes}\n\n"
          "Оберіть, який матеріал використати:\n\n"
          f"🧰 Простий Екстрактор рун: {c['simple']}\n• повертає 1 випадкову руну;\n• решта рун втратиться;\n• спорядження знищується.\n\n"
          f"✨ Досконалий Екстрактор рун: {c['perfect']}\n• повертає всі руни;\n• спорядження знищується.")
    kb.add(types.InlineKeyboardButton(text=f"🧰 Використати простий ×{c['simple']}",callback_data=f"re:simple:{equipment_id}:{int(page)}"))
    kb.add(types.InlineKeyboardButton(text=f"✨ Використати досконалий ×{c['perfect']}",callback_data=f"re:perfect:{equipment_id}:{int(page)}"))
    kb.add(types.InlineKeyboardButton(text="❌ Скасувати",callback_data=f"re:home:{int(page)}"));return text,kb


def build_simple_extractor_confirmation(user_id,equipment_id,page=0):
    from db import get_extractor_preview
    p=get_extractor_preview(user_id,equipment_id);kb=types.InlineKeyboardMarkup(row_width=1)
    if not p.get('success'):
        kb.add(types.InlineKeyboardButton(text="⬅️ До спорядження",callback_data=f"re:home:{int(page)}"));return p['message'],kb
    runes='\n'.join(f"• {r['name']}" for r in p['runes'])
    text=(f"⚠️ Просте вилучення рун\n\nСпорядження:\n• {p['equipment_name']}\n\nВставлені руни:\n{runes}\n\n"
          "Буде використано:\n• 🧰 Простий Екстрактор рун ×1\n\n"
          "Наслідки:\n• повернеться 1 випадкова руна;\n• спорядження буде знищено;\n• решта рун буде втрачена.\n\nЦю дію неможливо скасувати.")
    kb.add(types.InlineKeyboardButton(text="✅ Використати Простий Екстрактор",callback_data=f"re:confirm:{equipment_id}:{int(page)}"))
    kb.add(types.InlineKeyboardButton(text="⬅️ Змінити Екстрактор",callback_data=f"re:item:{equipment_id}:{int(page)}"));return text,kb


def register_simple_rune_extractor_handlers(bot):
    @bot.message_handler(func=lambda m:m.text=="🧰 Екстрактор")
    def show_extractor(message):
        text,kb=build_extractor_home(message.from_user.id,0);bot.send_message(message.chat.id,text,reply_markup=kb)
    @bot.callback_query_handler(func=lambda c:c.data.startswith('re:'))
    def extractor_callback(call):
        from db import use_simple_rune_extractor
        uid=call.from_user.id;parts=call.data.split(':');a=parts[1];bot.answer_callback_query(call.id)
        if a=='home':text,kb=build_extractor_home(uid,int(parts[2]))
        elif a=='item':text,kb=build_extractor_type_selection(uid,int(parts[2]),int(parts[3]))
        elif a=='simple':text,kb=build_simple_extractor_confirmation(uid,int(parts[2]),int(parts[3]))
        elif a=='perfect':
            text,kb=build_perfect_extractor_confirmation(uid,int(parts[2]),int(parts[3]))
        elif a=='perfect_confirm':
            from db import use_perfect_rune_extractor
            result=use_perfect_rune_extractor(uid,int(parts[2]));text=result.get('message','❌ Помилка досконалого вилучення.')
            kb=types.InlineKeyboardMarkup();kb.add(types.InlineKeyboardButton(text="🧰 До спорядження",callback_data=f"re:home:{int(parts[3])}"))
        elif a=='confirm':
            result=use_simple_rune_extractor(uid,int(parts[2]));text=result.get('message','❌ Помилка вилучення.')
            kb=types.InlineKeyboardMarkup();kb.add(types.InlineKeyboardButton(text="🧰 До спорядження",callback_data=f"re:home:{int(parts[3])}"))
        else:text,kb=build_extractor_home(uid,0)
        bot.edit_message_text(text,call.message.chat.id,call.message.message_id,reply_markup=kb)

# ==============================
# ROM 10.10.0 PERFECT RUNE EXTRACTOR UI
# ==============================


def build_perfect_extractor_confirmation(user_id, equipment_id, page=0):
    from db import get_extractor_preview

    preview = get_extractor_preview(user_id, equipment_id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if not preview.get("success"):
        keyboard.add(types.InlineKeyboardButton(
            text="⬅️ До спорядження",
            callback_data=f"re:home:{int(page)}",
        ))
        return preview["message"], keyboard

    if int(preview["materials"].get("perfect", 0) or 0) < 1:
        keyboard.add(types.InlineKeyboardButton(
            text="⬅️ Змінити Екстрактор",
            callback_data=f"re:item:{int(equipment_id)}:{int(page)}",
        ))
        return (
            "❌ В інвентарі немає Досконалого Екстрактора рун.\n\n"
            "Матеріал, спорядження та вставлені руни не змінено.",
            keyboard,
        )

    rune_lines = "\n".join(
        f"• {rune['name']}" for rune in preview["runes"]
    )
    text = (
        "⚠️ Досконале вилучення рун\n\n"
        f"Спорядження:\n• {preview['equipment_name']}\n\n"
        f"Вставлені руни:\n{rune_lines}\n\n"
        "Буде використано:\n"
        "• ✨ Досконалий Екстрактор рун ×1\n\n"
        "Наслідки:\n"
        "• усі вставлені руни повернуться в інвентар;\n"
        "• предмет спорядження буде знищено;\n"
        "• жодна вставлена руна не буде втрачена.\n\n"
        "Цю дію неможливо скасувати."
    )
    keyboard.add(types.InlineKeyboardButton(
        text="✅ Використати Досконалий Екстрактор",
        callback_data=f"re:perfect_confirm:{int(equipment_id)}:{int(page)}",
    ))
    keyboard.add(types.InlineKeyboardButton(
        text="⬅️ Змінити Екстрактор",
        callback_data=f"re:item:{int(equipment_id)}:{int(page)}",
    ))
    return text, keyboard

# ==============================
# ROM 10.13.0 RUNE MASTER SHOP UI
# ==============================

_RUNE_MASTER_SHOP_QUANTITY_STATE_10_13_0 = {}
_RUNE_MASTER_SHOP_NAVIGATION_TEXTS_10_13_0 = {
    "💠 Вставити руну", "🔄 Переробити руни", "🧰 Екстрактор",
    "🛒 Крамниця", "🔙 Ремісничий квартал",
}


def _clear_rune_master_shop_quantity_state_10_13_0(user_id):
    _RUNE_MASTER_SHOP_QUANTITY_STATE_10_13_0.pop(int(user_id), None)


def build_rune_master_shop(user_id):
    from db import get_rune_master_shop_state
    state = get_rune_master_shop_state(user_id)
    text = (
        "🛒 Крамниця Рунного Майстра\n\n"
        f"💰 Золото: {state['gold']:g}\n\n"
        "🧰 Простий Екстрактор рун\n"
        f"Ціна за 1: {state['simple_price']:g} золота\n"
        f"У сумці: {state['simple_owned']}\n\n"
        "Простий Екстрактор повертає одну випадкову вставлену руну, "
        "але знищує спорядження та решту вставлених рун.\n\n"
        "✨ Досконалий Екстрактор рун\n"
        f"У сумці: {state['perfect_owned']}\n"
        "Придбання за кристали буде додано в майбутньому."
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(
        text=f"🧰 Купити 1 за {state['simple_price']:g} золота",
        callback_data="rs:buy:1",
    ))
    keyboard.add(types.InlineKeyboardButton(
        text="🔢 Вказати кількість", callback_data="rs:quantity",
    ))
    keyboard.add(types.InlineKeyboardButton(
        text="🔄 Оновити", callback_data="rs:home",
    ))
    return text, keyboard


def build_rune_master_shop_quantity_prompt(user_id):
    from db import get_rune_master_shop_state
    state = get_rune_master_shop_state(user_id)
    price = float(state["simple_price"])
    affordable = min(100, int(float(state["gold"]) // price)) if price > 0 else 100
    return (
        "🧰 Купівля Простого Екстрактора\n\n"
        f"Ціна за 1: {price:g} золота\n"
        f"Доступно золота: {state['gold']:g}\n"
        f"Максимально можна придбати зараз: {affordable}\n\n"
        "Введіть потрібну кількість цілим числом від 1 до 100."
    )


def build_rune_master_shop_confirmation(user_id, quantity):
    from db import get_rune_master_shop_state
    state = get_rune_master_shop_state(user_id)
    quantity = int(quantity)
    unit_price = float(state["simple_price"])
    total_price = round(unit_price * quantity, 2)
    remaining = round(float(state["gold"]) - total_price, 2)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(
        text=f"✅ Купити {quantity}", callback_data=f"rs:confirm:{quantity}",
    ))
    keyboard.add(types.InlineKeyboardButton(
        text="❌ Скасувати", callback_data="rs:home",
    ))
    return (
        "🧰 Підтвердження покупки\n\n"
        "Предмет:\n• Простий Екстрактор рун\n\n"
        f"Кількість: {quantity}\n"
        f"Ціна за 1: {unit_price:g} золота\n"
        f"Загальна ціна: {total_price:g} золота\n"
        f"Після покупки залишиться: {remaining:g} золота",
        keyboard,
    )


def register_rune_master_shop_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == "🛒 Крамниця")
    def show_rune_master_shop(message):
        _clear_rune_master_shop_quantity_state_10_13_0(message.from_user.id)
        text, keyboard = build_rune_master_shop(message.from_user.id)
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("rs:"))
    def rune_master_shop_callback(call):
        # ROM 10.13.1 SHOP REFRESH NO-OP GUARD
        from db import buy_simple_rune_extractor
        user_id = call.from_user.id
        parts = call.data.split(":")
        action = parts[1] if len(parts) > 1 else "home"
        bot.answer_callback_query(call.id)
        if action == "quantity":
            _RUNE_MASTER_SHOP_QUANTITY_STATE_10_13_0[int(user_id)] = True
            bot.send_message(
                call.message.chat.id,
                build_rune_master_shop_quantity_prompt(user_id),
                reply_markup=rune_master_kb(),
            )
            return
        _clear_rune_master_shop_quantity_state_10_13_0(user_id)
        if action in ("buy", "confirm"):
            result = buy_simple_rune_extractor(user_id, int(parts[2]))
            shop_text, keyboard = build_rune_master_shop(user_id)
            text = result.get("message", "❌ Не вдалося виконати покупку.") + "\n\n" + shop_text
        else:
            text, keyboard = build_rune_master_shop(user_id)
        try:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard,
            )
        except Exception as error:
            # Telegram returns HTTP 400 when Refresh produces exactly the same
            # text and inline keyboard. This is a successful no-op, not a bot error.
            if "message is not modified" not in str(error).lower():
                raise

    @bot.message_handler(func=lambda message: (
        int(message.from_user.id) in _RUNE_MASTER_SHOP_QUANTITY_STATE_10_13_0
        and message.text not in _RUNE_MASTER_SHOP_NAVIGATION_TEXTS_10_13_0
    ))
    def rune_master_shop_quantity_input(message):
        from db import get_rune_master_shop_state
        user_id = int(message.from_user.id)
        try:
            quantity = int(str(message.text or "").strip())
        except Exception:
            bot.send_message(message.chat.id, "❌ Введіть ціле число від 1 до 100.", reply_markup=rune_master_kb())
            return
        if quantity < 1 or quantity > 100:
            bot.send_message(message.chat.id, "❌ Введіть ціле число від 1 до 100.", reply_markup=rune_master_kb())
            return
        state = get_rune_master_shop_state(user_id)
        total_price = round(float(state["simple_price"]) * quantity, 2)
        if float(state["gold"]) + 1e-9 < total_price:
            affordable = min(100, int(float(state["gold"]) // float(state["simple_price"])))
            bot.send_message(
                message.chat.id,
                "❌ Недостатньо золота.\n\n"
                f"Кількість: {quantity}\n"
                f"Загальна ціна: {total_price:g} золота\n"
                f"Доступно: {state['gold']:g} золота\n"
                f"Максимально можна придбати: {affordable}",
                reply_markup=rune_master_kb(),
            )
            return
        _clear_rune_master_shop_quantity_state_10_13_0(user_id)
        text, keyboard = build_rune_master_shop_confirmation(user_id, quantity)
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

