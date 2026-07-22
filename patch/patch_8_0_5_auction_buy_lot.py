from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_5_auction_buy_lot"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE BUY LOT V1"
DB_MARKER = "# ✅ AUCTION HOUSE BUY LOT WRAPPERS V1"
HANDLER_MARKER = "# ✅ AUCTION HOUSE BUY LOT UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE BUY LOT V1
# ==============================

AUCTION_BUY_PAGE_SIZE = 8


def _auction_get_user_gold(user_id):
    cursor.execute("SELECT gold FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return Decimal("0")

    try:
        value = row["gold"]
    except Exception:
        value = row[0]

    return Decimal(str(value or "0"))


def _auction_set_user_gold(user_id, gold_value):
    gold_value = Decimal(str(gold_value)).quantize(AUCTION_PRICE_QUANT, rounding=ROUND_DOWN)
    cursor.execute("UPDATE users SET gold=? WHERE user_id=?", (float(gold_value), user_id))


def _auction_count_inventory_rows(user_id):
    cursor.execute("SELECT COUNT(*) AS cnt FROM inventory WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    try:
        return int(row["cnt"] or 0)
    except Exception:
        return int(row[0] or 0) if row else 0


def _auction_get_inventory_limit(user_id):
    # Current project uses 40 slots by default. If a user/bag column exists later,
    # this helper can be expanded without touching buy logic.
    try:
        cursor.execute("SELECT bag_slots FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if row:
            try:
                value = row["bag_slots"]
            except Exception:
                value = row[0]
            if value:
                return int(value)
    except Exception:
        pass

    try:
        cursor.execute("SELECT inventory_slots FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if row:
            try:
                value = row["inventory_slots"]
            except Exception:
                value = row[0]
            if value:
                return int(value)
    except Exception:
        pass

    return 40


def _auction_has_inventory_space(user_id, required_slots=1):
    return _auction_count_inventory_rows(user_id) + int(required_slots or 1) <= _auction_get_inventory_limit(user_id)


def _auction_get_existing_stack_inventory_id(user_id, item_id):
    cursor.execute(
        "SELECT id FROM inventory WHERE user_id=? AND item_id=? ORDER BY id ASC LIMIT 1",
        (user_id, item_id)
    )
    row = cursor.fetchone()
    if not row:
        return None
    try:
        return row["id"]
    except Exception:
        return row[0]


def _auction_insert_inventory_from_snapshot(user_id, snapshot, quantity=None):
    """
    Restores a listed item to a user's inventory.

    - equipment snapshots are inserted as a new inventory row;
    - stack snapshots are merged into an existing stack when possible.
    """

    inv_cols = _auction_table_columns("inventory")
    row_data = snapshot.get("row") or {}
    item_id = int(snapshot.get("item_id", 0) or 0)

    if item_id <= 0:
        raise ValueError("Некоректний item_id у snapshot лота.")

    quantity = int(quantity if quantity is not None else snapshot.get("quantity", 1) or 1)
    quantity = max(1, quantity)

    is_stack = quantity > 1 or _auction_is_material_snapshot(snapshot) or _auction_is_potion_snapshot(snapshot)

    if is_stack:
        existing_id = _auction_get_existing_stack_inventory_id(user_id, item_id)
        if existing_id is not None:
            cursor.execute(
                "UPDATE inventory SET quantity = quantity + ? WHERE id=? AND user_id=?",
                (quantity, existing_id, user_id)
            )
            if cursor.rowcount != 1:
                raise ValueError("Не вдалося додати предмет до існуючого стеку.")
            return existing_id

        if not _auction_has_inventory_space(user_id, 1):
            raise ValueError("Недостатньо місця в інвентарі.")

    else:
        if not _auction_has_inventory_space(user_id, 1):
            raise ValueError("Недостатньо місця в інвентарі.")

    insert_cols = []
    insert_values = []

    for col in inv_cols:
        if col == "id":
            continue

        insert_cols.append(col)

        if col == "user_id":
            insert_values.append(user_id)
        elif col == "item_id":
            insert_values.append(item_id)
        elif col == "quantity":
            insert_values.append(quantity)
        elif col == "refine_level":
            insert_values.append(int(snapshot.get("refine_level", 0) or 0))
        elif f"inv_{col}" in row_data:
            insert_values.append(row_data.get(f"inv_{col}"))
        elif col in row_data:
            insert_values.append(row_data.get(col))
        else:
            # Safe defaults for common inventory columns.
            if col.endswith("_at") or col in ["created_at", "updated_at"]:
                insert_values.append(now_iso())
            elif col in ["equipped", "locked"]:
                insert_values.append(0)
            else:
                insert_values.append(None)

    placeholders = ", ".join(["?"] * len(insert_cols))
    sql = f"INSERT INTO inventory ({', '.join(insert_cols)}) VALUES ({placeholders})"
    cursor.execute(sql, tuple(insert_values))
    return cursor.lastrowid


def get_public_auction_lots_for_buyer(user_id, category=None, search_text=None, limit=8, offset=0, sort="new"):
    """
    Returns ACTIVE lots excluding the buyer's own lots.
    """

    init_auction_house()

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
    params = [AUCTION_STATUS_ACTIVE, user_id]

    if category:
        where.append("category=?")
        params.append(normalize_auction_category(category))

    if search_text:
        where.append("item_name_norm LIKE ?")
        params.append(f"%{str(search_text).strip().lower()}%")

    order_by = "created_at DESC"
    if sort == "old":
        order_by = "created_at ASC"
    elif sort == "price_asc":
        order_by = "CAST(price AS REAL) ASC, created_at DESC"
    elif sort == "price_desc":
        order_by = "CAST(price AS REAL) DESC, created_at DESC"
    elif sort == "rarity":
        order_by = "rarity DESC, created_at DESC"

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


def build_auction_lot_public_details(lot_id, viewer_user_id=None):
    init_auction_house()
    lot = get_auction_lot_by_id(lot_id)

    if not lot:
        return {
            "success": False,
            "message": "❌ Лот не знайдено.",
        }

    if lot["status"] != AUCTION_STATUS_ACTIVE:
        return {
            "success": False,
            "message": "⚠️ Лот уже недоступний.",
        }

    snapshot = safe_json_loads(lot["item_snapshot_json"])
    details = []
    details.append("📦 Лот Торгового Дому")
    details.append("")
    details.append(str(lot["item_name"]))
    details.append("")

    if lot["category"] == AUCTION_CATEGORY_EQUIPMENT:
        if lot["level"]:
            details.append(f"🏷 Рівень: {lot['level']}")
        if lot["enhancement_level"]:
            details.append(f"✨ Заточка: +{lot['enhancement_level']}")
        if lot["durability_current"] is not None:
            details.append(f"🔧 Міцність: {lot['durability_current']}/{lot['durability_max']}")
    else:
        details.append(f"📦 Кількість: {lot['quantity']}")

    details.append("")
    details.append(f"💰 Ціна: {lot['price']} золота")
    details.append("⏳ Активний лот: до 7 днів від створення")
    details.append("")
    details.append("Продавець прихований.")

    return {
        "success": True,
        "lot": lot,
        "snapshot": snapshot,
        "text": "\n".join(details),
    }


def buy_auction_lot(buyer_user_id, lot_id):
    """
    Transactional purchase.

    Checks:
    - lot exists and ACTIVE;
    - buyer is not seller;
    - buyer has enough gold;
    - buyer has inventory space or stack can be merged;
    - status update is guarded with WHERE status='ACTIVE'.
    """

    init_auction_house()
    lot_id = int(lot_id)
    buyer_user_id = int(buyer_user_id)

    try:
        conn.execute("BEGIN IMMEDIATE")

        cursor.execute("SELECT * FROM auction_lots WHERE id=?", (lot_id,))
        lot = cursor.fetchone()

        if not lot:
            conn.rollback()
            return {
                "success": False,
                "message": "❌ Лот не знайдено.",
            }

        if lot["status"] != AUCTION_STATUS_ACTIVE:
            conn.rollback()
            return {
                "success": False,
                "message": "⚠️ Лот уже продано або він недоступний.",
            }

        seller_user_id = int(lot["seller_user_id"])
        if seller_user_id == buyer_user_id:
            conn.rollback()
            return {
                "success": False,
                "message": "❌ Не можна купити власний лот.",
            }

        price = auction_price_to_decimal(lot["price"])
        buyer_gold = _auction_get_user_gold(buyer_user_id)

        if buyer_gold < price:
            conn.rollback()
            return {
                "success": False,
                "message": f"❌ Недостатньо золота. Потрібно: {lot['price']}.",
            }

        snapshot = safe_json_loads(lot["item_snapshot_json"])
        quantity = int(lot["quantity"] or 1)

        # Inventory space check before money/status changes.
        is_stack = lot["category"] in [AUCTION_CATEGORY_MATERIAL, AUCTION_CATEGORY_POTION]
        item_id = int(snapshot.get("item_id", 0) or 0)
        if is_stack and item_id > 0:
            existing_stack = _auction_get_existing_stack_inventory_id(buyer_user_id, item_id)
            needs_slot = existing_stack is None
        else:
            needs_slot = True

        if needs_slot and not _auction_has_inventory_space(buyer_user_id, 1):
            conn.rollback()
            return {
                "success": False,
                "message": "⚠️ Недостатньо місця в інвентарі.",
            }

        now = now_iso()
        delete_after = iso_after_days(AUCTION_CLAIM_DAYS)

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
            return {
                "success": False,
                "message": "⚠️ Лот уже продано.",
            }

        _auction_set_user_gold(buyer_user_id, buyer_gold - price)
        new_inventory_id = _auction_insert_inventory_from_snapshot(buyer_user_id, snapshot, quantity=quantity)

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
            AUCTION_HISTORY_SOLD,
            buyer_user_id,
            seller_user_id,
            buyer_user_id,
            lot["item_name"],
            lot["category"],
            quantity,
            lot["price"],
            AUCTION_STATUS_ACTIVE,
            AUCTION_STATUS_SOLD_UNCLAIMED,
            safe_json_dumps({"buyer_inventory_id": new_inventory_id}),
            now,
        ))

        conn.commit()

        return {
            "success": True,
            "message": "✅ Покупку завершено.",
            "lot_id": lot_id,
            "item_name": lot["item_name"],
            "price": lot["price"],
            "quantity": quantity,
            "inventory_id": new_inventory_id,
        }

    except Exception as error:
        try:
            conn.rollback()
        except Exception:
            pass

        return {
            "success": False,
            "message": f"❌ Помилка покупки: {error}",
        }
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE BUY LOT WRAPPERS V1
# ==============================


def get_public_auction_lots_for_buyer(user_id, category=None, search_text=None, limit=8, offset=0, sort="new"):
    from systems.auction_house_system import get_public_auction_lots_for_buyer as _func
    return _func(user_id=user_id, category=category, search_text=search_text, limit=limit, offset=offset, sort=sort)


def build_auction_lot_public_details(lot_id, viewer_user_id=None):
    from systems.auction_house_system import build_auction_lot_public_details as _func
    return _func(lot_id=lot_id, viewer_user_id=viewer_user_id)


def buy_auction_lot(buyer_user_id, lot_id):
    from systems.auction_house_system import buy_auction_lot as _func
    return _func(buyer_user_id=buyer_user_id, lot_id=lot_id)
'''

HANDLER_APPEND = r'''

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
            "❌ Помилка під час patch_8_0_5_auction_buy_lot.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.5 Auction Buy Lot застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- перегляд активних лотів через 🛒 Купити")
    print("- приховування власних лотів від покупця")
    print("- перегляд деталей лота")
    print("- підтвердження покупки")
    print("- транзакційна покупка через BEGIN IMMEDIATE")
    print("- перевірка: лот ACTIVE")
    print("- перевірка: не власний лот")
    print("- перевірка: достатньо золота")
    print("- перевірка: є місце в інвентарі")
    print("- статус ACTIVE -> SOLD_UNCLAIMED")
    print("- золото списується з покупця")
    print("- предмет додається покупцю")
    print("- продавець забере золото пізніше у 💰 Завершені продажі")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
