from telebot import types
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

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_BUTTON)
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

        button_text = f"📦 #{item['inventory_id']} {item['name']}{durability}"

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
        f"📦 {snapshot['name']}\n"
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
        f"{snapshot['name']}\n\n"
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

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_BUTTON)
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
        button_text = f"📦 #{item['inventory_id']} {item['name']} x{item['quantity']}"
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
        f"📦 {snapshot['name']} x{quantity}\n\n"
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
        f"{snapshot['name']} x{quantity}\n\n"
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

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_BUTTON)
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
        qty = f" x{quantity}" if quantity > 1 and f"x{quantity}" not in lot["item_name"] else ""
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
            label = f"📦 {item['name']}{durability}"
        else:
            label = f"📦 {item['name']} x{item['quantity']}"

        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_sell_item:{category}:{item['inventory_id']}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Попередні", callback_data=f"ah_sell_page:{category}:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Наступні", callback_data=f"ah_sell_page:{category}:{page + 1}"))
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

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_BUTTON)
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
        qty = f" x{quantity}" if quantity > 1 and f"x{quantity}" not in lot["item_name"] else ""
        label = f"🛒 {lot['item_name']}{qty} — {lot['price']} 💰"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_buy_lot:{lot['id']}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Попередні", callback_data=f"ah_buy_page:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Наступні", callback_data=f"ah_buy_page:{page + 1}"))
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

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_BUTTON)
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

