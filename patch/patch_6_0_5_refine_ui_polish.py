from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "6_0_5_refine_ui_polish"
TARGET_RELATIVE_PATH = Path("handlers") / "refine.py"

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


# ==============================
# TEXT HELPERS
# ==============================

def format_percent(value):
    try:
        value = float(value)
    except Exception:
        value = 0.0

    if value.is_integer():
        return str(int(value))

    return f"{value:.2f}".rstrip("0").rstrip(".")


def build_refine_rules_text():
    return (
        "ℹ️ Правила заточки:\n"
        "• ⚔️ Зброя: збільшує тільки шкоду.\n"
        "• 🛡️ Броня: збільшує тільки максимальне HP.\n"
        "• Захист і характеристики від заточки не змінюються.\n"
        "• 🪨 Камінь Посилення витрачається при кожній спробі.\n"
        "• 💎 Руна Успіху робить шанс успіху 100%."
    )


def build_refine_main_text(user_id):
    resources = get_refine_resource_counts(user_id)

    return (
        "✨ Заточка спорядження\n\n"
        "Коваль може посилити твою екіпіровку за допомогою спеціальних матеріалів.\n\n"
        f"Твої матеріали:\n"
        f"• 🪨 Камінь Посилення: {resources.get('stone', 0)}\n"
        f"• 💎 Руна Успіху: {resources.get('success_rune', 0)}\n\n"
        f"{build_refine_rules_text()}\n\n"
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


# ==============================
# KEYBOARDS
# ==============================

def build_refine_items_kb(user_id, page=0):
    items = get_refinable_inventory_items(user_id)
    kb = types.InlineKeyboardMarkup(row_width=1)

    if not items:
        kb.add(types.InlineKeyboardButton(
            text="🔙 Закрити",
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
        text="❌ Закрити",
        callback_data="refine_close"
    ))

    return kb


def build_refine_effect_text(info, check):
    refine_kind = check.get("refine_kind", "")
    current_level = int(info.get("refine_level", 0) or 0)
    max_level = int(check.get("max_level", 0) or 0)

    if refine_kind == "weapon":
        current_effect = get_weapon_refine_damage_multiplier(current_level)
        next_effect = get_weapon_refine_damage_multiplier(min(current_level + 1, max_level))

        text = (
            "⚔️ Ефект заточки зброї:\n"
            f"• Поточний множник шкоди: ×{current_effect:.2f}\n"
        )

        if current_level < max_level:
            text += f"• Після успіху: ×{next_effect:.2f}\n"

        return text

    if refine_kind == "armor":
        rarity = info.get("rarity", "common")
        current_effect = get_armor_refine_hp_bonus_percent(current_level, rarity)
        next_effect = get_armor_refine_hp_bonus_percent(min(current_level + 1, max_level), rarity)

        text = (
            "🛡️ Ефект заточки броні:\n"
            f"• Поточний бонус HP: +{format_percent(current_effect)}%\n"
        )

        if current_level < max_level:
            text += f"• Після успіху: +{format_percent(next_effect)}% HP\n"

        return text

    return ""


def build_refine_risk_text(info, check):
    refine_kind = check.get("refine_kind", "")
    current_level = int(info.get("refine_level", 0) or 0)
    max_level = int(check.get("max_level", 0) or 0)

    if current_level >= max_level:
        return "✅ Предмет уже має максимальний рівень заточки.\n"

    chance = get_refine_success_chance(refine_kind, current_level)
    failure_level = get_refine_failure_level(refine_kind, current_level)

    text = f"🎲 Шанс успіху: {chance}%\n"

    if failure_level < current_level:
        text += f"❌ При невдачі: +{current_level} → +{failure_level}\n"
    else:
        text += f"❌ При невдачі: +{current_level} без змін\n"

    return text


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
    elif refine_kind == "armor":
        kind_text = "🛡️ Броня"
    else:
        kind_text = "❓ Невідомий тип"

    text = (
        f"✨ Заточка предмета\n\n"
        f"📦 {name}\n"
        f"Тип: {kind_text}\n"
        f"Поточна заточка: +{current_level}/{max_level}\n\n"
        f"{build_refine_effect_text(info, check)}\n"
        f"{build_refine_risk_text(info, check)}\n"
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


# ==============================
# RESULT TEXT
# ==============================

def build_refine_attempt_result_text(user_id, inventory_id, before_info, after_info, result, use_success_rune):
    before_level = int((before_info or {}).get("refine_level", 0) or 0)
    after_level = int((after_info or {}).get("refine_level", 0) or 0)

    before_name = get_inventory_refined_display_name(
        inventory_id,
        (before_info or {}).get("name", "Предмет")
    )

    after_name = get_inventory_refined_display_name(
        inventory_id,
        (after_info or before_info or {}).get("name", "Предмет")
    )

    if not result.get("success"):
        return (
            f"❌ Заточка не виконана.\n\n"
            f"📦 {before_name}\n"
            f"ℹ️ {result.get('message', 'Спроба неможлива.')}"
        )

    lines = []

    if use_success_rune:
        lines.append("💎 Руна Успіху використана.")
        lines.append("🎯 Шанс успіху був 100%.")

    if after_level > before_level:
        lines.append("✅ Заточка успішна!")
        lines.append("")
        lines.append(f"📦 {after_name}")
        lines.append(f"✨ Було: +{before_level}")
        lines.append(f"✨ Стало: +{after_level}")

        refine_kind = result.get("refine_kind") or can_refine_item(after_info).get("refine_kind", "")

        if refine_kind == "weapon":
            lines.append("⚔️ Шкода збільшена.")
        elif refine_kind == "armor":
            lines.append("🛡️ Бонус до максимального HP збільшено.")

        lines.append("🪨 Камінь Посилення витрачено.")

    elif after_level < before_level:
        lines.append("❌ Заточка не вдалася.")
        lines.append("")
        lines.append(f"📦 {after_name}")
        lines.append(f"📉 Заточка знижена: +{before_level} → +{after_level}")
        lines.append("🪨 Камінь Посилення витрачено.")

    else:
        lines.append("❌ Заточка не вдалася.")
        lines.append("")
        lines.append(f"📦 {after_name}")
        lines.append("✨ Рівень заточки не змінився.")
        lines.append("🪨 Камінь Посилення витрачено.")

    return "\n".join(lines)


# ==============================
# SEND / OPEN
# ==============================

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


# ==============================
# HANDLERS
# ==============================

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

        before_info = get_inventory_item_refine_info(inventory_id)

        result = perform_refine_attempt(
            user_id=call.from_user.id,
            inventory_id=inventory_id,
            use_success_rune=use_success_rune
        )

        after_info = get_inventory_item_refine_info(inventory_id)

        bot.answer_callback_query(call.id)

        result_text = build_refine_attempt_result_text(
            user_id=call.from_user.id,
            inventory_id=inventory_id,
            before_info=before_info,
            after_info=after_info,
            result=result,
            use_success_rune=use_success_rune
        )

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


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / "handlers" / "refine.py"

    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/refine.py. Спочатку застосуй 6.0.4 UI patch.")

    original = target.read_text(encoding="utf-8")
    backup_path = make_backup(root, target)

    target.write_text(REFINE_HANDLER_CODE.strip() + "\n", encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_6_0_5_refine_ui_polish.\n"
            "handlers/refine.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 6.0.5 Refine UI Polish застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ handlers/refine.py пройшов py_compile.")
    print("")
    print("Що покращено:")
    print("- головне меню заточки має пояснення правил")
    print("- preview предмета показує ефект, шанс і ризик")
    print("- повідомлення успіху/невдачі стали зрозумілішими")
    print("- руна успіху явно показує 100% шанс")


if __name__ == "__main__":
    main()
