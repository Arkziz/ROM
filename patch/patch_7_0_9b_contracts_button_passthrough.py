from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "7_0_9b_contracts_button_passthrough"
TARGET_RELATIVE_PATH = Path("handlers") / "guild.py"
MARKER = "# ✅ CONTRACTS BUTTON PASS THROUGH FROM GUILD STATES V1"

APPEND_CODE = r'''

# ==============================
# ✅ CONTRACTS BUTTON PASS THROUGH FROM GUILD STATES V1
# ==============================

# 7.0.9b
# Fix: після меню гільдій могли залишатися активні guild state-handler-и.
# Вони перехоплювали звичайні кнопки міста/найманців, зокрема 📜 Контракти,
# і тому при натисканні нічого не відбувалося без помилки в логах.
#
# Рішення: глобальний guild-pass-through для кнопок:
# - 📜 Контракти
# - 📜 Гільдія Найманців
# - 🔙 Гільдія Найманців
# - 🏙️ Місто / 🔙 Місто
#
# Старі state-handler-и вже викликають _guild_progress_handle_global_guild_buttons_v1(),
# тому перевизначаємо цю функцію з підтримкою контрактів.

try:
    _base_guild_progress_handle_global_buttons_before_contracts_v1 = _guild_progress_handle_global_guild_buttons_v1
except Exception:
    _base_guild_progress_handle_global_buttons_before_contracts_v1 = None


def _guild_contracts_reset_guild_states_v1(user_id):
    for reset_func_name in [
        "reset_guild_browse_state",
        "reset_guild_application_review_state",
        "reset_guild_member_manage_state",
        "reset_guild_logs_state",
    ]:
        try:
            globals()[reset_func_name](user_id)
        except Exception:
            pass


def _guild_open_contracts_board_v1(bot, message):
    user_id = message.from_user.id
    _guild_contracts_reset_guild_states_v1(user_id)

    try:
        from handlers.contracts import build_contracts_text
        from keyboards import contracts_kb

        bot.send_message(
            message.chat.id,
            "📜 Ти підійшов до дошки контрактів.",
            reply_markup=contracts_kb()
        )

        text, kb = build_contracts_text(user_id)
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )
        return True
    except Exception as error:
        bot.send_message(
            message.chat.id,
            f"❌ Не вдалося відкрити контракти. Помилка: {error}",
            reply_markup=guild_hall_kb(user_id)
        )
        return True


def _guild_open_mercenary_hall_v1(bot, message):
    user_id = message.from_user.id
    _guild_contracts_reset_guild_states_v1(user_id)

    # Найкращий варіант: якщо в handlers.city є готовий builder Гільдії Найманців — використати його.
    try:
        from handlers.city import build_mercenary_guild_text
        from keyboards import mercenary_guild_kb

        bot.send_message(
            message.chat.id,
            build_mercenary_guild_text(user_id),
            reply_markup=mercenary_guild_kb()
        )
        return True
    except Exception:
        pass

    # Fallback: одразу відкрити дошку контрактів, бо саме вона потрібна гравцю.
    return _guild_open_contracts_board_v1(bot, message)


def _guild_open_city_from_stale_state_v1(bot, message):
    user_id = message.from_user.id
    _guild_contracts_reset_guild_states_v1(user_id)

    try:
        from handlers.city import build_city_text
        from keyboards import city_kb
        bot.send_message(
            message.chat.id,
            build_city_text(user_id),
            reply_markup=city_kb()
        )
        return True
    except Exception as error:
        bot.send_message(
            message.chat.id,
            f"❌ Не вдалося повернутися в місто. Помилка: {error}",
            reply_markup=guild_hall_kb(user_id)
        )
        return True


def _guild_progress_handle_global_guild_buttons_v1(bot, message):
    text = (message.text or "").strip()

    if text == "📜 Контракти":
        return _guild_open_contracts_board_v1(bot, message)

    if text in ["📜 Гільдія Найманців", "🔙 Гільдія Найманців"]:
        return _guild_open_mercenary_hall_v1(bot, message)

    if text in ["🏙️ Місто", "🔙 Місто"]:
        return _guild_open_city_from_stale_state_v1(bot, message)

    if _base_guild_progress_handle_global_buttons_before_contracts_v1 is not None:
        return _base_guild_progress_handle_global_buttons_before_contracts_v1(bot, message)

    return False
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
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(
            f"❌ Не знайдено файл: {target}\n"
            "Спочатку застосуй guild patches до handlers/guild.py."
        )

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ CONTRACTS BUTTON PASS THROUGH FROM GUILD STATES V1 уже застосований, пропускаю.")
        return

    if "_guild_progress_handle_global_guild_buttons_v1" not in original:
        raise SystemExit(
            "❌ У handlers/guild.py не знайдено _guild_progress_handle_global_guild_buttons_v1.\n"
            "Спочатку застосуй patch_7_0_7a_guild_progress_handler_order_fix.py"
        )

    backup_path = make_backup(root, target)
    updated = original.rstrip() + "\n" + APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_9b_contracts_button_passthrough.\n"
            "handlers/guild.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.9b Contracts Button Passthrough застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ handlers/guild.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- 📜 Контракти більше не мовчить, якщо залишився активний guild state-handler")
    print("- 📜 Гільдія Найманців / 🔙 Гільдія Найманців теж проходять через guild state")
    print("- 🔙 Місто теж проходить через guild state")
    print("- при переході очищаються завислі guild navigation states")
    print("")
    print("Після патча:")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
