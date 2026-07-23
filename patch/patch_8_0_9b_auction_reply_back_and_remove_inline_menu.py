from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_9b_auction_reply_back_and_remove_inline_menu"
TARGET_RELATIVE = Path("handlers") / "auction_house.py"
MARKER = "# ✅ AUCTION HOUSE REPLY BACK AND REMOVE INLINE MENU V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE REPLY BACK AND REMOVE INLINE MENU V1
# ==============================

AUCTION_BACK_TO_HOUSE_BUTTON_V1 = "🔙 Торговий дім"


def _auction_clear_runtime_states_v2(user_id):
    """
    Очищає runtime-стани Торгового Дому, щоб звичайна кнопка
    🔙 Торговий дім не ковталась state-router-ами.
    """

    possible_state_names = [
        "AUCTION_SELL_STATE",
        "AUCTION_BUY_STATE",
        "AUCTION_MY_LOTS_STATE",
        "AUCTION_UNCLAIMED_STATE",
        "AUCTION_COMPLETED_SALES_STATE",
        "AUCTION_SEARCH_STATE",
        "AUCTION_HISTORY_STATE",
    ]

    for state_name in possible_state_names:
        state_obj = globals().get(state_name)
        if not state_obj:
            continue

        try:
            if isinstance(state_obj, dict):
                state_obj.pop(user_id, None)
            elif isinstance(state_obj, set):
                state_obj.discard(user_id)
        except Exception:
            pass


def _auction_main_menu_text_v2(user_id=None):
    """
    Текст головного меню Торгового Дому.
    Не залежить від конкретної назви старого helper-а.
    """

    try:
        if "build_auction_house_text" in globals():
            if user_id is not None:
                try:
                    return build_auction_house_text(user_id)
                except TypeError:
                    return build_auction_house_text()
            return build_auction_house_text()
    except Exception:
        pass

    return (
        "🏛️ Торговий дім\n\n"
        "Тут гравці можуть виставляти товари на продаж, купувати лоти інших гравців "
        "та забирати золото за завершені продажі.\n\n"
        "Доступні дії:\n"
        "• 🛒 Купити\n"
        "• ➕ Виставити товар\n"
        "• 📦 Мої лоти\n"
        "• 📬 Незабрані предмети\n"
        "• 💰 Завершені продажі\n"
        "• 📜 Історія"
    )


def auction_buy_lots_inline_kb_v1(user_id, category="all", sort_key="new", page=0):
    """
    Override: список лотів лишається inline, але без inline-кнопки 🔙 Торговий дім.
    Повернення в Торговий Дім має бути через звичайну ReplyKeyboard-кнопку внизу.
    """

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

    # Сортування лишається inline.
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

    # У списку покупки лишаємо тільки повернення до категорій.
    # Назад у головне меню — звичайною кнопкою 🔙 Торговий дім.
    kb.add(types.InlineKeyboardButton("🔙 Категорії", callback_data="ah_buy2_categories"))
    return kb, visible_lots, has_next


def auction_buy_lot_view_kb_v1(lot_id, category="all", sort_key="new", page=0):
    """
    Override: у деталях лота прибрано inline 🔙 Торговий дім.
    """

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Купити", callback_data=f"ah_buy2_confirm:{lot_id}:{category}:{sort_key}:{page}"))
    kb.add(types.InlineKeyboardButton("🔙 До списку", callback_data=f"ah_buy2_page:{category}:{sort_key}:{page}"))
    return kb


def auction_buy_confirm_kb_v1(lot_id, category="all", sort_key="new", page=0):
    """
    Override: confirmation без inline 🔙 Торговий дім.
    """

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Підтвердити покупку", callback_data=f"ah_buy2_do:{lot_id}:{category}:{sort_key}:{page}"))
    kb.add(types.InlineKeyboardButton("❌ Назад", callback_data=f"ah_buy2_lot:{lot_id}:{category}:{sort_key}:{page}"))
    return kb


def _auction_register_reply_back_to_house_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_BACK_TO_HOUSE_BUTTON_V1)
    def auction_reply_back_to_house_v1(message):
        user_id = message.from_user.id
        _auction_clear_runtime_states_v2(user_id)

        bot.send_message(
            message.chat.id,
            _auction_main_menu_text_v2(user_id),
            reply_markup=auction_house_kb()
        )


try:
    _auction_base_register_handlers_before_reply_back_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_reply_back_v1 = None


def register_auction_house_handlers(bot):
    # Reply-кнопка 🔙 Торговий дім має реєструватися раніше старих state-router-ів.
    _auction_register_reply_back_to_house_v1(bot)

    if _auction_base_register_handlers_before_reply_back_v1:
        _auction_base_register_handlers_before_reply_back_v1(bot)
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
    target = root / TARGET_RELATIVE

    if not target.exists():
        raise SystemExit(f"❌ Не знайдено файл: {target}")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч уже застосовано раніше.")
        return

    backup = make_backup(root, target)

    try:
        target.write_text(original.rstrip() + "\n" + APPEND_CODE + "\n", encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_8_0_9b_auction_reply_back_and_remove_inline_menu.\n"
            "Файл handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.9b Auction reply back / remove inline menu застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- inline-кнопку 🔙 Торговий дім прибрано з екранів покупки")
    print("- стандартна ReplyKeyboard-кнопка 🔙 Торговий дім тепер повертає в головне меню Торгового Дому")
    print("- при поверненні очищаються завислі auction UI states")


if __name__ == "__main__":
    main()
