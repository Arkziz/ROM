from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "6_0_4_refine_ui_blacksmith"

REFINE_HANDLER_CODE = r'''
from telebot import types

from db import (
    get_inventory_detailed,
    get_inventory_item_refine_info,
    get_refine_resource_counts,
    get_inventory_refined_display_name,
)

from systems.refine_system import (
    can_refine_item,
    perform_refine_attempt,
    get_refine_success_chance,
    get_refine_failure_level,
    get_weapon_refine_damage_multiplier,
    get_armor_refine_hp_bonus_percent,
)


REFINE_ITEMS_PER_PAGE = 8


def build_refine_main_text(user_id):
    resources = get_refine_resource_counts(user_id)

    return (
        "✨ Заточка спорядження\n\n"
        "Коваль може посилити твою екіпіровку за допомогою матеріалів.\n\n"
        "🪨 Камінь Посилення — потрібен для кожної спроби.\n"
        "💎 Руна Успіху — гарантує успішну заточку.\n\n"
        f"Твої матеріали:\n"
        f"• 🪨 Камінь Посилення: {resources.get('stone', 0)}\n"
        f"• 💎 Руна Успіху: {resources.get('success_rune', 0)}\n\n"
        "Обери предмет для заточки."
    )


def get_refinable_inventory_items(user_id):
    result = []
    items = get_inventory_detailed(user_id)

    for item in items:
        try:
            inventory_id = item[0]
        except Exception:
            continue

        info = get_inventory_item_refine_info(inventory_id)
        check = can_refine_item(info)

        if not check.get("refine_kind"):
            continue

        current_level = int(info.get("refine_level", 0) or 0)
        max_level = int(check.get("max_level", 0) or 0)

        if max_level <= 0:
            continue

        name = get_inventory_refined_display_name(
            inventory_id,
            info.get("name", "Предмет")
        )

        result.append({
            "inventory_id": inventory_id,
            "name": name,
            "refine_kind": check.get("refine_kind", ""),
            "current_level": current_level,
            "max_level": max_level,
            "can_refine": bool(check.get("success")),
        })

    return result


def build_refine_items_kb(user_id, page=0):
    items = get_refinable_inventory_items(user_id)
    kb = types.InlineKeyboardMarkup(row_width=1)

    if not items:
        kb.add(types.InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="refine_close"
        ))
        return kb

    total_pages = max(1, (len(items) + REFINE_ITEMS_PER_PAGE - 1) // REFINE_ITEMS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start = page * REFINE_ITEMS_PER_PAGE
    end = start + REFINE_ITEMS_PER_PAGE

    for item in items[start:end]:
        prefix = "⚔️" if item["refine_kind"] == "weapon" else "🛡️"
        status = f"+{item['current_level']}/{item['max_level']}"

        kb.add(types.InlineKeyboardButton(
            text=f"{prefix} {item['name']} ({status})",
            callback_data=f"refine_item:{item['inventory_id']}:{page}"
        ))

    nav_buttons = []

    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"refine_page:{page - 1}"
        ))

    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton(
            text="➡️ Далі",
            callback_data=f"refine_page:{page + 1}"
        ))

    if nav_buttons:
        kb.row(*nav_buttons)

    kb.add(types.InlineKeyboardButton(
        text="🔙 Закрити",
        callback_data="refine_close"
    ))

    return kb


def build_refine_item_text(user_id, inventory_id):
    info = get_inventory_item_refine_info(inventory_id)

    if not info:
        return "❌ Предмет не знайдено."

    check = can_refine_item(info)
    resources = get_refine_resource_counts(user_id)

    name = get_inventory_refined_display_name(
        inventory_id,
        info.get("name", "Предмет")
    )

    refine_kind = check.get("refine_kind", "")
    current_level = int(info.get("refine_level", 0) or 0)
    max_level = int(check.get("max_level", 0) or 0)

    if refine_kind == "weapon":
        kind_text = "⚔️ Зброя"
        current_effect = get_weapon_refine_damage_multiplier(current_level)
        next_effect = get_weapon_refine_damage_multiplier(min(current_level + 1, max_level))

        effect_text = (
            "Ефект заточки:\n"
            f"• Поточний множник шкоди: ×{current_effect:.2f}\n"
        )

        if current_level < max_level:
            effect_text += f"• Після успіху: ×{next_effect:.2f}\n"

    elif refine_kind == "armor":
        kind_text = "🛡️ Броня"
        rarity = info.get("rarity", "common")
        current_effect = get_armor_refine_hp_bonus_percent(current_level, rarity)
        next_effect = get_armor_refine_hp_bonus_percent(min(current_level + 1, max_level), rarity)

        effect_text = (
            "Ефект заточки:\n"
            f"• Поточний бонус HP: +{current_effect:.2f}%\n"
        )

        if current_level < max_level:
            effect_text += f"• Після успіху: +{next_effect:.2f}% HP\n"

    else:
        kind_text = "❓ Невідомий тип"
        effect_text = ""

    if current_level >= max_level:
        chance_text = "✅ Предмет уже має максимальну заточку.\n"
        fail_text = ""
    else:
        chance = get_refine_success_chance(refine_kind, current_level)
        failure_level = get_refine_failure_level(refine_kind, current_level)

        chance_text = f"🎲 Шанс успіху: {chance}%\n"

        if failure_level < current_level:
            fail_text = f"❌ При невдачі: +{current_level} → +{failure_level}\n"
        else:
            fail_text = f"❌ При невдачі: +{current_level} без змін\n"

    text = (
        f"✨ Заточка предмета\n\n"
        f"📦 {name}\n"
        f"Тип: {kind_text}\n"
        f"Поточна заточка: +{current_level}/{max_level}\n\n"
        f"{effect_text}\n"
        f"{chance_text}"
        f"{fail_text}\n"
        f"Матеріали:\n"
        f"• 🪨 Камінь Посилення: {resources.get('stone', 0)}\n"
        f"• 💎 Руна Успіху: {resources.get('success_rune', 0)}"
    )

    return text


def build_refine_item_kb(user_id, inventory_id, page=0):
    info = get_inventory_item_refine_info(inventory_id)
    check = can_refine_item(info)
    resources = get_refine_resource_counts(user_id)

    kb = types.InlineKeyboardMarkup(row_width=1)

    if check.get("success"):
        if resources.get("stone", 0) > 0:
            kb.add(types.InlineKeyboardButton(
                text="✨ Заточити за 🪨 Камінь",
                callback_data=f"refine_do:{inventory_id}:0:{page}"
            ))
        else:
            kb.add(types.InlineKeyboardButton(
                text="❌ Немає 🪨 Каменя Посилення",
                callback_data="refine_noop"
            ))

        if resources.get("stone", 0) > 0 and resources.get("success_rune", 0) > 0:
            kb.add(types.InlineKeyboardButton(
                text="💎 Заточити з Руною Успіху",
                callback_data=f"refine_do:{inventory_id}:1:{page}"
            ))

    kb.add(types.InlineKeyboardButton(
        text="🔙 До списку",
        callback_data=f"refine_page:{page}"
    ))

    kb.add(types.InlineKeyboardButton(
        text="❌ Закрити",
        callback_data="refine_close"
    ))

    return kb


def _send_or_edit(bot, chat_id, text, reply_markup=None, message_id=None):
    if message_id:
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup
            )
            return
        except Exception:
            pass

    bot.send_message(
        chat_id,
        text,
        reply_markup=reply_markup
    )


def open_refine_menu(bot, chat_id, user_id, message_id=None, page=0):
    _send_or_edit(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        text=build_refine_main_text(user_id),
        reply_markup=build_refine_items_kb(user_id, page)
    )


def register_refine_handlers(bot):

    @bot.message_handler(commands=["refine", "zatocka", "refine_test"])
    def refine_command(message):
        open_refine_menu(
            bot=bot,
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )

    @bot.message_handler(func=lambda message: message.text == "✨ Заточка")
    def refine_text_button(message):
        open_refine_menu(
            bot=bot,
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )

    @bot.callback_query_handler(func=lambda call: call.data == "refine_menu")
    def refine_menu_callback(call):
        bot.answer_callback_query(call.id)
        open_refine_menu(
            bot=bot,
            chat_id=call.message.chat.id,
            user_id=call.from_user.id,
            message_id=call.message.message_id
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("refine_page:"))
    def refine_page_callback(call):
        page = int(call.data.split(":")[1])
        bot.answer_callback_query(call.id)
        open_refine_menu(
            bot=bot,
            chat_id=call.message.chat.id,
            user_id=call.from_user.id,
            message_id=call.message.message_id,
            page=page
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("refine_item:"))
    def refine_item_callback(call):
        parts = call.data.split(":")
        inventory_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        bot.answer_callback_query(call.id)
        _send_or_edit(
            bot=bot,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=build_refine_item_text(call.from_user.id, inventory_id),
            reply_markup=build_refine_item_kb(call.from_user.id, inventory_id, page)
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("refine_do:"))
    def refine_do_callback(call):
        parts = call.data.split(":")
        inventory_id = int(parts[1])
        use_success_rune = parts[2] == "1"
        page = int(parts[3]) if len(parts) > 3 else 0

        result = perform_refine_attempt(
            user_id=call.from_user.id,
            inventory_id=inventory_id,
            use_success_rune=use_success_rune
        )

        bot.answer_callback_query(call.id)

        result_text = result.get("message", "")
        item_text = build_refine_item_text(call.from_user.id, inventory_id)

        _send_or_edit(
            bot=bot,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"{result_text}\n\n{item_text}",
            reply_markup=build_refine_item_kb(call.from_user.id, inventory_id, page)
        )

    @bot.callback_query_handler(func=lambda call: call.data == "refine_noop")
    def refine_noop_callback(call):
        bot.answer_callback_query(call.id, "Недостатньо матеріалів.")

    @bot.callback_query_handler(func=lambda call: call.data == "refine_close")
    def refine_close_callback(call):
        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            bot.send_message(call.message.chat.id, "✅ Меню заточки закрито.")
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def write_refine_handler(root):
    target = root / "handlers" / "refine.py"
    target.parent.mkdir(exist_ok=True)

    backup_path = make_backup(root, target) if target.exists() else None
    target.write_text(REFINE_HANDLER_CODE.strip() + "\n", encoding="utf-8")

    return target, backup_path


def patch_main(root):
    target = root / "main.py"

    if not target.exists():
        raise SystemExit("❌ Не знайдено main.py")

    original = target.read_text(encoding="utf-8")
    text = original
    changed = False

    if "register_refine_handlers" not in text:
        import_line = "from handlers.refine import register_refine_handlers\n"

        # Вставляємо після останнього import з handlers, якщо можливо.
        matches = list(re.finditer(r"^from handlers\.[^\n]+\n", text, flags=re.M))

        if matches:
            last = matches[-1]
            text = text[:last.end()] + import_line + text[last.end():]
        else:
            text = import_line + text

        changed = True

    if "register_refine_handlers(bot)" not in text:
        matches = list(re.finditer(r"^(\s*)register_[A-Za-z0-9_]+_handlers\(bot\)\s*$", text, flags=re.M))

        if matches:
            last = matches[-1]
            indent = last.group(1)
            insert_at = last.end()
            text = text[:insert_at] + f"\n{indent}register_refine_handlers(bot)" + text[insert_at:]
            changed = True
        else:
            raise SystemExit(
                "❌ Не знайшов місце в main.py для register_refine_handlers(bot).\n"
                "Надішли main.py або додай вручну:\n"
                "from handlers.refine import register_refine_handlers\n"
                "register_refine_handlers(bot)"
            )

    if not changed:
        return target, None, original

    backup_path = make_backup(root, target)
    target.write_text(text, encoding="utf-8")

    return target, backup_path, original


def patch_city_optional(root):
    """
    Необов'язкова інтеграція кнопки в текстові меню.
    Якщо не знайдемо надійний патерн — не падаємо.
    Handler все одно працює через /refine або текст ✨ Заточка.
    """

    target = root / "handlers" / "city.py"

    if not target.exists():
        print("ℹ️ handlers/city.py не знайдено, пропускаю кнопку Коваля.")
        return None, None, None

    original = target.read_text(encoding="utf-8")

    if "✨ Заточка" in original:
        print("ℹ️ city.py: кнопка/текст ✨ Заточка вже є.")
        return target, None, original

    text = original
    changed = False

    # Найбезпечніший варіант: додати Inline-кнопку після кнопки ремонту, якщо є callback repair.
    patterns = [
        (
            "types.InlineKeyboardButton(\n                text=\"🛠️ Ремонт\"",
            "types.InlineKeyboardButton(\n                text=\"🛠️ Ремонт\""
        ),
        (
            "types.InlineKeyboardButton(\n                text=\"🔧 Ремонт\"",
            "types.InlineKeyboardButton(\n                text=\"🔧 Ремонт\""
        ),
    ]

    # Через різні варіанти city.py не робимо агресивну заміну.
    # Просто додаємо коментар-нагадування в кінець файлу, якщо автокнопку не знайшли.
    if not changed:
        text = text.rstrip() + "\n\n# 6.0.4 note: refine UI registered globally. Use /refine or text '✨ Заточка'.\n"
        changed = True

    backup_path = make_backup(root, target)
    target.write_text(text, encoding="utf-8")

    return target, backup_path, original


def main():
    root = Path(__file__).resolve().parents[1]

    changed_files = []
    backups = []
    originals = []

    try:
        refine_file, refine_backup = write_refine_handler(root)
        changed_files.append(refine_file)
        if refine_backup:
            backups.append(refine_backup)

        main_file, main_backup, main_original = patch_main(root)
        changed_files.append(main_file)
        originals.append((main_file, main_original))
        if main_backup:
            backups.append(main_backup)

        city_file, city_backup, city_original = patch_city_optional(root)
        if city_file:
            changed_files.append(city_file)
            originals.append((city_file, city_original))
        if city_backup:
            backups.append(city_backup)

        for file_path in changed_files:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            if original is not None:
                file_path.write_text(original, encoding="utf-8")

        raise SystemExit(
            "❌ Помилка під час patch_6_0_4_refine_ui_blacksmith.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 6.0.4 Refine UI застосовано успішно.")
    print("")
    print("Створено / оновлено:")
    for file_path in changed_files:
        print(f"- {file_path}")

    if backups:
        print("")
        print("Backup:")
        for backup in backups:
            print(f"- {backup}")

    print("")
    print("Як відкрити UI заточки:")
    print("- командою /refine")
    print("- або текстом: ✨ Заточка")
    print("- або callback refine_menu, якщо додаси кнопку в Коваля")
    print("")
    print("Важливо:")
    print("Якщо кнопка не зʼявилась у меню Коваля автоматично, UI все одно працює через /refine.")
    print("Для точного додавання кнопки в Коваля можна буде окремо пропатчити city.py по його актуальному коду.")


if __name__ == "__main__":
    main()
