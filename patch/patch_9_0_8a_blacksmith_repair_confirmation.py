from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_8a_blacksmith_repair_confirmation"
TARGET_RELATIVE = Path("handlers") / "blacksmith.py"
MARKER = "# ✅ ROM 9.0.8a BLACKSMITH REPAIR CONFIRMATION V1"

APPEND_CODE = r'''

# ==============================
# ✅ ROM 9.0.8a BLACKSMITH REPAIR CONFIRMATION V1
# ==============================

# UX fix:
# Раніше натискання на предмет у ремонті одразу ремонтувало його.
# Тепер ремонт одного предмета і ремонт усього спорядження проходять через підтвердження.


def _blacksmith_repair_confirm_kb_v1(confirm_callback, cancel_callback="repair_cancel_v1"):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Підтвердити ремонт", callback_data=confirm_callback))
    kb.add(types.InlineKeyboardButton("❌ Скасувати", callback_data=cancel_callback))
    return kb


def _blacksmith_safe_answer_callback_v1(bot, call, text=None):
    try:
        bot.answer_callback_query(call.id, text or "")
    except Exception:
        pass


def _blacksmith_normalize_text_kb_v1(result, fallback_kb=None):
    if isinstance(result, tuple):
        if len(result) >= 2:
            return result[0], result[1]
        if len(result) == 1:
            return result[0], fallback_kb
    return result, fallback_kb


def _blacksmith_show_repair_menu_v1(bot, chat_id, user_id):
    result = build_blacksmith_repair_text(user_id)
    text, kb = _blacksmith_normalize_text_kb_v1(result, blacksmith_kb())
    bot.send_message(chat_id, text, reply_markup=kb)


def _blacksmith_get_repair_item_name_v1(inventory_id):
    try:
        item = get_item_by_inventory_id_full(inventory_id)
    except Exception:
        item = None

    if not item:
        return f"предмет #{inventory_id}"

    try:
        # Типовий формат у проєкті: (inv_id, item_id, name, ...)
        name = item[2]
    except Exception:
        name = None

    if not name:
        return f"предмет #{inventory_id}"

    try:
        if "get_inventory_refined_display_name" in globals():
            return get_inventory_refined_display_name(inventory_id, name)
    except Exception:
        pass

    return name


def _blacksmith_register_repair_confirmation_handlers_v1(bot):

    @bot.callback_query_handler(func=lambda call: call.data == "repair_all_equipped")
    def blacksmith_repair_all_confirm_prompt_v1(call):
        user_id = call.from_user.id
        _blacksmith_safe_answer_callback_v1(bot, call)

        text = (
            "🛠️ Підтвердження ремонту\n\n"
            "Ви справді хочете відремонтувати все пошкоджене одягнене спорядження?\n\n"
            "Після підтвердження золото буде списано одразу."
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=_blacksmith_repair_confirm_kb_v1("repair_confirm_all_v1")
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("repair_one_"))
    def blacksmith_repair_one_confirm_prompt_v1(call):
        user_id = call.from_user.id
        _blacksmith_safe_answer_callback_v1(bot, call)

        try:
            inventory_id = int(call.data.split("_")[2])
        except Exception:
            bot.send_message(call.message.chat.id, "❌ Не вдалося визначити предмет для ремонту.")
            return

        item_name = _blacksmith_get_repair_item_name_v1(inventory_id)

        text = (
            "🛠️ Підтвердження ремонту\n\n"
            f"Предмет: {item_name}\n\n"
            "Ви справді хочете відремонтувати цей предмет?\n\n"
            "Після підтвердження золото буде списано одразу."
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=_blacksmith_repair_confirm_kb_v1(f"repair_confirm_one_v1_{inventory_id}")
        )

    @bot.callback_query_handler(func=lambda call: call.data == "repair_confirm_all_v1")
    def blacksmith_repair_all_do_v1(call):
        user_id = call.from_user.id
        _blacksmith_safe_answer_callback_v1(bot, call, "Ремонтую...")

        result = repair_all_equipped(user_id)

        bot.send_message(
            call.message.chat.id,
            result.get("message", "✅ Ремонт виконано."),
            reply_markup=blacksmith_kb()
        )

        _blacksmith_show_repair_menu_v1(bot, call.message.chat.id, user_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("repair_confirm_one_v1_"))
    def blacksmith_repair_one_do_v1(call):
        user_id = call.from_user.id
        _blacksmith_safe_answer_callback_v1(bot, call, "Ремонтую...")

        try:
            inventory_id = int(call.data.split("_")[-1])
        except Exception:
            bot.send_message(call.message.chat.id, "❌ Не вдалося визначити предмет для ремонту.")
            return

        result = repair_equipped_item(user_id, inventory_id)

        bot.send_message(
            call.message.chat.id,
            result.get("message", "✅ Ремонт виконано."),
            reply_markup=blacksmith_kb()
        )

        _blacksmith_show_repair_menu_v1(bot, call.message.chat.id, user_id)

    @bot.callback_query_handler(func=lambda call: call.data == "repair_cancel_v1")
    def blacksmith_repair_cancel_v1(call):
        user_id = call.from_user.id
        _blacksmith_safe_answer_callback_v1(bot, call, "Скасовано")

        bot.send_message(
            call.message.chat.id,
            "❌ Ремонт скасовано.",
            reply_markup=blacksmith_kb()
        )

        _blacksmith_show_repair_menu_v1(bot, call.message.chat.id, user_id)


try:
    _blacksmith_base_register_handlers_before_repair_confirmation_v1 = register_blacksmith_handlers
except NameError:
    _blacksmith_base_register_handlers_before_repair_confirmation_v1 = None


def register_blacksmith_handlers(bot):
    # Реєструємо confirmation-handlers перед старими repair handlers,
    # щоб старий repair_one_/repair_all_equipped не виконував ремонт одразу.
    _blacksmith_register_repair_confirmation_handlers_v1(bot)

    if _blacksmith_base_register_handlers_before_repair_confirmation_v1:
        _blacksmith_base_register_handlers_before_repair_confirmation_v1(bot)
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
            "❌ Помилка компіляції після patch_9_0_8a_blacksmith_repair_confirmation.\n"
            "Файл handlers/blacksmith.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.8a Blacksmith repair confirmation застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/blacksmith.py пройшов py_compile.")
    print("")
    print("Що додано:")
    print("- ремонт одного предмета тепер питає підтвердження")
    print("- ремонт всього спорядження тепер питає підтвердження")
    print("- додано кнопки ✅ Підтвердити ремонт / ❌ Скасувати")
    print("- старі repair handlers лишаються, але confirmation handlers реєструються першими")


if __name__ == "__main__":
    main()
