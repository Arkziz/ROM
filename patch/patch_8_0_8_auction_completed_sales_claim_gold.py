from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_8_auction_completed_sales_claim_gold"
SYSTEM_TARGET = Path("systems") / "auction_house_system.py"
DB_TARGET = Path("db.py")
HANDLER_TARGET = Path("handlers") / "auction_house.py"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE COMPLETED SALES CLAIM GOLD V1"
DB_MARKER = "# ✅ AUCTION HOUSE COMPLETED SALES CLAIM GOLD WRAPPERS V1"
HANDLER_MARKER = "# ✅ AUCTION HOUSE COMPLETED SALES CLAIM GOLD UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE COMPLETED SALES CLAIM GOLD V1
# ==============================

AUCTION_COMPLETED_SALES_PAGE_SIZE = 8


def get_user_unclaimed_auction_sales(user_id, limit=8, offset=0):
    """Sold lots whose gold is waiting for seller claim."""
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
    ORDER BY sold_at DESC, updated_at DESC, created_at DESC
    LIMIT ? OFFSET ?
    """, (
        int(user_id),
        AUCTION_STATUS_SOLD_UNCLAIMED,
        limit,
        offset,
    ))
    return cursor.fetchall()


def build_user_unclaimed_auction_sale_details(user_id, lot_id):
    init_auction_house()
    update_expired_auction_lots()

    cursor.execute(
        "SELECT * FROM auction_lots WHERE id=? AND seller_user_id=?",
        (int(lot_id), int(user_id))
    )
    lot = cursor.fetchone()

    if not lot:
        return {"success": False, "message": "❌ Продаж не знайдено."}

    if lot["status"] != AUCTION_STATUS_SOLD_UNCLAIMED:
        return {"success": False, "message": "⚠️ Це золото вже отримано або продаж недоступний."}

    snapshot = safe_json_loads(lot["item_snapshot_json"])
    category = lot["category"]
    quantity = int(lot["quantity"] or 1)

    lines = []
    lines.append("💰 Завершений продаж")
    lines.append("")
    lines.append(str(lot["item_name"]))
    lines.append("")
    lines.append(f"✅ Продано за: {lot['price']} золота")

    if lot["sold_at"]:
        lines.append(f"🕒 Дата продажу: {lot['sold_at']}")
    if lot["delete_after"]:
        lines.append(f"🗑 Видалення виплати після: {lot['delete_after']}")

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
    lines.append("Золото можна забрати вручну.")

    return {
        "success": True,
        "lot": lot,
        "snapshot": snapshot,
        "text": "\n".join(lines),
    }


def claim_auction_sale_gold(user_id, lot_id):
    """
    Claims gold from SOLD_UNCLAIMED sale.

    Status: SOLD_UNCLAIMED -> SOLD_CLAIMED.
    Gold is added to seller's balance.
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
            return {"success": False, "message": "❌ Продаж не знайдено."}

        if lot["status"] != AUCTION_STATUS_SOLD_UNCLAIMED:
            conn.rollback()
            return {"success": False, "message": "⚠️ Золото вже отримано або виплата недоступна."}

        price = auction_price_to_decimal(lot["price"])
        current_gold = _auction_get_user_gold(user_id)
        _auction_set_user_gold(user_id, current_gold + price)

        now = now_iso()
        cursor.execute("""
        UPDATE auction_lots
        SET status=?,
            claimed_at=?,
            updated_at=?
        WHERE id=? AND seller_user_id=? AND status=?
        """, (
            AUCTION_STATUS_SOLD_CLAIMED,
            now,
            now,
            lot_id,
            user_id,
            AUCTION_STATUS_SOLD_UNCLAIMED,
        ))

        if cursor.rowcount != 1:
            conn.rollback()
            return {"success": False, "message": "⚠️ Виплату вже отримано."}

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
            AUCTION_HISTORY_GOLD_CLAIMED,
            user_id,
            user_id,
            lot["buyer_user_id"],
            lot["item_name"],
            lot["category"],
            int(lot["quantity"] or 1),
            lot["price"],
            AUCTION_STATUS_SOLD_UNCLAIMED,
            AUCTION_STATUS_SOLD_CLAIMED,
            safe_json_dumps({"claimed_gold": lot["price"]}),
            now,
        ))

        conn.commit()

        return {
            "success": True,
            "message": f"✅ Отримано {lot['price']} золота.",
            "lot_id": lot_id,
            "item_name": lot["item_name"],
            "amount": lot["price"],
        }

    except Exception as error:
        try:
            conn.rollback()
        except Exception:
            pass
        return {"success": False, "message": f"❌ Помилка отримання золота: {error}"}
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE COMPLETED SALES CLAIM GOLD WRAPPERS V1
# ==============================


def get_user_unclaimed_auction_sales(user_id, limit=8, offset=0):
    from systems.auction_house_system import get_user_unclaimed_auction_sales as _func
    return _func(user_id=user_id, limit=limit, offset=offset)


def build_user_unclaimed_auction_sale_details(user_id, lot_id):
    from systems.auction_house_system import build_user_unclaimed_auction_sale_details as _func
    return _func(user_id=user_id, lot_id=lot_id)


def claim_auction_sale_gold(user_id, lot_id):
    from systems.auction_house_system import claim_auction_sale_gold as _func
    return _func(user_id=user_id, lot_id=lot_id)
'''

HANDLER_APPEND = r'''

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
        nav.append(types.InlineKeyboardButton("⬅️ Попередні", callback_data=f"ah_sale_page:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Наступні", callback_data=f"ah_sale_page:{page + 1}"))
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
            "❌ Помилка під час patch_8_0_8_auction_completed_sales_claim_gold.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.8 Auction Completed Sales / Claim Gold застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- 💰 Завершені продажі відкриває SOLD_UNCLAIMED лоти продавця")
    print("- inline-список по 8 продажів на сторінку")
    print("- перегляд завершеного продажу")
    print("- 💰 Забрати золото")
    print("- підтвердження отримання золота")
    print("- SOLD_UNCLAIMED -> SOLD_CLAIMED")
    print("- золото додається на баланс продавця")
    print("- виплата захищена транзакцією")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
