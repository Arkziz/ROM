from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_5a_auction_inline_items_pages"
TARGET_REL = Path("handlers") / "auction_house.py"
MARKER = "# ✅ AUCTION HOUSE INLINE ITEM LISTS V1"

APPEND_CODE = r'''

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
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_REL

    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/auction_house.py. Спочатку потрібні патчі Торгового Дому 8.0.")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч 8.0.5a вже застосовано. Змін не потрібно.")
        py_compile.compile(str(target), doraise=True)
        return

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + APPEND_CODE + "\n", encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_8_0_5a_auction_inline_items_pages.\n"
            "handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.5a Auction inline item lists застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("\nЩо змінено:")
    print("- товари при виставленні тепер inline-кнопками")
    print("- лоти при купівлі тепер inline-кнопками")
    print("- по 8 предметів/лотів на сторінку")
    print("- пагінація через inline-кнопки ⬅️ / ➡️")
    print("- введення кількості/ціни лишається текстом")
    print("\nПісля патча:")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
