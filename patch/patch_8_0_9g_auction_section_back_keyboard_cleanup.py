from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_9g_auction_section_back_keyboard_cleanup"
TARGET_RELATIVE = Path("handlers") / "auction_house.py"
MARKER = "# ✅ AUCTION HOUSE SECTION BACK KEYBOARD CLEANUP V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE SECTION BACK KEYBOARD CLEANUP V1
# ==============================

# Уніфікація навігації Торгового Дому:
# - inline-кнопка "🔙 Торговий дім" прибирається з розділів;
# - у нижній ReplyKeyboard лишається звичайна кнопка "🔙 Торговий дім";
# - це стосується: 📦 Мої лоти, 📬 Незабрані предмети,
#   💰 Завершені продажі, 📜 Історія.

AUCTION_REPLY_BACK_TO_HOUSE_BUTTON_V1 = "🔙 Торговий дім"


def auction_reply_back_only_kb_v1():
    """Нижня клавіатура для внутрішніх розділів Торгового Дому."""

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_REPLY_BACK_TO_HOUSE_BUTTON_V1)
    return kb


def _auction_strip_back_to_house_inline_v1(kb):
    """Прибирає inline-кнопки повернення в головне меню Торгового Дому."""

    try:
        new_keyboard = []

        for row in getattr(kb, "keyboard", []) or []:
            new_row = []

            for button in row:
                text = getattr(button, "text", "") or ""
                callback_data = getattr(button, "callback_data", "") or ""

                if callback_data == "ah_menu":
                    continue

                if "Торговий дім" in text:
                    continue

                new_row.append(button)

            if new_row:
                new_keyboard.append(new_row)

        kb.keyboard = new_keyboard
    except Exception:
        pass

    return kb


# ------------------------------
# Мої лоти: прибрати inline "Торговий дім"
# ------------------------------

try:
    _auction_base_my_lots_inline_kb_before_section_cleanup_v1 = auction_my_lots_inline_kb_v1
except NameError:
    _auction_base_my_lots_inline_kb_before_section_cleanup_v1 = None


def auction_my_lots_inline_kb_v1(user_id, page=0):
    if not _auction_base_my_lots_inline_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1), [], False

    kb, lots, has_next = _auction_base_my_lots_inline_kb_before_section_cleanup_v1(user_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb), lots, has_next


try:
    _auction_base_my_lot_view_kb_before_section_cleanup_v1 = auction_my_lot_view_kb_v1
except NameError:
    _auction_base_my_lot_view_kb_before_section_cleanup_v1 = None


def auction_my_lot_view_kb_v1(lot_id, page=0):
    if not _auction_base_my_lot_view_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1)

    kb = _auction_base_my_lot_view_kb_before_section_cleanup_v1(lot_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb)


# ------------------------------
# Незабрані предмети: прибрати inline "Торговий дім"
# ------------------------------

try:
    _auction_base_unclaimed_items_inline_kb_before_section_cleanup_v1 = auction_unclaimed_items_inline_kb_v1
except NameError:
    _auction_base_unclaimed_items_inline_kb_before_section_cleanup_v1 = None


def auction_unclaimed_items_inline_kb_v1(user_id, page=0):
    if not _auction_base_unclaimed_items_inline_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1), [], False

    kb, lots, has_next = _auction_base_unclaimed_items_inline_kb_before_section_cleanup_v1(user_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb), lots, has_next


try:
    _auction_base_unclaimed_item_view_kb_before_section_cleanup_v1 = auction_unclaimed_item_view_kb_v1
except NameError:
    _auction_base_unclaimed_item_view_kb_before_section_cleanup_v1 = None


def auction_unclaimed_item_view_kb_v1(lot_id, page=0):
    if not _auction_base_unclaimed_item_view_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1)

    kb = _auction_base_unclaimed_item_view_kb_before_section_cleanup_v1(lot_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb)


# ------------------------------
# Завершені продажі: прибрати inline "Торговий дім"
# ------------------------------

try:
    _auction_base_completed_sales_inline_kb_before_section_cleanup_v1 = auction_completed_sales_inline_kb_v1
except NameError:
    _auction_base_completed_sales_inline_kb_before_section_cleanup_v1 = None


def auction_completed_sales_inline_kb_v1(user_id, page=0):
    if not _auction_base_completed_sales_inline_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1), [], False

    kb, lots, has_next = _auction_base_completed_sales_inline_kb_before_section_cleanup_v1(user_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb), lots, has_next


try:
    _auction_base_completed_sale_view_kb_before_section_cleanup_v1 = auction_completed_sale_view_kb_v1
except NameError:
    _auction_base_completed_sale_view_kb_before_section_cleanup_v1 = None


def auction_completed_sale_view_kb_v1(lot_id, page=0):
    if not _auction_base_completed_sale_view_kb_before_section_cleanup_v1:
        return types.InlineKeyboardMarkup(row_width=1)

    kb = _auction_base_completed_sale_view_kb_before_section_cleanup_v1(lot_id, page=page)
    return _auction_strip_back_to_house_inline_v1(kb)


# ------------------------------
# Section start handlers: нижня ReplyKeyboard тільки з "🔙 Торговий дім"
# ------------------------------

def _auction_register_section_back_keyboard_cleanup_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_MY_LOTS_BUTTON)
    def auction_my_lots_start_section_cleanup_v1(message):
        user_id = message.from_user.id
        text, inline_kb = build_auction_my_lots_text_v1(user_id, page=0)
        inline_kb = _auction_strip_back_to_house_inline_v1(inline_kb)

        bot.send_message(
            message.chat.id,
            "📦 Розділ «Мої лоти» відкрито.",
            reply_markup=auction_reply_back_only_kb_v1()
        )
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)

    @bot.message_handler(func=lambda m: m.text == AUCTION_UNCLAIMED_ITEMS_BUTTON)
    def auction_unclaimed_items_start_section_cleanup_v1(message):
        user_id = message.from_user.id
        text, inline_kb = build_auction_unclaimed_items_text_v1(user_id, page=0)
        inline_kb = _auction_strip_back_to_house_inline_v1(inline_kb)

        bot.send_message(
            message.chat.id,
            "📬 Розділ «Незабрані предмети» відкрито.",
            reply_markup=auction_reply_back_only_kb_v1()
        )
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)

    @bot.message_handler(func=lambda m: m.text == AUCTION_SOLD_BUTTON)
    def auction_completed_sales_start_section_cleanup_v1(message):
        user_id = message.from_user.id
        text, inline_kb = build_auction_completed_sales_text_v1(user_id, page=0)
        inline_kb = _auction_strip_back_to_house_inline_v1(inline_kb)

        bot.send_message(
            message.chat.id,
            "💰 Розділ «Завершені продажі» відкрито.",
            reply_markup=auction_reply_back_only_kb_v1()
        )
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)

    @bot.message_handler(func=lambda m: m.text == AUCTION_HISTORY_BUTTON)
    def auction_history_start_section_cleanup_v1(message):
        text = (
            "📜 Історія\n\n"
            "Тут буде історія покупок, продажів і перегляд ринкових цін.\n\n"
            "Цей розділ буде реалізовано на наступному етапі Торгового Дому."
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=auction_reply_back_only_kb_v1()
        )


try:
    _auction_base_register_handlers_before_section_back_cleanup_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_section_back_cleanup_v1 = None


def register_auction_house_handlers(bot):
    # Реєструємо раніше старих placeholder/section handlers.
    _auction_register_section_back_keyboard_cleanup_v1(bot)

    if _auction_base_register_handlers_before_section_back_cleanup_v1:
        _auction_base_register_handlers_before_section_back_cleanup_v1(bot)
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
            "❌ Помилка компіляції після patch_8_0_9g_auction_section_back_keyboard_cleanup.\n"
            "Файл handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.9g Auction section back keyboard cleanup застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("")
    print("Що змінено:")
    print("- inline-кнопку 🔙 Торговий дім прибрано з Моїх лотів")
    print("- inline-кнопку 🔙 Торговий дім прибрано з Незабраних предметів")
    print("- inline-кнопку 🔙 Торговий дім прибрано із Завершених продажів")
    print("- для 📜 Історія використовується звичайна кнопка 🔙 Торговий дім")
    print("- при вході в ці розділи нижня ReplyKeyboard містить тільки 🔙 Торговий дім")


if __name__ == "__main__":
    main()
