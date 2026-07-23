from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_10_auction_buy_search"
SYSTEM_TARGET = Path("systems") / "auction_house_system.py"
DB_TARGET = Path("db.py")
HANDLER_TARGET = Path("handlers") / "auction_house.py"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE BUY SEARCH V1"
DB_MARKER = "# ✅ AUCTION HOUSE BUY SEARCH WRAPPERS V1"
HANDLER_MARKER = "# ✅ AUCTION HOUSE BUY SEARCH UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE BUY SEARCH V1
# ==============================

AUCTION_SEARCH_MIN_LENGTH = 2
AUCTION_SEARCH_PAGE_SIZE = 8


def normalize_auction_search_query(search_text):
    text = str(search_text or "").strip().lower()
    text = " ".join(text.split())
    return text


def get_auction_lots_for_buy_search(buyer_user_id, search_text, sort_key="new", limit=8, offset=0):
    """
    Search ACTIVE lots by public item name.

    - Own lots are hidden.
    - Search uses item_name_norm when available.
    - All words in the query must be present in the item name.
    """

    init_auction_house()
    update_expired_auction_lots()

    buyer_user_id = int(buyer_user_id)
    query = normalize_auction_search_query(search_text)

    if len(query) < AUCTION_SEARCH_MIN_LENGTH:
        return []

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

    tokens = [token for token in query.split(" ") if token]
    for token in tokens:
        where.append("(item_name_norm LIKE ? OR LOWER(item_name) LIKE ?)")
        params.append(f"%{token}%")
        params.append(f"%{token}%")

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
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE BUY SEARCH WRAPPERS V1
# ==============================


def get_auction_lots_for_buy_search(buyer_user_id, search_text, sort_key="new", limit=8, offset=0):
    from systems.auction_house_system import get_auction_lots_for_buy_search as _func
    return _func(buyer_user_id=buyer_user_id, search_text=search_text, sort_key=sort_key, limit=limit, offset=offset)


def normalize_auction_search_query(search_text):
    from systems.auction_house_system import normalize_auction_search_query as _func
    return _func(search_text=search_text)
'''

HANDLER_APPEND = r'''

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
        label = f"📦 {lot['item_name']}{qty} — {lot['price']} 💰"
        kb.add(types.InlineKeyboardButton(
            _auction_inline_truncate(label),
            callback_data=f"ah_search_lot:{lot['id']}:{sort_key}:{page}"
        ))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Попередні", callback_data=f"ah_search_page:{sort_key}:{page - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Наступні", callback_data=f"ah_search_page:{sort_key}:{page + 1}"))
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
            "❌ Помилка під час patch_8_0_10_auction_buy_search.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.10 Auction Buy Search застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- 🔍 Пошук у меню 🛒 Купити")
    print("- пошук активних лотів за частиною назви предмета")
    print("- власні лоти покупцю не показуються")
    print("- результати пошуку inline-кнопками по 8 на сторінку")
    print("- сортування результатів: нові, старі, дешеві, дорогі, рідкість")
    print("- покупка з результатів пошуку")
    print("- 🔍 Новий пошук")
    print("- 🔙 Категорії")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
