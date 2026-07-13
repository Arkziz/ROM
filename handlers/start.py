from telebot import types

from db import (
    create_user,
    init_character_class_system,

    needs_character_name,
    needs_character_class,

    set_character_name,
    set_character_class,

    get_character_name,
    get_character_class_display,

    CLASS_CONFIGS,

    has_class_change_available,
    consume_class_change_available,

    process_passive_regeneration,

    unequip_incompatible_items_after_class_change
)

from keyboards import main_kb

from handlers.city import build_main_menu_text


# ==============================
# TEMP STATE
# ==============================

PENDING_CHARACTER_NAME = set()


# ==============================
# KEYBOARDS
# ==============================

def build_class_selection_kb(mode="register"):
    kb = types.InlineKeyboardMarkup(row_width=1)

    for class_key, config in CLASS_CONFIGS.items():
        if mode == "change":
            callback_data = f"change_class:{class_key}"
        else:
            callback_data = f"select_class:{class_key}"

        kb.add(types.InlineKeyboardButton(
            text=config["name"],
            callback_data=callback_data
        ))

    return kb


# ==============================
# TEXT BUILDERS
# ==============================

def build_name_request_text():
    return (
        "👤 Створення персонажа\n\n"
        "Введи ім’я свого героя.\n\n"
        "Правила:\n"
        "• від 2 до 24 символів\n"
        "• без службових символів\n"
    )


def build_class_selection_text(user_id, mode="register"):
    character_name = get_character_name(user_id)
    current_class = get_character_class_display(user_id)

    if mode == "change":
        text = (
            f"🔮 Сфера нового шляху\n\n"
            f"Герой: {character_name}\n"
            f"Поточний клас: {current_class}\n\n"
            f"Оберіть новий клас персонажа.\n"
            f"Після вибору клас буде змінено.\n\n"
        )
    else:
        text = (
            f"🧭 Вибір класу\n\n"
            f"Герой: {character_name}\n\n"
            f"Оберіть шлях персонажа.\n"
            f"Клас визначить майбутні бойові навички та ресурс у бою.\n\n"
        )

    for class_key, config in CLASS_CONFIGS.items():
        text += (
            f"{config['name']}\n"
            f"{config['description']}\n\n"
        )

    return text


def build_class_change_unequip_text_local(unequip_result):
    """
    Локальна версія повідомлення після зміни класу.
    Не залежить від build_class_change_unequip_text з db.py.

    Формат:
    ⚠️ Несумісне спорядження знято:
    • Обладунок [Шкіра] 3 рівня — броня не підходить класу
    • Кинджал 3 рівня — зброя не підходить класу
    """

    def add_armor_type_to_name(name, inventory_id):
        if not inventory_id:
            return name

        try:
            from db import (
                get_item_classification_by_inventory_id,
                is_armor_slot,
                get_armor_type_label
            )

            classification = get_item_classification_by_inventory_id(inventory_id)

            if not classification:
                return name

            slot_key = classification.get("slot_key", "")
            armor_type = classification.get("armor_type", "")

            if not is_armor_slot(slot_key):
                return name

            if not armor_type:
                return name

            armor_label = get_armor_type_label(armor_type)

            if not armor_label:
                return name

            if f"[{armor_label}]" in name:
                return name

            marker = " рівня"

            if marker in name:
                index = name.rfind(marker)
                before_level = name[:index]
                after_level = name[index:]

                parts = before_level.rsplit(" ", 1)

                if len(parts) == 2 and parts[1].isdigit():
                    return f"{parts[0]} [{armor_label}] {parts[1]}{after_level}"

            return f"{name} [{armor_label}]"

        except Exception:
            return name

    def infer_reason(item):
        reason = item.get("reason", "") or ""
        reason_lower = reason.lower()

        if "тип броні" in reason_lower or "брон" in reason_lower:
            return "броня не підходить класу"

        if "збро" in reason_lower or "main_hand" in reason_lower:
            return "зброя не підходить класу"

        if "другої руки" in reason_lower or "другу руку" in reason_lower:
            return "предмет для другої руки не підходить класу"

        slot_key = item.get("slot_key", "")

        if slot_key in [
            "helmet",
            "shoulders",
            "chest",
            "gloves",
            "legs",
            "boots"
        ]:
            return "броня не підходить класу"

        if slot_key == "main_hand":
            return "зброя не підходить класу"

        if slot_key == "off_hand":
            return "предмет для другої руки не підходить класу"

        inventory_id = item.get("inventory_id")

        if inventory_id:
            try:
                from db import (
                    get_item_classification_by_inventory_id,
                    is_armor_slot
                )

                classification = get_item_classification_by_inventory_id(inventory_id)

                if classification:
                    real_slot_key = classification.get("slot_key", "")

                    if is_armor_slot(real_slot_key):
                        return "броня не підходить класу"

                    if real_slot_key == "main_hand":
                        return "зброя не підходить класу"

                    if real_slot_key == "off_hand":
                        return "предмет для другої руки не підходить класу"

            except Exception:
                pass

        return "не підходить новому класу"

    if not unequip_result:
        return ""

    removed_items = unequip_result.get("removed_items", [])

    if not removed_items:
        return "\n\n✅ Усе спорядження сумісне з новим класом."

    text = "\n\n⚠️ Несумісне спорядження знято:\n"

    for item in removed_items:
        name = item.get("name", "Невідомий предмет")
        inventory_id = item.get("inventory_id")

        display_name = add_armor_type_to_name(
            name=name,
            inventory_id=inventory_id
        )

        reason = infer_reason(item)

        text += f"• {display_name} — {reason}\n"

    text += "\nПредмети повернуто в інвентар."

    return text


# ==============================
# FLOW HELPERS
# ==============================

def continue_registration_or_main(bot, chat_id, user_id):
    init_character_class_system()
    create_user(user_id)
    process_passive_regeneration(user_id)

    if needs_character_name(user_id):
        PENDING_CHARACTER_NAME.add(user_id)

        bot.send_message(
            chat_id,
            build_name_request_text()
        )
        return

    if needs_character_class(user_id):
        bot.send_message(
            chat_id,
            build_class_selection_text(user_id, mode="register"),
            reply_markup=build_class_selection_kb(mode="register")
        )
        return

    bot.send_message(
        chat_id,
        build_main_menu_text(user_id),
        reply_markup=main_kb()
    )


def start_class_change_flow(bot, chat_id, user_id):
    init_character_class_system()

    if not has_class_change_available(user_id):
        bot.send_message(
            chat_id,
            "❌ Зміна класу зараз недоступна."
        )
        return

    bot.send_message(
        chat_id,
        build_class_selection_text(user_id, mode="change"),
        reply_markup=build_class_selection_kb(mode="change")
    )


# ==============================
# HANDLERS
# ==============================

def register_start_handlers(bot):

    # ==============================
    # /start
    # ==============================

    @bot.message_handler(commands=["start"])
    def start(message):
        user_id = message.from_user.id

        continue_registration_or_main(
            bot=bot,
            chat_id=message.chat.id,
            user_id=user_id
        )

    # ==============================
    # CHARACTER NAME INPUT
    # ==============================

    @bot.message_handler(func=lambda m: m.from_user.id in PENDING_CHARACTER_NAME)
    def receive_character_name(message):
        user_id = message.from_user.id

        if message.text and message.text.startswith("/"):
            bot.send_message(
                message.chat.id,
                "ℹ️ Спочатку введи ім’я персонажа."
            )
            return

        result = set_character_name(user_id, message.text)

        if not result["success"]:
            bot.send_message(
                message.chat.id,
                result["message"]
            )
            return

        PENDING_CHARACTER_NAME.discard(user_id)

        bot.send_message(
            message.chat.id,
            result["message"]
        )

        if needs_character_class(user_id):
            bot.send_message(
                message.chat.id,
                build_class_selection_text(user_id, mode="register"),
                reply_markup=build_class_selection_kb(mode="register")
            )
            return

        bot.send_message(
            message.chat.id,
            build_main_menu_text(user_id),
            reply_markup=main_kb()
        )

    # ==============================
    # INITIAL CLASS SELECTION
    # ==============================

    @bot.callback_query_handler(func=lambda call: call.data.startswith("select_class:"))
    def select_class(call):
        user_id = call.from_user.id
        class_key = call.data.split(":")[1]

        result = set_character_class(user_id, class_key)

        bot.answer_callback_query(call.id)

        if not result["success"]:
            bot.send_message(
                call.message.chat.id,
                result["message"]
            )
            return

        bot.send_message(
            call.message.chat.id,
            (
                f"{result['message']}\n\n"
                f"Твій шлях починається."
            )
        )

        bot.send_message(
            call.message.chat.id,
            build_main_menu_text(user_id),
            reply_markup=main_kb()
        )

    # ==============================
    # CLASS CHANGE BY SPHERE
    # ==============================

    @bot.callback_query_handler(func=lambda call: call.data.startswith("change_class:"))
    def change_class(call):
        user_id = call.from_user.id
        class_key = call.data.split(":")[1]

        if not has_class_change_available(user_id):
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "❌ Зміна класу недоступна."
            )
            return

        old_class = get_character_class_display(user_id)

        result = set_character_class(user_id, class_key)

        if not result["success"]:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                result["message"]
            )
            return

        consume_result = consume_class_change_available(user_id)

        bot.answer_callback_query(call.id)

        if not consume_result["success"]:
            bot.send_message(
                call.message.chat.id,
                consume_result["message"]
            )
            return

        unequip_result = unequip_incompatible_items_after_class_change(user_id)
        unequip_text = build_class_change_unequip_text_local(unequip_result)

        bot.send_message(
            call.message.chat.id,
            (
                f"🔮 Клас змінено.\n\n"
                f"Було: {old_class}\n"
                f"Стало: {result['class_name']}"
                f"{unequip_text}"
            )
        )

        bot.send_message(
            call.message.chat.id,
            build_main_menu_text(user_id),
            reply_markup=main_kb()
        )