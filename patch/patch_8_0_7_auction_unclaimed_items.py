from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_7_auction_unclaimed_items"
SYSTEM_TARGET = Path("systems") / "auction_house_system.py"
DB_TARGET = Path("db.py")
HANDLER_TARGET = Path("handlers") / "auction_house.py"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE UNCLAIMED ITEMS V1"
DB_MARKER = "# ✅ AUCTION HOUSE UNCLAIMED ITEMS WRAPPERS V1"
HANDLER_MARKER = "# ✅ AUCTION HOUSE UNCLAIMED ITEMS UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE UNCLAIMED ITEMS V1
# ==============================

AUCTION_UNCLAIMED_ITEMS_PAGE_SIZE = 8


def get_user_unclaimed_auction_items(user_id, limit=8, offset=0):
    """Expired lots whose items are waiting for seller claim."""
    init_auction_house()
    update_expired_auction_lots()

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

    cursor.execute("""
    SELECT *
    FROM auction_lots
    WHERE seller_user_id=? AND status=?
    ORDER BY updated_at DESC, created_at DESC
    LIMIT ? OFFSET ?
    """, (
        int(user_id),
        AUCTION_STATUS_EXPIRED_UNCLAIMED,
        limit,
        offset,
    ))
    return cursor.fetchall()


def build_user_unclaimed_auction_item_details(user_id, lot_id):
    init_auction_house()
    update_expired_auction_lots()

    cursor.execute(
        "SELECT * FROM auction_lots WHERE id=? AND seller_user_id=?",
        (int(lot_id), int(user_id))
    )
    lot = cursor.fetchone()

    if not lot:
        return {"success": False, "message": "❌ Лот не знайдено."}

    if lot["status"] != AUCTION_STATUS_EXPIRED_UNCLAIMED:
        return {"success": False, "message": "⚠️ Цей предмет уже не очікує отримання."}

    snapshot = safe_json_loads(lot["item_snapshot_json"])
    category = lot["category"]
    quantity = int(lot["quantity"] or 1)

    lines = []
    lines.append("📬 Незабраний предмет")
    lines.append("")
    lines.append(str(lot["item_name"]))
    lines.append("")
    lines.append("⏳ Лот завершився і не був проданий.")
    lines.append(f"💰 Ціна лота була: {lot['price']} золота")

    if lot["delete_after"]:
        lines.append(f"🗑 Видалення після: {lot['delete_after']}")

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
        desc_lines = _auction_collect_stack_description_lines(snapshot)
        if desc_lines:
            lines.append("")
            lines.extend(desc_lines)

    lines.append("")
    lines.append("Предмет можна повернути в інвентар, якщо там є місце.")

    return {
        "success": True,
        "lot": lot,
        "snapshot": snapshot,
        "text": "\n".join(lines),
    }


def claim_expired_auction_item(user_id, lot_id):
    """
    Claims an EXPIRED_UNCLAIMED auction item back to seller inventory.

    Status: EXPIRED_UNCLAIMED -> EXPIRED_CLAIMED.
    """
    init_auction_house()
    update_expired_auction_lots()

    user_id = int(user_id)
    lot_id = int(lot_id)

    try:
        conn.execute("BEGIN IMMEDIATE")

        cursor.execute(
            "SELECT * FROM auction_lots WHERE id=? AND seller_user_id=?",
            (lot_id, user_id)
        )
        lot = cursor.fetchone()

        if not lot:
            conn.rollback()
            return {"success": False, "message": "❌ Лот не знайдено."}

        if lot["status"] != AUCTION_STATUS_EXPIRED_UNCLAIMED:
            conn.rollback()
            return {"success": False, "message": "⚠️ Предмет уже не очікує отримання."}

        snapshot = safe_json_loads(lot["item_snapshot_json"])
        quantity = int(lot["quantity"] or 1)

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
            AUCTION_STATUS_EXPIRED_UNCLAIMED,
        ))

        if cursor.rowcount != 1:
            conn.rollback()
            return {"success": False, "message": "⚠️ Предмет уже забрано або видалено."}

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
            AUCTION_HISTORY_ITEM_CLAIMED,
            user_id,
            user_id,
            lot["item_name"],
            lot["category"],
            quantity,
            lot["price"],
            AUCTION_STATUS_EXPIRED_UNCLAIMED,
            AUCTION_STATUS_EXPIRED_CLAIMED,
            safe_json_dumps({"returned_inventory_id": returned_inventory_id}),
            now,
        ))

        conn.commit()

        return {
            "success": True,
            "message": "✅ Предмет повернено в інвентар.",
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
        return {"success": False, "message": f"❌ Помилка отримання предмета: {error}"}
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE UNCLAIMED ITEMS WRAPPERS V1
# ==============================


def get_user_unclaimed_auction_items(user_id, limit=8, offset=0):
    from systems.auction_house_system import get_user_unclaimed_auction_items as _func
    return _func(user_id=user_id, limit=limit, offset=offset)


def build_user_unclaimed_auction_item_details(user_id, lot_id):
    from systems.auction_house_system import build_user_unclaimed_auction_item_details as _func
    return _func(user_id=user_id, lot_id=lot_id)


def claim_expired_auction_item(user_id, lot_id):
    from systems.auction_house_system import claim_expired_auction_item as _func
    return _func(user_id=user_id, lot_id=lot_id)
'''

HANDLER_APPEND = r'''

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
        qty = f" x{quantity}" if quantity > 1 and f"x{quantity}" not in lot["item_name"] else ""
        label = f"📬 {lot['item_name']}{qty}"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_uncl_lot:{lot['id']}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Попередні", callback_data=f"ah_uncl_page:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Наступні", callback_data=f"ah_uncl_page:{page + 1}"))
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
            "❌ Помилка під час patch_8_0_7_auction_unclaimed_items.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.7 Auction Unclaimed Items застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- 📬 Незабрані предмети відкриває EXPIRED_UNCLAIMED лоти гравця")
    print("- inline-список по 8 предметів на сторінку")
    print("- перегляд незабраного предмета")
    print("- 📥 Забрати предмет")
    print("- підтвердження отримання")
    print("- EXPIRED_UNCLAIMED -> EXPIRED_CLAIMED")
    print("- предмет повертається в інвентар")
    print("- перевірка місця в інвентарі")
    print("- update_expired_auction_lots() викликається при відкритті меню")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
