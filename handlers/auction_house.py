# ROM 17.11.2 COMPACT TEXT LOCATION DESCRIPTION
# ROM 17.10.1 ITEM QUANTITY DISPLAY FORMAT
# ROM 17.9.1 GLOBAL PAGINATION BUTTON LABELS
import json

from telebot import types


# ==============================
# ROM 11.4.1 AUCTION EQUIPMENT TYPE DISPLAY
# ==============================

def _auction_equipment_typed_name_11_4_1(inventory_id, name):
    """Apply canonical armor type to auction list/prompt/confirmation names."""
    from db import get_item_classification_by_inventory_id, get_armor_type_label, is_armor_slot

    display_name = str(name or "Предмет")
    try:
        classification = get_item_classification_by_inventory_id(int(inventory_id)) or {}
        slot_key = classification.get("slot_key", "")
        armor_type = classification.get("armor_type", "")
        if not is_armor_slot(slot_key) or not armor_type:
            return display_name
        label = get_armor_type_label(armor_type)
        if not label or f"[{label}]" in display_name:
            return display_name
        marker = " рівня"
        if marker in display_name:
            index = display_name.rfind(marker)
            before = display_name[:index]
            after = display_name[index:]
            parts = before.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].isdigit():
                return f"{parts[0]} [{label}] {parts[1]}{after}"
        return f"{display_name} [{label}]"
    except Exception:
        return display_name


def _auction_snapshot_typed_name_11_4_1(snapshot):
    return _auction_equipment_typed_name_11_4_1(
        snapshot.get("inventory_id"), snapshot.get("name")
    )

def _auction_lot_typed_name_17_1_0(lot):
    """Use [armor type] only for armor slots; never type weapons or jewelry."""
    # ROM 17.4.4.1 AUCTION ARMOR-ONLY LOT DISPLAY NAME
    try:
        name = str(lot["item_name"] or "Предмет")
        if str(lot["category"] or "") != "equipment":
            return name

        raw = lot["item_snapshot_json"]
        snapshot = json.loads(raw) if isinstance(raw, str) and raw else (raw or {})
        if not isinstance(snapshot, dict):
            return name

        from data.equipment_profiles import ARMOR_TYPE_LABELS, ITEM_SUBTYPE_LABELS

        slot_key = str(snapshot.get("slot_key") or "").strip().lower()
        armor_type = str(snapshot.get("armor_type") or "").strip().lower()
        item_subtype = str(snapshot.get("item_subtype") or "").strip().lower()
        armor_slots = frozenset((
            "helmet", "shoulders", "chest", "gloves", "legs", "boots",
        ))

        # Normalize display-only artifacts from older formatters. The stored lot
        # name and snapshot are never mutated.
        known_labels = set()
        if armor_type:
            known_labels.add(str(ARMOR_TYPE_LABELS.get(armor_type) or armor_type).strip())
        if item_subtype:
            known_labels.add(str(ITEM_SUBTYPE_LABELS.get(item_subtype) or item_subtype).strip())

        if slot_key not in armor_slots:
            for label in known_labels:
                if label:
                    name = name.replace(f" [{label}]", "")
            return name

        if not armor_type:
            return name
        armor_label = str(ARMOR_TYPE_LABELS.get(armor_type) or armor_type).strip()
        if not armor_label:
            return name

        # Remove an obsolete subtype token before applying the armor-only token.
        for label in known_labels:
            if label and label != armor_label:
                name = name.replace(f" [{label}]", "")

        typed_token = f"[{armor_label}]"
        if typed_token.casefold() in name.casefold():
            return name

        marker = " рівня"
        if marker in name:
            index = name.rfind(marker)
            before, after = name[:index], name[index:]
            parts = before.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].isdigit():
                return f"{parts[0]} {typed_token} {parts[1]}{after}"
        return f"{name} {typed_token}"
    except Exception:
        try:
            return str(lot["item_name"] or "Предмет")
        except Exception:
            return "Предмет"


# ✅ AUCTION HOUSE POTION BUTTON CONFLICT FIX V1
# Кнопка категорії зілля в Торговому Домі не має збігатися з бойовою кнопкою "🧪 Зілля".
# Інакше бойовий handler перехоплює кнопку і відповідає: "❗ Ти не в бою".

import re

from db import (
    init_auction_house,
    get_auction_house_stats,
    update_expired_auction_lots,
)

try:
    from keyboards import city_kb
except Exception:
    city_kb = None

try:
    from keyboards import main_kb
except Exception:
    main_kb = None


AUCTION_MENU_BUTTON = "🏛️ Торговий дім"
AUCTION_BUY_BUTTON = "🛒 Купити"
AUCTION_SELL_BUTTON = "➕ Виставити товар"
AUCTION_MY_LOTS_BUTTON = "📦 Мої лоти"
AUCTION_UNCLAIMED_ITEMS_BUTTON = "📬 Незабрані предмети"
AUCTION_SOLD_BUTTON = "💰 Завершені продажі"
AUCTION_HISTORY_BUTTON = "📜 Історія"
AUCTION_BACK_TO_CITY_BUTTON = "🔙 Місто"


# ==============================
# KEYBOARDS
# ==============================

def auction_house_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Основні дії Торгового Дому згруповані по 2 кнопки в ряд.
    # 🔙 Місто завжди окремо і останньою кнопкою внизу.
    kb.add(AUCTION_BUY_BUTTON, AUCTION_SELL_BUTTON)
    kb.add(AUCTION_MY_LOTS_BUTTON, AUCTION_UNCLAIMED_ITEMS_BUTTON)
    kb.add(AUCTION_SOLD_BUTTON, AUCTION_HISTORY_BUTTON)
    kb.add(AUCTION_BACK_TO_CITY_BUTTON)

    return kb

def get_city_reply_keyboard():
    if city_kb:
        try:
            return city_kb()
        except Exception:
            pass

    if main_kb:
        try:
            return main_kb()
        except Exception:
            pass

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🏙️ Місто")
    return kb


# ==============================
# TEXT BUILDERS
# ==============================

def build_auction_house_text(user_id):
    init_auction_house()
    cleanup = update_expired_auction_lots()
    stats = get_auction_house_stats()

    active = int(stats.get("ACTIVE", 0) or 0)
    sold_unclaimed = int(stats.get("SOLD_UNCLAIMED", 0) or 0)
    expired_unclaimed = int(stats.get("EXPIRED_UNCLAIMED", 0) or 0)

    text = (
        "🏛️ Торговий дім\n\n"
        "Тут гравці можуть виставляти товари на продаж, купувати предмети інших героїв "
        "і поступово формувати ринкову економіку світу.\n\n"
        "Доступні дії:\n"
        "• 🛒 Купити — перегляд активних лотів.\n"
        "• ➕ Виставити товар — продати предмет іншому гравцю.\n"
        "• 📦 Мої лоти — твої активні продажі.\n"
        "• 📬 Незабрані предмети — лоти, термін яких завершився.\n"
        "• 💰 Завершені продажі — забрати золото за продані товари.\n"
        "• 📜 Історія — історія операцій.\n\n"
        "ℹ️ Правила:\n"
        "• Активний лот існує 7 днів.\n"
        "• Незабрані предмети та золото зберігаються 30 днів.\n"
        "• Максимум активних лотів: 20.\n"
        "• Мінімальна ціна: 1.0 золота.\n"
        "• Максимальна ціна: 999999.0 золота.\n\n"
        "📊 Поточний стан ринку:\n"
        f"• Активні лоти: {active}\n"
        f"• Продані, золото не забране: {sold_unclaimed}\n"
        f"• Завершені, предмети не забрані: {expired_unclaimed}\n"
    )

    if cleanup.get("expired") or cleanup.get("deleted"):
        text += (
            "\n🧹 Оновлення ринку:\n"
            f"• Завершено лотів: {cleanup.get('expired', 0)}\n"
            f"• Видалено прострочених записів: {cleanup.get('deleted', 0)}\n"
        )

    return text


def build_auction_placeholder_text(title, description):
    return (
        f"{title}\n\n"
        f"{description}\n\n"
        "Цей розділ буде реалізовано в наступних етапах Торгового Дому 8.0.\n\n"
        "Поточний етап 8.0.2 додав головне меню та підключив ядро БД."
    )


# ==============================
# HANDLER REGISTRATION
# ==============================

def register_auction_house_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_MENU_BUTTON)
    def show_auction_house(message):
        user_id = message.from_user.id
        bot.send_message(
            message.chat.id,
            build_auction_house_text(user_id),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_BACK_TO_CITY_BUTTON)
    def auction_back_to_city(message):
        bot.send_message(
            message.chat.id,
            "🏙️ Ти повернувся до міста.",
            reply_markup=get_city_reply_keyboard()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_BUY_BUTTON)
    def auction_buy_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "🛒 Купити",
                "Тут буде перегляд активних лотів, фільтри, сортування та пошук."
            ),
            reply_markup=auction_house_kb()
        )

    def auction_sell_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "➕ Виставити товар",
                "Тут буде вибір категорії, предмета, кількості для стеків, ціни та підтвердження лота."
            ),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_MY_LOTS_BUTTON)
    def auction_my_lots_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "📦 Мої лоти",
                "Тут будуть активні лоти гравця, пагінація і зняття з продажу."
            ),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_UNCLAIMED_ITEMS_BUTTON)
    def auction_unclaimed_items_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "📬 Незабрані предмети",
                "Тут будуть предмети з лотів, термін яких завершився, але які ще можна забрати."
            ),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_SOLD_BUTTON)
    def auction_sold_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "💰 Завершені продажі",
                "Тут буде золото за продані лоти, яке продавець має забрати вручну."
            ),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_HISTORY_BUTTON)
    def auction_history_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "📜 Історія",
                "Тут буде історія купівлі, продажу, зняття лотів і майбутня статистика цін."
            ),
            reply_markup=auction_house_kb()
        )


# ==============================
# ✅ AUCTION HOUSE SELL EQUIPMENT V1
# ==============================

AUCTION_SELL_STATE = {}
AUCTION_SELL_PAGE_SIZE = 8

AUCTION_EQUIPMENT_CATEGORY_BUTTON = "⚔️ Спорядження"
AUCTION_BACK_TO_MENU_BUTTON = "🔙 Торговий дім"
AUCTION_CANCEL_BUTTON = "❌ Скасувати"
AUCTION_CONFIRM_LIST_BUTTON = "✅ Виставити"
AUCTION_PREV_SELL_ITEMS_BUTTON = "⬅️ Попередні предмети"
AUCTION_NEXT_SELL_ITEMS_BUTTON = "➡️ Наступні предмети"


def clear_auction_sell_state(user_id):
    AUCTION_SELL_STATE.pop(user_id, None)


def auction_sell_category_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(AUCTION_EQUIPMENT_CATEGORY_BUTTON)
    kb.add(AUCTION_BACK_TO_MENU_BUTTON)
    return kb


def auction_sell_items_kb(user_id, page=0):
    from db import get_user_sellable_equipment_for_auction

    page = max(0, int(page or 0))
    offset = page * AUCTION_SELL_PAGE_SIZE
    items = get_user_sellable_equipment_for_auction(
        user_id=user_id,
        limit=AUCTION_SELL_PAGE_SIZE + 1,
        offset=offset
    )

    visible_items = items[:AUCTION_SELL_PAGE_SIZE]
    has_next = len(items) > AUCTION_SELL_PAGE_SIZE

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for item in visible_items:
        durability = ""
        if item.get("durability_current") is not None:
            durability = f" [{item.get('durability_current')}/{item.get('durability_max')}]"

        typed_name = _auction_equipment_typed_name_11_4_1(item['inventory_id'], item['name'])
        button_text = f"📦 #{item['inventory_id']} {typed_name}{durability}"

        # Telegram buttons can be large, but keep it reasonable.
        if len(button_text) > 90:
            button_text = button_text[:87] + "..."

        kb.add(button_text)

    nav = []
    if page > 0:
        nav.append(AUCTION_PREV_SELL_ITEMS_BUTTON)
    if has_next:
        nav.append(AUCTION_NEXT_SELL_ITEMS_BUTTON)
    if nav:
        kb.add(*nav)

    kb.add(AUCTION_BACK_TO_MENU_BUTTON)
    return kb, visible_items, has_next


def build_auction_sell_start_text():
    return (
        "➕ Виставити товар\n\n"
        "Оберіть категорію товару, який хочете виставити на продаж.\n\n"
        "На цьому етапі доступне виставлення тільки спорядження.\n\n"
        "Правила для спорядження:\n"
        "• предмет не має бути екіпірований;\n"
        "• міцність має бути більше 0;\n"
        "• після виставлення предмет зникає з інвентаря;\n"
        "• активний лот існує 7 днів;\n"
        "• ціна від 1.0 до 999999.0 золота."
    )


def build_auction_sell_item_list_text(user_id, page=0):
    kb, items, has_next = auction_sell_items_kb(user_id, page=page)

    text = (
        "⚔️ Виставлення спорядження\n\n"
        f"Сторінка: {int(page) + 1}\n\n"
    )

    if not items:
        text += (
            "Немає доступного спорядження для продажу.\n\n"
            "Не можна виставити екіпіровані або зламані предмети."
        )
        return text, kb

    text += (
        "Оберіть предмет кнопкою нижче.\n\n"
        "Після вибору потрібно буде ввести ціну лота."
    )

    return text, kb


def build_auction_sell_price_prompt(snapshot):
    durability = f"{snapshot.get('durability_current')}/{snapshot.get('durability_max')}"

    return (
        "💰 Введення ціни\n\n"
        f"📦 {_auction_snapshot_typed_name_11_4_1(snapshot)}\n"
        f"🔧 Міцність: {durability}\n\n"
        "Введіть ціну лота у золоті.\n"
        "Приклади:\n"
        "• 10\n"
        "• 25.5\n"
        "• 100.75\n\n"
        "Мінімальна ціна: 1.0\n"
        "Максимальна ціна: 999999.0"
    )


def build_auction_sell_confirm_text(snapshot, price):
    durability = f"{snapshot.get('durability_current')}/{snapshot.get('durability_max')}"

    return (
        "📦 Новий лот\n\n"
        f"{_auction_snapshot_typed_name_11_4_1(snapshot)}\n\n"
        f"🔧 Міцність: {durability}\n"
        f"💰 Ціна: {price} золота\n"
        "⏳ Термін: 7 днів\n\n"
        "Після виставлення предмет буде перенесено з інвентаря до Торгового Дому.\n"
        "Його не можна буде вдягти, продати NPC, відремонтувати або заточити, доки лот активний.\n\n"
        "Виставити цей предмет?"
    )


def auction_sell_confirm_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(AUCTION_CONFIRM_LIST_BUTTON)
    kb.add(AUCTION_CANCEL_BUTTON, AUCTION_BACK_TO_MENU_BUTTON)
    return kb


def _auction_parse_inventory_id_from_button(text):
    match = re.search(r"#(\d+)", text or "")
    if not match:
        return None
    return int(match.group(1))


def _auction_register_sell_equipment_handlers(bot):

    def auction_sell_start_v1(message):
        user_id = message.from_user.id
        AUCTION_SELL_STATE[user_id] = {
            "step": "category",
            "page": 0,
        }

        bot.send_message(
            message.chat.id,
            build_auction_sell_start_text(),
            reply_markup=auction_sell_category_kb()
        )

    @bot.message_handler(func=lambda m: m.from_user.id in AUCTION_SELL_STATE)
    def auction_sell_state_router_v1(message):
        user_id = message.from_user.id
        text = message.text or ""
        state = AUCTION_SELL_STATE.get(user_id) or {}
        step = state.get("step")

        if text == AUCTION_BACK_TO_MENU_BUTTON:
            clear_auction_sell_state(user_id)
            bot.send_message(
                message.chat.id,
                build_auction_house_text(user_id),
                reply_markup=auction_house_kb()
            )
            return

        if text == AUCTION_CANCEL_BUTTON:
            clear_auction_sell_state(user_id)
            bot.send_message(
                message.chat.id,
                "❌ Виставлення товару скасовано.",
                reply_markup=auction_house_kb()
            )
            return

        if step == "category":
            if text != AUCTION_EQUIPMENT_CATEGORY_BUTTON:
                bot.send_message(
                    message.chat.id,
                    "Оберіть категорію кнопкою нижче.",
                    reply_markup=auction_sell_category_kb()
                )
                return

            state["step"] = "item"
            state["page"] = 0
            AUCTION_SELL_STATE[user_id] = state
            list_text, kb = build_auction_sell_item_list_text(user_id, page=0)
            bot.send_message(message.chat.id, list_text, reply_markup=kb)
            return

        if step == "item":
            page = int(state.get("page", 0) or 0)

            if text == AUCTION_NEXT_SELL_ITEMS_BUTTON:
                page += 1
                state["page"] = page
                AUCTION_SELL_STATE[user_id] = state
                list_text, kb = build_auction_sell_item_list_text(user_id, page=page)
                bot.send_message(message.chat.id, list_text, reply_markup=kb)
                return

            if text == AUCTION_PREV_SELL_ITEMS_BUTTON:
                page = max(0, page - 1)
                state["page"] = page
                AUCTION_SELL_STATE[user_id] = state
                list_text, kb = build_auction_sell_item_list_text(user_id, page=page)
                bot.send_message(message.chat.id, list_text, reply_markup=kb)
                return

            inventory_id = _auction_parse_inventory_id_from_button(text)
            if not inventory_id:
                bot.send_message(
                    message.chat.id,
                    "Оберіть предмет кнопкою нижче.",
                    reply_markup=auction_sell_items_kb(user_id, page=page)[0]
                )
                return

            from db import get_inventory_item_snapshot_for_auction, validate_inventory_item_for_auction_equipment

            validation = validate_inventory_item_for_auction_equipment(user_id, inventory_id)
            if not validation.get("success"):
                bot.send_message(
                    message.chat.id,
                    validation.get("message", "❌ Предмет не можна виставити."),
                    reply_markup=auction_sell_items_kb(user_id, page=page)[0]
                )
                return

            snapshot = validation["snapshot"]
            state["step"] = "price"
            state["inventory_id"] = inventory_id
            state["snapshot"] = snapshot
            AUCTION_SELL_STATE[user_id] = state

            bot.send_message(
                message.chat.id,
                build_auction_sell_price_prompt(snapshot),
                reply_markup=types.ReplyKeyboardRemove()
            )
            return

        if step == "price":
            from db import validate_auction_price

            price_result = validate_auction_price(text)
            if not price_result.get("success"):
                bot.send_message(
                    message.chat.id,
                    price_result.get("message", "❌ Некоректна ціна.") + "\n\nСпробуйте ще раз або напишіть ❌ Скасувати.",
                    reply_markup=auction_sell_confirm_kb()
                )
                return

            state["step"] = "confirm"
            state["price"] = price_result["price"]
            AUCTION_SELL_STATE[user_id] = state

            bot.send_message(
                message.chat.id,
                build_auction_sell_confirm_text(state["snapshot"], price_result["price"]),
                reply_markup=auction_sell_confirm_kb()
            )
            return

        if step == "confirm":
            if text != AUCTION_CONFIRM_LIST_BUTTON:
                bot.send_message(
                    message.chat.id,
                    "Підтвердіть виставлення або скасуйте дію.",
                    reply_markup=auction_sell_confirm_kb()
                )
                return

            from db import create_equipment_auction_lot

            result = create_equipment_auction_lot(
                user_id=user_id,
                inventory_id=state.get("inventory_id"),
                price=state.get("price"),
            )

            clear_auction_sell_state(user_id)

            if not result.get("success"):
                bot.send_message(
                    message.chat.id,
                    result.get("message", "❌ Не вдалося створити лот."),
                    reply_markup=auction_house_kb()
                )
                return

            bot.send_message(
                message.chat.id,
                (
                    "✅ Лот виставлено на продаж!\n\n"
                    f"📦 {result.get('item_name')}\n"
                    f"💰 Ціна: {result.get('price')} золота\n"
                    "⏳ Термін: 7 днів\n\n"
                    "Предмет перенесено з інвентаря до Торгового Дому."
                ),
                reply_markup=auction_house_kb()
            )
            return

        # Unknown state fallback.
        clear_auction_sell_state(user_id)
        bot.send_message(
            message.chat.id,
            "ℹ️ Стан виставлення товару скинуто.",
            reply_markup=auction_house_kb()
        )


# Extend existing registrar without replacing the base menu handlers.
try:
    _auction_base_register_handlers_before_sell_equipment_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_sell_equipment_v1 = None


def register_auction_house_handlers(bot):
    # Важливо: handler для ➕ Виставити товар має реєструватися ДО placeholder-ів 8.0.2.
    # Інакше старий placeholder перехоплює кнопку раніше за реальний flow 8.0.3.
    _auction_register_sell_equipment_handlers(bot)

    if _auction_base_register_handlers_before_sell_equipment_v1:
        _auction_base_register_handlers_before_sell_equipment_v1(bot)


# ==============================
# ✅ AUCTION HOUSE SELL STACK ITEMS V2
# ==============================

AUCTION_SELL_STATE_V2 = {}
AUCTION_STACK_CATEGORY_POTION_BUTTON = "🧪 Зілля для продажу"
AUCTION_STACK_CATEGORY_MATERIAL_BUTTON = "🪨 Матеріали"
AUCTION_SELL_CATEGORY_LABELS = {
    AUCTION_EQUIPMENT_CATEGORY_BUTTON: "equipment",
    AUCTION_STACK_CATEGORY_POTION_BUTTON: "potion",
    AUCTION_STACK_CATEGORY_MATERIAL_BUTTON: "material",
}


def clear_auction_sell_state_v2(user_id):
    AUCTION_SELL_STATE_V2.pop(user_id, None)
    try:
        clear_auction_sell_state(user_id)
    except Exception:
        pass


def auction_sell_category_kb_v2():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(AUCTION_EQUIPMENT_CATEGORY_BUTTON, AUCTION_STACK_CATEGORY_POTION_BUTTON)
    kb.add(AUCTION_STACK_CATEGORY_MATERIAL_BUTTON)
    kb.add(AUCTION_BACK_TO_MENU_BUTTON)
    return kb


def build_auction_sell_start_text_v2():
    return (
        "➕ Виставити товар\n\n"
        "Оберіть категорію товару, який хочете виставити на продаж.\n\n"
        "Доступно зараз:\n"
        "• ⚔️ Спорядження — зброя, броня, щити, біжутерія.\n"
        "• 🧪 Зілля для продажу — стекові предмети, можна виставляти частинами.\n"
        "• 🪨 Матеріали — камені та матеріали, можна виставляти частинами.\n\n"
        "Обмеження:\n"
        "• 💎 Руну Успіху не можна продавати через Торговий Дім.\n"
        "• Екіпіровані та зламані предмети не можна виставляти.\n"
        "• Активний лот існує 7 днів.\n"
        "• Максимум активних лотів: 20."
    )


def auction_stack_items_kb_v2(user_id, category, page=0):
    from db import get_user_sellable_stack_items_for_auction

    page = max(0, int(page or 0))
    offset = page * AUCTION_SELL_PAGE_SIZE
    items = get_user_sellable_stack_items_for_auction(
        user_id=user_id,
        category=category,
        limit=AUCTION_SELL_PAGE_SIZE + 1,
        offset=offset,
    )

    visible_items = items[:AUCTION_SELL_PAGE_SIZE]
    has_next = len(items) > AUCTION_SELL_PAGE_SIZE

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for item in visible_items:
        button_text = f"📦 #{item['inventory_id']} {item['name']} ×{item['quantity']}"
        if len(button_text) > 90:
            button_text = button_text[:87] + "..."
        kb.add(button_text)

    nav = []
    if page > 0:
        nav.append(AUCTION_PREV_SELL_ITEMS_BUTTON)
    if has_next:
        nav.append(AUCTION_NEXT_SELL_ITEMS_BUTTON)
    if nav:
        kb.add(*nav)

    kb.add(AUCTION_BACK_TO_MENU_BUTTON)
    return kb, visible_items, has_next


def build_auction_stack_item_list_text_v2(user_id, category, page=0):
    kb, items, has_next = auction_stack_items_kb_v2(user_id, category, page=page)

    title = "🧪 Виставлення зілля" if category == "potion" else "🪨 Виставлення матеріалів"

    text = (
        f"{title}\n\n"
        f"Сторінка: {int(page) + 1}\n\n"
    )

    if not items:
        text += "Немає доступних предметів у цій категорії для продажу."
        return text, kb

    text += (
        "Оберіть предмет кнопкою нижче.\n\n"
        "Після вибору потрібно буде вказати кількість і ціну лота."
    )

    return text, kb


def build_auction_stack_quantity_prompt_v2(snapshot, category):
    return (
        "🔢 Вкажіть кількість\n\n"
        f"📦 {snapshot['name']}\n"
        f"📦 У наявності: {snapshot.get('quantity', 0)}\n\n"
        "Введіть кількість, яку хочете виставити на продаж."
    )


def build_auction_stack_price_prompt_v2(snapshot, quantity):
    return (
        "💰 Введення ціни\n\n"
        f"📦 {snapshot['name']} ×{quantity}\n\n"
        "Введіть ціну за весь лот у золоті.\n"
        "Приклади:\n"
        "• 10\n"
        "• 25.5\n"
        "• 100.75\n\n"
        "Мінімальна ціна: 1.0\n"
        "Максимальна ціна: 999999.0"
    )


def build_auction_stack_confirm_text_v2(snapshot, quantity, price):
    return (
        "📦 Новий лот\n\n"
        f"{snapshot['name']} ×{quantity}\n\n"
        f"💰 Ціна: {price} золота\n"
        "⏳ Термін: 7 днів\n\n"
        "Після виставлення ця кількість буде перенесена з інвентаря до Торгового Дому.\n\n"
        "Виставити цей лот?"
    )


def _auction_open_item_list_v2(bot, message, user_id, category, page=0):
    state = AUCTION_SELL_STATE_V2.get(user_id) or {}
    state["step"] = "item"
    state["category"] = category
    state["page"] = page
    AUCTION_SELL_STATE_V2[user_id] = state

    if category == "equipment":
        list_text, kb = build_auction_sell_item_list_text(user_id, page=page)
    else:
        list_text, kb = build_auction_stack_item_list_text_v2(user_id, category, page=page)

    bot.send_message(message.chat.id, list_text, reply_markup=kb)


def _auction_register_sell_all_handlers_v2(bot):

    def auction_sell_start_v2(message):
        user_id = message.from_user.id
        clear_auction_sell_state_v2(user_id)
        AUCTION_SELL_STATE_V2[user_id] = {
            "step": "category",
            "page": 0,
        }

        bot.send_message(
            message.chat.id,
            build_auction_sell_start_text_v2(),
            reply_markup=auction_sell_category_kb_v2(),
        )

    @bot.message_handler(func=lambda m: m.from_user.id in AUCTION_SELL_STATE_V2)
    def auction_sell_state_router_v2(message):
        user_id = message.from_user.id
        text = message.text or ""
        state = AUCTION_SELL_STATE_V2.get(user_id) or {}
        step = state.get("step")

        if text == AUCTION_BACK_TO_MENU_BUTTON:
            clear_auction_sell_state_v2(user_id)
            bot.send_message(
                message.chat.id,
                build_auction_house_text(user_id),
                reply_markup=auction_house_kb(),
            )
            return

        if text == AUCTION_CANCEL_BUTTON:
            clear_auction_sell_state_v2(user_id)
            bot.send_message(
                message.chat.id,
                "❌ Виставлення товару скасовано.",
                reply_markup=auction_house_kb(),
            )
            return

        if step == "category":
            if text not in AUCTION_SELL_CATEGORY_LABELS:
                bot.send_message(
                    message.chat.id,
                    "Оберіть категорію кнопкою нижче.",
                    reply_markup=auction_sell_category_kb_v2(),
                )
                return

            category = AUCTION_SELL_CATEGORY_LABELS[text]
            _auction_open_item_list_v2(bot, message, user_id, category, page=0)
            return

        if step == "item":
            category = state.get("category", "equipment")
            page = int(state.get("page", 0) or 0)

            if text == AUCTION_NEXT_SELL_ITEMS_BUTTON:
                _auction_open_item_list_v2(bot, message, user_id, category, page=page + 1)
                return

            if text == AUCTION_PREV_SELL_ITEMS_BUTTON:
                _auction_open_item_list_v2(bot, message, user_id, category, page=max(0, page - 1))
                return

            inventory_id = _auction_parse_inventory_id_from_button(text)
            if not inventory_id:
                _auction_open_item_list_v2(bot, message, user_id, category, page=page)
                return

            if category == "equipment":
                from db import validate_inventory_item_for_auction_equipment

                validation = validate_inventory_item_for_auction_equipment(user_id, inventory_id)
                if not validation.get("success"):
                    bot.send_message(
                        message.chat.id,
                        validation.get("message", "❌ Предмет не можна виставити."),
                        reply_markup=auction_sell_items_kb(user_id, page=page)[0],
                    )
                    return

                snapshot = validation["snapshot"]
                state.update({
                    "step": "price",
                    "category": category,
                    "inventory_id": inventory_id,
                    "snapshot": snapshot,
                    "quantity": 1,
                })
                AUCTION_SELL_STATE_V2[user_id] = state

                bot.send_message(
                    message.chat.id,
                    build_auction_sell_price_prompt(snapshot),
                    reply_markup=types.ReplyKeyboardRemove(),
                )
                return

            from db import get_inventory_item_snapshot_for_auction

            snapshot_result = get_inventory_item_snapshot_for_auction(user_id, inventory_id)
            if not snapshot_result.get("success"):
                bot.send_message(
                    message.chat.id,
                    snapshot_result.get("message", "❌ Предмет не знайдено."),
                    reply_markup=auction_stack_items_kb_v2(user_id, category, page=page)[0],
                )
                return

            snapshot = snapshot_result["snapshot"]
            state.update({
                "step": "quantity",
                "category": category,
                "inventory_id": inventory_id,
                "snapshot": snapshot,
            })
            AUCTION_SELL_STATE_V2[user_id] = state

            bot.send_message(
                message.chat.id,
                build_auction_stack_quantity_prompt_v2(snapshot, category),
                reply_markup=types.ReplyKeyboardRemove(),
            )
            return

        if step == "quantity":
            category = state.get("category")
            inventory_id = state.get("inventory_id")
            snapshot = state.get("snapshot") or {}

            try:
                quantity = int(text)
            except Exception:
                bot.send_message(message.chat.id, "❌ Введіть кількість числом.")
                return

            from db import validate_inventory_stack_item_for_auction

            validation = validate_inventory_stack_item_for_auction(
                user_id=user_id,
                inventory_id=inventory_id,
                category=category,
                quantity=quantity,
            )
            if not validation.get("success"):
                bot.send_message(message.chat.id, validation.get("message", "❌ Некоректна кількість."))
                return

            snapshot = validation["snapshot"]
            state.update({
                "step": "price",
                "quantity": quantity,
                "snapshot": snapshot,
            })
            AUCTION_SELL_STATE_V2[user_id] = state

            bot.send_message(
                message.chat.id,
                build_auction_stack_price_prompt_v2(snapshot, quantity),
                reply_markup=types.ReplyKeyboardRemove(),
            )
            return

        if step == "price":
            from db import validate_auction_price

            price_result = validate_auction_price(text)
            if not price_result.get("success"):
                bot.send_message(
                    message.chat.id,
                    price_result.get("message", "❌ Некоректна ціна.") + "\n\nСпробуйте ще раз або напишіть ❌ Скасувати.",
                    reply_markup=auction_sell_confirm_kb(),
                )
                return

            state["step"] = "confirm"
            state["price"] = price_result["price"]
            AUCTION_SELL_STATE_V2[user_id] = state

            if state.get("category") == "equipment":
                confirm_text = build_auction_sell_confirm_text(state["snapshot"], price_result["price"])
            else:
                confirm_text = build_auction_stack_confirm_text_v2(
                    state["snapshot"],
                    state.get("quantity", 1),
                    price_result["price"],
                )

            bot.send_message(message.chat.id, confirm_text, reply_markup=auction_sell_confirm_kb())
            return

        if step == "confirm":
            if text != AUCTION_CONFIRM_LIST_BUTTON:
                bot.send_message(
                    message.chat.id,
                    "Підтвердіть виставлення або скасуйте дію.",
                    reply_markup=auction_sell_confirm_kb(),
                )
                return

            category = state.get("category")

            if category == "equipment":
                from db import create_equipment_auction_lot
                result = create_equipment_auction_lot(
                    user_id=user_id,
                    inventory_id=state.get("inventory_id"),
                    price=state.get("price"),
                )
            else:
                from db import create_stack_auction_lot
                result = create_stack_auction_lot(
                    user_id=user_id,
                    inventory_id=state.get("inventory_id"),
                    category=category,
                    quantity=state.get("quantity"),
                    price=state.get("price"),
                )

            clear_auction_sell_state_v2(user_id)

            if not result.get("success"):
                bot.send_message(
                    message.chat.id,
                    result.get("message", "❌ Не вдалося створити лот."),
                    reply_markup=auction_house_kb(),
                )
                return

            quantity_text = ""
            if int(result.get("quantity", 1) or 1) > 1:
                quantity_text = f" x{result.get('quantity')}"

            bot.send_message(
                message.chat.id,
                (
                    "✅ Лот виставлено на продаж!\n\n"
                    f"📦 {result.get('item_name')}{quantity_text}\n"
                    f"💰 Ціна: {result.get('price')} золота\n"
                    "⏳ Термін: 7 днів\n\n"
                    "Предмет перенесено з інвентаря до Торгового Дому."
                ),
                reply_markup=auction_house_kb(),
            )
            return

        clear_auction_sell_state_v2(user_id)
        bot.send_message(
            message.chat.id,
            "ℹ️ Стан виставлення товару скинуто.",
            reply_markup=auction_house_kb(),
        )


try:
    _auction_base_register_handlers_before_stack_listing_v2 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_stack_listing_v2 = None


def register_auction_house_handlers(bot):
    # V2 має бути першим, щоб реальний flow перехоплював ➕ Виставити товар до старих placeholder-ів.
    _auction_register_sell_all_handlers_v2(bot)

    if _auction_base_register_handlers_before_stack_listing_v2:
        _auction_base_register_handlers_before_stack_listing_v2(bot)


# ==============================
# ✅ AUCTION HOUSE BUY LOT UI V1
# ==============================

AUCTION_BUY_STATE = {}
AUCTION_BUY_PAGE_SIZE = 8
AUCTION_LOT_BACK_BUTTON = "🔙 Назад до лотів"
AUCTION_CONFIRM_BUY_BUTTON = "✅ Купити"
AUCTION_CANCEL_BUY_BUTTON = "❌ Назад"
AUCTION_NEXT_LOTS_BUTTON = "➡️ Наступні лоти"
AUCTION_PREV_LOTS_BUTTON = "⬅️ Попередні лоти"


def clear_auction_buy_state(user_id):
    AUCTION_BUY_STATE.pop(user_id, None)


def _auction_parse_lot_id_from_button(text):
    match = re.search(r"#(\d+)", text or "")
    if not match:
        return None
    return int(match.group(1))


def auction_buy_lots_kb(user_id, page=0):
    from db import get_public_auction_lots_for_buyer

    page = max(0, int(page or 0))
    offset = page * AUCTION_BUY_PAGE_SIZE
    lots = get_public_auction_lots_for_buyer(
        user_id=user_id,
        limit=AUCTION_BUY_PAGE_SIZE + 1,
        offset=offset,
        sort="new",
    )

    visible_lots = lots[:AUCTION_BUY_PAGE_SIZE]
    has_next = len(lots) > AUCTION_BUY_PAGE_SIZE

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for lot in visible_lots:
        quantity = int(lot["quantity"] or 1)
        qty = f" ×{quantity}" if quantity > 1 and f"×{quantity}" not in lot["item_name"] else ""
        button_text = f"🛒 #{lot['id']} {lot['item_name']}{qty} — {lot['price']} 💰"
        if len(button_text) > 95:
            button_text = button_text[:92] + "..."
        kb.add(button_text)

    nav = []
    if page > 0:
        nav.append(AUCTION_PREV_LOTS_BUTTON)
    if has_next:
        nav.append(AUCTION_NEXT_LOTS_BUTTON)
    if nav:
        kb.add(*nav)

    kb.add(AUCTION_BACK_TO_MENU_BUTTON)
    return kb, visible_lots, has_next


def build_auction_buy_list_text(user_id, page=0):
    kb, lots, has_next = auction_buy_lots_kb(user_id, page=page)

    text = (
        "🛒 Купити\n\n"
        f"Сторінка: {int(page) + 1}\n\n"
    )

    if not lots:
        text += "Активних лотів від інших гравців поки немає."
        return text, kb

    text += (
        "Оберіть лот кнопкою нижче.\n\n"
        "Продавець прихований.\n"
        "Після вибору буде показано деталі та підтвердження покупки."
    )

    return text, kb


def auction_lot_view_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(AUCTION_CONFIRM_BUY_BUTTON)
    kb.add(AUCTION_LOT_BACK_BUTTON, AUCTION_BACK_TO_MENU_BUTTON)
    return kb


def build_auction_buy_confirm_text(details_text):
    return (
        "⚠️ Підтвердження покупки\n\n"
        f"{details_text}\n\n"
        "Після покупки скасування неможливе.\n"
        "Якщо лот уже купив хтось інший, покупка не відбудеться."
    )


def _auction_register_buy_lot_handlers_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_BUY_BUTTON)
    def auction_buy_start_v1(message):
        user_id = message.from_user.id
        clear_auction_buy_state(user_id)
        AUCTION_BUY_STATE[user_id] = {
            "step": "list",
            "page": 0,
        }
        text, kb = build_auction_buy_list_text(user_id, page=0)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.from_user.id in AUCTION_BUY_STATE)
    def auction_buy_state_router_v1(message):
        user_id = message.from_user.id
        text = message.text or ""
        state = AUCTION_BUY_STATE.get(user_id) or {}
        step = state.get("step")

        if text == AUCTION_BACK_TO_MENU_BUTTON:
            clear_auction_buy_state(user_id)
            bot.send_message(
                message.chat.id,
                build_auction_house_text(user_id),
                reply_markup=auction_house_kb(),
            )
            return

        if step == "list":
            page = int(state.get("page", 0) or 0)

            if text == AUCTION_NEXT_LOTS_BUTTON:
                page += 1
                state["page"] = page
                AUCTION_BUY_STATE[user_id] = state
                list_text, kb = build_auction_buy_list_text(user_id, page=page)
                bot.send_message(message.chat.id, list_text, reply_markup=kb)
                return

            if text == AUCTION_PREV_LOTS_BUTTON:
                page = max(0, page - 1)
                state["page"] = page
                AUCTION_BUY_STATE[user_id] = state
                list_text, kb = build_auction_buy_list_text(user_id, page=page)
                bot.send_message(message.chat.id, list_text, reply_markup=kb)
                return

            lot_id = _auction_parse_lot_id_from_button(text)
            if not lot_id:
                list_text, kb = build_auction_buy_list_text(user_id, page=page)
                bot.send_message(message.chat.id, list_text, reply_markup=kb)
                return

            from db import build_auction_lot_public_details

            details = build_auction_lot_public_details(lot_id, viewer_user_id=user_id)
            if not details.get("success"):
                bot.send_message(
                    message.chat.id,
                    details.get("message", "⚠️ Лот недоступний."),
                    reply_markup=auction_buy_lots_kb(user_id, page=page)[0],
                )
                return

            state["step"] = "view"
            state["lot_id"] = lot_id
            AUCTION_BUY_STATE[user_id] = state

            bot.send_message(
                message.chat.id,
                details["text"],
                reply_markup=auction_lot_view_kb(),
            )
            return

        if step == "view":
            lot_id = state.get("lot_id")

            if text == AUCTION_LOT_BACK_BUTTON:
                state["step"] = "list"
                AUCTION_BUY_STATE[user_id] = state
                page = int(state.get("page", 0) or 0)
                list_text, kb = build_auction_buy_list_text(user_id, page=page)
                bot.send_message(message.chat.id, list_text, reply_markup=kb)
                return

            if text != AUCTION_CONFIRM_BUY_BUTTON:
                from db import build_auction_lot_public_details
                details = build_auction_lot_public_details(lot_id, viewer_user_id=user_id)
                if not details.get("success"):
                    clear_auction_buy_state(user_id)
                    bot.send_message(message.chat.id, details.get("message", "⚠️ Лот недоступний."), reply_markup=auction_house_kb())
                    return
                bot.send_message(message.chat.id, details["text"], reply_markup=auction_lot_view_kb())
                return

            from db import build_auction_lot_public_details
            details = build_auction_lot_public_details(lot_id, viewer_user_id=user_id)
            if not details.get("success"):
                clear_auction_buy_state(user_id)
                bot.send_message(message.chat.id, details.get("message", "⚠️ Лот недоступний."), reply_markup=auction_house_kb())
                return

            state["step"] = "confirm"
            AUCTION_BUY_STATE[user_id] = state
            bot.send_message(
                message.chat.id,
                build_auction_buy_confirm_text(details["text"]),
                reply_markup=auction_lot_view_kb(),
            )
            return

        if step == "confirm":
            lot_id = state.get("lot_id")

            if text in [AUCTION_CANCEL_BUY_BUTTON, AUCTION_LOT_BACK_BUTTON]:
                state["step"] = "view"
                AUCTION_BUY_STATE[user_id] = state
                from db import build_auction_lot_public_details
                details = build_auction_lot_public_details(lot_id, viewer_user_id=user_id)
                if details.get("success"):
                    bot.send_message(message.chat.id, details["text"], reply_markup=auction_lot_view_kb())
                else:
                    clear_auction_buy_state(user_id)
                    bot.send_message(message.chat.id, details.get("message", "⚠️ Лот недоступний."), reply_markup=auction_house_kb())
                return

            if text != AUCTION_CONFIRM_BUY_BUTTON:
                bot.send_message(message.chat.id, "Підтвердьте покупку або поверніться назад.", reply_markup=auction_lot_view_kb())
                return

            from db import buy_auction_lot

            result = buy_auction_lot(buyer_user_id=user_id, lot_id=lot_id)
            clear_auction_buy_state(user_id)

            if not result.get("success"):
                bot.send_message(
                    message.chat.id,
                    result.get("message", "❌ Не вдалося купити лот."),
                    reply_markup=auction_house_kb(),
                )
                return

            bot.send_message(
                message.chat.id,
                (
                    "✅ Покупку завершено!\n\n"
                    f"📦 {result.get('item_name')}\n"
                    f"💰 Сплачено: {result.get('price')} золота\n\n"
                    "Предмет додано в інвентар."
                ),
                reply_markup=auction_house_kb(),
            )
            return

        clear_auction_buy_state(user_id)
        bot.send_message(message.chat.id, "ℹ️ Стан покупки скинуто.", reply_markup=auction_house_kb())


try:
    _auction_base_register_handlers_before_buy_lot_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_buy_lot_v1 = None


def register_auction_house_handlers(bot):
    # Buy handler must be registered before old placeholder for 🛒 Купити.
    _auction_register_buy_lot_handlers_v1(bot)

    if _auction_base_register_handlers_before_buy_lot_v1:
        _auction_base_register_handlers_before_buy_lot_v1(bot)


# ==============================
# ✅ AUCTION HOUSE INLINE ITEM LISTS V1
# ==============================

# 8.0.5a
# Предмети у списках виставлення і покупки тепер показуються inline-кнопками.
# По 8 предметів/лотів на сторінку, навігація через inline-кнопки.

AUCTION_INLINE_PAGE_SIZE = 8
AUCTION_SELL_INLINE_STATE = {}
AUCTION_SELL_INLINE_CATEGORY_BUTTONS = {
    AUCTION_EQUIPMENT_CATEGORY_BUTTON: "equipment",
    globals().get("AUCTION_STACK_CATEGORY_POTION_BUTTON", "🧪 Зілля для продажу"): "potion",
    globals().get("AUCTION_STACK_CATEGORY_MATERIAL_BUTTON", "🪨 Матеріали"): "material",
}


def _auction_clear_all_sell_states_v1(user_id):
    AUCTION_SELL_INLINE_STATE.pop(user_id, None)

    for state_name in ["AUCTION_SELL_STATE", "AUCTION_SELL_STATE_V2"]:
        try:
            globals().get(state_name, {}).pop(user_id, None)
        except Exception:
            pass


def _auction_clear_all_buy_states_v1(user_id):
    try:
        AUCTION_BUY_STATE.pop(user_id, None)
    except Exception:
        pass


def _auction_inline_truncate(text, limit=58):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[:limit - 3] + "..."


# ==============================
# SELL INLINE LISTS
# ==============================

def auction_sell_inline_category_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(AUCTION_EQUIPMENT_CATEGORY_BUTTON, globals().get("AUCTION_STACK_CATEGORY_POTION_BUTTON", "🧪 Зілля для продажу"))
    kb.add(globals().get("AUCTION_STACK_CATEGORY_MATERIAL_BUTTON", "🪨 Матеріали"))
    kb.add(AUCTION_BACK_TO_MENU_BUTTON)
    return kb


def build_auction_sell_start_text_inline_v1():
    return (
        "➕ Виставити товар\n\n"
        "Оберіть категорію товару.\n\n"
        "Після вибору категорії предмети будуть показані inline-кнопками по 8 на сторінку.\n\n"
        "Доступно зараз:\n"
        "• ⚔️ Спорядження\n"
        "• 🧪 Зілля для продажу\n"
        "• 🪨 Матеріали\n\n"
        "Обмеження:\n"
        "• 💎 Руну Успіху не можна продавати через Торговий Дім.\n"
        "• Екіпіровані та зламані предмети не можна виставляти.\n"
        "• Максимум активних лотів: 20."
    )


def auction_sell_items_inline_kb_v1(user_id, category, page=0):
    page = max(0, int(page or 0))
    offset = page * AUCTION_INLINE_PAGE_SIZE

    if category == "equipment":
        from db import get_user_sellable_equipment_for_auction
        items = get_user_sellable_equipment_for_auction(
            user_id=user_id,
            limit=AUCTION_INLINE_PAGE_SIZE + 1,
            offset=offset,
        )
    else:
        from db import get_user_sellable_stack_items_for_auction
        items = get_user_sellable_stack_items_for_auction(
            user_id=user_id,
            category=category,
            limit=AUCTION_INLINE_PAGE_SIZE + 1,
            offset=offset,
        )

    visible_items = items[:AUCTION_INLINE_PAGE_SIZE]
    has_next = len(items) > AUCTION_INLINE_PAGE_SIZE

    kb = types.InlineKeyboardMarkup(row_width=1)

    for item in visible_items:
        if category == "equipment":
            durability = ""
            if item.get("durability_current") is not None:
                durability = f" [{item.get('durability_current')}/{item.get('durability_max')}]"
            typed_name = _auction_equipment_typed_name_11_4_1(item['inventory_id'], item['name'])
            label = f"📦 {typed_name}{durability}"
        else:
            label = f"📦 {item['name']} ×{item['quantity']}"

        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_sell_item:{category}:{item['inventory_id']}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"ah_sell_page:{category}:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Далі", callback_data=f"ah_sell_page:{category}:{page + 1}"))
    if nav:
        kb.row(*nav)

    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb, visible_items, has_next


def build_auction_sell_inline_list_text_v1(user_id, category, page=0):
    titles = {
        "equipment": "⚔️ Виставлення спорядження",
        "potion": "🧪 Виставлення зілля",
        "material": "🪨 Виставлення матеріалів",
    }

    kb, items, has_next = auction_sell_items_inline_kb_v1(user_id, category, page=page)
    text = f"{titles.get(category, '➕ Виставити товар')}\n\nСторінка: {int(page) + 1}\n\n"

    if not items:
        text += "Немає доступних предметів у цій категорії для продажу."
    else:
        text += "Оберіть предмет inline-кнопкою нижче."

    return text, kb


def _auction_register_sell_inline_handlers_v1(bot):

    def auction_sell_start_inline_v1(message):
        user_id = message.from_user.id
        _auction_clear_all_sell_states_v1(user_id)
        AUCTION_SELL_INLINE_STATE[user_id] = {
            "step": "category",
        }
        bot.send_message(
            message.chat.id,
            build_auction_sell_start_text_inline_v1(),
            reply_markup=auction_sell_inline_category_kb_v1(),
        )

    @bot.message_handler(func=lambda m: m.from_user.id in AUCTION_SELL_INLINE_STATE)
    def auction_sell_inline_state_message_v1(message):
        user_id = message.from_user.id
        text = message.text or ""
        state = AUCTION_SELL_INLINE_STATE.get(user_id) or {}
        step = state.get("step")

        if text == AUCTION_BACK_TO_MENU_BUTTON:
            _auction_clear_all_sell_states_v1(user_id)
            bot.send_message(message.chat.id, build_auction_house_text(user_id), reply_markup=auction_house_kb())
            return

        if text == AUCTION_CANCEL_BUTTON:
            _auction_clear_all_sell_states_v1(user_id)
            bot.send_message(message.chat.id, "❌ Виставлення товару скасовано.", reply_markup=auction_house_kb())
            return

        if step == "category":
            if text not in AUCTION_SELL_INLINE_CATEGORY_BUTTONS:
                bot.send_message(message.chat.id, "Оберіть категорію кнопкою нижче.", reply_markup=auction_sell_inline_category_kb_v1())
                return

            category = AUCTION_SELL_INLINE_CATEGORY_BUTTONS[text]
            state.update({"step": "item_inline", "category": category, "page": 0})
            AUCTION_SELL_INLINE_STATE[user_id] = state
            list_text, kb = build_auction_sell_inline_list_text_v1(user_id, category, page=0)
            bot.send_message(message.chat.id, list_text, reply_markup=kb)
            return

        if step == "quantity":
            category = state.get("category")
            inventory_id = state.get("inventory_id")

            try:
                quantity = int(text)
            except Exception:
                bot.send_message(message.chat.id, "❌ Введіть кількість числом.")
                return

            from db import validate_inventory_stack_item_for_auction
            validation = validate_inventory_stack_item_for_auction(
                user_id=user_id,
                inventory_id=inventory_id,
                category=category,
                quantity=quantity,
            )

            if not validation.get("success"):
                bot.send_message(message.chat.id, validation.get("message", "❌ Некоректна кількість."))
                return

            state.update({
                "step": "price",
                "quantity": quantity,
                "snapshot": validation["snapshot"],
            })
            AUCTION_SELL_INLINE_STATE[user_id] = state
            bot.send_message(message.chat.id, build_auction_stack_price_prompt_v2(validation["snapshot"], quantity), reply_markup=types.ReplyKeyboardRemove())
            return

        if step == "price":
            from db import validate_auction_price
            price_result = validate_auction_price(text)
            if not price_result.get("success"):
                bot.send_message(message.chat.id, price_result.get("message", "❌ Некоректна ціна.") + "\n\nСпробуйте ще раз або напишіть ❌ Скасувати.", reply_markup=auction_sell_confirm_kb())
                return

            state["step"] = "confirm"
            state["price"] = price_result["price"]
            AUCTION_SELL_INLINE_STATE[user_id] = state

            if state.get("category") == "equipment":
                confirm_text = build_auction_sell_confirm_text(state["snapshot"], price_result["price"])
            else:
                confirm_text = build_auction_stack_confirm_text_v2(state["snapshot"], state.get("quantity", 1), price_result["price"])

            bot.send_message(message.chat.id, confirm_text, reply_markup=auction_sell_confirm_kb())
            return

        if step == "confirm":
            if text != AUCTION_CONFIRM_LIST_BUTTON:
                bot.send_message(message.chat.id, "Підтвердіть виставлення або скасуйте дію.", reply_markup=auction_sell_confirm_kb())
                return

            category = state.get("category")

            if category == "equipment":
                from db import create_equipment_auction_lot
                result = create_equipment_auction_lot(
                    user_id=user_id,
                    inventory_id=state.get("inventory_id"),
                    price=state.get("price"),
                )
            else:
                from db import create_stack_auction_lot
                result = create_stack_auction_lot(
                    user_id=user_id,
                    inventory_id=state.get("inventory_id"),
                    category=category,
                    quantity=state.get("quantity"),
                    price=state.get("price"),
                )

            _auction_clear_all_sell_states_v1(user_id)

            if not result.get("success"):
                bot.send_message(message.chat.id, result.get("message", "❌ Не вдалося створити лот."), reply_markup=auction_house_kb())
                return

            bot.send_message(
                message.chat.id,
                (
                    "✅ Лот виставлено на продаж!\n\n"
                    f"📦 {result.get('item_name')}\n"
                    f"💰 Ціна: {result.get('price')} золота\n"
                    "⏳ Термін: 7 днів\n\n"
                    "Предмет перенесено з інвентаря до Торгового Дому."
                ),
                reply_markup=auction_house_kb(),
            )
            return

        _auction_clear_all_sell_states_v1(user_id)
        bot.send_message(message.chat.id, "ℹ️ Стан виставлення товару скинуто.", reply_markup=auction_house_kb())

    @bot.callback_query_handler(func=lambda call: call.data == "ah_menu")
    def auction_inline_menu_callback_v1(call):
        user_id = call.from_user.id
        _auction_clear_all_sell_states_v1(user_id)
        _auction_clear_all_buy_states_v1(user_id)
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        bot.send_message(call.message.chat.id, build_auction_house_text(user_id), reply_markup=auction_house_kb())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_sell_page:"))
    def auction_sell_inline_page_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        category = parts[1]
        page = int(parts[2])
        state = AUCTION_SELL_INLINE_STATE.get(user_id) or {}
        state.update({"step": "item_inline", "category": category, "page": page})
        AUCTION_SELL_INLINE_STATE[user_id] = state
        text, kb = build_auction_sell_inline_list_text_v1(user_id, category, page=page)
        try:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_sell_item:"))
    def auction_sell_inline_item_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        category = parts[1]
        inventory_id = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if category == "equipment":
            from db import validate_inventory_item_for_auction_equipment
            validation = validate_inventory_item_for_auction_equipment(user_id, inventory_id)
            if not validation.get("success"):
                text, kb = build_auction_sell_inline_list_text_v1(user_id, category, page=page)
                bot.send_message(call.message.chat.id, validation.get("message", "❌ Предмет не можна виставити."), reply_markup=auction_house_kb())
                bot.send_message(call.message.chat.id, text, reply_markup=kb)
                return

            snapshot = validation["snapshot"]
            AUCTION_SELL_INLINE_STATE[user_id] = {
                "step": "price",
                "category": category,
                "inventory_id": inventory_id,
                "snapshot": snapshot,
                "quantity": 1,
                "page": page,
            }
            bot.send_message(call.message.chat.id, build_auction_sell_price_prompt(snapshot), reply_markup=types.ReplyKeyboardRemove())
            return

        from db import get_inventory_item_snapshot_for_auction
        snapshot_result = get_inventory_item_snapshot_for_auction(user_id, inventory_id)
        if not snapshot_result.get("success"):
            text, kb = build_auction_sell_inline_list_text_v1(user_id, category, page=page)
            bot.send_message(call.message.chat.id, snapshot_result.get("message", "❌ Предмет не знайдено."), reply_markup=auction_house_kb())
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
            return

        snapshot = snapshot_result["snapshot"]
        AUCTION_SELL_INLINE_STATE[user_id] = {
            "step": "quantity",
            "category": category,
            "inventory_id": inventory_id,
            "snapshot": snapshot,
            "page": page,
        }
        bot.send_message(call.message.chat.id, build_auction_stack_quantity_prompt_v2(snapshot, category), reply_markup=types.ReplyKeyboardRemove())


# ==============================
# BUY INLINE LISTS
# ==============================

def auction_buy_lots_inline_kb_v1(user_id, page=0):
    from db import get_public_auction_lots_for_buyer

    page = max(0, int(page or 0))
    offset = page * AUCTION_INLINE_PAGE_SIZE
    lots = get_public_auction_lots_for_buyer(
        user_id=user_id,
        limit=AUCTION_INLINE_PAGE_SIZE + 1,
        offset=offset,
        sort="new",
    )

    visible_lots = lots[:AUCTION_INLINE_PAGE_SIZE]
    has_next = len(lots) > AUCTION_INLINE_PAGE_SIZE

    kb = types.InlineKeyboardMarkup(row_width=1)

    for lot in visible_lots:
        quantity = int(lot["quantity"] or 1)
        qty = f" ×{quantity}" if quantity > 1 and f"×{quantity}" not in lot["item_name"] else ""
        label = f"🛒 {_auction_lot_typed_name_17_1_0(lot)}{qty} — {lot['price']} 💰"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_buy_lot:{lot['id']}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"ah_buy_page:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Далі", callback_data=f"ah_buy_page:{page + 1}"))
    if nav:
        kb.row(*nav)

    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb, visible_lots, has_next


def build_auction_buy_inline_list_text_v1(user_id, page=0):
    kb, lots, has_next = auction_buy_lots_inline_kb_v1(user_id, page=page)
    text = f"🛒 Купити\n\nСторінка: {int(page) + 1}\n\n"

    if not lots:
        text += "Активних лотів від інших гравців поки немає."
    else:
        text += (
            "Оберіть лот inline-кнопкою нижче.\n\n"
            "Продавець прихований."
        )

    return text, kb


def auction_lot_inline_view_kb_v1(lot_id, page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Купити", callback_data=f"ah_buy_confirm:{lot_id}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад до лотів", callback_data=f"ah_buy_page:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb


def auction_lot_inline_confirm_kb_v1(lot_id, page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Підтвердити покупку", callback_data=f"ah_buy_execute:{lot_id}"))
    kb.add(types.InlineKeyboardButton("❌ Назад", callback_data=f"ah_buy_lot:{lot_id}:{page}"))
    return kb


def _auction_register_buy_inline_handlers_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_BUY_BUTTON)
    def auction_buy_start_inline_v1(message):
        user_id = message.from_user.id
        _auction_clear_all_buy_states_v1(user_id)
        text, kb = build_auction_buy_inline_list_text_v1(user_id, page=0)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_buy_page:"))
    def auction_buy_inline_page_callback_v1(call):
        user_id = call.from_user.id
        page = int(call.data.split(":")[1])
        text, kb = build_auction_buy_inline_list_text_v1(user_id, page=page)
        try:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_buy_lot:"))
    def auction_buy_inline_lot_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        from db import build_auction_lot_public_details
        details = build_auction_lot_public_details(lot_id, viewer_user_id=user_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            text, kb = build_auction_buy_inline_list_text_v1(user_id, page=page)
            bot.send_message(call.message.chat.id, details.get("message", "⚠️ Лот недоступний."), reply_markup=auction_house_kb())
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
            return

        try:
            bot.edit_message_text(details["text"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_lot_inline_view_kb_v1(lot_id, page=page))
        except Exception:
            bot.send_message(call.message.chat.id, details["text"], reply_markup=auction_lot_inline_view_kb_v1(lot_id, page=page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_buy_confirm:"))
    def auction_buy_inline_confirm_callback_v1(call):
        user_id = call.from_user.id
        lot_id = int(call.data.split(":")[1])

        from db import build_auction_lot_public_details
        details = build_auction_lot_public_details(lot_id, viewer_user_id=user_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            bot.send_message(call.message.chat.id, details.get("message", "⚠️ Лот недоступний."), reply_markup=auction_house_kb())
            return

        text = build_auction_buy_confirm_text(details["text"])
        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_lot_inline_confirm_kb_v1(lot_id))
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=auction_lot_inline_confirm_kb_v1(lot_id))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_buy_execute:"))
    def auction_buy_inline_execute_callback_v1(call):
        user_id = call.from_user.id
        lot_id = int(call.data.split(":")[1])

        from db import buy_auction_lot
        result = buy_auction_lot(buyer_user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not result.get("success"):
            bot.send_message(call.message.chat.id, result.get("message", "❌ Не вдалося купити лот."), reply_markup=auction_house_kb())
            return

        bot.send_message(
            call.message.chat.id,
            (
                "✅ Покупку завершено!\n\n"
                f"📦 {result.get('item_name')}\n"
                f"💰 Сплачено: {result.get('price')} золота\n\n"
                "Предмет додано в інвентар."
            ),
            reply_markup=auction_house_kb(),
        )


try:
    _auction_base_register_handlers_before_inline_lists_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_inline_lists_v1 = None


def register_auction_house_handlers(bot):
    # Inline handlers must be registered before previous reply-based/placeholder handlers.
    _auction_register_sell_inline_handlers_v1(bot)
    _auction_register_buy_inline_handlers_v1(bot)

    if _auction_base_register_handlers_before_inline_lists_v1:
        _auction_base_register_handlers_before_inline_lists_v1(bot)


# ==============================
# ✅ AUCTION HOUSE SELL REVIEW BEFORE PRICE V1
# ==============================

AUCTION_SELL_REVIEW_STATE = {}


def _auction_clear_sell_review_state_v1(user_id):
    AUCTION_SELL_REVIEW_STATE.pop(user_id, None)
    try:
        _auction_clear_all_sell_states_v1(user_id)
    except Exception:
        pass


def auction_sell_review_kb_v1(category, inventory_id, page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)

    if category == "equipment":
        kb.add(types.InlineKeyboardButton("💰 Ввести ціну", callback_data=f"ahsrp:{category}:{inventory_id}:{page}"))
    else:
        kb.add(types.InlineKeyboardButton("🔢 Вказати кількість", callback_data=f"ahsrq:{category}:{inventory_id}:{page}"))

    kb.add(types.InlineKeyboardButton("🔙 До списку предметів", callback_data=f"ah_sell_page:{category}:{page}"))
    kb.add(types.InlineKeyboardButton("❌ Скасувати", callback_data="ah_menu"))
    return kb


def _auction_send_sell_review_v1(bot, chat_id, user_id, inventory_id, category, page=0, edit_message=None):
    from db import build_auction_sell_item_review_text

    review = build_auction_sell_item_review_text(user_id=user_id, inventory_id=inventory_id, category=category)
    if not review.get("success"):
        text, kb = build_auction_sell_inline_list_text_v1(user_id, category, page=page)
        bot.send_message(chat_id, review.get("message", "❌ Предмет не можна виставити."), reply_markup=auction_house_kb())
        bot.send_message(chat_id, text, reply_markup=kb)
        return

    AUCTION_SELL_REVIEW_STATE[user_id] = {
        "step": "review",
        "category": category,
        "inventory_id": inventory_id,
        "snapshot": review.get("snapshot"),
        "page": page,
    }

    kb = auction_sell_review_kb_v1(category, inventory_id, page=page)

    if edit_message is not None:
        try:
            bot.edit_message_text(review["text"], chat_id=chat_id, message_id=edit_message.message_id, reply_markup=kb)
            return
        except Exception:
            pass

    bot.send_message(chat_id, review["text"], reply_markup=kb)


def _auction_register_sell_review_before_price_handlers_v1(bot):

    def auction_sell_start_review_v1(message):
        user_id = message.from_user.id
        _auction_clear_sell_review_state_v1(user_id)
        AUCTION_SELL_REVIEW_STATE[user_id] = {"step": "category"}
        bot.send_message(
            message.chat.id,
            build_auction_sell_start_text_inline_v1(),
            reply_markup=auction_sell_inline_category_kb_v1(),
        )

    @bot.message_handler(func=lambda m: m.from_user.id in AUCTION_SELL_REVIEW_STATE)
    def auction_sell_review_message_router_v1(message):
        user_id = message.from_user.id
        text = message.text or ""
        state = AUCTION_SELL_REVIEW_STATE.get(user_id) or {}
        step = state.get("step")

        if text == AUCTION_BACK_TO_MENU_BUTTON:
            _auction_clear_sell_review_state_v1(user_id)
            bot.send_message(message.chat.id, build_auction_house_text(user_id), reply_markup=auction_house_kb())
            return

        if text == AUCTION_CANCEL_BUTTON:
            _auction_clear_sell_review_state_v1(user_id)
            bot.send_message(message.chat.id, "❌ Виставлення товару скасовано.", reply_markup=auction_house_kb())
            return

        if step == "category":
            if text not in AUCTION_SELL_INLINE_CATEGORY_BUTTONS:
                bot.send_message(message.chat.id, "Оберіть категорію кнопкою нижче.", reply_markup=auction_sell_inline_category_kb_v1())
                return

            category = AUCTION_SELL_INLINE_CATEGORY_BUTTONS[text]
            state.update({"step": "item_inline", "category": category, "page": 0})
            AUCTION_SELL_REVIEW_STATE[user_id] = state
            list_text, kb = build_auction_sell_inline_list_text_v1(user_id, category, page=0)
            bot.send_message(message.chat.id, list_text, reply_markup=kb)
            return

        if step == "quantity":
            category = state.get("category")
            inventory_id = state.get("inventory_id")

            try:
                quantity = int(text)
            except Exception:
                bot.send_message(message.chat.id, "❌ Введіть кількість числом.")
                return

            from db import validate_inventory_stack_item_for_auction
            validation = validate_inventory_stack_item_for_auction(
                user_id=user_id,
                inventory_id=inventory_id,
                category=category,
                quantity=quantity,
            )

            if not validation.get("success"):
                bot.send_message(message.chat.id, validation.get("message", "❌ Некоректна кількість."))
                return

            state.update({
                "step": "price",
                "quantity": quantity,
                "snapshot": validation["snapshot"],
            })
            AUCTION_SELL_REVIEW_STATE[user_id] = state
            bot.send_message(message.chat.id, build_auction_stack_price_prompt_v2(validation["snapshot"], quantity), reply_markup=types.ReplyKeyboardRemove())
            return

        if step == "price":
            from db import validate_auction_price
            price_result = validate_auction_price(text)
            if not price_result.get("success"):
                bot.send_message(message.chat.id, price_result.get("message", "❌ Некоректна ціна.") + "\n\nСпробуйте ще раз або напишіть ❌ Скасувати.", reply_markup=auction_sell_confirm_kb())
                return

            state["step"] = "confirm"
            state["price"] = price_result["price"]
            AUCTION_SELL_REVIEW_STATE[user_id] = state

            if state.get("category") == "equipment":
                confirm_text = build_auction_sell_confirm_text(state["snapshot"], price_result["price"])
            else:
                confirm_text = build_auction_stack_confirm_text_v2(state["snapshot"], state.get("quantity", 1), price_result["price"])

            bot.send_message(message.chat.id, confirm_text, reply_markup=auction_sell_confirm_kb())
            return

        if step == "confirm":
            if text != AUCTION_CONFIRM_LIST_BUTTON:
                bot.send_message(message.chat.id, "Підтвердіть виставлення або скасуйте дію.", reply_markup=auction_sell_confirm_kb())
                return

            category = state.get("category")

            if category == "equipment":
                from db import create_equipment_auction_lot
                result = create_equipment_auction_lot(
                    user_id=user_id,
                    inventory_id=state.get("inventory_id"),
                    price=state.get("price"),
                )
            else:
                from db import create_stack_auction_lot
                result = create_stack_auction_lot(
                    user_id=user_id,
                    inventory_id=state.get("inventory_id"),
                    category=category,
                    quantity=state.get("quantity"),
                    price=state.get("price"),
                )

            _auction_clear_sell_review_state_v1(user_id)

            if not result.get("success"):
                bot.send_message(message.chat.id, result.get("message", "❌ Не вдалося створити лот."), reply_markup=auction_house_kb())
                return

            bot.send_message(
                message.chat.id,
                (
                    "✅ Лот виставлено на продаж!\n\n"
                    f"📦 {result.get('item_name')}\n"
                    f"💰 Ціна: {result.get('price')} золота\n"
                    "⏳ Термін: 7 днів\n\n"
                    "Предмет перенесено з інвентаря до Торгового Дому."
                ),
                reply_markup=auction_house_kb(),
            )
            return

        bot.send_message(message.chat.id, "Оберіть предмет зі списку або поверніться до Торгового Дому.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_sell_item:"))
    def auction_sell_review_item_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        category = parts[1]
        inventory_id = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        _auction_send_sell_review_v1(
            bot=bot,
            chat_id=call.message.chat.id,
            user_id=user_id,
            inventory_id=inventory_id,
            category=category,
            page=page,
            edit_message=call.message,
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ahsrp:"))
    def auction_sell_review_price_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        category = parts[1]
        inventory_id = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0

        from db import build_auction_sell_item_review_text
        review = build_auction_sell_item_review_text(user_id=user_id, inventory_id=inventory_id, category=category)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not review.get("success"):
            bot.send_message(call.message.chat.id, review.get("message", "❌ Предмет не можна виставити."), reply_markup=auction_house_kb())
            return

        AUCTION_SELL_REVIEW_STATE[user_id] = {
            "step": "price",
            "category": category,
            "inventory_id": inventory_id,
            "snapshot": review["snapshot"],
            "quantity": 1,
            "page": page,
        }
        bot.send_message(call.message.chat.id, build_auction_sell_price_prompt(review["snapshot"]), reply_markup=types.ReplyKeyboardRemove())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ahsrq:"))
    def auction_sell_review_quantity_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        category = parts[1]
        inventory_id = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0

        from db import build_auction_sell_item_review_text
        review = build_auction_sell_item_review_text(user_id=user_id, inventory_id=inventory_id, category=category)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not review.get("success"):
            bot.send_message(call.message.chat.id, review.get("message", "❌ Предмет не можна виставити."), reply_markup=auction_house_kb())
            return

        AUCTION_SELL_REVIEW_STATE[user_id] = {
            "step": "quantity",
            "category": category,
            "inventory_id": inventory_id,
            "snapshot": review["snapshot"],
            "page": page,
        }
        bot.send_message(call.message.chat.id, build_auction_stack_quantity_prompt_v2(review["snapshot"], category), reply_markup=types.ReplyKeyboardRemove())


try:
    _auction_base_register_handlers_before_sell_review_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_sell_review_v1 = None


def register_auction_house_handlers(bot):
    # Review handlers must be registered before previous sell inline handlers.
    _auction_register_sell_review_before_price_handlers_v1(bot)

    if _auction_base_register_handlers_before_sell_review_v1:
        _auction_base_register_handlers_before_sell_review_v1(bot)


# ==============================
# ✅ AUCTION HOUSE MY LOTS CANCEL UI V1
# ==============================

AUCTION_MY_LOTS_PAGE_SIZE = 8


def auction_my_lots_inline_kb_v1(user_id, page=0):
    from db import get_user_auction_lots

    page = max(0, int(page or 0))
    offset = page * AUCTION_MY_LOTS_PAGE_SIZE
    lots = get_user_auction_lots(
        user_id=user_id,
        status="ACTIVE",
        limit=AUCTION_MY_LOTS_PAGE_SIZE + 1,
        offset=offset,
    )

    visible_lots = lots[:AUCTION_MY_LOTS_PAGE_SIZE]
    has_next = len(lots) > AUCTION_MY_LOTS_PAGE_SIZE

    kb = types.InlineKeyboardMarkup(row_width=1)

    for lot in visible_lots:
        quantity = int(lot["quantity"] or 1)
        qty = f" ×{quantity}" if quantity > 1 and f"×{quantity}" not in lot["item_name"] else ""
        label = f"📦 {_auction_lot_typed_name_17_1_0(lot)}{qty} — {lot['price']} 💰"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_my_lot:{lot['id']}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"ah_my_page:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Далі", callback_data=f"ah_my_page:{page + 1}"))
    if nav:
        kb.row(*nav)

    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb, visible_lots, has_next


def build_auction_my_lots_text_v1(user_id, page=0):
    kb, lots, has_next = auction_my_lots_inline_kb_v1(user_id, page=page)
    text = f"📦 Мої лоти\n\nСторінка: {int(page) + 1}\n\n"

    if not lots:
        text += "У тебе немає активних лотів."
    else:
        text += (
            "Оберіть активний лот inline-кнопкою нижче.\n\n"
            "У картці лота можна зняти товар з продажу."
        )

    return text, kb


def auction_my_lot_view_kb_v1(lot_id, page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📥 Зняти з продажу", callback_data=f"ah_my_cancel_confirm:{lot_id}:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 До моїх лотів", callback_data=f"ah_my_page:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb


def auction_my_lot_cancel_confirm_kb_v1(lot_id, page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Підтвердити зняття", callback_data=f"ah_my_cancel_do:{lot_id}:{page}"))
    kb.add(types.InlineKeyboardButton("❌ Назад", callback_data=f"ah_my_lot:{lot_id}:{page}"))
    return kb


def _auction_register_my_lots_cancel_handlers_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_MY_LOTS_BUTTON)
    def auction_my_lots_start_v1(message):
        user_id = message.from_user.id
        text, kb = build_auction_my_lots_text_v1(user_id, page=0)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_my_page:"))
    def auction_my_lots_page_callback_v1(call):
        user_id = call.from_user.id
        page = int(call.data.split(":")[1])
        text, kb = build_auction_my_lots_text_v1(user_id, page=page)
        try:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_my_lot:"))
    def auction_my_lot_view_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        from db import build_user_auction_lot_details
        details = build_user_auction_lot_details(user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            text, kb = build_auction_my_lots_text_v1(user_id, page=page)
            bot.send_message(call.message.chat.id, details.get("message", "❌ Лот недоступний."), reply_markup=auction_house_kb())
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
            return

        try:
            bot.edit_message_text(details["text"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_my_lot_view_kb_v1(lot_id, page=page))
        except Exception:
            bot.send_message(call.message.chat.id, details["text"], reply_markup=auction_my_lot_view_kb_v1(lot_id, page=page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_my_cancel_confirm:"))
    def auction_my_lot_cancel_confirm_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        from db import build_user_auction_lot_details
        details = build_user_auction_lot_details(user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            bot.send_message(call.message.chat.id, details.get("message", "❌ Лот недоступний."), reply_markup=auction_house_kb())
            return

        text = (
            "⚠️ Підтвердження зняття лота\n\n"
            f"{details['text']}\n\n"
            "Після підтвердження предмет повернеться в інвентар, якщо там є місце."
        )

        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_my_lot_cancel_confirm_kb_v1(lot_id, page=page))
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=auction_my_lot_cancel_confirm_kb_v1(lot_id, page=page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_my_cancel_do:"))
    def auction_my_lot_cancel_do_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        from db import cancel_active_auction_lot
        result = cancel_active_auction_lot(user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not result.get("success"):
            bot.send_message(call.message.chat.id, result.get("message", "❌ Не вдалося зняти лот."), reply_markup=auction_house_kb())
            return

        bot.send_message(
            call.message.chat.id,
            (
                "✅ Лот знято з продажу!\n\n"
                f"📦 {result.get('item_name')}\n"
                "Предмет повернено в інвентар."
            ),
            reply_markup=auction_house_kb(),
        )

        text, kb = build_auction_my_lots_text_v1(user_id, page=page)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


try:
    _auction_base_register_handlers_before_my_lots_cancel_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_my_lots_cancel_v1 = None


def register_auction_house_handlers(bot):
    # My lots handler must be registered before old placeholder for 📦 Мої лоти.
    _auction_register_my_lots_cancel_handlers_v1(bot)

    if _auction_base_register_handlers_before_my_lots_cancel_v1:
        _auction_base_register_handlers_before_my_lots_cancel_v1(bot)


# ==============================
# ✅ AUCTION HOUSE UNCLAIMED ITEMS UI V1
# ==============================

AUCTION_UNCLAIMED_ITEMS_PAGE_SIZE = 8


def auction_unclaimed_items_inline_kb_v1(user_id, page=0):
    from db import get_user_unclaimed_auction_items

    page = max(0, int(page or 0))
    offset = page * AUCTION_UNCLAIMED_ITEMS_PAGE_SIZE
    lots = get_user_unclaimed_auction_items(
        user_id=user_id,
        limit=AUCTION_UNCLAIMED_ITEMS_PAGE_SIZE + 1,
        offset=offset,
    )

    visible_lots = lots[:AUCTION_UNCLAIMED_ITEMS_PAGE_SIZE]
    has_next = len(lots) > AUCTION_UNCLAIMED_ITEMS_PAGE_SIZE

    kb = types.InlineKeyboardMarkup(row_width=1)

    for lot in visible_lots:
        quantity = int(lot["quantity"] or 1)
        qty = f" ×{quantity}" if quantity > 1 and f"×{quantity}" not in lot["item_name"] else ""
        label = f"📬 {lot['item_name']}{qty}"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_uncl_lot:{lot['id']}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"ah_uncl_page:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Далі", callback_data=f"ah_uncl_page:{page + 1}"))
    if nav:
        kb.row(*nav)

    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb, visible_lots, has_next


def build_auction_unclaimed_items_text_v1(user_id, page=0):
    kb, lots, has_next = auction_unclaimed_items_inline_kb_v1(user_id, page=page)
    text = f"📬 Незабрані предмети\n\nСторінка: {int(page) + 1}\n\n"

    if not lots:
        text += "У тебе немає незабраних предметів."
    else:
        text += (
            "Тут зберігаються предмети з лотів, термін яких завершився без продажу.\n\n"
            "Оберіть предмет inline-кнопкою нижче, щоб забрати його в інвентар."
        )

    return text, kb


def auction_unclaimed_item_view_kb_v1(lot_id, page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📥 Забрати предмет", callback_data=f"ah_uncl_claim_confirm:{lot_id}:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 До незабраних", callback_data=f"ah_uncl_page:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb


def auction_unclaimed_claim_confirm_kb_v1(lot_id, page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Підтвердити отримання", callback_data=f"ah_uncl_claim_do:{lot_id}:{page}"))
    kb.add(types.InlineKeyboardButton("❌ Назад", callback_data=f"ah_uncl_lot:{lot_id}:{page}"))
    return kb


def _auction_register_unclaimed_items_handlers_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_UNCLAIMED_ITEMS_BUTTON)
    def auction_unclaimed_items_start_v1(message):
        user_id = message.from_user.id
        text, kb = build_auction_unclaimed_items_text_v1(user_id, page=0)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_uncl_page:"))
    def auction_unclaimed_items_page_callback_v1(call):
        user_id = call.from_user.id
        page = int(call.data.split(":")[1])
        text, kb = build_auction_unclaimed_items_text_v1(user_id, page=page)
        try:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_uncl_lot:"))
    def auction_unclaimed_item_view_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        from db import build_user_unclaimed_auction_item_details
        details = build_user_unclaimed_auction_item_details(user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            text, kb = build_auction_unclaimed_items_text_v1(user_id, page=page)
            bot.send_message(call.message.chat.id, details.get("message", "❌ Предмет недоступний."), reply_markup=auction_house_kb())
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
            return

        try:
            bot.edit_message_text(details["text"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_unclaimed_item_view_kb_v1(lot_id, page=page))
        except Exception:
            bot.send_message(call.message.chat.id, details["text"], reply_markup=auction_unclaimed_item_view_kb_v1(lot_id, page=page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_uncl_claim_confirm:"))
    def auction_unclaimed_claim_confirm_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        from db import build_user_unclaimed_auction_item_details
        details = build_user_unclaimed_auction_item_details(user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            bot.send_message(call.message.chat.id, details.get("message", "❌ Предмет недоступний."), reply_markup=auction_house_kb())
            return

        text = (
            "⚠️ Підтвердження отримання предмета\n\n"
            f"{details['text']}\n\n"
            "Після підтвердження предмет повернеться в інвентар, якщо там є місце."
        )

        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_unclaimed_claim_confirm_kb_v1(lot_id, page=page))
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=auction_unclaimed_claim_confirm_kb_v1(lot_id, page=page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_uncl_claim_do:"))
    def auction_unclaimed_claim_do_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        from db import claim_expired_auction_item
        result = claim_expired_auction_item(user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not result.get("success"):
            bot.send_message(call.message.chat.id, result.get("message", "❌ Не вдалося отримати предмет."), reply_markup=auction_house_kb())
            return

        bot.send_message(
            call.message.chat.id,
            (
                "✅ Предмет повернено в інвентар!\n\n"
                f"📦 {result.get('item_name')}"
            ),
            reply_markup=auction_house_kb(),
        )

        text, kb = build_auction_unclaimed_items_text_v1(user_id, page=page)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


try:
    _auction_base_register_handlers_before_unclaimed_items_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_unclaimed_items_v1 = None


def register_auction_house_handlers(bot):
    # Unclaimed items handler must be registered before old placeholder for 📬 Незабрані предмети.
    _auction_register_unclaimed_items_handlers_v1(bot)

    if _auction_base_register_handlers_before_unclaimed_items_v1:
        _auction_base_register_handlers_before_unclaimed_items_v1(bot)


# ==============================
# ✅ AUCTION HOUSE COMPLETED SALES CLAIM GOLD UI V1
# ==============================

AUCTION_COMPLETED_SALES_PAGE_SIZE = 8


def auction_completed_sales_inline_kb_v1(user_id, page=0):
    from db import get_user_unclaimed_auction_sales

    page = max(0, int(page or 0))
    offset = page * AUCTION_COMPLETED_SALES_PAGE_SIZE
    lots = get_user_unclaimed_auction_sales(
        user_id=user_id,
        limit=AUCTION_COMPLETED_SALES_PAGE_SIZE + 1,
        offset=offset,
    )

    visible_lots = lots[:AUCTION_COMPLETED_SALES_PAGE_SIZE]
    has_next = len(lots) > AUCTION_COMPLETED_SALES_PAGE_SIZE

    kb = types.InlineKeyboardMarkup(row_width=1)

    for lot in visible_lots:
        quantity = int(lot["quantity"] or 1)
        qty = f" x{quantity}" if quantity > 1 and f"x{quantity}" not in lot["item_name"] else ""
        label = f"💰 {lot['item_name']}{qty} — {lot['price']} золота"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_sale_lot:{lot['id']}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"ah_sale_page:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Далі", callback_data=f"ah_sale_page:{page + 1}"))
    if nav:
        kb.row(*nav)

    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb, visible_lots, has_next


def build_auction_completed_sales_text_v1(user_id, page=0):
    kb, lots, has_next = auction_completed_sales_inline_kb_v1(user_id, page=page)
    text = f"💰 Завершені продажі\n\nСторінка: {int(page) + 1}\n\n"

    if not lots:
        text += "У тебе немає завершених продажів із незабраним золотом."
    else:
        text += (
            "Тут зберігається золото за продані лоти.\n\n"
            "Оберіть продаж inline-кнопкою нижче, щоб забрати золото."
        )

    return text, kb


def auction_completed_sale_view_kb_v1(lot_id, page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("💰 Забрати золото", callback_data=f"ah_sale_claim_confirm:{lot_id}:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 До завершених продажів", callback_data=f"ah_sale_page:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb


def auction_completed_sale_claim_confirm_kb_v1(lot_id, page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Підтвердити отримання золота", callback_data=f"ah_sale_claim_do:{lot_id}:{page}"))
    kb.add(types.InlineKeyboardButton("❌ Назад", callback_data=f"ah_sale_lot:{lot_id}:{page}"))
    return kb


def _auction_register_completed_sales_handlers_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_SOLD_BUTTON)
    def auction_completed_sales_start_v1(message):
        user_id = message.from_user.id
        text, kb = build_auction_completed_sales_text_v1(user_id, page=0)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_sale_page:"))
    def auction_completed_sales_page_callback_v1(call):
        user_id = call.from_user.id
        page = int(call.data.split(":")[1])
        text, kb = build_auction_completed_sales_text_v1(user_id, page=page)
        try:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_sale_lot:"))
    def auction_completed_sale_view_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        from db import build_user_unclaimed_auction_sale_details
        details = build_user_unclaimed_auction_sale_details(user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            text, kb = build_auction_completed_sales_text_v1(user_id, page=page)
            bot.send_message(call.message.chat.id, details.get("message", "❌ Продаж недоступний."), reply_markup=auction_house_kb())
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
            return

        try:
            bot.edit_message_text(details["text"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_completed_sale_view_kb_v1(lot_id, page=page))
        except Exception:
            bot.send_message(call.message.chat.id, details["text"], reply_markup=auction_completed_sale_view_kb_v1(lot_id, page=page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_sale_claim_confirm:"))
    def auction_completed_sale_claim_confirm_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        from db import build_user_unclaimed_auction_sale_details
        details = build_user_unclaimed_auction_sale_details(user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            bot.send_message(call.message.chat.id, details.get("message", "❌ Продаж недоступний."), reply_markup=auction_house_kb())
            return

        text = (
            "⚠️ Підтвердження отримання золота\n\n"
            f"{details['text']}\n\n"
            "Після підтвердження золото буде додано на баланс персонажа."
        )

        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_completed_sale_claim_confirm_kb_v1(lot_id, page=page))
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=auction_completed_sale_claim_confirm_kb_v1(lot_id, page=page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_sale_claim_do:"))
    def auction_completed_sale_claim_do_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        from db import claim_auction_sale_gold
        result = claim_auction_sale_gold(user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not result.get("success"):
            bot.send_message(call.message.chat.id, result.get("message", "❌ Не вдалося отримати золото."), reply_markup=auction_house_kb())
            return

        bot.send_message(
            call.message.chat.id,
            (
                f"✅ Отримано {result.get('amount')} золота!\n\n"
                f"📦 Проданий лот: {result.get('item_name')}"
            ),
            reply_markup=auction_house_kb(),
        )

        text, kb = build_auction_completed_sales_text_v1(user_id, page=page)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


try:
    _auction_base_register_handlers_before_completed_sales_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_completed_sales_v1 = None


def register_auction_house_handlers(bot):
    # Completed sales handler must be registered before old placeholder for 💰 Завершені продажі.
    _auction_register_completed_sales_handlers_v1(bot)

    if _auction_base_register_handlers_before_completed_sales_v1:
        _auction_base_register_handlers_before_completed_sales_v1(bot)


# ==============================
# ✅ AUCTION HOUSE BUY FILTERS SORTING UI V1
# ==============================

AUCTION_BUY_PAGE_SIZE = 8

AUCTION_BUY_CATEGORY_BUTTONS_V1 = {
    "all": "🔎 Усі лоти",
    "equipment": "⚔️ Спорядження в продажу",
    "potion": "🧪 Зілля в продажу",
    "material": "🪨 Матеріали в продажу",
}

AUCTION_BUY_CATEGORY_BY_BUTTON_V1 = {
    value: key for key, value in AUCTION_BUY_CATEGORY_BUTTONS_V1.items()
}

AUCTION_BUY_SORT_LABELS_V1 = {
    "new": "🆕 Нові",
    "old": "⏳ Старі",
    "price_asc": "💰 Дешеві",
    "price_desc": "💰 Дорогі",
    "rarity": "⭐ Рідкість",
}


def auction_buy_category_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["all"])
    kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["equipment"], AUCTION_BUY_CATEGORY_BUTTONS_V1["potion"])
    kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["material"])
    kb.row("🔙 Торговий дім")
    return kb


def auction_buy_sort_inline_row_v1(category, current_sort):
    buttons = []
    for sort_key, label in AUCTION_BUY_SORT_LABELS_V1.items():
        prefix = "✅ " if sort_key == current_sort else ""
        buttons.append(types.InlineKeyboardButton(
            prefix + label,
            callback_data=f"ah_buy2_page:{category}:{sort_key}:0"
        ))
    return buttons


def auction_buy_lots_inline_kb_v1(user_id, category="all", sort_key="new", page=0):
    from db import get_auction_lots_for_buy_filtered

    page = max(0, int(page or 0))
    offset = page * AUCTION_BUY_PAGE_SIZE
    lots = get_auction_lots_for_buy_filtered(
        buyer_user_id=user_id,
        category=category,
        sort_key=sort_key,
        limit=AUCTION_BUY_PAGE_SIZE + 1,
        offset=offset,
    )

    visible_lots = lots[:AUCTION_BUY_PAGE_SIZE]
    has_next = len(lots) > AUCTION_BUY_PAGE_SIZE

    kb = types.InlineKeyboardMarkup(row_width=1)

    # Sort controls, split into two rows to avoid very wide buttons.
    sort_buttons = auction_buy_sort_inline_row_v1(category, sort_key)
    kb.row(*sort_buttons[:2])
    kb.row(*sort_buttons[2:4])
    kb.row(*sort_buttons[4:])

    for lot in visible_lots:
        quantity = int(lot["quantity"] or 1)
        qty = f" ×{quantity}" if quantity > 1 and f"×{quantity}" not in lot["item_name"] else ""
        label = f"📦 {_auction_lot_typed_name_17_1_0(lot)}{qty} — {lot['price']} 💰"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_buy2_lot:{lot['id']}:{category}:{sort_key}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"ah_buy2_page:{category}:{sort_key}:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Далі", callback_data=f"ah_buy2_page:{category}:{sort_key}:{page + 1}"))
    if nav:
        kb.row(*nav)

    kb.add(types.InlineKeyboardButton("🔙 Категорії", callback_data="ah_buy2_categories"))
    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb, visible_lots, has_next


def build_auction_buy_category_text_v1():
    return (
        "🛒 Купити\n\n"
        "Оберіть категорію лотів.\n\n"
        "Доступні категорії:\n"
        "• 🔎 Усі лоти\n"
        "• ⚔️ Спорядження\n"
        "• 🧪 Зілля\n"
        "• 🪨 Матеріали\n\n"
        "Продавці приховані. Власні лоти у списку покупки не показуються."
    )


def build_auction_buy_lots_text_v1(category="all", sort_key="new", page=0):
    category_label = AUCTION_BUY_CATEGORY_BUTTONS_V1.get(category, AUCTION_BUY_CATEGORY_BUTTONS_V1["all"])
    sort_label = AUCTION_BUY_SORT_LABELS_V1.get(sort_key, AUCTION_BUY_SORT_LABELS_V1["new"])
    return (
        "🛒 Купити\n\n"
        f"📂 Категорія: {category_label}\n"
        f"↕️ Сортування: {sort_label}\n"
        f"📄 Сторінка: {int(page) + 1}\n\n"
        "Оберіть лот inline-кнопкою нижче."
    )


def auction_buy_lot_view_kb_v1(lot_id, category="all", sort_key="new", page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Купити", callback_data=f"ah_buy2_confirm:{lot_id}:{category}:{sort_key}:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 До списку", callback_data=f"ah_buy2_page:{category}:{sort_key}:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 Торговий дім", callback_data="ah_menu"))
    return kb


def auction_buy_confirm_kb_v1(lot_id, category="all", sort_key="new", page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Підтвердити покупку", callback_data=f"ah_buy2_do:{lot_id}:{category}:{sort_key}:{page}"))
    kb.add(types.InlineKeyboardButton("❌ Назад", callback_data=f"ah_buy2_lot:{lot_id}:{category}:{sort_key}:{page}"))
    return kb


def _auction_register_buy_filters_handlers_v1(bot):

    @bot.message_handler(func=lambda m: m.text == "🛒 Купити")
    def auction_buy_start_v1(message):
        bot.send_message(
            message.chat.id,
            build_auction_buy_category_text_v1(),
            reply_markup=auction_buy_category_kb_v1()
        )

    def auction_buy_category_selected_v1(message):
        user_id = message.from_user.id
        category = AUCTION_BUY_CATEGORY_BY_BUTTON_V1.get(message.text, "all")
        sort_key = "new"
        page = 0
        text = build_auction_buy_lots_text_v1(category=category, sort_key=sort_key, page=page)
        kb, lots, has_next = auction_buy_lots_inline_kb_v1(user_id, category=category, sort_key=sort_key, page=page)

        if not lots:
            text += "\n\nЛотів у цій категорії поки немає."

        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "ah_buy2_categories")
    def auction_buy_categories_callback_v1(call):
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        bot.send_message(call.message.chat.id, build_auction_buy_category_text_v1(), reply_markup=auction_buy_category_kb_v1())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_buy2_page:"))
    def auction_buy_page_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        category = parts[1]
        sort_key = parts[2]
        page = int(parts[3])

        text = build_auction_buy_lots_text_v1(category=category, sort_key=sort_key, page=page)
        kb, lots, has_next = auction_buy_lots_inline_kb_v1(user_id, category=category, sort_key=sort_key, page=page)

        if not lots:
            text += "\n\nЛотів у цій категорії поки немає."

        try:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_buy2_lot:"))
    def auction_buy_lot_view_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        category = parts[2]
        sort_key = parts[3]
        page = int(parts[4])

        from db import build_auction_buy_lot_details_v2
        details = build_auction_buy_lot_details_v2(buyer_user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            bot.send_message(call.message.chat.id, details.get("message", "❌ Лот недоступний."), reply_markup=auction_house_kb())
            return

        try:
            bot.edit_message_text(details["text"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_buy_lot_view_kb_v1(lot_id, category, sort_key, page))
        except Exception:
            bot.send_message(call.message.chat.id, details["text"], reply_markup=auction_buy_lot_view_kb_v1(lot_id, category, sort_key, page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_buy2_confirm:"))
    def auction_buy_confirm_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        category = parts[2]
        sort_key = parts[3]
        page = int(parts[4])

        from db import build_auction_buy_lot_details_v2
        details = build_auction_buy_lot_details_v2(buyer_user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            bot.send_message(call.message.chat.id, details.get("message", "❌ Лот недоступний."), reply_markup=auction_house_kb())
            return

        text = (
            "⚠️ Підтвердження покупки\n\n"
            f"{details['text']}\n\n"
            "Після підтвердження золото буде списано, а предмет додано в інвентар."
        )

        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_buy_confirm_kb_v1(lot_id, category, sort_key, page))
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=auction_buy_confirm_kb_v1(lot_id, category, sort_key, page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_buy2_do:"))
    def auction_buy_do_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        category = parts[2]
        sort_key = parts[3]
        page = int(parts[4])

        from db import buy_auction_lot_v2
        result = buy_auction_lot_v2(buyer_user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not result.get("success"):
            bot.send_message(call.message.chat.id, result.get("message", "❌ Не вдалося купити лот."), reply_markup=auction_house_kb())
            return

        bot.send_message(
            call.message.chat.id,
            (
                "✅ Покупку завершено!\n\n"
                f"📦 {result.get('item_name')}\n"
                f"💰 Сплачено: {result.get('price')} золота\n\n"
                "Предмет додано в інвентар."
            ),
            reply_markup=auction_house_kb(),
        )

        text = build_auction_buy_lots_text_v1(category=category, sort_key=sort_key, page=page)
        kb, lots, has_next = auction_buy_lots_inline_kb_v1(user_id, category=category, sort_key=sort_key, page=page)
        if not lots:
            text += "\n\nЛотів у цій категорії поки немає."
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


try:
    _auction_base_register_handlers_before_buy_filters_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_buy_filters_v1 = None


def register_auction_house_handlers(bot):
    # Buy filters handler must be registered before older buy handlers/placeholders.
    _auction_register_buy_filters_handlers_v1(bot)

    if _auction_base_register_handlers_before_buy_filters_v1:
        _auction_base_register_handlers_before_buy_filters_v1(bot)


# ==============================
# ✅ AUCTION HOUSE BACK TO MENU CALLBACK FIX V1
# ==============================


def _auction_clear_runtime_states_v1(user_id):
    """
    Best-effort cleanup for Auction House UI states.
    This prevents old sell/buy state routers from swallowing navigation buttons.
    """

    possible_state_names = [
        "AUCTION_SELL_STATE",
        "AUCTION_BUY_STATE",
        "AUCTION_MY_LOTS_STATE",
        "AUCTION_UNCLAIMED_STATE",
        "AUCTION_COMPLETED_SALES_STATE",
        "AUCTION_SEARCH_STATE",
        "AUCTION_HISTORY_STATE",
    ]

    for state_name in possible_state_names:
        state_obj = globals().get(state_name)
        if not state_obj:
            continue

        try:
            if isinstance(state_obj, dict):
                state_obj.pop(user_id, None)
            elif isinstance(state_obj, set):
                state_obj.discard(user_id)
        except Exception:
            pass


def _auction_main_menu_text_v1(user_id=None):
    """
    Returns Auction House main menu text without relying on a specific older helper name.
    """

    try:
        if "build_auction_house_text" in globals():
            if user_id is not None:
                try:
                    return build_auction_house_text(user_id)
                except TypeError:
                    return build_auction_house_text()
            return build_auction_house_text()
    except Exception:
        pass

    return (
        "🏛️ Торговий дім\n\n"
        "Тут гравці можуть виставляти товари на продаж, купувати лоти інших гравців "
        "та забирати золото за завершені продажі.\n\n"
        "Доступні дії:\n"
        "• 🛒 Купити\n"
        "• ➕ Виставити товар\n"
        "• 📦 Мої лоти\n"
        "• 📬 Незабрані предмети\n"
        "• 💰 Завершені продажі\n"
        "• 📜 Історія"
    )


def _auction_register_back_to_menu_callback_v1(bot):

    @bot.callback_query_handler(func=lambda call: call.data == "ah_menu")
    def auction_back_to_menu_callback_v1(call):
        user_id = call.from_user.id
        _auction_clear_runtime_states_v1(user_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        # Main Auction House menu uses ReplyKeyboardMarkup, so send a fresh message.
        # Telegram edit_message_text cannot attach ReplyKeyboardMarkup.
        bot.send_message(
            call.message.chat.id,
            _auction_main_menu_text_v1(user_id),
            reply_markup=auction_house_kb()
        )


try:
    _auction_base_register_handlers_before_back_to_menu_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_back_to_menu_v1 = None


def register_auction_house_handlers(bot):
    # Register ah_menu callback before older handlers, so every inline "🔙 Торговий дім" works.
    _auction_register_back_to_menu_callback_v1(bot)

    if _auction_base_register_handlers_before_back_to_menu_v1:
        _auction_base_register_handlers_before_back_to_menu_v1(bot)


# ==============================
# ✅ AUCTION HOUSE REPLY BACK AND REMOVE INLINE MENU V1
# ==============================

AUCTION_BACK_TO_HOUSE_BUTTON_V1 = "🔙 Торговий дім"


def _auction_clear_runtime_states_v2(user_id):
    """
    Очищає runtime-стани Торгового Дому, щоб звичайна кнопка
    🔙 Торговий дім не ковталась state-router-ами.
    """

    possible_state_names = [
        "AUCTION_SELL_STATE",
        "AUCTION_BUY_STATE",
        "AUCTION_MY_LOTS_STATE",
        "AUCTION_UNCLAIMED_STATE",
        "AUCTION_COMPLETED_SALES_STATE",
        "AUCTION_SEARCH_STATE",
        "AUCTION_HISTORY_STATE",
    ]

    for state_name in possible_state_names:
        state_obj = globals().get(state_name)
        if not state_obj:
            continue

        try:
            if isinstance(state_obj, dict):
                state_obj.pop(user_id, None)
            elif isinstance(state_obj, set):
                state_obj.discard(user_id)
        except Exception:
            pass


def _auction_main_menu_text_v2(user_id=None):
    """
    Текст головного меню Торгового Дому.
    Не залежить від конкретної назви старого helper-а.
    """

    try:
        if "build_auction_house_text" in globals():
            if user_id is not None:
                try:
                    return build_auction_house_text(user_id)
                except TypeError:
                    return build_auction_house_text()
            return build_auction_house_text()
    except Exception:
        pass

    return (
        "🏛️ Торговий дім\n\n"
        "Тут гравці можуть виставляти товари на продаж, купувати лоти інших гравців "
        "та забирати золото за завершені продажі.\n\n"
        "Доступні дії:\n"
        "• 🛒 Купити\n"
        "• ➕ Виставити товар\n"
        "• 📦 Мої лоти\n"
        "• 📬 Незабрані предмети\n"
        "• 💰 Завершені продажі\n"
        "• 📜 Історія"
    )


def auction_buy_lots_inline_kb_v1(user_id, category="all", sort_key="new", page=0):
    """
    Override: список лотів лишається inline, але без inline-кнопки 🔙 Торговий дім.
    Повернення в Торговий Дім має бути через звичайну ReplyKeyboard-кнопку внизу.
    """

    from db import get_auction_lots_for_buy_filtered

    page = max(0, int(page or 0))
    offset = page * AUCTION_BUY_PAGE_SIZE
    lots = get_auction_lots_for_buy_filtered(
        buyer_user_id=user_id,
        category=category,
        sort_key=sort_key,
        limit=AUCTION_BUY_PAGE_SIZE + 1,
        offset=offset,
    )

    visible_lots = lots[:AUCTION_BUY_PAGE_SIZE]
    has_next = len(lots) > AUCTION_BUY_PAGE_SIZE

    kb = types.InlineKeyboardMarkup(row_width=1)

    # Сортування лишається inline.
    sort_buttons = auction_buy_sort_inline_row_v1(category, sort_key)
    kb.row(*sort_buttons[:2])
    kb.row(*sort_buttons[2:4])
    kb.row(*sort_buttons[4:])

    for lot in visible_lots:
        quantity = int(lot["quantity"] or 1)
        qty = f" ×{quantity}" if quantity > 1 and f"×{quantity}" not in lot["item_name"] else ""
        label = f"📦 {_auction_lot_typed_name_17_1_0(lot)}{qty} — {lot['price']} 💰"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_buy2_lot:{lot['id']}:{category}:{sort_key}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"ah_buy2_page:{category}:{sort_key}:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Далі", callback_data=f"ah_buy2_page:{category}:{sort_key}:{page + 1}"))
    if nav:
        kb.row(*nav)

    # У списку покупки лишаємо тільки повернення до категорій.
    # Назад у головне меню — звичайною кнопкою 🔙 Торговий дім.
    kb.add(types.InlineKeyboardButton("🔙 Категорії", callback_data="ah_buy2_categories"))
    return kb, visible_lots, has_next


def auction_buy_lot_view_kb_v1(lot_id, category="all", sort_key="new", page=0):
    """
    Override: у деталях лота прибрано inline 🔙 Торговий дім.
    """

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Купити", callback_data=f"ah_buy2_confirm:{lot_id}:{category}:{sort_key}:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 До списку", callback_data=f"ah_buy2_page:{category}:{sort_key}:{page}"))
    return kb


def auction_buy_confirm_kb_v1(lot_id, category="all", sort_key="new", page=0):
    """
    Override: confirmation без inline 🔙 Торговий дім.
    """

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Підтвердити покупку", callback_data=f"ah_buy2_do:{lot_id}:{category}:{sort_key}:{page}"))
    kb.add(types.InlineKeyboardButton("❌ Назад", callback_data=f"ah_buy2_lot:{lot_id}:{category}:{sort_key}:{page}"))
    return kb


def _auction_register_reply_back_to_house_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_BACK_TO_HOUSE_BUTTON_V1)
    def auction_reply_back_to_house_v1(message):
        user_id = message.from_user.id
        _auction_clear_runtime_states_v2(user_id)

        bot.send_message(
            message.chat.id,
            _auction_main_menu_text_v2(user_id),
            reply_markup=auction_house_kb()
        )


try:
    _auction_base_register_handlers_before_reply_back_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_reply_back_v1 = None


def register_auction_house_handlers(bot):
    # Reply-кнопка 🔙 Торговий дім має реєструватися раніше старих state-router-ів.
    _auction_register_reply_back_to_house_v1(bot)

    if _auction_base_register_handlers_before_reply_back_v1:
        _auction_base_register_handlers_before_reply_back_v1(bot)


# ==============================
# ✅ AUCTION HOUSE BUY CATEGORY KEYBOARD CLEANUP V1
# ==============================


def auction_buy_lots_reply_back_kb_v1():
    """
    ReplyKeyboard для екранів зі списком лотів.

    Коли гравець уже обрав категорію, кнопки категорій знизу більше не потрібні.
    Лишається тільки звичайна кнопка повернення в головне меню Торгового Дому.
    """

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Торговий дім")
    return kb


# ROM Stage 17.31.1.12 canonical buy-category handler mapping
def _auction_register_buy_category_keyboard_cleanup_v1(bot):

    @bot.message_handler(func=lambda m: m.text in AUCTION_BUY_CATEGORY_BY_BUTTON_V1)
    def auction_buy_category_selected_clean_keyboard_v1(message):
        user_id = message.from_user.id
        category = AUCTION_BUY_CATEGORY_BY_BUTTON_V1.get(message.text)
        if category is None:
            bot.send_message(
                message.chat.id,
                "❌ Невідома категорія лотів.",
                reply_markup=auction_buy_category_kb_v1(),
            )
            return
        sort_key = "new"
        page = 0

        text = build_auction_buy_lots_text_v1(
            category=category,
            sort_key=sort_key,
            page=page
        )

        inline_kb, lots, has_next = auction_buy_lots_inline_kb_v1(
            user_id,
            category=category,
            sort_key=sort_key,
            page=page
        )

        if not lots:
            text += "\n\nЛотів у цій категорії поки немає."

        # Важливо: спочатку міняємо нижню ReplyKeyboard на одну кнопку 🔙 Торговий дім,
        # а потім надсилаємо список з inline-кнопками.
        bot.send_message(
            message.chat.id,
            "📂 Категорію відкрито. Для повернення до категорій використай inline-кнопку «🔙 Категорії» під списком.",
            reply_markup=auction_buy_lots_reply_back_kb_v1()
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=inline_kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "ah_buy2_categories")
    def auction_buy_categories_restore_reply_keyboard_v1(call):
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        # При поверненні до категорій повертаємо нижні кнопки категорій.
        bot.send_message(
            call.message.chat.id,
            build_auction_buy_category_text_v1(),
            reply_markup=auction_buy_category_kb_v1()
        )


try:
    _auction_base_register_handlers_before_buy_cat_keyboard_cleanup_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_buy_cat_keyboard_cleanup_v1 = None


def register_auction_house_handlers(bot):
    # Реєструємо раніше старих category handlers, щоб прибирати нижні кнопки категорій після вибору.
    _auction_register_buy_category_keyboard_cleanup_v1(bot)

    if _auction_base_register_handlers_before_buy_cat_keyboard_cleanup_v1:
        _auction_base_register_handlers_before_buy_cat_keyboard_cleanup_v1(bot)


# ==============================
# ✅ AUCTION HOUSE SELL CATEGORY KEYBOARD CLEANUP V1
# ROM Stage 17.31.1.3 canonical Auction sell-route consolidation
# ==============================

AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V1 = "ah_sell_categories"
AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1 = "🔙 Торговий дім"

AUCTION_SELL_CATEGORY_BUTTONS_V1 = {
    "equipment": "⚔️ Спорядження",
    "potion": "🧪 Зілля для продажу",
    "material": "🪨 Матеріали",
    "rune": "💠 Руни",
    "consumable": "🧰 Витратні предмети",
}


def auction_sell_category_kb_v1():
    """ReplyKeyboard з категоріями виставлення товару."""

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_SELL_CATEGORY_BUTTONS_V1["equipment"], AUCTION_SELL_CATEGORY_BUTTONS_V1["potion"])
    kb.row(AUCTION_SELL_CATEGORY_BUTTONS_V1["material"], AUCTION_SELL_CATEGORY_BUTTONS_V1["rune"])
    kb.row(AUCTION_SELL_CATEGORY_BUTTONS_V1["consumable"])
    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1)
    return kb


def auction_sell_listing_back_kb_v1():
    """
    ReplyKeyboard для екранів зі списком предметів на продаж.

    Коли гравець уже обрав категорію, кнопки інших категорій знизу не потрібні.
    Лишається тільки повернення в головне меню Торгового Дому.
    """

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1)
    return kb


def build_auction_sell_category_text_v1():
    return (
        "➕ Виставити товар\n\n"
        "Оберіть категорію товару, який хочете виставити на продаж.\n\n"
        "Доступно зараз:\n"
        "• ⚔️ Спорядження — зброя, броня, щити, біжутерія.\n"
        "• 🧪 Зілля — стекові предмети, можна виставляти частинами.\n"
        "• 🪨 Матеріали — камені та матеріали, можна виставляти частинами.\n"
        "• 💠 Руни — дозволені руни, які не належать до захищених предметів.\n"
        "• 🧰 Витратні предмети — їжа, напої та інші стекові предмети для використання.\n\n"
        "Обмеження:\n"
        "• 💎 Руну Успіху не можна продавати через Торговий Дім.\n"
        "• Екіпіровані та зламані предмети не можна виставляти.\n"
        "• Активний лот існує 7 днів.\n"
        "• Максимум активних лотів: 20."
    )


def _auction_sanitize_sell_inline_kb_v1(kb):
    """
    Прибирає inline-кнопку 🔙 Торговий дім зі списків виставлення товару
    і додає inline-кнопку 🔙 Категорії виставлення.
    """

    try:
        new_keyboard = []
        for row in getattr(kb, "keyboard", []) or []:
            new_row = []
            for button in row:
                text = getattr(button, "text", "") or ""
                callback_data = getattr(button, "callback_data", "") or ""

                if callback_data == "ah_menu":
                    continue
                if "Торговий дім" in text:
                    continue

                new_row.append(button)

            if new_row:
                new_keyboard.append(new_row)

        kb.keyboard = new_keyboard
    except Exception:
        pass

    try:
        kb.add(types.InlineKeyboardButton("🔙 Категорії виставлення", callback_data=AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V1))
    except Exception:
        pass

    return kb


def _auction_call_equipment_sell_list_v1(user_id, page=0):
    """Пробує викликати наявний helper списку спорядження."""

    fn = globals().get("build_auction_sell_item_list_text")
    if not fn:
        return None

    try:
        return fn(user_id, page=page)
    except TypeError:
        try:
            return fn(user_id=user_id, page=page)
        except TypeError:
            try:
                return fn(user_id)
            except Exception:
                return None
    except Exception:
        raise


def _auction_try_stack_sell_list_v1(user_id, category, page=0):
    """Пробує знайти і викликати helper списку стекових предметів."""

    candidate_names = [
        "build_auction_sell_stack_item_list_text",
        "build_auction_sell_stack_items_text",
        "build_auction_sell_stack_list_text",
        "build_auction_sell_stack_items_list_text",
        "build_auction_sell_potion_material_list_text",
    ]

    for name in candidate_names:
        fn = globals().get(name)
        if not fn:
            continue

        call_patterns = [
            lambda: fn(user_id=user_id, category=category, page=page),
            lambda: fn(user_id, category, page=page),
            lambda: fn(user_id, category, page),
            lambda: fn(user_id=user_id, item_category=category, page=page),
            lambda: fn(user_id, item_category=category, page=page),
        ]

        for call_fn in call_patterns:
            try:
                return call_fn()
            except TypeError:
                continue
            except Exception:
                raise

    return None


# ROM Stage 17.31.1.6 canonical inline category dispatch
def _auction_send_sell_category_listing_v1(bot, message, category):
    """Open one sell category through the canonical inline item-list flow."""

    user_id = message.from_user.id
    category = str(category or "").strip().lower()
    allowed_categories = {"equipment", "potion", "material", "rune", "consumable"}

    if category not in allowed_categories:
        bot.send_message(
            message.chat.id,
            "❌ Невідома категорія товару.",
            reply_markup=auction_sell_category_kb_v1(),
        )
        return

    # A concrete category must never remain in the persistent reply keyboard.
    # The item list itself is always rendered by InlineKeyboardMarkup.
    bot.send_message(
        message.chat.id,
        "📂 Категорію відкрито. Для повернення до категорій використай inline-кнопку «🔙 Категорії виставлення» під списком.",
        reply_markup=auction_sell_listing_back_kb_v1(),
    )

    try:
        text, inline_kb = build_auction_sell_inline_list_text_v1(
            user_id=user_id,
            category=category,
            page=0,
        )
    except TypeError:
        text, inline_kb = build_auction_sell_inline_list_text_v1(user_id, category, 0)
    except Exception as error:
        bot.send_message(
            message.chat.id,
            f"❌ Не вдалося відкрити категорію: {error}",
            reply_markup=auction_sell_listing_back_kb_v1(),
        )
        return

    if not isinstance(inline_kb, types.InlineKeyboardMarkup):
        bot.send_message(
            message.chat.id,
            "❌ Список категорії має некоректний формат клавіатури.",
            reply_markup=auction_sell_listing_back_kb_v1(),
        )
        return

    inline_kb = _auction_sanitize_sell_inline_kb_v1(inline_kb)
    bot.send_message(message.chat.id, text, reply_markup=inline_kb)


# ROM Stage 17.31.1.4 canonical sell-entry registration
def _auction_register_sell_category_keyboard_cleanup_v1(bot):

    @bot.message_handler(func=lambda m: m.text == "➕ Виставити товар")
    def auction_sell_start_categories_v1(message):
        # Повертаємо нижні кнопки категорій при вході у виставлення товару.
        bot.send_message(
            message.chat.id,
            build_auction_sell_category_text_v1(),
            reply_markup=auction_sell_category_kb_v1()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_CATEGORY_BUTTONS_V1["equipment"])
    def auction_sell_category_equipment_v1(message):
        _auction_send_sell_category_listing_v1(bot, message, "equipment")

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_CATEGORY_BUTTONS_V1["potion"])
    def auction_sell_category_potion_v1(message):
        _auction_send_sell_category_listing_v1(bot, message, "potion")

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_CATEGORY_BUTTONS_V1["material"])
    def auction_sell_category_material_v1(message):
        _auction_send_sell_category_listing_v1(bot, message, "material")

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_CATEGORY_BUTTONS_V1["rune"])
    def auction_sell_category_rune_v1(message):
        _auction_send_sell_category_listing_v1(bot, message, "rune")

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_CATEGORY_BUTTONS_V1["consumable"])
    def auction_sell_category_consumable_v1(message):
        _auction_send_sell_category_listing_v1(bot, message, "consumable")

    @bot.callback_query_handler(func=lambda call: call.data == AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V1)
    def auction_sell_back_to_categories_callback_v1(call):
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        bot.send_message(
            call.message.chat.id,
            build_auction_sell_category_text_v1(),
            reply_markup=auction_sell_category_kb_v1()
        )


try:
    _auction_base_register_handlers_before_sell_cat_cleanup_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_sell_cat_cleanup_v1 = None


def register_auction_house_handlers(bot):
    # Реєструємо раніше старих sell handlers, щоб керувати ReplyKeyboard категорій.
    _auction_register_sell_category_keyboard_cleanup_v1(bot)

    if _auction_base_register_handlers_before_sell_cat_cleanup_v1:
        _auction_base_register_handlers_before_sell_cat_cleanup_v1(bot)


# ==============================
# ✅ AUCTION HOUSE RESTORE SELL INLINE FLOW V1
# ROM Stage 17.31.1.5 canonical sell registration reachability
# ==============================

# ВАЖЛИВО:
# patch_8_0_9d_auction_sell_category_keyboard_cleanup.py виявився занадто агресивним:
# він відкривав старий sell-list helper, через що предмети для продажу знову стали
# ReplyKeyboard-кнопками, а стекові категорії не знаходили свій helper.
#
# Цей hotfix вимикає проблемний register wrapper 8.0.9d і повертає попередній
# робочий sell-flow з inline-кнопками для предметів.
#
# Після цього точну логіку "прибрати категорії після вибору" краще робити
# вже під фактичну структуру handlers/auction_house.py, щоб не ламати callback-и.


def _auction_register_reply_back_to_house_restore_v1(bot):
    """Залишаємо робочу звичайну кнопку 🔙 Торговий дім."""

    @bot.message_handler(func=lambda m: m.text == "🔙 Торговий дім")
    def auction_reply_back_to_house_restore_v1(message):
        user_id = message.from_user.id

        try:
            if "_auction_clear_runtime_states_v2" in globals():
                _auction_clear_runtime_states_v2(user_id)
            elif "_auction_clear_runtime_states_v1" in globals():
                _auction_clear_runtime_states_v1(user_id)
        except Exception:
            pass

        try:
            text = _auction_main_menu_text_v2(user_id)
        except Exception:
            try:
                text = _auction_main_menu_text_v1(user_id)
            except Exception:
                text = (
                    "🏛️ Торговий дім\n\n"
                    "Тут гравці можуть виставляти товари на продаж, купувати лоти інших гравців "
                    "та забирати золото за завершені продажі."
                )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=auction_house_kb()
        )


try:
    _auction_register_before_broken_sell_cleanup_v1 = _auction_base_register_handlers_before_sell_cat_cleanup_v1
except NameError:
    _auction_register_before_broken_sell_cleanup_v1 = None

try:
    _auction_current_register_before_restore_sell_inline_v1 = register_auction_house_handlers
except NameError:
    _auction_current_register_before_restore_sell_inline_v1 = None


def register_auction_house_handlers(bot):
    """
    Restore handler chain before the broken 8.0.9d sell-category wrapper.

    If _auction_base_register_handlers_before_sell_cat_cleanup_v1 exists, it points to
    the register_auction_house_handlers version that existed before 8.0.9d was applied.
    Calling it restores the previous working inline sell flow while preserving older
    working fixes, including buy category cleanup and reply back to Auction House.
    """

    # Register navigation and the single canonical sell-entry route before the legacy chain.
    _auction_register_reply_back_to_house_restore_v1(bot)
    _auction_register_sell_category_keyboard_cleanup_v1(bot)

    if _auction_register_before_broken_sell_cleanup_v1:
        _auction_register_before_broken_sell_cleanup_v1(bot)
    elif _auction_current_register_before_restore_sell_inline_v1:
        _auction_current_register_before_restore_sell_inline_v1(bot)


# ==============================
# ✅ AUCTION HOUSE SECTION BACK KEYBOARD CLEANUP V1
# ==============================

# Уніфікація навігації Торгового Дому:
# - inline-кнопка "🔙 Торговий дім" прибирається з розділів;
# - у нижній ReplyKeyboard лишається звичайна кнопка "🔙 Торговий дім";
# - це стосується: 📦 Мої лоти, 📬 Незабрані предмети,
#   💰 Завершені продажі, 📜 Історія.

AUCTION_REPLY_BACK_TO_HOUSE_BUTTON_V1 = "🔙 Торговий дім"


def auction_reply_back_only_kb_v1():
    """Нижня клавіатура для внутрішніх розділів Торгового Дому."""

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_REPLY_BACK_TO_HOUSE_BUTTON_V1)
    return kb


def _auction_strip_back_to_house_inline_v1(kb):
    """Прибирає inline-кнопки повернення в головне меню Торгового Дому."""

    try:
        new_keyboard = []

        for row in getattr(kb, "keyboard", []) or []:
            new_row = []

            for button in row:
                text = getattr(button, "text", "") or ""
                callback_data = getattr(button, "callback_data", "") or ""

                if callback_data == "ah_menu":
                    continue

                if "Торговий дім" in text:
                    continue

                new_row.append(button)

            if new_row:
                new_keyboard.append(new_row)

        kb.keyboard = new_keyboard
    except Exception:
        pass

    return kb


# ------------------------------
# Мої лоти: прибрати inline "Торговий дім"
# ------------------------------

try:
    _auction_base_my_lots_inline_kb_before_section_cleanup_v1 = auction_my_lots_inline_kb_v1
except NameError:
    _auction_base_my_lots_inline_kb_before_section_cleanup_v1 = None


def auction_my_lots_inline_kb_v1(user_id, page=0):
    if not _auction_base_my_lots_inline_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1), [], False

    kb, lots, has_next = _auction_base_my_lots_inline_kb_before_section_cleanup_v1(user_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb), lots, has_next


try:
    _auction_base_my_lot_view_kb_before_section_cleanup_v1 = auction_my_lot_view_kb_v1
except NameError:
    _auction_base_my_lot_view_kb_before_section_cleanup_v1 = None


def auction_my_lot_view_kb_v1(lot_id, page=0):
    if not _auction_base_my_lot_view_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1)

    kb = _auction_base_my_lot_view_kb_before_section_cleanup_v1(lot_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb)


# ------------------------------
# Незабрані предмети: прибрати inline "Торговий дім"
# ------------------------------

try:
    _auction_base_unclaimed_items_inline_kb_before_section_cleanup_v1 = auction_unclaimed_items_inline_kb_v1
except NameError:
    _auction_base_unclaimed_items_inline_kb_before_section_cleanup_v1 = None


def auction_unclaimed_items_inline_kb_v1(user_id, page=0):
    if not _auction_base_unclaimed_items_inline_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1), [], False

    kb, lots, has_next = _auction_base_unclaimed_items_inline_kb_before_section_cleanup_v1(user_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb), lots, has_next


try:
    _auction_base_unclaimed_item_view_kb_before_section_cleanup_v1 = auction_unclaimed_item_view_kb_v1
except NameError:
    _auction_base_unclaimed_item_view_kb_before_section_cleanup_v1 = None


def auction_unclaimed_item_view_kb_v1(lot_id, page=0):
    if not _auction_base_unclaimed_item_view_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1)

    kb = _auction_base_unclaimed_item_view_kb_before_section_cleanup_v1(lot_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb)


# ------------------------------
# Завершені продажі: прибрати inline "Торговий дім"
# ------------------------------

try:
    _auction_base_completed_sales_inline_kb_before_section_cleanup_v1 = auction_completed_sales_inline_kb_v1
except NameError:
    _auction_base_completed_sales_inline_kb_before_section_cleanup_v1 = None


def auction_completed_sales_inline_kb_v1(user_id, page=0):
    if not _auction_base_completed_sales_inline_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1), [], False

    kb, lots, has_next = _auction_base_completed_sales_inline_kb_before_section_cleanup_v1(user_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb), lots, has_next


try:
    _auction_base_completed_sale_view_kb_before_section_cleanup_v1 = auction_completed_sale_view_kb_v1
except NameError:
    _auction_base_completed_sale_view_kb_before_section_cleanup_v1 = None


def auction_completed_sale_view_kb_v1(lot_id, page=0):
    if not _auction_base_completed_sale_view_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1)

    kb = _auction_base_completed_sale_view_kb_before_section_cleanup_v1(lot_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb)


# ------------------------------
# Section start handlers: нижня ReplyKeyboard тільки з "🔙 Торговий дім"
# ------------------------------

def _auction_register_section_back_keyboard_cleanup_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_MY_LOTS_BUTTON)
    def auction_my_lots_start_section_cleanup_v1(message):
        user_id = message.from_user.id
        text, inline_kb = build_auction_my_lots_text_v1(user_id, page=0)
        inline_kb = _auction_strip_back_to_house_inline_v1(inline_kb)

        bot.send_message(
            message.chat.id,
            "📦 Розділ «Мої лоти» відкрито.",
            reply_markup=auction_reply_back_only_kb_v1()
        )
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)

    @bot.message_handler(func=lambda m: m.text == AUCTION_UNCLAIMED_ITEMS_BUTTON)
    def auction_unclaimed_items_start_section_cleanup_v1(message):
        user_id = message.from_user.id
        text, inline_kb = build_auction_unclaimed_items_text_v1(user_id, page=0)
        inline_kb = _auction_strip_back_to_house_inline_v1(inline_kb)

        bot.send_message(
            message.chat.id,
            "📬 Розділ «Незабрані предмети» відкрито.",
            reply_markup=auction_reply_back_only_kb_v1()
        )
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)

    @bot.message_handler(func=lambda m: m.text == AUCTION_SOLD_BUTTON)
    def auction_completed_sales_start_section_cleanup_v1(message):
        user_id = message.from_user.id
        text, inline_kb = build_auction_completed_sales_text_v1(user_id, page=0)
        inline_kb = _auction_strip_back_to_house_inline_v1(inline_kb)

        bot.send_message(
            message.chat.id,
            "💰 Розділ «Завершені продажі» відкрито.",
            reply_markup=auction_reply_back_only_kb_v1()
        )
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)

    @bot.message_handler(func=lambda m: m.text == AUCTION_HISTORY_BUTTON)
    def auction_history_start_section_cleanup_v1(message):
        text = (
            "📜 Історія\n\n"
            "Тут буде історія покупок, продажів і перегляд ринкових цін.\n\n"
            "Цей розділ буде реалізовано на наступному етапі Торгового Дому."
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=auction_reply_back_only_kb_v1()
        )


try:
    _auction_base_register_handlers_before_section_back_cleanup_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_section_back_cleanup_v1 = None


def register_auction_house_handlers(bot):
    # Реєструємо раніше старих placeholder/section handlers.
    _auction_register_section_back_keyboard_cleanup_v1(bot)

    if _auction_base_register_handlers_before_section_back_cleanup_v1:
        _auction_base_register_handlers_before_section_back_cleanup_v1(bot)


# ==============================
# ✅ AUCTION HOUSE BUY SEARCH UI V1
# ==============================

AUCTION_SEARCH_BUTTON_V1 = "🔍 Пошук"
AUCTION_SEARCH_STATE_V1 = {}
AUCTION_SEARCH_PAGE_SIZE_V1 = 8


def auction_buy_category_kb_v1():
    """Override buy category keyboard: add Search button."""

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_SEARCH_BUTTON_V1)
    kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["all"])
    kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["equipment"], AUCTION_BUY_CATEGORY_BUTTONS_V1["potion"])
    kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["material"])
    kb.row("🔙 Торговий дім")
    return kb


def build_auction_buy_category_text_v1():
    """Override buy category text: mention Search."""

    return (
        "🛒 Купити\n\n"
        "Оберіть категорію лотів або скористайтесь пошуком.\n\n"
        "Доступні дії:\n"
        "• 🔍 Пошук — знайти лот за назвою предмета\n"
        "• 🔎 Усі лоти\n"
        "• ⚔️ Спорядження\n"
        "• 🧪 Зілля\n"
        "• 🪨 Матеріали\n\n"
        "Продавці приховані. Власні лоти у списку покупки не показуються."
    )


def auction_search_reply_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Категорії")
    kb.row("🔙 Торговий дім")
    return kb


def auction_search_results_reply_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Категорії")
    kb.row("🔍 Новий пошук")
    kb.row("🔙 Торговий дім")
    return kb


def build_auction_search_prompt_text_v1():
    return (
        "🔍 Пошук лотів\n\n"
        "Введіть частину назви предмета, який хочете знайти.\n\n"
        "Приклади запиту:\n"
        "• жезл\n"
        "• обладунок\n"
        "• камінь\n"
        "• зілля\n\n"
        "Мінімум: 2 символи."
    )


def auction_search_sort_inline_buttons_v1(sort_key):
    buttons = []
    for key, label in AUCTION_BUY_SORT_LABELS_V1.items():
        prefix = "✅ " if key == sort_key else ""
        buttons.append(types.InlineKeyboardButton(prefix + label, callback_data=f"ah_search_page:{key}:0"))
    return buttons


def auction_search_results_inline_kb_v1(user_id, query, sort_key="new", page=0):
    from db import get_auction_lots_for_buy_search

    page = max(0, int(page or 0))
    offset = page * AUCTION_SEARCH_PAGE_SIZE_V1
    lots = get_auction_lots_for_buy_search(
        buyer_user_id=user_id,
        search_text=query,
        sort_key=sort_key,
        limit=AUCTION_SEARCH_PAGE_SIZE_V1 + 1,
        offset=offset,
    )

    visible_lots = lots[:AUCTION_SEARCH_PAGE_SIZE_V1]
    has_next = len(lots) > AUCTION_SEARCH_PAGE_SIZE_V1

    kb = types.InlineKeyboardMarkup(row_width=1)

    sort_buttons = auction_search_sort_inline_buttons_v1(sort_key)
    kb.row(*sort_buttons[:2])
    kb.row(*sort_buttons[2:4])
    kb.row(*sort_buttons[4:])

    for lot in visible_lots:
        quantity = int(lot["quantity"] or 1)
        qty = f" x{quantity}" if quantity > 1 and f"x{quantity}" not in lot["item_name"] else ""
        label = f"📦 {_auction_lot_typed_name_17_1_0(lot)}{qty} — {lot['price']} 💰"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_search_lot:{lot['id']}:{sort_key}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"ah_search_page:{sort_key}:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Далі", callback_data=f"ah_search_page:{sort_key}:{page + 1}"))
    if nav:
        kb.row(*nav)

    # Назад до категорій робимо через inline, бо це повернення саме до buy-category screen.
    kb.add(types.InlineKeyboardButton("🔙 Категорії", callback_data="ah_buy2_categories"))
    return kb, visible_lots, has_next


def build_auction_search_results_text_v1(query, sort_key="new", page=0):
    sort_label = AUCTION_BUY_SORT_LABELS_V1.get(sort_key, AUCTION_BUY_SORT_LABELS_V1["new"])
    return (
        "🔍 Результати пошуку\n\n"
        f"Запит: {query}\n"
        f"↕️ Сортування: {sort_label}\n"
        f"📄 Сторінка: {int(page) + 1}\n\n"
        "Оберіть лот inline-кнопкою нижче."
    )


def auction_search_lot_view_kb_v1(lot_id, sort_key="new", page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Купити", callback_data=f"ah_search_confirm:{lot_id}:{sort_key}:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 До результатів", callback_data=f"ah_search_page:{sort_key}:{page}"))
    return kb


def auction_search_confirm_kb_v1(lot_id, sort_key="new", page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Підтвердити покупку", callback_data=f"ah_search_do:{lot_id}:{sort_key}:{page}"))
    kb.add(types.InlineKeyboardButton("❌ Назад", callback_data=f"ah_search_lot:{lot_id}:{sort_key}:{page}"))
    return kb


def _auction_get_search_query_v1(user_id):
    state = AUCTION_SEARCH_STATE_V1.get(user_id) or {}
    return state.get("query", "")


def _auction_show_search_results_v1(bot, chat_id, user_id, sort_key="new", page=0, edit_message=None):
    query = _auction_get_search_query_v1(user_id)
    text = build_auction_search_results_text_v1(query, sort_key=sort_key, page=page)
    kb, lots, has_next = auction_search_results_inline_kb_v1(user_id, query, sort_key=sort_key, page=page)

    if not lots:
        text += "\n\nНічого не знайдено. Спробуйте інший запит."

    if edit_message is not None:
        try:
            bot.edit_message_text(text, chat_id=chat_id, message_id=edit_message.message_id, reply_markup=kb)
            return
        except Exception:
            pass

    bot.send_message(chat_id, text, reply_markup=kb)


def _auction_register_buy_search_handlers_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_SEARCH_BUTTON_V1)
    def auction_search_start_v1(message):
        user_id = message.from_user.id
        AUCTION_SEARCH_STATE_V1[user_id] = {"step": "query"}
        bot.send_message(
            message.chat.id,
            build_auction_search_prompt_text_v1(),
            reply_markup=auction_search_reply_kb_v1()
        )

    @bot.message_handler(func=lambda m: m.text == "🔍 Новий пошук")
    def auction_search_new_v1(message):
        user_id = message.from_user.id
        AUCTION_SEARCH_STATE_V1[user_id] = {"step": "query"}
        bot.send_message(
            message.chat.id,
            build_auction_search_prompt_text_v1(),
            reply_markup=auction_search_reply_kb_v1()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Категорії")
    def auction_search_back_to_categories_v1(message):
        user_id = message.from_user.id
        AUCTION_SEARCH_STATE_V1.pop(user_id, None)
        bot.send_message(
            message.chat.id,
            build_auction_buy_category_text_v1(),
            reply_markup=auction_buy_category_kb_v1()
        )

    @bot.message_handler(func=lambda m: m.from_user.id in AUCTION_SEARCH_STATE_V1)
    def auction_search_query_router_v1(message):
        user_id = message.from_user.id
        text = (message.text or "").strip()

        if text == "🔙 Торговий дім":
            AUCTION_SEARCH_STATE_V1.pop(user_id, None)
            try:
                if "_auction_main_menu_text_v2" in globals():
                    menu_text = _auction_main_menu_text_v2(user_id)
                else:
                    menu_text = build_auction_house_text(user_id)
            except Exception:
                menu_text = build_auction_house_text(user_id)

            bot.send_message(message.chat.id, menu_text, reply_markup=auction_house_kb())
            return

        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Введіть мінімум 2 символи для пошуку.", reply_markup=auction_search_reply_kb_v1())
            return

        from db import normalize_auction_search_query
        query = normalize_auction_search_query(text)

        AUCTION_SEARCH_STATE_V1[user_id] = {
            "step": "results",
            "query": query,
            "sort_key": "new",
            "page": 0,
        }

        bot.send_message(
            message.chat.id,
            "🔍 Пошук виконано.",
            reply_markup=auction_search_results_reply_kb_v1()
        )
        _auction_show_search_results_v1(bot, message.chat.id, user_id, sort_key="new", page=0)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_search_page:"))
    def auction_search_page_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        sort_key = parts[1]
        page = int(parts[2])

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not _auction_get_search_query_v1(user_id):
            bot.send_message(call.message.chat.id, build_auction_search_prompt_text_v1(), reply_markup=auction_search_reply_kb_v1())
            return

        AUCTION_SEARCH_STATE_V1[user_id]["sort_key"] = sort_key
        AUCTION_SEARCH_STATE_V1[user_id]["page"] = page
        _auction_show_search_results_v1(bot, call.message.chat.id, user_id, sort_key=sort_key, page=page, edit_message=call.message)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_search_lot:"))
    def auction_search_lot_view_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        sort_key = parts[2]
        page = int(parts[3])

        from db import build_auction_buy_lot_details_v2
        details = build_auction_buy_lot_details_v2(buyer_user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            bot.send_message(call.message.chat.id, details.get("message", "❌ Лот недоступний."), reply_markup=auction_search_results_reply_kb_v1())
            return

        try:
            bot.edit_message_text(details["text"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_search_lot_view_kb_v1(lot_id, sort_key, page))
        except Exception:
            bot.send_message(call.message.chat.id, details["text"], reply_markup=auction_search_lot_view_kb_v1(lot_id, sort_key, page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_search_confirm:"))
    def auction_search_confirm_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        sort_key = parts[2]
        page = int(parts[3])

        from db import build_auction_buy_lot_details_v2
        details = build_auction_buy_lot_details_v2(buyer_user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not details.get("success"):
            bot.send_message(call.message.chat.id, details.get("message", "❌ Лот недоступний."), reply_markup=auction_search_results_reply_kb_v1())
            return

        text = (
            "⚠️ Підтвердження покупки\n\n"
            f"{details['text']}\n\n"
            "Після підтвердження золото буде списано, а предмет додано в інвентар."
        )

        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=auction_search_confirm_kb_v1(lot_id, sort_key, page))
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=auction_search_confirm_kb_v1(lot_id, sort_key, page))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_search_do:"))
    def auction_search_do_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        lot_id = int(parts[1])
        sort_key = parts[2]
        page = int(parts[3])

        from db import buy_auction_lot_v2
        result = buy_auction_lot_v2(buyer_user_id=user_id, lot_id=lot_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not result.get("success"):
            bot.send_message(call.message.chat.id, result.get("message", "❌ Не вдалося купити лот."), reply_markup=auction_search_results_reply_kb_v1())
            return

        bot.send_message(
            call.message.chat.id,
            (
                "✅ Покупку завершено!\n\n"
                f"📦 {result.get('item_name')}\n"
                f"💰 Сплачено: {result.get('price')} золота\n\n"
                "Предмет додано в інвентар."
            ),
            reply_markup=auction_search_results_reply_kb_v1()
        )

        _auction_show_search_results_v1(bot, call.message.chat.id, user_id, sort_key=sort_key, page=page)


try:
    _auction_base_register_handlers_before_buy_search_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_buy_search_v1 = None


def register_auction_house_handlers(bot):
    # Register search before older buy/category handlers, so search reply buttons work predictably.
    _auction_register_buy_search_handlers_v1(bot)

    if _auction_base_register_handlers_before_buy_search_v1:
        _auction_base_register_handlers_before_buy_search_v1(bot)


# ==============================
# ✅ AUCTION HOUSE HISTORY AND MARKET PRICES UI V1
# ==============================

AUCTION_HISTORY_PAGE_SIZE_V1 = 8
AUCTION_HISTORY_STATE_V1 = {}
AUCTION_MARKET_PRICE_SEARCH_STATE_V1 = {}

AUCTION_HISTORY_MODE_LABELS_V1 = {
    "all": "📜 Уся історія",
    "buy": "🛒 Мої покупки",
    "sell": "💰 Мої продажі",
}


def auction_history_reply_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📈 Ринкові ціни")
    kb.row("🔙 Торговий дім")
    return kb


def auction_market_price_search_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Історія")
    kb.row("🔙 Торговий дім")
    return kb


def auction_history_inline_kb_v1(mode="all", page=0, has_next=False):
    kb = types.InlineKeyboardMarkup(row_width=1)

    row = []
    for key, label in AUCTION_HISTORY_MODE_LABELS_V1.items():
        prefix = "✅ " if key == mode else ""
        row.append(types.InlineKeyboardButton(prefix + label, callback_data=f"ah_hist:{key}:0"))
    kb.row(*row)

    nav = []
    if int(page) > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"ah_hist:{mode}:{int(page) - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Далі", callback_data=f"ah_hist:{mode}:{int(page) + 1}"))
    if nav:
        kb.row(*nav)

    return kb


def _auction_history_row_to_line_v1(row, viewer_user_id, index):
    from db import format_auction_history_date

    seller_id = int(row["seller_user_id"] or 0)
    buyer_id = int(row["buyer_user_id"] or 0)

    if buyer_id == int(viewer_user_id):
        action = "🛒 Куплено"
    elif seller_id == int(viewer_user_id):
        action = "💰 Продано"
    else:
        action = "📦 Угода"

    sold_date = row["sold_at"] if "sold_at" in row.keys() else row["created_at"]
    date_text = format_auction_history_date(sold_date, with_time=True)

    quantity = int(row["quantity"] or 1)
    qty = f" x{quantity}" if quantity > 1 and f"x{quantity}" not in row["item_name"] else ""

    return (
        f"{index}. {action}: {row['item_name']}{qty}\n"
        f"   💰 {row['price']} золота | 🕒 {date_text}"
    )


def build_auction_history_text_v1(user_id, mode="all", page=0):
    from db import get_user_auction_history

    page = max(0, int(page or 0))
    offset = page * AUCTION_HISTORY_PAGE_SIZE_V1
    rows = get_user_auction_history(user_id, mode=mode, limit=AUCTION_HISTORY_PAGE_SIZE_V1 + 1, offset=offset)

    visible = rows[:AUCTION_HISTORY_PAGE_SIZE_V1]
    has_next = len(rows) > AUCTION_HISTORY_PAGE_SIZE_V1
    mode_label = AUCTION_HISTORY_MODE_LABELS_V1.get(mode, AUCTION_HISTORY_MODE_LABELS_V1["all"])

    text = (
        "📜 Історія Торгового Дому\n\n"
        f"Розділ: {mode_label}\n"
        f"Сторінка: {page + 1}\n\n"
    )

    if not visible:
        text += "Записів поки немає."
    else:
        lines = []
        for idx, row in enumerate(visible, start=offset + 1):
            lines.append(_auction_history_row_to_line_v1(row, user_id, idx))
        text += "\n".join(lines)

    return text, auction_history_inline_kb_v1(mode=mode, page=page, has_next=has_next)


def build_auction_market_price_prompt_v1():
    return (
        "📈 Ринкові ціни\n\n"
        "Введіть частину назви предмета, щоб подивитися історію продажів.\n\n"
        "Приклади:\n"
        "• жезл\n"
        "• обладунок\n"
        "• камінь\n"
        "• зілля\n\n"
        "Мінімум: 2 символи."
    )


def build_auction_market_price_search_text_v1(query):
    from db import search_auction_market_price_stats, format_auction_history_date

    rows = search_auction_market_price_stats(query, limit=10)

    text = (
        "📈 Ринкові ціни\n\n"
        f"Запит: {query}\n\n"
    )

    if not rows:
        text += "Продажів за цим запитом ще не знайдено."
        return text

    lines = []
    for idx, row in enumerate(rows, start=1):
        try:
            avg_price = float(row["avg_price"] or 0)
            min_price = float(row["min_price"] or 0)
            max_price = float(row["max_price"] or 0)
        except Exception:
            avg_price = min_price = max_price = 0.0

        last_sale = format_auction_history_date(row["last_sale_at"], with_time=True)

        lines.append(
            f"{idx}. {row['item_name']}\n"
            f"   Продажів: {row['sales_count']} | Середня: {avg_price:.2f} 💰\n"
            f"   Мін: {min_price:.2f} 💰 | Макс: {max_price:.2f} 💰\n"
            f"   Останній продаж: {last_sale}"
        )

    text += "\n\n".join(lines)
    return text


def build_auction_lot_market_price_text_v1(lot_id):
    from db import get_auction_lot_market_price_stats, format_auction_history_date

    result = get_auction_lot_market_price_stats(lot_id)

    if not result.get("success"):
        return result.get("message", "❌ Не вдалося отримати історію цін.")

    item_name = result.get("item_name", "Предмет")

    text = (
        "📈 Ринкові ціни\n\n"
        f"📦 {item_name}\n\n"
    )

    if int(result.get("count", 0) or 0) <= 0:
        text += result.get("message", "Історії продажів ще немає.")
        return text

    text += (
        f"Продажів враховано: {result['count']}\n"
        f"Остання ціна: {float(result['last_price']):.2f} 💰\n"
        f"Середня ціна: {float(result['avg_price']):.2f} 💰\n"
        f"Мінімальна ціна: {float(result['min_price']):.2f} 💰\n"
        f"Максимальна ціна: {float(result['max_price']):.2f} 💰\n\n"
        "Останні продажі:\n"
    )

    for row in result.get("rows", [])[:5]:
        date_text = format_auction_history_date(row["history_date"], with_time=True)
        text += f"• {row['price']} 💰 — {date_text}\n"

    return text.rstrip()


# Add 📈 button into lot view keyboards, without adding back-to-house inline.
try:
    _auction_base_buy_lot_view_kb_before_history_v1 = auction_buy_lot_view_kb_v1
except NameError:
    _auction_base_buy_lot_view_kb_before_history_v1 = None


def auction_buy_lot_view_kb_v1(lot_id, category="all", sort_key="new", page=0):
    if not _auction_base_buy_lot_view_kb_before_history_v1:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("✅ Купити", callback_data=f"ah_buy2_confirm:{lot_id}:{category}:{sort_key}:{page}"))
        kb.add(types.InlineKeyboardButton("📈 Ринкові ціни", callback_data=f"ah_price_lot:{lot_id}"))
        return kb

    kb = _auction_base_buy_lot_view_kb_before_history_v1(lot_id, category=category, sort_key=sort_key, page=page)
    try:
        kb.add(types.InlineKeyboardButton("📈 Ринкові ціни", callback_data=f"ah_price_lot:{lot_id}"))
    except Exception:
        pass
    try:
        if "_auction_strip_back_to_house_inline_v1" in globals():
            kb = _auction_strip_back_to_house_inline_v1(kb)
    except Exception:
        pass
    return kb

try:
    _auction_base_search_lot_view_kb_before_history_v1 = auction_search_lot_view_kb_v1
except NameError:
    _auction_base_search_lot_view_kb_before_history_v1 = None


def auction_search_lot_view_kb_v1(lot_id, sort_key="new", page=0):
    if not _auction_base_search_lot_view_kb_before_history_v1:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("✅ Купити", callback_data=f"ah_search_confirm:{lot_id}:{sort_key}:{page}"))
        kb.add(types.InlineKeyboardButton("📈 Ринкові ціни", callback_data=f"ah_price_lot:{lot_id}"))
        return kb

    kb = _auction_base_search_lot_view_kb_before_history_v1(lot_id, sort_key=sort_key, page=page)
    try:
        kb.add(types.InlineKeyboardButton("📈 Ринкові ціни", callback_data=f"ah_price_lot:{lot_id}"))
    except Exception:
        pass
    return kb


def auction_price_back_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Торговий дім")
    return kb


def _auction_register_history_market_prices_handlers_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_HISTORY_BUTTON)
    def auction_history_start_v1(message):
        user_id = message.from_user.id
        text, inline_kb = build_auction_history_text_v1(user_id, mode="all", page=0)
        bot.send_message(
            message.chat.id,
            "📜 Розділ «Історія» відкрито.",
            reply_markup=auction_history_reply_kb_v1()
        )
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_hist:"))
    def auction_history_page_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        mode = parts[1]
        page = int(parts[2])
        text, inline_kb = build_auction_history_text_v1(user_id, mode=mode, page=page)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=inline_kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=inline_kb)

    @bot.message_handler(func=lambda m: m.text == "📈 Ринкові ціни")
    def auction_market_price_search_start_v1(message):
        user_id = message.from_user.id
        AUCTION_MARKET_PRICE_SEARCH_STATE_V1[user_id] = True
        bot.send_message(
            message.chat.id,
            build_auction_market_price_prompt_v1(),
            reply_markup=auction_market_price_search_kb_v1()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Історія")
    def auction_market_price_back_history_v1(message):
        user_id = message.from_user.id
        AUCTION_MARKET_PRICE_SEARCH_STATE_V1.pop(user_id, None)
        text, inline_kb = build_auction_history_text_v1(user_id, mode="all", page=0)
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)

    @bot.message_handler(func=lambda m: m.from_user.id in AUCTION_MARKET_PRICE_SEARCH_STATE_V1)
    def auction_market_price_search_query_v1(message):
        user_id = message.from_user.id
        text = (message.text or "").strip()

        if text == "🔙 Торговий дім":
            AUCTION_MARKET_PRICE_SEARCH_STATE_V1.pop(user_id, None)
            try:
                if "_auction_main_menu_text_v2" in globals():
                    menu_text = _auction_main_menu_text_v2(user_id)
                else:
                    menu_text = build_auction_house_text(user_id)
            except Exception:
                menu_text = build_auction_house_text(user_id)
            bot.send_message(message.chat.id, menu_text, reply_markup=auction_house_kb())
            return

        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Введіть мінімум 2 символи.", reply_markup=auction_market_price_search_kb_v1())
            return

        bot.send_message(
            message.chat.id,
            build_auction_market_price_search_text_v1(text),
            reply_markup=auction_market_price_search_kb_v1()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_price_lot:"))
    def auction_lot_price_history_callback_v1(call):
        lot_id = int(call.data.split(":")[1])

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        text = build_auction_lot_market_price_text_v1(lot_id)
        bot.send_message(call.message.chat.id, text, reply_markup=auction_price_back_kb_v1())


try:
    _auction_base_register_handlers_before_history_market_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_history_market_v1 = None


def register_auction_house_handlers(bot):
    # History/market price handlers should be before old placeholder history handlers.
    _auction_register_history_market_prices_handlers_v1(bot)

    if _auction_base_register_handlers_before_history_market_v1:
        _auction_base_register_handlers_before_history_market_v1(bot)


# ==============================
# ✅ AUCTION HISTORY KEYBOARD RESTORE V1
# ==============================

# Виправлення UX у розділі історії:
# після натискання звичайної кнопки "🔙 Історія" з меню ринкових цін
# нижня ReplyKeyboard має повертатися до клавіатури історії:
#   📈 Ринкові ціни
#   🔙 Торговий дім
# а не залишати кнопку "🔙 Історія".


def _auction_open_history_screen_v1(bot, chat_id, user_id, mode="all", page=0):
    """Відкриває історію і гарантовано повертає правильну нижню клавіатуру."""

    try:
        AUCTION_MARKET_PRICE_SEARCH_STATE_V1.pop(user_id, None)
    except Exception:
        pass

    try:
        text, inline_kb = build_auction_history_text_v1(user_id, mode=mode, page=page)
    except Exception:
        text = "📜 Історія Торгового Дому\n\nЗаписів поки немає."
        inline_kb = None

    # Спочатку міняємо нижню клавіатуру на клавіатуру розділу історії.
    try:
        bot.send_message(
            chat_id,
            "📜 Розділ «Історія» відкрито.",
            reply_markup=auction_history_reply_kb_v1()
        )
    except Exception:
        pass

    # Потім надсилаємо саму історію з inline-фільтрами.
    bot.send_message(chat_id, text, reply_markup=inline_kb)


def _auction_register_history_keyboard_restore_v1(bot):

    @bot.message_handler(func=lambda m: m.text == "🔙 Історія")
    def auction_history_back_restore_keyboard_v1(message):
        user_id = message.from_user.id
        _auction_open_history_screen_v1(
            bot=bot,
            chat_id=message.chat.id,
            user_id=user_id,
            mode="all",
            page=0,
        )


try:
    _auction_base_register_handlers_before_history_keyboard_restore_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_history_keyboard_restore_v1 = None


def register_auction_house_handlers(bot):
    # Має реєструватися раніше старого handler-а "🔙 Історія",
    # який повертав історію без відновлення нижньої клавіатури.
    _auction_register_history_keyboard_restore_v1(bot)

    if _auction_base_register_handlers_before_history_keyboard_restore_v1:
        _auction_base_register_handlers_before_history_keyboard_restore_v1(bot)


# ==============================
# ✅ AUCTION HOUSE EXPIRATION CLEANUP UI V2
# ==============================


def build_auction_cleanup_report_text_v2(result=None):
    if result is None:
        from db import get_auction_cleanup_report
        result = get_auction_cleanup_report()

    counts = result.get("status_counts", {}) if isinstance(result, dict) else {}

    return (
        "🧹 Auction cleanup / Торговий Дім\n\n"
        f"ACTIVE: {counts.get('ACTIVE', 0)}\n"
        f"SOLD_UNCLAIMED: {counts.get('SOLD_UNCLAIMED', 0)}\n"
        f"SOLD_CLAIMED: {counts.get('SOLD_CLAIMED', 0)}\n"
        f"EXPIRED_UNCLAIMED: {counts.get('EXPIRED_UNCLAIMED', 0)}\n"
        f"EXPIRED_CLAIMED: {counts.get('EXPIRED_CLAIMED', 0)}\n"
        f"DELETED: {counts.get('DELETED', 0)}"
    )


try:
    _auction_base_build_auction_house_text_before_cleanup_v2 = build_auction_house_text
except NameError:
    _auction_base_build_auction_house_text_before_cleanup_v2 = None


def build_auction_house_text(user_id):
    """Override: cleanup runs whenever player opens Auction House."""

    try:
        from db import update_expired_auction_lots
        update_expired_auction_lots()
    except Exception:
        pass

    if _auction_base_build_auction_house_text_before_cleanup_v2:
        return _auction_base_build_auction_house_text_before_cleanup_v2(user_id)

    return (
        "🏛️ Торговий дім\n\n"
        "Тут гравці можуть виставляти товари, купувати лоти та забирати завершені продажі."
    )


def _auction_register_expiration_cleanup_handlers_v2(bot):

    @bot.message_handler(commands=["auction_cleanup"])
    def auction_cleanup_command_v2(message):
        from db import update_expired_auction_lots, get_auction_cleanup_report

        cleanup = update_expired_auction_lots()
        report = get_auction_cleanup_report()

        text = (
            "🧹 Cleanup виконано.\n\n"
            f"ACTIVE → EXPIRED_UNCLAIMED: {cleanup.get('expired_active', 0)}\n"
            f"EXPIRED_UNCLAIMED → DELETED: {cleanup.get('deleted_expired_unclaimed', 0)}\n"
            f"SOLD_UNCLAIMED → DELETED: {cleanup.get('deleted_sold_unclaimed', 0)}\n"
            f"Виправлено delete_after: {cleanup.get('fixed_missing_delete_after', 0)}\n\n"
            f"{build_auction_cleanup_report_text_v2(report)}"
        )

        bot.send_message(message.chat.id, text)

    @bot.message_handler(commands=["auction_debug"])
    def auction_debug_command_v2(message):
        from db import get_auction_cleanup_report
        bot.send_message(message.chat.id, build_auction_cleanup_report_text_v2(get_auction_cleanup_report()))


try:
    _auction_base_register_handlers_before_expiration_cleanup_v2 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_expiration_cleanup_v2 = None


def register_auction_house_handlers(bot):
    _auction_register_expiration_cleanup_handlers_v2(bot)

    if _auction_base_register_handlers_before_expiration_cleanup_v2:
        _auction_base_register_handlers_before_expiration_cleanup_v2(bot)


# ==============================
# ✅ AUCTION HOUSE STABILIZATION DIAGNOSTICS UI V1
# ==============================


def _auction_list_short_v1(values, limit=10):
    values = list(values or [])
    if not values:
        return "немає"

    shown = values[:limit]
    text = ", ".join(str(x) for x in shown)
    if len(values) > limit:
        text += f" ... +{len(values) - limit}"
    return text


def build_auction_diagnostics_text_v1(report):
    counts = report.get("status_counts", {}) if isinstance(report, dict) else {}
    active_by_seller = report.get("active_lots_by_seller", []) if isinstance(report, dict) else []

    top_sellers = []
    for row in active_by_seller[:5]:
        top_sellers.append(f"{row.get('seller_user_id')}: {row.get('active_count')}")

    if not top_sellers:
        top_sellers_text = "немає"
    else:
        top_sellers_text = "\n".join(f"• {x}" for x in top_sellers)

    return (
        "🧪 Auction diagnostics\n\n"
        f"Таблиці OK: {'так' if report.get('tables_ok') else 'ні'}\n"
        f"Всього лотів: {report.get('total_lots', 0)}\n\n"
        "Статуси:\n"
        f"• ACTIVE: {counts.get('ACTIVE', 0)}\n"
        f"• SOLD_UNCLAIMED: {counts.get('SOLD_UNCLAIMED', 0)}\n"
        f"• SOLD_CLAIMED: {counts.get('SOLD_CLAIMED', 0)}\n"
        f"• EXPIRED_UNCLAIMED: {counts.get('EXPIRED_UNCLAIMED', 0)}\n"
        f"• EXPIRED_CLAIMED: {counts.get('EXPIRED_CLAIMED', 0)}\n"
        f"• DELETED: {counts.get('DELETED', 0)}\n\n"
        "Потенційні проблеми:\n"
        f"• Некоректна ціна: {_auction_list_short_v1(report.get('bad_price_lots'))}\n"
        f"• Немає snapshot: {_auction_list_short_v1(report.get('missing_snapshot_lots'))}\n"
        f"• ACTIVE без expires_at: {_auction_list_short_v1(report.get('active_missing_expires_at'))}\n"
        f"• Unclaimed без delete_after: {_auction_list_short_v1(report.get('unclaimed_missing_delete_after'))}\n"
        f"• SOLD_UNCLAIMED без buyer: {_auction_list_short_v1(report.get('sold_unclaimed_without_buyer'))}\n\n"
        "Активні лоти за продавцями TOP-5:\n"
        f"{top_sellers_text}"
    )


def _auction_register_stabilization_diagnostics_handlers_v1(bot):

    @bot.message_handler(commands=["auction_sanity"])
    def auction_sanity_command_v1(message):
        from db import get_auction_diagnostics_report
        report = get_auction_diagnostics_report()
        bot.send_message(message.chat.id, build_auction_diagnostics_text_v1(report))

    @bot.message_handler(commands=["auction_fix"])
    def auction_fix_command_v1(message):
        from db import run_auction_sanity_fix
        result = run_auction_sanity_fix()
        cleanup = result.get("cleanup", {})
        after = result.get("after", {})

        text = (
            "🛠 Auction sanity fix виконано.\n\n"
            f"ACTIVE → EXPIRED_UNCLAIMED: {cleanup.get('expired_active', 0)}\n"
            f"EXPIRED_UNCLAIMED → DELETED: {cleanup.get('deleted_expired_unclaimed', 0)}\n"
            f"SOLD_UNCLAIMED → DELETED: {cleanup.get('deleted_sold_unclaimed', 0)}\n"
            f"Виправлено delete_after: {cleanup.get('fixed_missing_delete_after', 0)}\n\n"
            f"{build_auction_diagnostics_text_v1(after)}"
        )

        bot.send_message(message.chat.id, text)


try:
    _auction_base_register_handlers_before_stabilization_diagnostics_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_stabilization_diagnostics_v1 = None


def register_auction_house_handlers(bot):
    _auction_register_stabilization_diagnostics_handlers_v1(bot)

    if _auction_base_register_handlers_before_stabilization_diagnostics_v1:
        _auction_base_register_handlers_before_stabilization_diagnostics_v1(bot)


# ==============================
# ✅ AUCTION ADMIN COMMAND GUARD V1
# ==============================

# Захищає технічні команди Торгового Дому від звичайних гравців.
# Команди:
# /auction_sanity
# /auction_fix
# /auction_cleanup
# /auction_debug
#
# За замовчуванням дозволено user_id=243129101.
# Додатково можна задати змінну середовища:
# AUCTION_ADMIN_IDS=243129101,123456789
# або ADMIN_USER_IDS=243129101,123456789


def _auction_get_admin_ids_v1():
    import os

    raw = (
        os.getenv("AUCTION_ADMIN_IDS")
        or os.getenv("ADMIN_USER_IDS")
        or "243129101"
    )

    result = set()

    for part in str(raw).replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.add(int(part))
        except Exception:
            pass

    return result


def _auction_is_admin_v1(user_id):
    return int(user_id) in _auction_get_admin_ids_v1()


def _auction_admin_denied_text_v1():
    return (
        "⛔ Команда доступна тільки адміністратору.\n\n"
        "Це технічна команда Торгового Дому."
    )


def _auction_safe_report_text_v1():
    try:
        from db import get_auction_diagnostics_report
        report = get_auction_diagnostics_report()
        return build_auction_diagnostics_text_v1(report)
    except Exception:
        try:
            from db import get_auction_cleanup_report
            result = get_auction_cleanup_report()
            return build_auction_cleanup_report_text_v2(result)
        except Exception as error:
            return f"❌ Не вдалося сформувати звіт Торгового Дому.\n\n{error}"


def _auction_register_admin_command_guard_v1(bot):

    @bot.message_handler(commands=["auction_sanity"])
    def auction_sanity_admin_guard_v1(message):
        if not _auction_is_admin_v1(message.from_user.id):
            bot.send_message(message.chat.id, _auction_admin_denied_text_v1())
            return

        bot.send_message(message.chat.id, _auction_safe_report_text_v1())

    @bot.message_handler(commands=["auction_debug"])
    def auction_debug_admin_guard_v1(message):
        if not _auction_is_admin_v1(message.from_user.id):
            bot.send_message(message.chat.id, _auction_admin_denied_text_v1())
            return

        bot.send_message(message.chat.id, _auction_safe_report_text_v1())

    @bot.message_handler(commands=["auction_fix"])
    def auction_fix_admin_guard_v1(message):
        if not _auction_is_admin_v1(message.from_user.id):
            bot.send_message(message.chat.id, _auction_admin_denied_text_v1())
            return

        try:
            from db import run_auction_sanity_fix
            result = run_auction_sanity_fix()
            cleanup = result.get("cleanup", {})
            after = result.get("after", {})

            text = (
                "🛠 Auction sanity fix виконано.\n\n"
                f"ACTIVE → EXPIRED_UNCLAIMED: {cleanup.get('expired_active', 0)}\n"
                f"EXPIRED_UNCLAIMED → DELETED: {cleanup.get('deleted_expired_unclaimed', 0)}\n"
                f"SOLD_UNCLAIMED → DELETED: {cleanup.get('deleted_sold_unclaimed', 0)}\n"
                f"Виправлено delete_after: {cleanup.get('fixed_missing_delete_after', 0)}\n\n"
                f"{build_auction_diagnostics_text_v1(after)}"
            )

        except Exception as error:
            text = f"❌ Помилка auction_fix.\n\n{error}"

        bot.send_message(message.chat.id, text)

    @bot.message_handler(commands=["auction_cleanup"])
    def auction_cleanup_admin_guard_v1(message):
        if not _auction_is_admin_v1(message.from_user.id):
            bot.send_message(message.chat.id, _auction_admin_denied_text_v1())
            return

        try:
            from db import update_expired_auction_lots, get_auction_cleanup_report
            cleanup = update_expired_auction_lots()
            report = get_auction_cleanup_report()

            text = (
                "🧹 Cleanup виконано.\n\n"
                f"ACTIVE → EXPIRED_UNCLAIMED: {cleanup.get('expired_active', 0)}\n"
                f"EXPIRED_UNCLAIMED → DELETED: {cleanup.get('deleted_expired_unclaimed', 0)}\n"
                f"SOLD_UNCLAIMED → DELETED: {cleanup.get('deleted_sold_unclaimed', 0)}\n"
                f"Виправлено delete_after: {cleanup.get('fixed_missing_delete_after', 0)}\n\n"
                f"{build_auction_cleanup_report_text_v2(report)}"
            )

        except Exception as error:
            text = f"❌ Помилка auction_cleanup.\n\n{error}"

        bot.send_message(message.chat.id, text)


try:
    _auction_base_register_handlers_before_admin_guard_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_admin_guard_v1 = None


def register_auction_house_handlers(bot):
    # Реєструємо guard ПЕРЕД старими технічними handlers,
    # щоб звичайні гравці не могли виконати debug/fix/cleanup.
    _auction_register_admin_command_guard_v1(bot)

    if _auction_base_register_handlers_before_admin_guard_v1:
        _auction_base_register_handlers_before_admin_guard_v1(bot)

# ROM 12.6.3c AUCTION RUNE CATEGORY AND TRANSFER POLICY ALIGNMENT
# ROM Stage 17.31.1.8 distinct Auction buy labels
AUCTION_RUNE_CATEGORY_BUTTON_12_6_3C = "💠 Руни"
AUCTION_BUY_RUNE_CATEGORY_BUTTON_17_31_1_8 = "💠 Руни в продажу"
AUCTION_BUY_CONSUMABLE_CATEGORY_BUTTON_17_31_1_8 = "🧰 Витратні предмети в продажу"
AUCTION_SELL_INLINE_CATEGORY_BUTTONS[AUCTION_RUNE_CATEGORY_BUTTON_12_6_3C] = "rune"
AUCTION_SELL_CATEGORY_BUTTONS_V1["rune"] = AUCTION_RUNE_CATEGORY_BUTTON_12_6_3C
AUCTION_BUY_CATEGORY_BUTTONS_V1["rune"] = AUCTION_BUY_RUNE_CATEGORY_BUTTON_17_31_1_8
AUCTION_BUY_CATEGORY_BUTTONS_V1["consumable"] = AUCTION_BUY_CONSUMABLE_CATEGORY_BUTTON_17_31_1_8
AUCTION_BUY_CATEGORY_BY_BUTTON_V1[AUCTION_BUY_RUNE_CATEGORY_BUTTON_17_31_1_8] = "rune"
AUCTION_BUY_CATEGORY_BY_BUTTON_V1[AUCTION_BUY_CONSUMABLE_CATEGORY_BUTTON_17_31_1_8] = "consumable"


def auction_sell_inline_category_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_EQUIPMENT_CATEGORY_BUTTON, globals().get("AUCTION_STACK_CATEGORY_POTION_BUTTON", "🧪 Зілля для продажу"))
    kb.row(globals().get("AUCTION_STACK_CATEGORY_MATERIAL_BUTTON", "🪨 Матеріали"), AUCTION_RUNE_CATEGORY_BUTTON_12_6_3C)
    kb.row(AUCTION_BACK_TO_MENU_BUTTON)
    return kb


def build_auction_sell_start_text_inline_v1():
    return (
        "➕ Виставити товар\n\nОберіть категорію товару.\n\n"
        "Предмети показуються inline-кнопками по 8 на сторінку.\n\n"
        "Доступні категорії:\n• ⚔️ Спорядження\n• 🧪 Зілля\n• 🪨 Матеріали\n• 💠 Руни\n\n"
        "Не можна виставляти Сферу нового шляху, Руну Успіху, Жетони Фіріуса, "
        "Досконалий Екстрактор, екіпіровані, зламані, bound/quest/DEV/premium та "
        "зарезервовані прямим обміном предмети."
    )


_auction_base_build_sell_list_text_12_6_3c = build_auction_sell_inline_list_text_v1

def build_auction_sell_inline_list_text_v1(user_id, category, page=0):
    if category == "rune":
        kb, items, has_next = auction_sell_items_inline_kb_v1(user_id, category, page=page)
        text = f"💠 Виставлення рун\n\nСторінка: {int(page)+1}\n\n"
        text += "Оберіть предмет inline-кнопкою нижче." if items else "Немає доступних рун для продажу."
        return text, kb
    return _auction_base_build_sell_list_text_12_6_3c(user_id, category, page=page)


def auction_buy_category_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["all"])
    kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["equipment"], AUCTION_BUY_CATEGORY_BUTTONS_V1["potion"])
    kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["material"], AUCTION_BUY_CATEGORY_BUTTONS_V1["rune"])
    kb.row(AUCTION_BUY_CATEGORY_BUTTONS_V1["consumable"])
    kb.row(AUCTION_BACK_TO_MENU_BUTTON)
    return kb

# Stage 17.11.2 compact Auction House text wrappers.
def _compact_action_list_17_11_2(text, stop_marker=None):
    marker = "\n\nДоступні дії:\n"
    if marker not in text:
        marker = "Доступні дії:\n"
    if marker not in text:
        return text
    start = text.index(marker)
    if stop_marker and stop_marker in text[start:]:
        end = text.index(stop_marker, start)
        return (text[:start].rstrip() + "\n\n" + text[end:].lstrip()).strip()
    return text[:start].rstrip()

_BASE_BUILD_AUCTION_HOUSE_TEXT_17_11_2 = build_auction_house_text
_BASE_AUCTION_MAIN_MENU_TEXT_V1_17_11_2 = _auction_main_menu_text_v1
_BASE_AUCTION_MAIN_MENU_TEXT_V2_17_11_2 = _auction_main_menu_text_v2
_BASE_AUCTION_BUY_CATEGORY_TEXT_17_11_2 = build_auction_buy_category_text_v1


def build_auction_house_text(*args, **kwargs):
    return _compact_action_list_17_11_2(
        _BASE_BUILD_AUCTION_HOUSE_TEXT_17_11_2(*args, **kwargs),
        stop_marker="ℹ️ Правила:",
    )


def _auction_main_menu_text_v1(*args, **kwargs):
    return _compact_action_list_17_11_2(
        _BASE_AUCTION_MAIN_MENU_TEXT_V1_17_11_2(*args, **kwargs)
    )


def _auction_main_menu_text_v2(*args, **kwargs):
    return _compact_action_list_17_11_2(
        _BASE_AUCTION_MAIN_MENU_TEXT_V2_17_11_2(*args, **kwargs)
    )


def build_auction_buy_category_text_v1(*args, **kwargs):
    text = _BASE_AUCTION_BUY_CATEGORY_TEXT_17_11_2(*args, **kwargs)
    return _compact_action_list_17_11_2(
        text,
        stop_marker="Продавці приховані.",
    )


# ROM Stage 17.31.1 canonical consumables integration
