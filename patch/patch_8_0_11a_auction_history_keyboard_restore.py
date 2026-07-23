from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_11a_auction_history_keyboard_restore"
TARGET_RELATIVE = Path("handlers") / "auction_house.py"
MARKER = "# ✅ AUCTION HISTORY KEYBOARD RESTORE V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HISTORY KEYBOARD RESTORE V1
# ==============================

# Виправлення UX у розділі історії:
# після натискання звичайної кнопки "🔙 Історія" з меню ринкових цін
# нижня ReplyKeyboard має повертатися до клавіатури історії:
#   📈 Ринкові ціни
#   🔙 Торговий дім
# а не залишати кнопку "🔙 Історія".


def _auction_open_history_screen_v1(bot, chat_id, user_id, mode="all", page=0):
    """Відкриває історію і гарантовано повертає правильну нижню клавіатуру."""

    try:
        AUCTION_MARKET_PRICE_SEARCH_STATE_V1.pop(user_id, None)
    except Exception:
        pass

    try:
        text, inline_kb = build_auction_history_text_v1(user_id, mode=mode, page=page)
    except Exception:
        text = "📜 Історія Торгового Дому\n\nЗаписів поки немає."
        inline_kb = None

    # Спочатку міняємо нижню клавіатуру на клавіатуру розділу історії.
    try:
        bot.send_message(
            chat_id,
            "📜 Розділ «Історія» відкрито.",
            reply_markup=auction_history_reply_kb_v1()
        )
    except Exception:
        pass

    # Потім надсилаємо саму історію з inline-фільтрами.
    bot.send_message(chat_id, text, reply_markup=inline_kb)


def _auction_register_history_keyboard_restore_v1(bot):

    @bot.message_handler(func=lambda m: m.text == "🔙 Історія")
    def auction_history_back_restore_keyboard_v1(message):
        user_id = message.from_user.id
        _auction_open_history_screen_v1(
            bot=bot,
            chat_id=message.chat.id,
            user_id=user_id,
            mode="all",
            page=0,
        )


try:
    _auction_base_register_handlers_before_history_keyboard_restore_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_history_keyboard_restore_v1 = None


def register_auction_house_handlers(bot):
    # Має реєструватися раніше старого handler-а "🔙 Історія",
    # який повертав історію без відновлення нижньої клавіатури.
    _auction_register_history_keyboard_restore_v1(bot)

    if _auction_base_register_handlers_before_history_keyboard_restore_v1:
        _auction_base_register_handlers_before_history_keyboard_restore_v1(bot)
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
            "❌ Помилка компіляції після patch_8_0_11a_auction_history_keyboard_restore.\n"
            "Файл handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.11a Auction history keyboard restore застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- після натискання 🔙 Історія з ринкових цін нижня клавіатура знову показує 📈 Ринкові ціни")
    print("- кнопка 🔙 Історія більше не залишається у нижній клавіатурі після повернення в історію")
    print("- inline-фільтри історії залишаються без змін")


if __name__ == "__main__":
    main()
