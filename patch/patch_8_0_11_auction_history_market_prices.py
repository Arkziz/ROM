from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_11_auction_history_market_prices"
SYSTEM_TARGET = Path("systems") / "auction_house_system.py"
DB_TARGET = Path("db.py")
HANDLER_TARGET = Path("handlers") / "auction_house.py"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE HISTORY AND MARKET PRICES V1"
DB_MARKER = "# ✅ AUCTION HOUSE HISTORY AND MARKET PRICES WRAPPERS V1"
HANDLER_MARKER = "# ✅ AUCTION HOUSE HISTORY AND MARKET PRICES UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE HISTORY AND MARKET PRICES V1
# ==============================

AUCTION_HISTORY_PAGE_SIZE = 8
AUCTION_PRICE_HISTORY_LIMIT = 10


def _auction_table_columns_v1(table_name):
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in cursor.fetchall()}
    except Exception:
        return set()


def _auction_iso_to_ua_v1(value, with_time=True):
    value = str(value or "").strip()
    if not value:
        return "—"

    try:
        # Supports both 'YYYY-MM-DDTHH:MM:SS' and 'YYYY-MM-DD HH:MM:SS'.
        normalized = value.replace("Z", "").replace("T", " ")
        dt = datetime.fromisoformat(normalized)
        if with_time:
            return dt.strftime("%d.%m.%Y %H:%M")
        return dt.strftime("%d.%m.%Y")
    except Exception:
        if len(value) >= 10 and value[4] == "-" and value[7] == "-":
            date = f"{value[8:10]}.{value[5:7]}.{value[0:4]}"
            if with_time and len(value) >= 16:
                return f"{date} {value[11:16]}"
            return date
        return value


def _auction_sold_statuses_v1():
    return (
        AUCTION_STATUS_SOLD_UNCLAIMED,
        AUCTION_STATUS_SOLD_CLAIMED,
    )


def get_user_auction_history(user_id, mode="all", limit=8, offset=0):
    """
    Returns user's auction history using sold lots:
    - mode='buy'  -> lots bought by user
    - mode='sell' -> lots sold by user
    - mode='all'  -> both bought and sold
    """

    init_auction_house()

    user_id = int(user_id)
    mode = str(mode or "all")

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

    sold_statuses = _auction_sold_statuses_v1()
    params = list(sold_statuses)

    status_filter = "status IN (?, ?)"

    if mode == "buy":
        actor_filter = "buyer_user_id=?"
        params.append(user_id)
    elif mode == "sell":
        actor_filter = "seller_user_id=?"
        params.append(user_id)
    else:
        actor_filter = "(buyer_user_id=? OR seller_user_id=?)"
        params.extend([user_id, user_id])

    columns = _auction_table_columns_v1("auction_lots")
    date_col = "sold_at" if "sold_at" in columns else "created_at"

    sql = f"""
    SELECT *
    FROM auction_lots
    WHERE {status_filter}
      AND {actor_filter}
    ORDER BY COALESCE({date_col}, created_at) DESC, id DESC
    LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    cursor.execute(sql, tuple(params))
    return cursor.fetchall()


def get_auction_lot_market_price_stats(lot_id):
    """
    Returns market price stats for the selected lot based on completed sales
    of the same normalized item name.
    """

    init_auction_house()

    lot = get_auction_lot_by_id(lot_id)
    if not lot:
        return {
            "success": False,
            "message": "❌ Лот не знайдено."
        }

    columns = _auction_table_columns_v1("auction_lots")
    has_norm = "item_name_norm" in columns
    has_sold_at = "sold_at" in columns

    if has_norm:
        norm = str(lot["item_name_norm"] or "").strip().lower()
    else:
        norm = str(lot["item_name"] or "").strip().lower()

    if not norm:
        return {
            "success": False,
            "message": "❌ Не вдалося визначити назву предмета для історії цін."
        }

    name_expr = "item_name_norm" if has_norm else "LOWER(item_name)"
    date_col = "sold_at" if has_sold_at else "created_at"

    sql = f"""
    SELECT price, item_name, {date_col} AS history_date
    FROM auction_lots
    WHERE status IN (?, ?)
      AND {name_expr}=?
    ORDER BY COALESCE({date_col}, created_at) DESC, id DESC
    LIMIT ?
    """

    cursor.execute(sql, (
        AUCTION_STATUS_SOLD_UNCLAIMED,
        AUCTION_STATUS_SOLD_CLAIMED,
        norm,
        AUCTION_PRICE_HISTORY_LIMIT,
    ))
    rows = cursor.fetchall()

    prices = []
    for row in rows:
        try:
            prices.append(float(row["price"] or 0))
        except Exception:
            pass

    if not prices:
        return {
            "success": True,
            "lot": lot,
            "item_name": lot["item_name"],
            "count": 0,
            "message": "📈 Історії продажів для цього предмета ще немає."
        }

    return {
        "success": True,
        "lot": lot,
        "item_name": lot["item_name"],
        "count": len(prices),
        "min_price": min(prices),
        "max_price": max(prices),
        "avg_price": sum(prices) / len(prices),
        "last_price": prices[0],
        "rows": rows,
    }


def search_auction_market_price_stats(search_text, limit=10):
    """
    Searches completed sales by item name and returns grouped price stats.
    """

    init_auction_house()

    query = normalize_auction_search_query(search_text)
    if len(query) < 2:
        return []

    try:
        limit = int(limit)
    except Exception:
        limit = 10
    limit = max(1, min(20, limit))

    columns = _auction_table_columns_v1("auction_lots")
    has_norm = "item_name_norm" in columns
    group_expr = "item_name_norm" if has_norm else "LOWER(item_name)"

    tokens = [token for token in query.split(" ") if token]
    where = ["status IN (?, ?)"]
    params = [AUCTION_STATUS_SOLD_UNCLAIMED, AUCTION_STATUS_SOLD_CLAIMED]

    for token in tokens:
        where.append("(LOWER(item_name) LIKE ? OR " + group_expr + " LIKE ?)")
        params.append(f"%{token}%")
        params.append(f"%{token}%")

    sql = f"""
    SELECT
        {group_expr} AS item_key,
        MAX(item_name) AS item_name,
        COUNT(*) AS sales_count,
        MIN(CAST(price AS REAL)) AS min_price,
        MAX(CAST(price AS REAL)) AS max_price,
        AVG(CAST(price AS REAL)) AS avg_price,
        MAX(COALESCE(sold_at, created_at)) AS last_sale_at
    FROM auction_lots
    WHERE {' AND '.join(where)}
    GROUP BY {group_expr}
    ORDER BY sales_count DESC, last_sale_at DESC
    LIMIT ?
    """
    params.append(limit)

    cursor.execute(sql, tuple(params))
    return cursor.fetchall()


def format_auction_history_date(value, with_time=True):
    return _auction_iso_to_ua_v1(value, with_time=with_time)
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE HISTORY AND MARKET PRICES WRAPPERS V1
# ==============================


def get_user_auction_history(user_id, mode="all", limit=8, offset=0):
    from systems.auction_house_system import get_user_auction_history as _func
    return _func(user_id=user_id, mode=mode, limit=limit, offset=offset)


def get_auction_lot_market_price_stats(lot_id):
    from systems.auction_house_system import get_auction_lot_market_price_stats as _func
    return _func(lot_id=lot_id)


def search_auction_market_price_stats(search_text, limit=10):
    from systems.auction_house_system import search_auction_market_price_stats as _func
    return _func(search_text=search_text, limit=limit)


def format_auction_history_date(value, with_time=True):
    from systems.auction_house_system import format_auction_history_date as _func
    return _func(value=value, with_time=with_time)
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE HISTORY AND MARKET PRICES UI V1
# ==============================

AUCTION_HISTORY_PAGE_SIZE_V1 = 8
AUCTION_HISTORY_STATE_V1 = {}
AUCTION_MARKET_PRICE_SEARCH_STATE_V1 = {}

AUCTION_HISTORY_MODE_LABELS_V1 = {
    "all": "📜 Уся історія",
    "buy": "🛒 Мої покупки",
    "sell": "💰 Мої продажі",
}


def auction_history_reply_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📈 Ринкові ціни")
    kb.row("🔙 Торговий дім")
    return kb


def auction_market_price_search_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Історія")
    kb.row("🔙 Торговий дім")
    return kb


def auction_history_inline_kb_v1(mode="all", page=0, has_next=False):
    kb = types.InlineKeyboardMarkup(row_width=1)

    row = []
    for key, label in AUCTION_HISTORY_MODE_LABELS_V1.items():
        prefix = "✅ " if key == mode else ""
        row.append(types.InlineKeyboardButton(prefix + label, callback_data=f"ah_hist:{key}:0"))
    kb.row(*row)

    nav = []
    if int(page) > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Попередні", callback_data=f"ah_hist:{mode}:{int(page) - 1}"))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️ Наступні", callback_data=f"ah_hist:{mode}:{int(page) + 1}"))
    if nav:
        kb.row(*nav)

    return kb


def _auction_history_row_to_line_v1(row, viewer_user_id, index):
    from db import format_auction_history_date

    seller_id = int(row["seller_user_id"] or 0)
    buyer_id = int(row["buyer_user_id"] or 0)

    if buyer_id == int(viewer_user_id):
        action = "🛒 Куплено"
    elif seller_id == int(viewer_user_id):
        action = "💰 Продано"
    else:
        action = "📦 Угода"

    sold_date = row["sold_at"] if "sold_at" in row.keys() else row["created_at"]
    date_text = format_auction_history_date(sold_date, with_time=True)

    quantity = int(row["quantity"] or 1)
    qty = f" x{quantity}" if quantity > 1 and f"x{quantity}" not in row["item_name"] else ""

    return (
        f"{index}. {action}: {row['item_name']}{qty}\n"
        f"   💰 {row['price']} золота | 🕒 {date_text}"
    )


def build_auction_history_text_v1(user_id, mode="all", page=0):
    from db import get_user_auction_history

    page = max(0, int(page or 0))
    offset = page * AUCTION_HISTORY_PAGE_SIZE_V1
    rows = get_user_auction_history(user_id, mode=mode, limit=AUCTION_HISTORY_PAGE_SIZE_V1 + 1, offset=offset)

    visible = rows[:AUCTION_HISTORY_PAGE_SIZE_V1]
    has_next = len(rows) > AUCTION_HISTORY_PAGE_SIZE_V1
    mode_label = AUCTION_HISTORY_MODE_LABELS_V1.get(mode, AUCTION_HISTORY_MODE_LABELS_V1["all"])

    text = (
        "📜 Історія Торгового Дому\n\n"
        f"Розділ: {mode_label}\n"
        f"Сторінка: {page + 1}\n\n"
    )

    if not visible:
        text += "Записів поки немає."
    else:
        lines = []
        for idx, row in enumerate(visible, start=offset + 1):
            lines.append(_auction_history_row_to_line_v1(row, user_id, idx))
        text += "\n".join(lines)

    return text, auction_history_inline_kb_v1(mode=mode, page=page, has_next=has_next)


def build_auction_market_price_prompt_v1():
    return (
        "📈 Ринкові ціни\n\n"
        "Введіть частину назви предмета, щоб подивитися історію продажів.\n\n"
        "Приклади:\n"
        "• жезл\n"
        "• обладунок\n"
        "• камінь\n"
        "• зілля\n\n"
        "Мінімум: 2 символи."
    )


def build_auction_market_price_search_text_v1(query):
    from db import search_auction_market_price_stats, format_auction_history_date

    rows = search_auction_market_price_stats(query, limit=10)

    text = (
        "📈 Ринкові ціни\n\n"
        f"Запит: {query}\n\n"
    )

    if not rows:
        text += "Продажів за цим запитом ще не знайдено."
        return text

    lines = []
    for idx, row in enumerate(rows, start=1):
        try:
            avg_price = float(row["avg_price"] or 0)
            min_price = float(row["min_price"] or 0)
            max_price = float(row["max_price"] or 0)
        except Exception:
            avg_price = min_price = max_price = 0.0

        last_sale = format_auction_history_date(row["last_sale_at"], with_time=True)

        lines.append(
            f"{idx}. {row['item_name']}\n"
            f"   Продажів: {row['sales_count']} | Середня: {avg_price:.2f} 💰\n"
            f"   Мін: {min_price:.2f} 💰 | Макс: {max_price:.2f} 💰\n"
            f"   Останній продаж: {last_sale}"
        )

    text += "\n\n".join(lines)
    return text


def build_auction_lot_market_price_text_v1(lot_id):
    from db import get_auction_lot_market_price_stats, format_auction_history_date

    result = get_auction_lot_market_price_stats(lot_id)

    if not result.get("success"):
        return result.get("message", "❌ Не вдалося отримати історію цін.")

    item_name = result.get("item_name", "Предмет")

    text = (
        "📈 Ринкові ціни\n\n"
        f"📦 {item_name}\n\n"
    )

    if int(result.get("count", 0) or 0) <= 0:
        text += result.get("message", "Історії продажів ще немає.")
        return text

    text += (
        f"Продажів враховано: {result['count']}\n"
        f"Остання ціна: {float(result['last_price']):.2f} 💰\n"
        f"Середня ціна: {float(result['avg_price']):.2f} 💰\n"
        f"Мінімальна ціна: {float(result['min_price']):.2f} 💰\n"
        f"Максимальна ціна: {float(result['max_price']):.2f} 💰\n\n"
        "Останні продажі:\n"
    )

    for row in result.get("rows", [])[:5]:
        date_text = format_auction_history_date(row["history_date"], with_time=True)
        text += f"• {row['price']} 💰 — {date_text}\n"

    return text.rstrip()


# Add 📈 button into lot view keyboards, without adding back-to-house inline.
try:
    _auction_base_buy_lot_view_kb_before_history_v1 = auction_buy_lot_view_kb_v1
except NameError:
    _auction_base_buy_lot_view_kb_before_history_v1 = None


def auction_buy_lot_view_kb_v1(lot_id, category="all", sort_key="new", page=0):
    if not _auction_base_buy_lot_view_kb_before_history_v1:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("✅ Купити", callback_data=f"ah_buy2_confirm:{lot_id}:{category}:{sort_key}:{page}"))
        kb.add(types.InlineKeyboardButton("📈 Ринкові ціни", callback_data=f"ah_price_lot:{lot_id}"))
        return kb

    kb = _auction_base_buy_lot_view_kb_before_history_v1(lot_id, category=category, sort_key=sort_key, page=page)
    try:
        kb.add(types.InlineKeyboardButton("📈 Ринкові ціни", callback_data=f"ah_price_lot:{lot_id}"))
    except Exception:
        pass
    try:
        if "_auction_strip_back_to_house_inline_v1" in globals():
            kb = _auction_strip_back_to_house_inline_v1(kb)
    except Exception:
        pass
    return kb

try:
    _auction_base_search_lot_view_kb_before_history_v1 = auction_search_lot_view_kb_v1
except NameError:
    _auction_base_search_lot_view_kb_before_history_v1 = None


def auction_search_lot_view_kb_v1(lot_id, sort_key="new", page=0):
    if not _auction_base_search_lot_view_kb_before_history_v1:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("✅ Купити", callback_data=f"ah_search_confirm:{lot_id}:{sort_key}:{page}"))
        kb.add(types.InlineKeyboardButton("📈 Ринкові ціни", callback_data=f"ah_price_lot:{lot_id}"))
        return kb

    kb = _auction_base_search_lot_view_kb_before_history_v1(lot_id, sort_key=sort_key, page=page)
    try:
        kb.add(types.InlineKeyboardButton("📈 Ринкові ціни", callback_data=f"ah_price_lot:{lot_id}"))
    except Exception:
        pass
    return kb


def auction_price_back_kb_v1():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Торговий дім")
    return kb


def _auction_register_history_market_prices_handlers_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_HISTORY_BUTTON)
    def auction_history_start_v1(message):
        user_id = message.from_user.id
        text, inline_kb = build_auction_history_text_v1(user_id, mode="all", page=0)
        bot.send_message(
            message.chat.id,
            "📜 Розділ «Історія» відкрито.",
            reply_markup=auction_history_reply_kb_v1()
        )
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_hist:"))
    def auction_history_page_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        mode = parts[1]
        page = int(parts[2])
        text, inline_kb = build_auction_history_text_v1(user_id, mode=mode, page=page)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=inline_kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=inline_kb)

    @bot.message_handler(func=lambda m: m.text == "📈 Ринкові ціни")
    def auction_market_price_search_start_v1(message):
        user_id = message.from_user.id
        AUCTION_MARKET_PRICE_SEARCH_STATE_V1[user_id] = True
        bot.send_message(
            message.chat.id,
            build_auction_market_price_prompt_v1(),
            reply_markup=auction_market_price_search_kb_v1()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Історія")
    def auction_market_price_back_history_v1(message):
        user_id = message.from_user.id
        AUCTION_MARKET_PRICE_SEARCH_STATE_V1.pop(user_id, None)
        text, inline_kb = build_auction_history_text_v1(user_id, mode="all", page=0)
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)

    @bot.message_handler(func=lambda m: m.from_user.id in AUCTION_MARKET_PRICE_SEARCH_STATE_V1)
    def auction_market_price_search_query_v1(message):
        user_id = message.from_user.id
        text = (message.text or "").strip()

        if text == "🔙 Торговий дім":
            AUCTION_MARKET_PRICE_SEARCH_STATE_V1.pop(user_id, None)
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
            bot.send_message(message.chat.id, "❌ Введіть мінімум 2 символи.", reply_markup=auction_market_price_search_kb_v1())
            return

        bot.send_message(
            message.chat.id,
            build_auction_market_price_search_text_v1(text),
            reply_markup=auction_market_price_search_kb_v1()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_price_lot:"))
    def auction_lot_price_history_callback_v1(call):
        lot_id = int(call.data.split(":")[1])

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        text = build_auction_lot_market_price_text_v1(lot_id)
        bot.send_message(call.message.chat.id, text, reply_markup=auction_price_back_kb_v1())


try:
    _auction_base_register_handlers_before_history_market_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_history_market_v1 = None


def register_auction_house_handlers(bot):
    # History/market price handlers should be before old placeholder history handlers.
    _auction_register_history_market_prices_handlers_v1(bot)

    if _auction_base_register_handlers_before_history_market_v1:
        _auction_base_register_handlers_before_history_market_v1(bot)
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

        for rel_path in [SYSTEM_TARGET, DB_TARGET, HANDLER_TARGET]:
            py_compile.compile(str(root / rel_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass

        raise SystemExit(
            "❌ Помилка під час patch_8_0_11_auction_history_market_prices.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.11 Auction History / Market Prices застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- 📜 Історія Торгового Дому")
    print("- фільтри історії: уся історія, покупки, продажі")
    print("- ринкові ціни за лотом")
    print("- ручний пошук ринкових цін за назвою")
    print("- статистика: мін/макс/середня/остання ціна")
    print("- дати у форматі DD.MM.YYYY HH:MM")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
