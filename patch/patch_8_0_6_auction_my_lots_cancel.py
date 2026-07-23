from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_6_auction_my_lots_cancel"
SYSTEM_TARGET = Path("systems") / "auction_house_system.py"
DB_TARGET = Path("db.py")
HANDLER_TARGET = Path("handlers") / "auction_house.py"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE MY LOTS CANCEL V1"
DB_MARKER = "# ✅ AUCTION HOUSE MY LOTS CANCEL WRAPPERS V1"
HANDLER_MARKER = "# ✅ AUCTION HOUSE MY LOTS CANCEL UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE MY LOTS CANCEL V1
# ==============================

AUCTION_MY_LOTS_PAGE_SIZE = 8


def get_user_auction_lots(user_id, status=None, limit=8, offset=0):
    """Returns user's auction lots. By default only ACTIVE lots are used by UI."""
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

    where = ["seller_user_id=?"]
    params = [int(user_id)]

    if status:
        where.append("status=?")
        params.append(str(status))

    sql = f"""
    SELECT *
    FROM auction_lots
    WHERE {' AND '.join(where)}
    ORDER BY created_at DESC
    LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(sql, tuple(params))
    return cursor.fetchall()


def get_user_auction_lot_by_id(user_id, lot_id):
    init_auction_house()
    cursor.execute(
        "SELECT * FROM auction_lots WHERE id=? AND seller_user_id=?",
        (int(lot_id), int(user_id))
    )
    return cursor.fetchone()


def build_user_auction_lot_details(user_id, lot_id):
    init_auction_house()
    lot = get_user_auction_lot_by_id(user_id, lot_id)

    if not lot:
        return {"success": False, "message": "❌ Лот не знайдено."}

    snapshot = safe_json_loads(lot["item_snapshot_json"])
    status = lot["status"]
    category = lot["category"]
    quantity = int(lot["quantity"] or 1)

    lines = []
    lines.append("📦 Мій лот")
    lines.append("")
    lines.append(str(lot["item_name"]))
    lines.append("")
    lines.append(f"📌 Статус: {status}")
    lines.append(f"💰 Ціна: {lot['price']} золота")

    if category == AUCTION_CATEGORY_EQUIPMENT:
        refine_level = int(lot["enhancement_level"] or snapshot.get("refine_level", 0) or 0)
        item_type = snapshot.get("item_type") or _auction_snapshot_value(snapshot, "type", "item_type", default="")
        slot_key = snapshot.get("slot_key") or _auction_snapshot_value(snapshot, "slot_key", "slot", default="")
        level = int(lot["level"] or snapshot.get("level", 0) or 0)

        lines.append("")
        lines.append(_auction_inventory_style_type_line(AUCTION_CATEGORY_EQUIPMENT))
        lines.append(f"🎯 Слот: {_auction_inventory_style_slot(snapshot, slot_key, item_type)}")
        if level:
            lines.append(f"🏷 Рівень предмета: {level} 🔒")
        if refine_level:
            lines.append(f"✨ Заточка: +{refine_level}")
        if lot["durability_current"] is not None:
            lines.append(f"🧱 Міцність: {lot['durability_current']}/{lot['durability_max']}")

        damage_lines = _auction_inventory_style_damage_lines(snapshot)
        defense_lines = _auction_collect_inventory_style_defense_lines(snapshot)
        bonus_lines = _auction_collect_inventory_style_bonus_lines(snapshot)

        if damage_lines:
            lines.append("")
            lines.extend(damage_lines)
        if defense_lines:
            lines.extend(defense_lines)
        if bonus_lines:
            lines.append("")
            lines.append("📊 Бонуси:")
            lines.extend(bonus_lines)
    else:
        lines.append("")
        lines.append(_auction_inventory_style_type_line(category))
        lines.append(f"📦 Кількість: {quantity}")

    lines.append("")
    if status == AUCTION_STATUS_ACTIVE:
        lines.append("Цей активний лот можна зняти з продажу.")
    else:
        lines.append("Цей лот уже не є активним.")

    return {
        "success": True,
        "lot": lot,
        "snapshot": snapshot,
        "text": "\n".join(lines),
    }


def cancel_active_auction_lot(user_id, lot_id):
    """
    Cancels seller's ACTIVE lot and returns item to inventory.

    Status: ACTIVE -> EXPIRED_CLAIMED.
    This mirrors manual cancel in the spec: the seller receives the item back immediately.
    """
    init_auction_house()
    user_id = int(user_id)
    lot_id = int(lot_id)

    try:
        conn.execute("BEGIN IMMEDIATE")

        cursor.execute("SELECT * FROM auction_lots WHERE id=? AND seller_user_id=?", (lot_id, user_id))
        lot = cursor.fetchone()

        if not lot:
            conn.rollback()
            return {"success": False, "message": "❌ Лот не знайдено."}

        if lot["status"] != AUCTION_STATUS_ACTIVE:
            conn.rollback()
            return {"success": False, "message": "⚠️ Зняти можна тільки активний лот."}

        snapshot = safe_json_loads(lot["item_snapshot_json"])
        quantity = int(lot["quantity"] or 1)

        # Return item first; this checks/uses inventory space.
        returned_inventory_id = _auction_insert_inventory_from_snapshot(user_id, snapshot, quantity=quantity)

        now = now_iso()
        cursor.execute("""
        UPDATE auction_lots
        SET status=?,
            claimed_at=?,
            updated_at=?
        WHERE id=? AND seller_user_id=? AND status=?
        """, (
            AUCTION_STATUS_EXPIRED_CLAIMED,
            now,
            now,
            lot_id,
            user_id,
            AUCTION_STATUS_ACTIVE,
        ))

        if cursor.rowcount != 1:
            conn.rollback()
            return {"success": False, "message": "⚠️ Лот уже недоступний."}

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
        ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lot_id,
            AUCTION_HISTORY_CANCELLED,
            user_id,
            user_id,
            lot["item_name"],
            lot["category"],
            quantity,
            lot["price"],
            AUCTION_STATUS_ACTIVE,
            AUCTION_STATUS_EXPIRED_CLAIMED,
            safe_json_dumps({"returned_inventory_id": returned_inventory_id}),
            now,
        ))

        conn.commit()

        return {
            "success": True,
            "message": "✅ Лот знято з продажу.",
            "lot_id": lot_id,
            "item_name": lot["item_name"],
            "quantity": quantity,
            "inventory_id": returned_inventory_id,
        }

    except Exception as error:
        try:
            conn.rollback()
        except Exception:
            pass
        return {"success": False, "message": f"❌ Помилка зняття лота: {error}"}
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE MY LOTS CANCEL WRAPPERS V1
# ==============================


def get_user_auction_lots(user_id, status=None, limit=8, offset=0):
    from systems.auction_house_system import get_user_auction_lots as _func
    return _func(user_id=user_id, status=status, limit=limit, offset=offset)


def get_user_auction_lot_by_id(user_id, lot_id):
    from systems.auction_house_system import get_user_auction_lot_by_id as _func
    return _func(user_id=user_id, lot_id=lot_id)


def build_user_auction_lot_details(user_id, lot_id):
    from systems.auction_house_system import build_user_auction_lot_details as _func
    return _func(user_id=user_id, lot_id=lot_id)


def cancel_active_auction_lot(user_id, lot_id):
    from systems.auction_house_system import cancel_active_auction_lot as _func
    return _func(user_id=user_id, lot_id=lot_id)
'''

HANDLER_APPEND = r'''

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
        qty = f" x{quantity}" if quantity > 1 and f"x{quantity}" not in lot["item_name"] else ""
        label = f"📦 {lot['item_name']}{qty} — {lot['price']} 💰"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_my_lot:{lot['id']}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Попередні", callback_data=f"ah_my_page:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Наступні", callback_data=f"ah_my_page:{page + 1}"))
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
            "❌ Помилка під час patch_8_0_6_auction_my_lots_cancel.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.6 Auction My Lots / Cancel застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- 📦 Мої лоти відкриває активні лоти гравця")
    print("- inline-список по 8 лотів на сторінку")
    print("- перегляд свого лота")
    print("- 📥 Зняти з продажу")
    print("- підтвердження зняття")
    print("- ACTIVE -> EXPIRED_CLAIMED")
    print("- предмет повертається в інвентар")
    print("- перевірка місця в інвентарі")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
