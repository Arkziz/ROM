from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_9e_restore_sell_inline_flow"
TARGET_RELATIVE = Path("handlers") / "auction_house.py"
MARKER = "# ✅ AUCTION HOUSE RESTORE SELL INLINE FLOW V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE RESTORE SELL INLINE FLOW V1
# ==============================

# ВАЖЛИВО:
# patch_8_0_9d_auction_sell_category_keyboard_cleanup.py виявився занадто агресивним:
# він відкривав старий sell-list helper, через що предмети для продажу знову стали
# ReplyKeyboard-кнопками, а стекові категорії не знаходили свій helper.
#
# Цей hotfix вимикає проблемний register wrapper 8.0.9d і повертає попередній
# робочий sell-flow з inline-кнопками для предметів.
#
# Після цього точну логіку "прибрати категорії після вибору" краще робити
# вже під фактичну структуру handlers/auction_house.py, щоб не ламати callback-и.


def _auction_register_reply_back_to_house_restore_v1(bot):
    """Залишаємо робочу звичайну кнопку 🔙 Торговий дім."""

    @bot.message_handler(func=lambda m: m.text == "🔙 Торговий дім")
    def auction_reply_back_to_house_restore_v1(message):
        user_id = message.from_user.id

        try:
            if "_auction_clear_runtime_states_v2" in globals():
                _auction_clear_runtime_states_v2(user_id)
            elif "_auction_clear_runtime_states_v1" in globals():
                _auction_clear_runtime_states_v1(user_id)
        except Exception:
            pass

        try:
            text = _auction_main_menu_text_v2(user_id)
        except Exception:
            try:
                text = _auction_main_menu_text_v1(user_id)
            except Exception:
                text = (
                    "🏛️ Торговий дім\n\n"
                    "Тут гравці можуть виставляти товари на продаж, купувати лоти інших гравців "
                    "та забирати золото за завершені продажі."
                )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=auction_house_kb()
        )


try:
    _auction_register_before_broken_sell_cleanup_v1 = _auction_base_register_handlers_before_sell_cat_cleanup_v1
except NameError:
    _auction_register_before_broken_sell_cleanup_v1 = None

try:
    _auction_current_register_before_restore_sell_inline_v1 = register_auction_house_handlers
except NameError:
    _auction_current_register_before_restore_sell_inline_v1 = None


def register_auction_house_handlers(bot):
    """
    Restore handler chain before the broken 8.0.9d sell-category wrapper.

    If _auction_base_register_handlers_before_sell_cat_cleanup_v1 exists, it points to
    the register_auction_house_handlers version that existed before 8.0.9d was applied.
    Calling it restores the previous working inline sell flow while preserving older
    working fixes, including buy category cleanup and reply back to Auction House.
    """

    # Register this first so normal ReplyKeyboard back remains responsive.
    _auction_register_reply_back_to_house_restore_v1(bot)

    if _auction_register_before_broken_sell_cleanup_v1:
        _auction_register_before_broken_sell_cleanup_v1(bot)
    elif _auction_current_register_before_restore_sell_inline_v1:
        _auction_current_register_before_restore_sell_inline_v1(bot)
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
            "❌ Помилка компіляції після patch_8_0_9e_restore_sell_inline_flow.\n"
            "Файл handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.9e Restore sell inline flow застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- вимкнено проблемний wrapper 8.0.9d, який переводив список предметів у ReplyKeyboard")
    print("- повернуто попередній робочий sell-flow з inline-кнопками")
    print("- звичайна кнопка 🔙 Торговий дім лишається робочою")
    print("")
    print("Примітка:")
    print("- точне прибирання категорій при виставленні краще зробити окремим патчем після перегляду актуального handlers/auction_house.py")


if __name__ == "__main__":
    main()
