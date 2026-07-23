from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_9c_auction_buy_category_keyboard_cleanup"
TARGET_RELATIVE = Path("handlers") / "auction_house.py"
MARKER = "# ✅ AUCTION HOUSE BUY CATEGORY KEYBOARD CLEANUP V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE BUY CATEGORY KEYBOARD CLEANUP V1
# ==============================


def auction_buy_lots_reply_back_kb_v1():
    """
    ReplyKeyboard для екранів зі списком лотів.

    Коли гравець уже обрав категорію, кнопки категорій знизу більше не потрібні.
    Лишається тільки звичайна кнопка повернення в головне меню Торгового Дому.
    """

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Торговий дім")
    return kb


def _auction_register_buy_category_keyboard_cleanup_v1(bot):

    @bot.message_handler(func=lambda m: m.text in AUCTION_BUY_CATEGORY_BY_BUTTON_V1)
    def auction_buy_category_selected_clean_keyboard_v1(message):
        user_id = message.from_user.id
        category = AUCTION_BUY_CATEGORY_BY_BUTTON_V1.get(message.text, "all")
        sort_key = "new"
        page = 0

        text = build_auction_buy_lots_text_v1(
            category=category,
            sort_key=sort_key,
            page=page
        )

        inline_kb, lots, has_next = auction_buy_lots_inline_kb_v1(
            user_id,
            category=category,
            sort_key=sort_key,
            page=page
        )

        if not lots:
            text += "\n\nЛотів у цій категорії поки немає."

        # Важливо: спочатку міняємо нижню ReplyKeyboard на одну кнопку 🔙 Торговий дім,
        # а потім надсилаємо список з inline-кнопками.
        bot.send_message(
            message.chat.id,
            "📂 Категорію відкрито. Для повернення до категорій використай inline-кнопку «🔙 Категорії» під списком.",
            reply_markup=auction_buy_lots_reply_back_kb_v1()
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=inline_kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "ah_buy2_categories")
    def auction_buy_categories_restore_reply_keyboard_v1(call):
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        # При поверненні до категорій повертаємо нижні кнопки категорій.
        bot.send_message(
            call.message.chat.id,
            build_auction_buy_category_text_v1(),
            reply_markup=auction_buy_category_kb_v1()
        )


try:
    _auction_base_register_handlers_before_buy_cat_keyboard_cleanup_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_buy_cat_keyboard_cleanup_v1 = None


def register_auction_house_handlers(bot):
    # Реєструємо раніше старих category handlers, щоб прибирати нижні кнопки категорій після вибору.
    _auction_register_buy_category_keyboard_cleanup_v1(bot)

    if _auction_base_register_handlers_before_buy_cat_keyboard_cleanup_v1:
        _auction_base_register_handlers_before_buy_cat_keyboard_cleanup_v1(bot)
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
            "❌ Помилка компіляції після patch_8_0_9c_auction_buy_category_keyboard_cleanup.\n"
            "Файл handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.9c Auction buy category keyboard cleanup застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("")
    print("Що змінено:")
    print("- після вибору категорії покупки нижні кнопки категорій прибираються")
    print("- у нижній ReplyKeyboard лишається тільки 🔙 Торговий дім")
    print("- inline-кнопка 🔙 Категорії повертає нижні кнопки категорій")
    print("- inline-список лотів і сортування залишаються без змін")


if __name__ == "__main__":
    main()
