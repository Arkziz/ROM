from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_9f_auction_sell_category_keyboard_cleanup_safe"
TARGET_RELATIVE = Path("handlers") / "auction_house.py"
MARKER = "# ✅ AUCTION HOUSE SELL CATEGORY KEYBOARD CLEANUP SAFE V2"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE SELL CATEGORY KEYBOARD CLEANUP SAFE V2
# ==============================

# Цей patch робить те саме, що планувалося у 8.0.9d, але без виклику старого
# reply-based helper-а. Він використовує вже робочий inline-flow:
# build_auction_sell_inline_list_text_v1() / auction_sell_items_inline_kb_v1().

AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V2 = "ah_sell_categories_v2"
AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V2 = "🔙 Торговий дім"

AUCTION_SELL_CATEGORY_BUTTONS_V2 = {
    "equipment": "⚔️ Спорядження",
    "potion": "🧪 Зілля для продажу",
    "material": "🪨 Матеріали",
}

AUCTION_SELL_CATEGORY_BY_BUTTON_V2 = {
    value: key for key, value in AUCTION_SELL_CATEGORY_BUTTONS_V2.items()
}


def auction_sell_category_kb_v2_safe():
    """ReplyKeyboard з категоріями виставлення товару."""

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_SELL_CATEGORY_BUTTONS_V2["equipment"], AUCTION_SELL_CATEGORY_BUTTONS_V2["potion"])
    kb.row(AUCTION_SELL_CATEGORY_BUTTONS_V2["material"])
    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V2)
    return kb


def auction_sell_listing_reply_back_kb_v2_safe():
    """ReplyKeyboard після відкриття конкретної категорії: тільки назад у Торговий Дім."""

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V2)
    return kb


def build_auction_sell_category_text_v2_safe():
    try:
        if "build_auction_sell_start_text_inline_v1" in globals():
            return build_auction_sell_start_text_inline_v1()
    except Exception:
        pass

    try:
        if "build_auction_sell_start_text_v2" in globals():
            return build_auction_sell_start_text_v2()
    except Exception:
        pass

    return (
        "➕ Виставити товар\n\n"
        "Оберіть категорію товару, який хочете виставити на продаж.\n\n"
        "Доступно зараз:\n"
        "• ⚔️ Спорядження — зброя, броня, щити, біжутерія.\n"
        "• 🧪 Зілля для продажу — стекові предмети, можна виставляти частинами.\n"
        "• 🪨 Матеріали — камені та матеріали, можна виставляти частинами.\n\n"
        "Обмеження:\n"
        "• 💎 Руну Успіху не можна продавати через Торговий Дім.\n"
        "• Екіпіровані та зламані предмети не можна виставляти.\n"
        "• Активний лот існує 7 днів.\n"
        "• Максимум активних лотів: 20."
    )


def _auction_sanitize_sell_inline_keyboard_v2_safe(kb):
    """
    Видаляє inline 🔙 Торговий дім і додає inline 🔙 Категорії виставлення.
    """

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
                if callback_data == AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V2:
                    continue

                new_row.append(button)

            if new_row:
                new_keyboard.append(new_row)

        kb.keyboard = new_keyboard
    except Exception:
        pass

    try:
        kb.add(types.InlineKeyboardButton("🔙 Категорії виставлення", callback_data=AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V2))
    except Exception:
        pass

    return kb


try:
    _auction_base_sell_items_inline_kb_before_sell_cleanup_v2 = auction_sell_items_inline_kb_v1
except NameError:
    _auction_base_sell_items_inline_kb_before_sell_cleanup_v2 = None


def auction_sell_items_inline_kb_v1(user_id, category, page=0):
    """
    Override робочого inline-list helper-а:
    - предмети залишаються inline;
    - прибираємо inline 🔙 Торговий дім;
    - додаємо inline 🔙 Категорії виставлення.
    """

    if not _auction_base_sell_items_inline_kb_before_sell_cleanup_v2:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("🔙 Категорії виставлення", callback_data=AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V2))
        return kb, [], False

    kb, items, has_next = _auction_base_sell_items_inline_kb_before_sell_cleanup_v2(user_id, category, page=page)
    kb = _auction_sanitize_sell_inline_keyboard_v2_safe(kb)
    return kb, items, has_next


try:
    _auction_base_sell_review_kb_before_sell_cleanup_v2 = auction_sell_review_kb_v1
except NameError:
    _auction_base_sell_review_kb_before_sell_cleanup_v2 = None


def auction_sell_review_kb_v1(category, inventory_id, page=0):
    """
    Override review-кнопок на екрані огляду товару перед ціною:
    - прибираємо inline 🔙 Торговий дім;
    - додаємо inline 🔙 Категорії виставлення.
    """

    if not _auction_base_sell_review_kb_before_sell_cleanup_v2:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("🔙 Категорії виставлення", callback_data=AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V2))
        return kb

    kb = _auction_base_sell_review_kb_before_sell_cleanup_v2(category, inventory_id, page=page)
    kb = _auction_sanitize_sell_inline_keyboard_v2_safe(kb)
    return kb


def _auction_open_sell_inline_category_v2_safe(bot, message, category):
    user_id = message.from_user.id
    page = 0

    # Спершу прибираємо нижні категорії і залишаємо тільки звичайну кнопку назад.
    bot.send_message(
        message.chat.id,
        "📂 Категорію відкрито. Для повернення до категорій використай inline-кнопку «🔙 Категорії виставлення» під списком.",
        reply_markup=auction_sell_listing_reply_back_kb_v2_safe()
    )

    try:
        text, inline_kb = build_auction_sell_inline_list_text_v1(user_id, category, page=page)
        inline_kb = _auction_sanitize_sell_inline_keyboard_v2_safe(inline_kb)
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)
    except Exception as error:
        bot.send_message(
            message.chat.id,
            f"⚠️ Не вдалося відкрити список товарів цієї категорії: {error}",
            reply_markup=auction_sell_listing_reply_back_kb_v2_safe()
        )


def _auction_register_sell_category_keyboard_cleanup_v2_safe(bot):

    @bot.message_handler(func=lambda m: m.text == "➕ Виставити товар")
    def auction_sell_start_categories_v2_safe(message):
        # При вході у виставлення повертаємо нижні кнопки категорій.
        bot.send_message(
            message.chat.id,
            build_auction_sell_category_text_v2_safe(),
            reply_markup=auction_sell_category_kb_v2_safe()
        )

    @bot.message_handler(func=lambda m: m.text in AUCTION_SELL_CATEGORY_BY_BUTTON_V2)
    def auction_sell_category_selected_v2_safe(message):
        category = AUCTION_SELL_CATEGORY_BY_BUTTON_V2.get(message.text, "equipment")
        _auction_open_sell_inline_category_v2_safe(bot, message, category)

    @bot.callback_query_handler(func=lambda call: call.data == AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V2)
    def auction_sell_back_to_categories_v2_safe(call):
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        bot.send_message(
            call.message.chat.id,
            build_auction_sell_category_text_v2_safe(),
            reply_markup=auction_sell_category_kb_v2_safe()
        )


try:
    _auction_base_register_handlers_before_sell_keyboard_cleanup_v2_safe = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_sell_keyboard_cleanup_v2_safe = None


def register_auction_house_handlers(bot):
    # Цей handler має бути раніше старих sell category handlers, щоб коректно керувати ReplyKeyboard.
    _auction_register_sell_category_keyboard_cleanup_v2_safe(bot)

    if _auction_base_register_handlers_before_sell_keyboard_cleanup_v2_safe:
        _auction_base_register_handlers_before_sell_keyboard_cleanup_v2_safe(bot)
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
            "❌ Помилка компіляції після patch_8_0_9f_auction_sell_category_keyboard_cleanup_safe.\n"
            "Файл handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.9f Auction sell category keyboard cleanup safe застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("")
    print("Що змінено:")
    print("- після вибору категорії виставлення нижні кнопки категорій прибираються")
    print("- у нижній ReplyKeyboard лишається тільки 🔙 Торговий дім")
    print("- предмети для продажу залишаються inline-кнопками")
    print("- inline 🔙 Торговий дім прибрано зі списку/огляду товару")
    print("- dodано inline 🔙 Категорії виставлення")
    print("- натискання 🔙 Категорії виставлення повертає нижні кнопки категорій")


if __name__ == "__main__":
    main()
