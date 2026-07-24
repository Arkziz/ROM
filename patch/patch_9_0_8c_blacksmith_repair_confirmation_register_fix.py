from pathlib import Path
from datetime import datetime
import py_compile


PATCH_NAME = "9_0_8c_blacksmith_repair_confirmation_register_fix"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"

    backup_path.write_text(
        target.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    return backup_path


def find_blacksmith_file(root):
    candidates = [
        root / "handlers" / "blacksmith.py",
        root / "handlers" / "blacksmith_repair_hotfix.py",
        root / "handlers" / "blacksmith_repair.py",
    ]

    for path in candidates:
        if path.exists():
            return path

    found = sorted((root / "handlers").glob("blacksmith*.py"))

    if found:
        return found[0]

    raise SystemExit("❌ Не знайдено blacksmith handler file.")


def write_confirmation_module(root):
    target = root / "handlers" / "blacksmith_repair_confirm.py"

    if target.exists():
        make_backup(root, target)

    content = r'''from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def _safe_answer(bot, call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


def _get_item_name(inventory_id):
    try:
        from db import get_item_by_inventory_id_full
        item = get_item_by_inventory_id_full(inventory_id)

        if isinstance(item, dict):
            return item.get("name") or item.get("item_name") or f"Предмет #{inventory_id}"

        if item:
            return str(item)

    except Exception:
        pass

    try:
        from db import get_item_by_inventory_id
        item = get_item_by_inventory_id(inventory_id)

        if isinstance(item, dict):
            return item.get("name") or item.get("item_name") or f"Предмет #{inventory_id}"

        if item:
            return str(item)

    except Exception:
        pass

    return f"Предмет #{inventory_id}"


def _result_message(result, default_text):
    if isinstance(result, dict):
        if result.get("message"):
            return result["message"]

        if result.get("success"):
            return default_text

        return result.get("error") or result.get("reason") or "❌ Дію не виконано."

    if isinstance(result, str):
        return result

    return default_text


def _confirm_one_kb(inventory_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "✅ Підтвердити ремонт",
            callback_data=f"brc_confirm_one_{inventory_id}"
        )
    )
    kb.add(
        InlineKeyboardButton(
            "❌ Скасувати",
            callback_data="brc_cancel"
        )
    )
    return kb


def _confirm_all_kb():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "✅ Підтвердити ремонт всього",
            callback_data="brc_confirm_all"
        )
    )
    kb.add(
        InlineKeyboardButton(
            "❌ Скасувати",
            callback_data="brc_cancel"
        )
    )
    return kb


def register_blacksmith_repair_confirmation_handlers(bot):
    """
    Register repair confirmation handlers before old instant repair handlers.

    Expected prompt callbacks:
    - repair_prompt_one_v3_<inventory_id>
    - brc_prompt_one_<inventory_id>
    - repair_prompt_all_v3
    - brc_prompt_all
    """

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("repair_prompt_one_v3_")
        or call.data.startswith("brc_prompt_one_")
    )
    def blacksmith_repair_prompt_one(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id
        data = call.data or ""

        try:
            inventory_id = int(data.rsplit("_", 1)[1])
        except Exception:
            bot.send_message(
                call.message.chat.id,
                "❌ Не вдалося визначити предмет для ремонту."
            )
            return

        item_name = _get_item_name(inventory_id)

        text = (
            "🛠️ Підтвердження ремонту\n\n"
            f"📦 {item_name}\n\n"
            "Ви справді хочете відремонтувати цей предмет?\n\n"
            "Після підтвердження буде списано золото за ремонт."
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=_confirm_one_kb(inventory_id)
        )

    @bot.callback_query_handler(
        func=lambda call: call.data in ("repair_prompt_all_v3", "brc_prompt_all")
    )
    def blacksmith_repair_prompt_all(call):
        _safe_answer(bot, call)

        text = (
            "🛠️ Підтвердження ремонту всього спорядження\n\n"
            "Ви справді хочете відремонтувати все одягнене спорядження?\n\n"
            "Після підтвердження буде списано золото за ремонт усіх пошкоджених предметів."
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=_confirm_all_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("brc_confirm_one_"))
    def blacksmith_repair_confirm_one(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id
        data = call.data or ""

        try:
            inventory_id = int(data.rsplit("_", 1)[1])
        except Exception:
            bot.send_message(
                call.message.chat.id,
                "❌ Не вдалося визначити предмет для ремонту."
            )
            return

        try:
            from db import repair_equipped_item
            result = repair_equipped_item(user_id, inventory_id)
        except TypeError:
            try:
                from db import repair_equipped_item
                result = repair_equipped_item(user_id=user_id, inventory_id=inventory_id)
            except Exception as error:
                bot.send_message(
                    call.message.chat.id,
                    f"❌ Помилка ремонту: {error}"
                )
                return
        except Exception as error:
            bot.send_message(
                call.message.chat.id,
                f"❌ Помилка ремонту: {error}"
            )
            return

        bot.send_message(
            call.message.chat.id,
            _result_message(result, "✅ Предмет відремонтовано.")
        )

    @bot.callback_query_handler(func=lambda call: call.data == "brc_confirm_all")
    def blacksmith_repair_confirm_all(call):
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
                bot.send_message(
                    call.message.chat.id,
                    f"❌ Помилка ремонту: {error}"
                )
                return
        except Exception as error:
            bot.send_message(
                call.message.chat.id,
                f"❌ Помилка ремонту: {error}"
            )
            return

        bot.send_message(
            call.message.chat.id,
            _result_message(result, "✅ Одягнене спорядження відремонтовано.")
        )

    @bot.callback_query_handler(func=lambda call: call.data == "brc_cancel")
    def blacksmith_repair_cancel(call):
        _safe_answer(bot, call)

        bot.send_message(
            call.message.chat.id,
            "❌ Ремонт скасовано."
        )
'''

    target.write_text(content, encoding="utf-8")
    py_compile.compile(str(target), doraise=True)

    return target


def patch_blacksmith_callbacks(root, target):
    original = target.read_text(encoding="utf-8")
    text = original

    changed = False

    replacements = [
        ("repair_one_", "repair_prompt_one_v3_"),
        ("repair_all_equipped", "repair_prompt_all_v3"),
    ]

    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            changed = True

    if changed:
        make_backup(root, target)
        target.write_text(text, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)

    return changed


def patch_main(root):
    target = root / "main.py"

    if not target.exists():
        raise SystemExit("❌ main.py не знайдено.")

    original = target.read_text(encoding="utf-8")
    text = original

    import_line = "from handlers.blacksmith_repair_confirm import register_blacksmith_repair_confirmation_handlers\n"
    call_line = "register_blacksmith_repair_confirmation_handlers(bot)\n"

    changed = False

    if import_line not in text:
        # Вставляємо після останнього імпорту handlers.*, якщо можливо.
        lines = text.splitlines(keepends=True)
        insert_index = 0

        for i, line in enumerate(lines):
            if line.startswith("from handlers.") or line.startswith("import handlers."):
                insert_index = i + 1

        lines.insert(insert_index, import_line)
        text = "".join(lines)
        changed = True

    if call_line not in text:
        # Реєстрація має бути до старих blacksmith/city handlers.
        possible_anchors = [
            "register_blacksmith_repair_hotfix(bot)",
            "register_city_handlers(bot)",
            "register_contract_handlers(bot)",
        ]

        inserted = False

        for anchor in possible_anchors:
            if anchor in text:
                text = text.replace(anchor, call_line + anchor, 1)
                inserted = True
                changed = True
                break

        if not inserted:
            # fallback: перед polling
            if "run_bot_polling_resilient(bot)" in text:
                text = text.replace(
                    "run_bot_polling_resilient(bot)",
                    call_line + "run_bot_polling_resilient(bot)",
                    1
                )
                changed = True
            elif "bot.infinity_polling" in text:
                text = text.replace(
                    "bot.infinity_polling",
                    call_line + "bot.infinity_polling",
                    1
                )
                changed = True
            else:
                raise SystemExit("❌ Не вдалося знайти місце для register_blacksmith_repair_confirmation_handlers(bot).")

    if changed:
        make_backup(root, target)
        target.write_text(text, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)

    return changed


def main():
    root = Path(__file__).resolve().parents[1]

    confirmation_module = write_confirmation_module(root)
    blacksmith_file = find_blacksmith_file(root)

    callbacks_changed = patch_blacksmith_callbacks(root, blacksmith_file)
    main_changed = patch_main(root)

    py_compile.compile(str(confirmation_module), doraise=True)
    py_compile.compile(str(blacksmith_file), doraise=True)
    py_compile.compile(str(root / "main.py"), doraise=True)

    print("✅ Патч 9.0.8c Blacksmith repair confirmation register fix застосовано успішно.")
    print(f"✅ Створено/оновлено: {confirmation_module}")
    print(f"✅ Оновлено blacksmith handler: {blacksmith_file}")
    print(f"✅ main.py registration updated: {main_changed}")
    print(f"✅ callback replacement updated: {callbacks_changed}")
    print("")
    print("Після патча запусти:")
    print("python -m py_compile .\\handlers\\blacksmith_repair_confirm.py")
    print("python -m py_compile .\\handlers\\blacksmith_repair_hotfix.py")
    print("python -m py_compile .\\main.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()