from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_4_auction_sell_stack_items"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE STACK LISTING V1"
DB_MARKER = "# ✅ AUCTION HOUSE STACK LISTING WRAPPERS V1"
HANDLER_MARKER = "# ✅ AUCTION HOUSE SELL STACK ITEMS V2"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE STACK LISTING V1
# ==============================

AUCTION_STACK_PAGE_SIZE = 8
AUCTION_FORBIDDEN_AUCTION_ITEM_IDS = {
    402,  # 💎 Руна Успіху — майбутній premium/crystal item, не продається на ринку.
}


def _auction_is_success_rune(snapshot):
    item_id = int(snapshot.get("item_id", 0) or 0)
    name = str(snapshot.get("name", "") or snapshot.get("raw_name", ""))
    return item_id in AUCTION_FORBIDDEN_AUCTION_ITEM_IDS or "Руна Успіху" in name


def _auction_is_potion_snapshot(snapshot):
    item_type = str(snapshot.get("item_type", "") or "").lower()
    item_category = str(snapshot.get("item_category", "") or "").lower()
    name = str(snapshot.get("name", "") or snapshot.get("raw_name", "")).lower()

    if item_type in ["potion", "heal_potion", "mana_potion"]:
        return True

    if item_category in ["potion", "potions"]:
        return True

    if "зіл" in name or "potion" in name:
        return True

    return False


def _auction_is_material_snapshot(snapshot):
    item_id = int(snapshot.get("item_id", 0) or 0)
    item_type = str(snapshot.get("item_type", "") or "").lower()
    item_category = str(snapshot.get("item_category", "") or "").lower()
    name = str(snapshot.get("name", "") or snapshot.get("raw_name", "")).lower()

    if item_id == 401:
        return True

    if item_type in ["material", "refine_stone", "craft_material"]:
        return True

    if item_category in ["material", "materials"]:
        return True

    if "камінь посилення" in name:
        return True

    return False


def _auction_stack_category_matches(snapshot, category):
    category = normalize_auction_category(category)

    if category == AUCTION_CATEGORY_POTION:
        return _auction_is_potion_snapshot(snapshot)

    if category == AUCTION_CATEGORY_MATERIAL:
        return _auction_is_material_snapshot(snapshot)

    return False


def validate_inventory_stack_item_for_auction(user_id, inventory_id, category, quantity):
    """
    Validates stackable item listing for potions/materials.

    Rules:
    - item must belong to the requested category;
    - quantity must be > 0 and <= owned quantity;
    - 💎 Runa Uspikhu / item_id=402 is forbidden;
    - equipment is handled by create_equipment_auction_lot(), not here.
    """

    category = normalize_auction_category(category)

    if category not in [AUCTION_CATEGORY_POTION, AUCTION_CATEGORY_MATERIAL]:
        return {
            "success": False,
            "message": "❌ Для стекових предметів доступні тільки категорії 🧪 Зілля та 🪨 Матеріали.",
        }

    snapshot_result = get_inventory_item_snapshot_for_auction(user_id, inventory_id)

    if not snapshot_result.get("success"):
        return snapshot_result

    snapshot = snapshot_result["snapshot"]

    if _auction_is_success_rune(snapshot):
        return {
            "success": False,
            "message": "❌ 💎 Руну Успіху не можна виставити на Торговий Дім.",
        }

    if not _auction_stack_category_matches(snapshot, category):
        return {
            "success": False,
            "message": "❌ Предмет не належить до обраної категорії.",
        }

    owned_quantity = int(snapshot.get("quantity", 0) or 0)

    try:
        quantity = int(quantity)
    except Exception:
        return {
            "success": False,
            "message": "❌ Кількість має бути числом.",
        }

    if quantity <= 0:
        return {
            "success": False,
            "message": "❌ Кількість має бути більшою за 0.",
        }

    if quantity > owned_quantity:
        return {
            "success": False,
            "message": f"❌ У тебе є тільки {owned_quantity} шт.",
        }

    snapshot["auction_quantity"] = quantity
    snapshot["owned_quantity"] = owned_quantity

    return {
        "success": True,
        "snapshot": snapshot,
    }


def get_user_sellable_stack_items_for_auction(user_id, category, limit=50, offset=0):
    init_auction_house()

    category = normalize_auction_category(category)

    try:
        limit = int(limit)
    except Exception:
        limit = 50
    try:
        offset = int(offset)
    except Exception:
        offset = 0

    cursor.execute("""
    SELECT inv.id AS inventory_id
    FROM inventory inv
    JOIN items it ON inv.item_id = it.id
    WHERE inv.user_id=?
    ORDER BY inv.id DESC
    LIMIT 300
    """, (user_id,))

    rows = cursor.fetchall()
    result = []

    for row in rows:
        try:
            inventory_id = row["inventory_id"]
        except Exception:
            inventory_id = row[0]

        snapshot_result = get_inventory_item_snapshot_for_auction(user_id, inventory_id)

        if not snapshot_result.get("success"):
            continue

        snapshot = snapshot_result["snapshot"]

        if _auction_is_success_rune(snapshot):
            continue

        if not _auction_stack_category_matches(snapshot, category):
            continue

        quantity = int(snapshot.get("quantity", 0) or 0)
        if quantity <= 0:
            continue

        result.append({
            "inventory_id": inventory_id,
            "name": snapshot["name"],
            "quantity": quantity,
            "item_id": snapshot.get("item_id"),
            "item_type": snapshot.get("item_type"),
            "item_category": snapshot.get("item_category"),
        })

    return result[offset:offset + limit]


def create_stack_auction_lot(user_id, inventory_id, category, quantity, price):
    """
    Creates ACTIVE auction lot from a stackable item.

    If quantity equals the whole inventory stack, the row is deleted.
    If quantity is smaller, the inventory row quantity is reduced.
    """

    init_auction_house()

    category = normalize_auction_category(category)

    validation = validate_inventory_stack_item_for_auction(user_id, inventory_id, category, quantity)
    if not validation.get("success"):
        return validation

    can_create = can_user_create_auction_lot(user_id)
    if not can_create.get("success"):
        return can_create

    price_result = validate_auction_price(price)
    if not price_result.get("success"):
        return price_result

    snapshot = validation["snapshot"]
    quantity = int(snapshot.get("auction_quantity", quantity) or quantity)
    owned_quantity = int(snapshot.get("owned_quantity", snapshot.get("quantity", 0)) or 0)

    now = now_iso()
    expires_at = iso_after_days(AUCTION_ACTIVE_DAYS)

    try:
        conn.execute("BEGIN IMMEDIATE")

        # Re-check inside transaction.
        validation_inside = validate_inventory_stack_item_for_auction(user_id, inventory_id, category, quantity)
        if not validation_inside.get("success"):
            conn.rollback()
            return validation_inside

        snapshot = validation_inside["snapshot"]
        owned_quantity = int(snapshot.get("owned_quantity", snapshot.get("quantity", 0)) or 0)
        quantity = int(snapshot.get("auction_quantity", quantity) or quantity)

        snapshot_for_lot = dict(snapshot)
        snapshot_for_lot["quantity"] = quantity
        snapshot_for_lot["auction_quantity"] = quantity
        snapshot_for_lot["owned_quantity_before_listing"] = owned_quantity

        item_name = snapshot_for_lot["name"]
        if quantity > 1:
            item_name = f"{item_name} x{quantity}"

        cursor.execute("""
        INSERT INTO auction_lots (
            seller_user_id,
            buyer_user_id,
            item_type,
            item_source,
            item_ref_id,
            item_snapshot_json,
            item_name,
            item_name_norm,
            category,
            rarity,
            level,
            enhancement_level,
            durability_current,
            durability_max,
            quantity,
            price,
            status,
            created_at,
            expires_at,
            updated_at
        ) VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            snapshot_for_lot.get("item_type") or category,
            "inventory_stack",
            int(inventory_id),
            safe_json_dumps(snapshot_for_lot),
            item_name,
            item_name.lower(),
            category,
            snapshot_for_lot.get("rarity", ""),
            0,
            0,
            None,
            None,
            quantity,
            price_result["price"],
            AUCTION_STATUS_ACTIVE,
            now,
            expires_at,
            now,
        ))

        lot_id = cursor.lastrowid

        if quantity >= owned_quantity:
            cursor.execute(
                "DELETE FROM inventory WHERE id=? AND user_id=?",
                (inventory_id, user_id)
            )
        else:
            cursor.execute(
                "UPDATE inventory SET quantity = quantity - ? WHERE id=? AND user_id=? AND quantity>=?",
                (quantity, inventory_id, user_id, quantity)
            )

        if cursor.rowcount != 1:
            conn.rollback()
            return {
                "success": False,
                "message": "❌ Не вдалося перенести кількість предметів з інвентаря.",
            }

        cursor.execute("""
        INSERT INTO auction_history (
            lot_id,
            event_type,
            actor_user_id,
            seller_user_id,
            buyer_user_id,
            item_name,
            category,
            quantity,
            price,
            status_before,
            status_after,
            details_json,
            created_at
        ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, NULL, ?, ?, ?)
        """, (
            lot_id,
            AUCTION_HISTORY_LISTED,
            user_id,
            user_id,
            item_name,
            category,
            quantity,
            price_result["price"],
            AUCTION_STATUS_ACTIVE,
            safe_json_dumps({
                "inventory_id": inventory_id,
                "item_id": snapshot_for_lot.get("item_id"),
                "owned_quantity_before_listing": owned_quantity,
            }),
            now,
        ))

        conn.commit()

        return {
            "success": True,
            "lot_id": lot_id,
            "item_name": item_name,
            "quantity": quantity,
            "price": price_result["price"],
            "expires_at": expires_at,
            "message": "✅ Лот виставлено на продаж.",
        }

    except Exception as error:
        try:
            conn.rollback()
        except Exception:
            pass

        return {
            "success": False,
            "message": f"❌ Помилка створення лота: {error}",
        }
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE STACK LISTING WRAPPERS V1
# ==============================


def get_user_sellable_stack_items_for_auction(user_id, category, limit=50, offset=0):
    from systems.auction_house_system import get_user_sellable_stack_items_for_auction as _func
    return _func(user_id=user_id, category=category, limit=limit, offset=offset)


def validate_inventory_stack_item_for_auction(user_id, inventory_id, category, quantity):
    from systems.auction_house_system import validate_inventory_stack_item_for_auction as _func
    return _func(user_id=user_id, inventory_id=inventory_id, category=category, quantity=quantity)


def create_stack_auction_lot(user_id, inventory_id, category, quantity, price):
    from systems.auction_house_system import create_stack_auction_lot as _func
    return _func(user_id=user_id, inventory_id=inventory_id, category=category, quantity=quantity, price=price)
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE SELL STACK ITEMS V2
# ==============================

AUCTION_SELL_STATE_V2 = {}
AUCTION_STACK_CATEGORY_POTION_BUTTON = "🧪 Зілля"
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
        "• 🧪 Зілля — стекові предмети, можна виставляти частинами.\n"
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
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def patch_system(root):
    target = root / "systems" / "auction_house_system.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено systems/auction_house_system.py. Спочатку потрібен патч 8.0.1.")

    original = target.read_text(encoding="utf-8")
    if SYSTEM_MARKER in original:
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + SYSTEM_APPEND + "\n", encoding="utf-8")
    return target, backup, original, True


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")

    original = target.read_text(encoding="utf-8")
    if DB_MARKER in original:
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + DB_APPEND + "\n", encoding="utf-8")
    return target, backup, original, True


def patch_handler(root):
    target = root / "handlers" / "auction_house.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/auction_house.py. Спочатку потрібен патч 8.0.2.")

    original = target.read_text(encoding="utf-8")
    if HANDLER_MARKER in original:
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + HANDLER_APPEND + "\n", encoding="utf-8")
    return target, backup, original, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_system, patch_db, patch_handler]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        compile_targets = [
            root / "systems" / "auction_house_system.py",
            root / "db.py",
            root / "handlers" / "auction_house.py",
        ]
        for file_path in compile_targets:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_8_0_4_auction_sell_stack_items.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.4 Auction Sell Stack Items застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- виставлення 🧪 Зілля")
    print("- виставлення 🪨 Матеріалів")
    print("- продаж частини стеку")
    print("- перевірка кількості")
    print("- 💎 Руна Успіху заборонена для продажу")
    print("- 🪨 Камінь Посилення дозволений")
    print("- якщо виставлено весь стек, inventory row видаляється")
    print("- якщо виставлено частину, quantity зменшується")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
