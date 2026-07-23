from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_9_auction_buy_filters_sorting"
SYSTEM_TARGET = Path("systems") / "auction_house_system.py"
DB_TARGET = Path("db.py")
HANDLER_TARGET = Path("handlers") / "auction_house.py"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE BUY FILTERS SORTING V1"
DB_MARKER = "# ✅ AUCTION HOUSE BUY FILTERS SORTING WRAPPERS V1"
HANDLER_MARKER = "# ✅ AUCTION HOUSE BUY FILTERS SORTING UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE BUY FILTERS SORTING V1
# ==============================

AUCTION_BUY_PAGE_SIZE = 8
AUCTION_BUY_CATEGORY_ALL = "all"

AUCTION_BUY_CATEGORY_LABELS = {
    "all": "Усі лоти",
    "equipment": "⚔️ Спорядження",
    "potion": "🧪 Зілля",
    "material": "🪨 Матеріали",
}

AUCTION_BUY_SORT_LABELS = {
    "new": "Нові",
    "old": "Старі",
    "price_asc": "Ціна ↑",
    "price_desc": "Ціна ↓",
    "rarity": "Рідкість",
}


def _auction_buy_normalize_category(category):
    category = str(category or AUCTION_BUY_CATEGORY_ALL).strip().lower()
    if category in ("all", "any", "*"):
        return AUCTION_BUY_CATEGORY_ALL
    if category in ("equipment", "gear", AUCTION_CATEGORY_EQUIPMENT):
        return AUCTION_CATEGORY_EQUIPMENT
    if category in ("potion", "potions", AUCTION_CATEGORY_POTION):
        return AUCTION_CATEGORY_POTION
    if category in ("material", "materials", AUCTION_CATEGORY_MATERIAL):
        return AUCTION_CATEGORY_MATERIAL
    return AUCTION_BUY_CATEGORY_ALL


def _auction_buy_normalize_sort(sort_key):
    sort_key = str(sort_key or "new").strip().lower()
    if sort_key in ("new", "old", "price_asc", "price_desc", "rarity"):
        return sort_key
    return "new"


def get_auction_lots_for_buy_filtered(buyer_user_id, category="all", sort_key="new", limit=8, offset=0):
    """
    Returns ACTIVE lots for buyer with category filter and sorting.

    Own lots are hidden from buyer.
    """
    init_auction_house()
    update_expired_auction_lots()

    buyer_user_id = int(buyer_user_id)
    category = _auction_buy_normalize_category(category)
    sort_key = _auction_buy_normalize_sort(sort_key)

    try:
        limit = int(limit)
    except Exception:
        limit = 8
    try:
        offset = int(offset)
    except Exception:
        offset = 0

    limit = max(1, min(50, limit))
    offset = max(0, offset)

    where = ["status=?", "seller_user_id<>?"]
    params = [AUCTION_STATUS_ACTIVE, buyer_user_id]

    if category != AUCTION_BUY_CATEGORY_ALL:
        where.append("category=?")
        params.append(category)

    order_by = "created_at DESC"
    if sort_key == "old":
        order_by = "created_at ASC"
    elif sort_key == "price_asc":
        order_by = "CAST(price AS REAL) ASC, created_at DESC"
    elif sort_key == "price_desc":
        order_by = "CAST(price AS REAL) DESC, created_at DESC"
    elif sort_key == "rarity":
        order_by = """
        CASE rarity
            WHEN 'epic' THEN 4
            WHEN 'rare' THEN 3
            WHEN 'uncommon' THEN 2
            WHEN 'common' THEN 1
            ELSE 0
        END DESC,
        level DESC,
        created_at DESC
        """

    sql = f"""
    SELECT *
    FROM auction_lots
    WHERE {' AND '.join(where)}
    ORDER BY {order_by}
    LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    cursor.execute(sql, tuple(params))
    return cursor.fetchall()


def build_auction_buy_lot_details_v2(buyer_user_id, lot_id):
    """
    Inventory-style lot details for buyer.
    Seller remains hidden.
    """
    init_auction_house()
    update_expired_auction_lots()

    cursor.execute("SELECT * FROM auction_lots WHERE id=?", (int(lot_id),))
    lot = cursor.fetchone()

    if not lot:
        return {"success": False, "message": "❌ Лот не знайдено."}

    if lot["status"] != AUCTION_STATUS_ACTIVE:
        return {"success": False, "message": "⚠️ Лот уже недоступний."}

    if int(lot["seller_user_id"] or 0) == int(buyer_user_id):
        return {"success": False, "message": "⚠️ Не можна купити власний лот."}

    snapshot = safe_json_loads(lot["item_snapshot_json"])
    category = lot["category"]
    quantity = int(lot["quantity"] or 1)

    lines = []
    lines.append("📦 Лот Торгового Дому")
    lines.append("")
    lines.append(str(lot["item_name"]))
    lines.append("")

    if category == AUCTION_CATEGORY_EQUIPMENT:
        refine_level = int(lot["enhancement_level"] or snapshot.get("refine_level", 0) or 0)
        item_type = snapshot.get("item_type") or _auction_snapshot_value(snapshot, "type", "item_type", default="")
        slot_key = snapshot.get("slot_key") or _auction_snapshot_value(snapshot, "slot_key", "slot", default="")
        level = int(lot["level"] or snapshot.get("level", 0) or 0)

        lines.append(_auction_inventory_style_type_line(AUCTION_CATEGORY_EQUIPMENT))
        lines.append(f"🎯 Слот: {_auction_inventory_style_slot(snapshot, slot_key, item_type)}")

        try:
            allowed_classes = _auction_inventory_style_allowed_classes(snapshot)
            if allowed_classes:
                lines.append(f"👥 Підходить класам: {allowed_classes}")
        except Exception:
            pass

        if level:
            lines.append(f"🏷 Рівень предмета: {level} 🔒")
        if refine_level:
            lines.append(f"✨ Заточка: +{refine_level}")

        weapon_type_line = _auction_inventory_style_weapon_type_line(snapshot)
        if weapon_type_line:
            lines.append(weapon_type_line)

        damage_lines = _auction_inventory_style_damage_lines(snapshot)
        if damage_lines:
            lines.extend(damage_lines)

        if lot["durability_current"] is not None:
            lines.append(f"🧱 Міцність: {lot['durability_current']}/{lot['durability_max']}")

        defense_lines = _auction_collect_inventory_style_defense_lines(snapshot)
        bonus_lines = _auction_collect_inventory_style_bonus_lines(snapshot)

        if defense_lines:
            lines.append("")
            lines.extend(defense_lines)
        if bonus_lines:
            lines.append("")
            lines.append("📊 Бонуси:")
            lines.extend(bonus_lines)
    else:
        lines.append(_auction_inventory_style_type_line(category))
        lines.append(f"📦 Кількість: {quantity}")
        desc_lines = _auction_collect_stack_description_lines(snapshot)
        if desc_lines:
            lines.append("")
            lines.extend(desc_lines)

    lines.append("")
    lines.append(f"💰 Ціна: {lot['price']} золота")
    lines.append("⏳ Активний лот: до 7 днів від створення")
    lines.append("")
    lines.append("Продавець прихований.")

    return {
        "success": True,
        "lot": lot,
        "snapshot": snapshot,
        "text": "\n".join(lines),
    }


def buy_auction_lot_v2(buyer_user_id, lot_id):
    """
    Transactional auction purchase.

    ACTIVE -> SOLD_UNCLAIMED.
    Buyer receives item immediately.
    Seller claims gold later in completed sales.
    """
    init_auction_house()
    update_expired_auction_lots()

    buyer_user_id = int(buyer_user_id)
    lot_id = int(lot_id)

    try:
        conn.execute("BEGIN IMMEDIATE")

        cursor.execute("SELECT * FROM auction_lots WHERE id=?", (lot_id,))
        lot = cursor.fetchone()

        if not lot:
            conn.rollback()
            return {"success": False, "message": "❌ Лот не знайдено."}

        if lot["status"] != AUCTION_STATUS_ACTIVE:
            conn.rollback()
            return {"success": False, "message": "⚠️ Лот уже недоступний."}

        seller_user_id = int(lot["seller_user_id"] or 0)
        if seller_user_id == buyer_user_id:
            conn.rollback()
            return {"success": False, "message": "⚠️ Не можна купити власний лот."}

        price = auction_price_to_decimal(lot["price"])
        buyer_gold = _auction_get_user_gold(buyer_user_id)

        if buyer_gold < price:
            conn.rollback()
            return {
                "success": False,
                "message": (
                    "❌ Недостатньо золота.\n\n"
                    f"💰 Потрібно: {format_auction_price(price)}\n"
                    f"💰 У тебе: {format_auction_price(buyer_gold)}"
                )
            }

        snapshot = safe_json_loads(lot["item_snapshot_json"])
        quantity = int(lot["quantity"] or 1)

        inventory_id = _auction_insert_inventory_from_snapshot(
            buyer_user_id,
            snapshot,
            quantity=quantity,
        )

        _auction_set_user_gold(buyer_user_id, buyer_gold - price)

        now = now_iso()
        delete_after = add_days_iso(now, AUCTION_UNCLAIMED_RETENTION_DAYS)

        cursor.execute("""
        UPDATE auction_lots
        SET status=?,
            buyer_user_id=?,
            sold_at=?,
            delete_after=?,
            updated_at=?
        WHERE id=? AND status=?
        """, (
            AUCTION_STATUS_SOLD_UNCLAIMED,
            buyer_user_id,
            now,
            delete_after,
            now,
            lot_id,
            AUCTION_STATUS_ACTIVE,
        ))

        if cursor.rowcount != 1:
            conn.rollback()
            return {"success": False, "message": "⚠️ Лот уже куплений іншим гравцем."}

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
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lot_id,
            AUCTION_HISTORY_PURCHASED,
            buyer_user_id,
            seller_user_id,
            buyer_user_id,
            lot["item_name"],
            lot["category"],
            quantity,
            lot["price"],
            AUCTION_STATUS_ACTIVE,
            AUCTION_STATUS_SOLD_UNCLAIMED,
            safe_json_dumps({"buyer_inventory_id": inventory_id}),
            now,
        ))

        conn.commit()

        return {
            "success": True,
            "message": "✅ Покупку завершено!",
            "lot_id": lot_id,
            "item_name": lot["item_name"],
            "quantity": quantity,
            "price": lot["price"],
            "inventory_id": inventory_id,
        }

    except Exception as error:
        try:
            conn.rollback()
        except Exception:
            pass
        return {"success": False, "message": f"❌ Помилка покупки: {error}"}
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE BUY FILTERS SORTING WRAPPERS V1
# ==============================


def get_auction_lots_for_buy_filtered(buyer_user_id, category="all", sort_key="new", limit=8, offset=0):
    from systems.auction_house_system import get_auction_lots_for_buy_filtered as _func
    return _func(buyer_user_id=buyer_user_id, category=category, sort_key=sort_key, limit=limit, offset=offset)


def build_auction_buy_lot_details_v2(buyer_user_id, lot_id):
    from systems.auction_house_system import build_auction_buy_lot_details_v2 as _func
    return _func(buyer_user_id=buyer_user_id, lot_id=lot_id)


def buy_auction_lot_v2(buyer_user_id, lot_id):
    from systems.auction_house_system import buy_auction_lot_v2 as _func
    return _func(buyer_user_id=buyer_user_id, lot_id=lot_id)
'''

HANDLER_APPEND = r'''

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
        qty = f" x{quantity}" if quantity > 1 and f"x{quantity}" not in lot["item_name"] else ""
        label = f"📦 {lot['item_name']}{qty} — {lot['price']} 💰"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_buy2_lot:{lot['id']}:{category}:{sort_key}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Попередні", callback_data=f"ah_buy2_page:{category}:{sort_key}:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Наступні", callback_data=f"ah_buy2_page:{category}:{sort_key}:{page + 1}"))
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

    @bot.message_handler(func=lambda m: m.text in AUCTION_BUY_CATEGORY_BY_BUTTON_V1)
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
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def append_once(root, rel_path, marker, append_code):
    target = root / rel_path
    if not target.exists():
        raise SystemExit(f"❌ Не знайдено {rel_path}")

    original = target.read_text(encoding="utf-8")
    if marker in original:
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + append_code + "\n", encoding="utf-8")
    return target, backup, original, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        patches = [
            (SYSTEM_TARGET, SYSTEM_MARKER, SYSTEM_APPEND),
            (DB_TARGET, DB_MARKER, DB_APPEND),
            (HANDLER_TARGET, HANDLER_MARKER, HANDLER_APPEND),
        ]

        for rel_path, marker, append_code in patches:
            file_path, backup, original, changed = append_once(root, rel_path, marker, append_code)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        compile_targets = [root / SYSTEM_TARGET, root / DB_TARGET, root / HANDLER_TARGET]
        for file_path in compile_targets:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_8_0_9_auction_buy_filters_sorting.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.9 Auction Buy Filters / Sorting застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- 🛒 Купити тепер відкриває вибір категорії")
    print("- Категорії: усі, спорядження, зілля, матеріали")
    print("- Лоти показуються inline-кнопками по 8 на сторінку")
    print("- Сортування: нові, старі, дешеві, дорогі, рідкість")
    print("- Власні лоти покупцю не показуються")
    print("- Купівля залишилась транзакційною")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
