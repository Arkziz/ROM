from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "8_0_3_auction_sell_equipment"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE EQUIPMENT LISTING V1"
DB_MARKER = "# ✅ AUCTION HOUSE EQUIPMENT LISTING WRAPPERS V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE EQUIPMENT LISTING V1
# ==============================

AUCTION_EQUIPMENT_PAGE_SIZE = 8


def _auction_row_to_dict(row):
    if row is None:
        return None

    try:
        return dict(row)
    except Exception:
        pass

    try:
        keys = row.keys()
        return {key: row[key] for key in keys}
    except Exception:
        return {}


def _auction_table_columns(table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    columns = []

    for row in rows:
        try:
            columns.append(row["name"])
        except Exception:
            columns.append(row[1])

    return columns


def _auction_has_table(table_name):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def _auction_get_inventory_row(inventory_id, user_id=None):
    init_auction_house()

    inventory_id = int(inventory_id)

    sql = """
    SELECT
        inv.id AS inventory_id,
        inv.user_id AS inventory_user_id,
        inv.item_id AS inventory_item_id,
        inv.quantity AS inventory_quantity,
        inv.refine_level AS inventory_refine_level,
        inv.*,
        it.id AS item_id,
        it.name AS item_name,
        it.type AS item_type,
        it.category AS item_category,
        it.slot_key AS item_slot_key,
        it.rarity AS item_rarity,
        it.level AS item_level,
        it.*
    FROM inventory inv
    JOIN items it ON inv.item_id = it.id
    WHERE inv.id=?
    """
    params = [inventory_id]

    if user_id is not None:
        sql += " AND inv.user_id=?"
        params.append(user_id)

    cursor.execute(sql, tuple(params))
    return cursor.fetchone()


def _auction_get_int(row_dict, *keys, default=0):
    for key in keys:
        if key in row_dict and row_dict.get(key) is not None:
            try:
                return int(row_dict.get(key))
            except Exception:
                pass
    return int(default)


def _auction_get_str(row_dict, *keys, default=""):
    for key in keys:
        value = row_dict.get(key)
        if value is not None:
            value = str(value)
            if value:
                return value
    return default


def _auction_get_durability(row_dict):
    current = None
    maximum = None

    current_keys = [
        "durability",
        "current_durability",
        "durability_current",
        "inventory_durability",
        "item_durability",
    ]
    max_keys = [
        "max_durability",
        "durability_max",
        "inventory_max_durability",
        "item_max_durability",
    ]

    for key in current_keys:
        if key in row_dict and row_dict.get(key) is not None:
            try:
                current = int(row_dict.get(key))
                break
            except Exception:
                pass

    for key in max_keys:
        if key in row_dict and row_dict.get(key) is not None:
            try:
                maximum = int(row_dict.get(key))
                break
            except Exception:
                pass

    if current is None:
        current = 100

    if maximum is None:
        maximum = 100

    return current, maximum


def _auction_format_refined_name(name, refine_level):
    try:
        refine_level = int(refine_level or 0)
    except Exception:
        refine_level = 0

    if refine_level <= 0:
        return name

    marker = f"[+{refine_level}]"

    if marker in name:
        return name

    level_marker = " рівня"

    if level_marker in name:
        index = name.rfind(level_marker)
        level_end = index + len(level_marker)
        return f"{name[:level_end]} {marker}{name[level_end:]}"

    return f"{name} {marker}"


def _auction_is_inventory_equipped(user_id, inventory_id):
    if not _auction_has_table("equipment_slots"):
        return False

    columns = _auction_table_columns("equipment_slots")

    if "inventory_id" in columns:
        cursor.execute(
            "SELECT 1 FROM equipment_slots WHERE user_id=? AND inventory_id=? LIMIT 1",
            (user_id, inventory_id)
        )
        return cursor.fetchone() is not None

    # Fallback for wide slot columns if project uses that schema.
    possible_slot_columns = [
        "main_hand", "off_hand", "helmet", "shoulders", "chest", "gloves",
        "legs", "boots", "necklace", "ring",
    ]

    existing = [col for col in possible_slot_columns if col in columns]

    for col in existing:
        cursor.execute(
            f"SELECT 1 FROM equipment_slots WHERE user_id=? AND {col}=? LIMIT 1",
            (user_id, inventory_id)
        )
        if cursor.fetchone() is not None:
            return True

    return False


def _auction_is_equipment_row(row_dict):
    slot_key = _auction_get_str(row_dict, "item_slot_key", "slot_key", default="")
    item_type = _auction_get_str(row_dict, "item_type", "type", default="").lower()
    item_category = _auction_get_str(row_dict, "item_category", "category", default="").lower()

    if slot_key:
        return True

    if item_type in [
        "weapon", "main_hand", "off_hand", "helmet", "shoulders", "chest",
        "gloves", "legs", "boots", "necklace", "ring",
    ]:
        return True

    if item_category == "equipment":
        return True

    return False


def get_inventory_item_snapshot_for_auction(user_id, inventory_id):
    """
    Builds a full enough snapshot of an inventory item for Auction House listing.
    Does not mutate inventory.
    """

    row = _auction_get_inventory_row(inventory_id=inventory_id, user_id=user_id)

    if not row:
        return {
            "success": False,
            "message": "❌ Предмет не знайдено в інвентарі.",
        }

    data = _auction_row_to_dict(row)

    item_id = _auction_get_int(data, "item_id", "inventory_item_id")
    quantity = _auction_get_int(data, "inventory_quantity", "quantity", default=1)
    refine_level = _auction_get_int(data, "inventory_refine_level", "refine_level", default=0)
    raw_name = _auction_get_str(data, "item_name", "name", default="Предмет")
    display_name = _auction_format_refined_name(raw_name, refine_level)

    durability_current, durability_max = _auction_get_durability(data)

    rarity = _auction_get_str(data, "item_rarity", "rarity", default="")
    level = _auction_get_int(data, "item_level", "level", default=0)
    slot_key = _auction_get_str(data, "item_slot_key", "slot_key", default="")
    item_type = _auction_get_str(data, "item_type", "type", default="")
    item_category = _auction_get_str(data, "item_category", "category", default="")

    snapshot = {
        "inventory_id": int(inventory_id),
        "item_id": item_id,
        "quantity": quantity,
        "refine_level": refine_level,
        "name": display_name,
        "raw_name": raw_name,
        "rarity": rarity,
        "level": level,
        "slot_key": slot_key,
        "item_type": item_type,
        "item_category": item_category,
        "durability_current": durability_current,
        "durability_max": durability_max,
        "row": data,
    }

    return {
        "success": True,
        "snapshot": snapshot,
    }


def validate_inventory_item_for_auction_equipment(user_id, inventory_id):
    snapshot_result = get_inventory_item_snapshot_for_auction(user_id, inventory_id)

    if not snapshot_result.get("success"):
        return snapshot_result

    snapshot = snapshot_result["snapshot"]

    if not _auction_is_equipment_row(snapshot["row"]):
        return {
            "success": False,
            "message": "❌ На цьому етапі можна виставляти тільки спорядження.",
        }

    if _auction_is_inventory_equipped(user_id, inventory_id):
        return {
            "success": False,
            "message": "❌ Екіпірований предмет не можна виставити на продаж.",
        }

    if int(snapshot.get("durability_current", 100) or 0) <= 0:
        return {
            "success": False,
            "message": "⚠️ Неможливо виставити зламаний предмет.",
        }

    return {
        "success": True,
        "snapshot": snapshot,
    }


def get_user_sellable_equipment_for_auction(user_id, limit=50, offset=0):
    init_auction_house()

    try:
        limit = int(limit)
    except Exception:
        limit = 50
    try:
        offset = int(offset)
    except Exception:
        offset = 0

    # Fetch a wider slice and filter in Python because schemas vary across project patches.
    cursor.execute("""
    SELECT inv.id AS inventory_id
    FROM inventory inv
    JOIN items it ON inv.item_id = it.id
    WHERE inv.user_id=?
    ORDER BY inv.id DESC
    LIMIT 200
    """, (user_id,))

    rows = cursor.fetchall()
    result = []

    for row in rows:
        try:
            inventory_id = row["inventory_id"]
        except Exception:
            inventory_id = row[0]

        check = validate_inventory_item_for_auction_equipment(user_id, inventory_id)

        if check.get("success"):
            snapshot = check["snapshot"]
            result.append({
                "inventory_id": inventory_id,
                "name": snapshot["name"],
                "quantity": snapshot["quantity"],
                "rarity": snapshot["rarity"],
                "level": snapshot["level"],
                "refine_level": snapshot["refine_level"],
                "durability_current": snapshot["durability_current"],
                "durability_max": snapshot["durability_max"],
                "slot_key": snapshot["slot_key"],
            })

    return result[offset:offset + limit]


def create_equipment_auction_lot(user_id, inventory_id, price):
    """
    Creates an ACTIVE auction lot from a single equipment inventory item and removes it from inventory.

    This is the first real item-listing implementation for Auction House 8.0.3.
    Stackable items/materials are intentionally handled later.
    """

    init_auction_house()

    check = validate_inventory_item_for_auction_equipment(user_id, inventory_id)

    if not check.get("success"):
        return check

    can_create = can_user_create_auction_lot(user_id)
    if not can_create.get("success"):
        return can_create

    price_result = validate_auction_price(price)
    if not price_result.get("success"):
        return price_result

    snapshot = check["snapshot"]
    now = now_iso()
    expires_at = iso_after_days(AUCTION_ACTIVE_DAYS)

    try:
        conn.execute("BEGIN IMMEDIATE")

        # Re-check ownership and active status inside transaction.
        check_inside = validate_inventory_item_for_auction_equipment(user_id, inventory_id)
        if not check_inside.get("success"):
            conn.rollback()
            return check_inside

        snapshot = check_inside["snapshot"]

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
            snapshot.get("item_type") or "equipment",
            "inventory",
            int(inventory_id),
            safe_json_dumps(snapshot),
            snapshot["name"],
            snapshot["name"].lower(),
            AUCTION_CATEGORY_EQUIPMENT,
            snapshot.get("rarity", ""),
            int(snapshot.get("level", 0) or 0),
            int(snapshot.get("refine_level", 0) or 0),
            snapshot.get("durability_current"),
            snapshot.get("durability_max"),
            1,
            price_result["price"],
            AUCTION_STATUS_ACTIVE,
            now,
            expires_at,
            now,
        ))

        lot_id = cursor.lastrowid

        cursor.execute(
            "DELETE FROM inventory WHERE id=? AND user_id=?",
            (inventory_id, user_id)
        )

        if cursor.rowcount != 1:
            conn.rollback()
            return {
                "success": False,
                "message": "❌ Не вдалося перенести предмет з інвентаря.",
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
            snapshot["name"],
            AUCTION_CATEGORY_EQUIPMENT,
            1,
            price_result["price"],
            AUCTION_STATUS_ACTIVE,
            safe_json_dumps({"inventory_id": inventory_id, "item_id": snapshot.get("item_id")}),
            now,
        ))

        conn.commit()

        return {
            "success": True,
            "lot_id": lot_id,
            "item_name": snapshot["name"],
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
# ✅ AUCTION HOUSE EQUIPMENT LISTING WRAPPERS V1
# ==============================


def get_user_sellable_equipment_for_auction(user_id, limit=50, offset=0):
    from systems.auction_house_system import get_user_sellable_equipment_for_auction as _func
    return _func(user_id=user_id, limit=limit, offset=offset)


def get_inventory_item_snapshot_for_auction(user_id, inventory_id):
    from systems.auction_house_system import get_inventory_item_snapshot_for_auction as _func
    return _func(user_id=user_id, inventory_id=inventory_id)


def validate_inventory_item_for_auction_equipment(user_id, inventory_id):
    from systems.auction_house_system import validate_inventory_item_for_auction_equipment as _func
    return _func(user_id=user_id, inventory_id=inventory_id)


def create_equipment_auction_lot(user_id, inventory_id, price):
    from systems.auction_house_system import create_equipment_auction_lot as _func
    return _func(user_id=user_id, inventory_id=inventory_id, price=price)
'''

HANDLER_MARKER = "# ✅ AUCTION HOUSE SELL EQUIPMENT V1"
HANDLER_APPEND = r'''

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
    if _auction_base_register_handlers_before_sell_equipment_v1:
        _auction_base_register_handlers_before_sell_equipment_v1(bot)

    _auction_register_sell_equipment_handlers(bot)
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
            "❌ Помилка під час patch_8_0_3_auction_sell_equipment.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.3 Auction Sell Equipment застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- виставлення спорядження через ➕ Виставити товар")
    print("- категорія ⚔️ Спорядження")
    print("- список доступного спорядження")
    print("- перевірка: не екіпіровано")
    print("- перевірка: міцність > 0")
    print("- введення ціни Decimal")
    print("- підтвердження лота")
    print("- після виставлення предмет видаляється з inventory і переходить у auction_lots")
    print("- лот ACTIVE на 7 днів")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
