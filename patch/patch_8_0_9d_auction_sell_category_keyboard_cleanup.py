from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_9d_auction_sell_category_keyboard_cleanup"
TARGET_RELATIVE = Path("handlers") / "auction_house.py"
MARKER = "# ✅ AUCTION HOUSE SELL CATEGORY KEYBOARD CLEANUP V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE SELL CATEGORY KEYBOARD CLEANUP V1
# ==============================

AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V1 = "ah_sell_categories"
AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1 = "🔙 Торговий дім"

AUCTION_SELL_CATEGORY_BUTTONS_V1 = {
    "equipment": "⚔️ Спорядження",
    "potion": "🧪 Зілля для продажу",
    "material": "🪨 Матеріали",
}


def auction_sell_category_kb_v1():
    """ReplyKeyboard з категоріями виставлення товару."""

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_SELL_CATEGORY_BUTTONS_V1["equipment"], AUCTION_SELL_CATEGORY_BUTTONS_V1["potion"])
    kb.row(AUCTION_SELL_CATEGORY_BUTTONS_V1["material"])
    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1)
    return kb


def auction_sell_listing_back_kb_v1():
    """
    ReplyKeyboard для екранів зі списком предметів на продаж.

    Коли гравець уже обрав категорію, кнопки інших категорій знизу не потрібні.
    Лишається тільки повернення в головне меню Торгового Дому.
    """

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(AUCTION_SELL_BACK_TO_HOUSE_BUTTON_V1)
    return kb


def build_auction_sell_category_text_v1():
    return (
        "➕ Виставити товар\n\n"
        "Оберіть категорію товару, який хочете виставити на продаж.\n\n"
        "Доступно зараз:\n"
        "• ⚔️ Спорядження — зброя, броня, щити, біжутерія.\n"
        "• 🧪 Зілля — стекові предмети, можна виставляти частинами.\n"
        "• 🪨 Матеріали — камені та матеріали, можна виставляти частинами.\n\n"
        "Обмеження:\n"
        "• 💎 Руну Успіху не можна продавати через Торговий Дім.\n"
        "• Екіпіровані та зламані предмети не можна виставляти.\n"
        "• Активний лот існує 7 днів.\n"
        "• Максимум активних лотів: 20."
    )


def _auction_sanitize_sell_inline_kb_v1(kb):
    """
    Прибирає inline-кнопку 🔙 Торговий дім зі списків виставлення товару
    і додає inline-кнопку 🔙 Категорії виставлення.
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

                new_row.append(button)

            if new_row:
                new_keyboard.append(new_row)

        kb.keyboard = new_keyboard
    except Exception:
        pass

    try:
        kb.add(types.InlineKeyboardButton("🔙 Категорії виставлення", callback_data=AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V1))
    except Exception:
        pass

    return kb


def _auction_call_equipment_sell_list_v1(user_id, page=0):
    """Пробує викликати наявний helper списку спорядження."""

    fn = globals().get("build_auction_sell_item_list_text")
    if not fn:
        return None

    try:
        return fn(user_id, page=page)
    except TypeError:
        try:
            return fn(user_id=user_id, page=page)
        except TypeError:
            try:
                return fn(user_id)
            except Exception:
                return None
    except Exception:
        raise


def _auction_try_stack_sell_list_v1(user_id, category, page=0):
    """Пробує знайти і викликати helper списку стекових предметів."""

    candidate_names = [
        "build_auction_sell_stack_item_list_text",
        "build_auction_sell_stack_items_text",
        "build_auction_sell_stack_list_text",
        "build_auction_sell_stack_items_list_text",
        "build_auction_sell_potion_material_list_text",
    ]

    for name in candidate_names:
        fn = globals().get(name)
        if not fn:
            continue

        call_patterns = [
            lambda: fn(user_id=user_id, category=category, page=page),
            lambda: fn(user_id, category, page=page),
            lambda: fn(user_id, category, page),
            lambda: fn(user_id=user_id, item_category=category, page=page),
            lambda: fn(user_id, item_category=category, page=page),
        ]

        for call_fn in call_patterns:
            try:
                return call_fn()
            except TypeError:
                continue
            except Exception:
                raise

    return None


def _auction_send_sell_category_listing_v1(bot, message, category):
    user_id = message.from_user.id
    page = 0

    # Перемикаємо нижню ReplyKeyboard на одну кнопку повернення.
    bot.send_message(
        message.chat.id,
        "📂 Категорію відкрито. Для повернення до категорій використай inline-кнопку «🔙 Категорії виставлення» під списком.",
        reply_markup=auction_sell_listing_back_kb_v1()
    )

    if category == "equipment":
        result = _auction_call_equipment_sell_list_v1(user_id, page=page)
        if result:
            text, inline_kb = result
            inline_kb = _auction_sanitize_sell_inline_kb_v1(inline_kb)
            bot.send_message(message.chat.id, text, reply_markup=inline_kb)
            return

        bot.send_message(
            message.chat.id,
            "⚠️ Не вдалося відкрити список спорядження для продажу.",
            reply_markup=auction_sell_listing_back_kb_v1()
        )
        return

    stack_category = "potion" if category == "potion" else "material"
    result = _auction_try_stack_sell_list_v1(user_id, stack_category, page=page)

    if result:
        text, inline_kb = result
        inline_kb = _auction_sanitize_sell_inline_kb_v1(inline_kb)
        bot.send_message(message.chat.id, text, reply_markup=inline_kb)
        return

    # Якщо helper має іншу назву, краще показати зрозумілий текст, а не мовчати.
    label = "зілля" if category == "potion" else "матеріалів"
    bot.send_message(
        message.chat.id,
        f"⚠️ Не вдалося відкрити список {label} для продажу. Якщо це повториться — скинь handlers/auction_house.py, я підключу точний helper.",
        reply_markup=auction_sell_listing_back_kb_v1()
    )


def _auction_register_sell_category_keyboard_cleanup_v1(bot):

    @bot.message_handler(func=lambda m: m.text == "➕ Виставити товар")
    def auction_sell_start_categories_v1(message):
        # Повертаємо нижні кнопки категорій при вході у виставлення товару.
        bot.send_message(
            message.chat.id,
            build_auction_sell_category_text_v1(),
            reply_markup=auction_sell_category_kb_v1()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_CATEGORY_BUTTONS_V1["equipment"])
    def auction_sell_category_equipment_v1(message):
        _auction_send_sell_category_listing_v1(bot, message, "equipment")

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_CATEGORY_BUTTONS_V1["potion"])
    def auction_sell_category_potion_v1(message):
        _auction_send_sell_category_listing_v1(bot, message, "potion")

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_CATEGORY_BUTTONS_V1["material"])
    def auction_sell_category_material_v1(message):
        _auction_send_sell_category_listing_v1(bot, message, "material")

    @bot.callback_query_handler(func=lambda call: call.data == AUCTION_SELL_BACK_TO_CATEGORIES_CALLBACK_V1)
    def auction_sell_back_to_categories_callback_v1(call):
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        bot.send_message(
            call.message.chat.id,
            build_auction_sell_category_text_v1(),
            reply_markup=auction_sell_category_kb_v1()
        )


try:
    _auction_base_register_handlers_before_sell_cat_cleanup_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_sell_cat_cleanup_v1 = None


def register_auction_house_handlers(bot):
    # Реєструємо раніше старих sell handlers, щоб керувати ReplyKeyboard категорій.
    _auction_register_sell_category_keyboard_cleanup_v1(bot)

    if _auction_base_register_handlers_before_sell_cat_cleanup_v1:
        _auction_base_register_handlers_before_sell_cat_cleanup_v1(bot)
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
            "❌ Помилка компіляції після patch_8_0_9d_auction_sell_category_keyboard_cleanup.\n"
            "Файл handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.9d Auction sell category keyboard cleanup застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("")
    print("Що змінено:")
    print("- після вибору категорії виставлення нижні кнопки інших категорій прибираються")
    print("- у нижній ReplyKeyboard лишається тільки 🔙 Торговий дім")
    print("- inline-кнопку 🔙 Торговий дім прибрано зі списків виставлення")
    print("- додано inline-кнопку 🔙 Категорії виставлення")
    print("- натискання 🔙 Категорії виставлення повертає нижні кнопки категорій")


if __name__ == "__main__":
    main()
