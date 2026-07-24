from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_8f_blacksmith_repair_show_menu_after_success"
TARGET_RELATIVE = Path("handlers") / "blacksmith_repair_confirm.py"
MARKER = "# ✅ ROM 9.0.8f BLACKSMITH SHOW REPAIR MENU AFTER SUCCESS V1"

APPEND_CODE = r'''

# ==============================
# ✅ ROM 9.0.8f BLACKSMITH SHOW REPAIR MENU AFTER SUCCESS V1
# ==============================

# UX improvement:
# Після успішного ремонту одразу знову показуємо актуальний список предметів,
# які ще можна відремонтувати — ніби гравець повторно натиснув 🛠️ Ремонт.


def _brc_show_repair_menu_after_action_v1(bot, chat_id, user_id):
    try:
        from handlers.city import build_blacksmith_repair_text
        from keyboards import blacksmith_kb

        result = build_blacksmith_repair_text(user_id)

        if isinstance(result, tuple):
            text = result[0]
            kb = result[1] if len(result) > 1 else blacksmith_kb()
        else:
            text = result
            kb = blacksmith_kb()

        bot.send_message(chat_id, text, reply_markup=kb)
    except Exception as error:
        try:
            bot.send_message(chat_id, f"⚠️ Не вдалося оновити список ремонту: {error}")
        except Exception:
            pass


def register_blacksmith_repair_confirmation_handlers(bot):
    """
    Final repair confirmation handlers.

    Difference from previous version:
    - after successful/cancelled repair, shows fresh repair menu again.
    """

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("repair_prompt_one_v3_")
        or call.data.startswith("brc_prompt_one_")
    )
    def blacksmith_repair_prompt_one_v1(call):
        _safe_answer(bot, call)

        data = call.data or ""
        try:
            inventory_id = int(data.rsplit("_", 1)[1])
        except Exception:
            bot.send_message(call.message.chat.id, "❌ Не вдалося визначити предмет для ремонту.")
            return

        item_name = _get_item_name(inventory_id)

        text = (
            "🛠️ Підтвердження ремонту\n\n"
            f"📦 {item_name}\n\n"
            "Ви справді хочете відремонтувати цей предмет?\n\n"
            "Після підтвердження буде списано золото за ремонт."
        )

        bot.send_message(call.message.chat.id, text, reply_markup=_confirm_one_kb(inventory_id))

    @bot.callback_query_handler(func=lambda call: call.data in ("repair_prompt_all_v3", "brc_prompt_all"))
    def blacksmith_repair_prompt_all_v1(call):
        _safe_answer(bot, call)

        text = (
            "🛠️ Підтвердження ремонту всього спорядження\n\n"
            "Ви справді хочете відремонтувати все одягнене спорядження?\n\n"
            "Після підтвердження буде списано золото за ремонт усіх пошкоджених предметів."
        )

        bot.send_message(call.message.chat.id, text, reply_markup=_confirm_all_kb())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("brc_confirm_one_"))
    def blacksmith_repair_confirm_one_v1(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id
        data = call.data or ""

        try:
            inventory_id = int(data.rsplit("_", 1)[1])
        except Exception:
            bot.send_message(call.message.chat.id, "❌ Не вдалося визначити предмет для ремонту.")
            return

        try:
            from db import repair_equipped_item
            result = repair_equipped_item(user_id, inventory_id)
        except TypeError:
            try:
                from db import repair_equipped_item
                result = repair_equipped_item(user_id=user_id, inventory_id=inventory_id)
            except Exception as error:
                bot.send_message(call.message.chat.id, f"❌ Помилка ремонту: {error}")
                return
        except Exception as error:
            bot.send_message(call.message.chat.id, f"❌ Помилка ремонту: {error}")
            return

        bot.send_message(call.message.chat.id, _result_message(result, "✅ Предмет відремонтовано."))
        _brc_show_repair_menu_after_action_v1(bot, call.message.chat.id, user_id)

    @bot.callback_query_handler(func=lambda call: call.data == "brc_confirm_all")
    def blacksmith_repair_confirm_all_v1(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id

        try:
            from db import repair_all_equipped
            result = repair_all_equipped(user_id)
        except TypeError:
            try:
                from db import repair_all_equipped
                result = repair_all_equipped(user_id=user_id)
            except Exception as error:
                bot.send_message(call.message.chat.id, f"❌ Помилка ремонту: {error}")
                return
        except Exception as error:
            bot.send_message(call.message.chat.id, f"❌ Помилка ремонту: {error}")
            return

        bot.send_message(call.message.chat.id, _result_message(result, "✅ Одягнене спорядження відремонтовано."))
        _brc_show_repair_menu_after_action_v1(bot, call.message.chat.id, user_id)

    @bot.callback_query_handler(func=lambda call: call.data == "brc_cancel")
    def blacksmith_repair_cancel_v1(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id
        bot.send_message(call.message.chat.id, "❌ Ремонт скасовано.")
        _brc_show_repair_menu_after_action_v1(bot, call.message.chat.id, user_id)
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
            "❌ Помилка компіляції після patch_9_0_8f_blacksmith_repair_show_menu_after_success.\n"
            "Файл handlers/blacksmith_repair_confirm.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.8f Blacksmith show repair menu after success застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/blacksmith_repair_confirm.py пройшов py_compile.")
    print("")
    print("Що додано:")
    print("- після ремонту одного предмета знову показується актуальний список ремонту")
    print("- після ремонту всього спорядження знову показується актуальний список ремонту")
    print("- після скасування ремонту також повертається список ремонту")


if __name__ == "__main__":
    main()
