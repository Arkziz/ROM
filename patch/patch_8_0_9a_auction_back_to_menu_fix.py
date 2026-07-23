from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_9a_auction_back_to_menu_fix"
TARGET_RELATIVE = Path("handlers") / "auction_house.py"
MARKER = "# ✅ AUCTION HOUSE BACK TO MENU CALLBACK FIX V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE BACK TO MENU CALLBACK FIX V1
# ==============================


def _auction_clear_runtime_states_v1(user_id):
    """
    Best-effort cleanup for Auction House UI states.
    This prevents old sell/buy state routers from swallowing navigation buttons.
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


def _auction_main_menu_text_v1(user_id=None):
    """
    Returns Auction House main menu text without relying on a specific older helper name.
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


def _auction_register_back_to_menu_callback_v1(bot):

    @bot.callback_query_handler(func=lambda call: call.data == "ah_menu")
    def auction_back_to_menu_callback_v1(call):
        user_id = call.from_user.id
        _auction_clear_runtime_states_v1(user_id)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        # Main Auction House menu uses ReplyKeyboardMarkup, so send a fresh message.
        # Telegram edit_message_text cannot attach ReplyKeyboardMarkup.
        bot.send_message(
            call.message.chat.id,
            _auction_main_menu_text_v1(user_id),
            reply_markup=auction_house_kb()
        )


try:
    _auction_base_register_handlers_before_back_to_menu_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_back_to_menu_v1 = None


def register_auction_house_handlers(bot):
    # Register ah_menu callback before older handlers, so every inline "🔙 Торговий дім" works.
    _auction_register_back_to_menu_callback_v1(bot)

    if _auction_base_register_handlers_before_back_to_menu_v1:
        _auction_base_register_handlers_before_back_to_menu_v1(bot)
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
            "❌ Помилка компіляції після patch_8_0_9a_auction_back_to_menu_fix.\n"
            "Файл handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.9a Auction back-to-menu fix застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- inline-кнопка 🔙 Торговий дім тепер відкриває головне меню Торгового Дому")
    print("- меню надсилається новим повідомленням із ReplyKeyboard, бо edit_message_text не підтримує ReplyKeyboardMarkup")
    print("- при поверненні очищаються завислі auction UI states")


if __name__ == "__main__":
    main()
