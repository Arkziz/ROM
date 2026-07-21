from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "7_0_7a_guild_progress_handler_order_fix"
TARGET_RELATIVE_PATH = Path("handlers") / "guild.py"
MARKER = "# ✅ GUILD PROGRESS HANDLER ORDER FIX V1"

APPEND_CODE = r'''

# ==============================
# ✅ GUILD PROGRESS HANDLER ORDER FIX V1
# ==============================

# 7.0.7a
# Fix: кнопки 🏛 Прогрес гільдії / 📊 Внесок і команда /guild_add_progress
# могли "мовчати", якщо був активний старий state-handler:
# - GUILD_BROWSE_STATE
# - GUILD_APPLICATION_REVIEW_STATE
# - GUILD_MEMBER_MANAGE_STATE
#
# Старі state-handler-и зареєстровані раніше і перехоплюють повідомлення першими.
# Тому тут перевизначаємо їхні handle_* функції так, щоб вони пропускали
# глобальні кнопки Зали Гільдій і DEV-команду прогресу.


def _guild_progress_reset_navigation_states_v1(user_id):
    for reset_func_name in [
        "reset_guild_browse_state",
        "reset_guild_application_review_state",
        "reset_guild_member_manage_state",
    ]:
        try:
            globals()[reset_func_name](user_id)
        except Exception:
            pass


def _guild_progress_handle_dev_command_v1(bot, message):
    text = (message.text or "").strip()

    if not (text.startswith("/guild_add_progress") or text.startswith("/dev_guild_progress")):
        return False

    parts = text.split()

    if len(parts) < 5:
        bot.send_message(
            message.chat.id,
            "Формат: /guild_add_progress EXP RESOURCE KILLS CONTRACTS\n"
            "Приклад: /guild_add_progress 100 5 1 0",
            reply_markup=guild_hall_kb(message.from_user.id)
        )
        return True

    try:
        exp = int(parts[1])
        resource = int(parts[2])
        kills = int(parts[3])
        contracts = int(parts[4])
    except Exception:
        bot.send_message(
            message.chat.id,
            "❌ Значення мають бути цілими числами.",
            reply_markup=guild_hall_kb(message.from_user.id)
        )
        return True

    try:
        result = add_user_guild_progress(
            user_id=message.from_user.id,
            exp=exp,
            resource=resource,
            kills=kills,
            contracts=contracts,
            reason=f"DEV progress: +{exp} EXP, +{resource} resource, +{kills} kills, +{contracts} contracts"
        )

        bot.send_message(
            message.chat.id,
            result.get("message", "") + "\n\n" + build_guild_progress_text(message.from_user.id),
            reply_markup=guild_hall_kb(message.from_user.id)
        )
    except Exception as error:
        bot.send_message(
            message.chat.id,
            f"❌ Не вдалося додати прогрес гільдії. Помилка: {error}",
            reply_markup=guild_hall_kb(message.from_user.id)
        )

    return True


def _guild_progress_handle_global_guild_buttons_v1(bot, message):
    user_id = message.from_user.id
    text = (message.text or "").strip()

    if _guild_progress_handle_dev_command_v1(bot, message):
        return True

    if text == "🏛 Прогрес гільдії":
        _guild_progress_reset_navigation_states_v1(user_id)
        send_guild_progress(bot, message)
        return True

    if text in ["📊 Внесок", "📊 Внесок за місяць"]:
        _guild_progress_reset_navigation_states_v1(user_id)
        send_guild_contribution(bot, message, "monthly")
        return True

    if text == "📊 Внесок за весь час":
        _guild_progress_reset_navigation_states_v1(user_id)
        send_guild_contribution(bot, message, "total")
        return True

    # Також даємо можливість вийти зі stale-state без мовчання.
    if text == "🏰 Зала Гільдій":
        _guild_progress_reset_navigation_states_v1(user_id)
        open_guild_hall(bot, message.chat.id, user_id)
        return True

    if text == "👥 Учасники":
        try:
            _guild_progress_reset_navigation_states_v1(user_id)
            show_guild_members_manage(bot, message)
            return True
        except Exception:
            pass

    if text == "📨 Заявки":
        try:
            _guild_progress_reset_navigation_states_v1(user_id)
            show_guild_applications(bot, message)
            return True
        except Exception:
            pass

    return False


try:
    _base_handle_guild_list_message_before_progress_order_v1 = handle_guild_list_message
except Exception:
    _base_handle_guild_list_message_before_progress_order_v1 = None


def handle_guild_list_message(bot, message):
    if _guild_progress_handle_global_guild_buttons_v1(bot, message):
        return True

    if _base_handle_guild_list_message_before_progress_order_v1 is not None:
        return _base_handle_guild_list_message_before_progress_order_v1(bot, message)

    return False


try:
    _base_handle_guild_application_review_message_before_progress_order_v1 = handle_guild_application_review_message
except Exception:
    _base_handle_guild_application_review_message_before_progress_order_v1 = None


def handle_guild_application_review_message(bot, message):
    if _guild_progress_handle_global_guild_buttons_v1(bot, message):
        return True

    if _base_handle_guild_application_review_message_before_progress_order_v1 is not None:
        return _base_handle_guild_application_review_message_before_progress_order_v1(bot, message)

    return False


try:
    _base_handle_guild_member_manage_message_before_progress_order_v1 = handle_guild_member_manage_message
except Exception:
    _base_handle_guild_member_manage_message_before_progress_order_v1 = None


def handle_guild_member_manage_message(bot, message):
    if _guild_progress_handle_global_guild_buttons_v1(bot, message):
        return True

    if _base_handle_guild_member_manage_message_before_progress_order_v1 is not None:
        return _base_handle_guild_member_manage_message_before_progress_order_v1(bot, message)

    return False


try:
    _base_handle_guild_creation_message_before_progress_order_v1 = handle_guild_creation_message
except Exception:
    _base_handle_guild_creation_message_before_progress_order_v1 = None


def handle_guild_creation_message(bot, message):
    # Під час створення гільдії не перехоплюємо звичайні кнопки прогресу,
    # але даємо DEV-команді не мовчати, якщо state випадково завис.
    if _guild_progress_handle_dev_command_v1(bot, message):
        return True

    if _base_handle_guild_creation_message_before_progress_order_v1 is not None:
        return _base_handle_guild_creation_message_before_progress_order_v1(bot, message)

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
            "Спочатку застосуй 7.0.7 для handlers/guild.py."
        )

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ GUILD PROGRESS HANDLER ORDER FIX V1 уже застосований, пропускаю.")
        return

    if "def send_guild_progress" not in original or "def send_guild_contribution" not in original:
        raise SystemExit(
            "❌ У handlers/guild.py не знайдено send_guild_progress/send_guild_contribution.\n"
            "Спочатку застосуй patch_7_0_7_guild_progress_contributions.py"
        )

    backup_path = make_backup(root, target)
    updated = original.rstrip() + "\n" + APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_7a_guild_progress_handler_order_fix.\n"
            "handlers/guild.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.7a Guild Progress Handler Order Fix застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ handlers/guild.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- 🏛 Прогрес гільдії більше не мовчить, якщо був активний старий state-handler")
    print("- 📊 Внесок більше не мовчить")
    print("- /guild_add_progress більше не ковтається state-handler-ами")
    print("- при натисканні глобальних кнопок Зали Гільдій очищаються завислі стани навігації")
    print("")
    print("Після патча:")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
