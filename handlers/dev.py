from db import (
    add_item,
    set_player_level_for_test,
    reset_player_level_for_test,
    get_user_progress,
    restore_energy_for_test,
    get_user_energy,
    set_gold_for_test,
    create_generated_equipment_item,
    reset_hero_for_test
)

from keyboards import main_kb


# ==============================
# DEV CONFIG
# ==============================

DEV_MODE = True


VALID_DROP_RARITIES = {
    "common": "common",
    "white": "common",
    "білий": "common",
    "bilyi": "common",

    "uncommon": "uncommon",
    "green": "uncommon",
    "зелений": "uncommon",
    "zelenyi": "uncommon",

    "rare": "rare",
    "blue": "rare",
    "синій": "rare",
    "synii": "rare",

    "epic": "epic",
    "purple": "epic",
    "фіолетовий": "epic",
    "fioletovyi": "epic"
}


def register_dev_handlers(bot):

    # ==============================
    # /give item_id quantity
    # ==============================

    @bot.message_handler(commands=["give"])
    def give_item(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        parts = message.text.split()

        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                (
                    "❌ Формат:\n"
                    "/give item_id [quantity]\n\n"
                    "Приклад:\n"
                    "/give 201 5"
                ),
                reply_markup=main_kb()
            )
            return

        try:
            item_id = int(parts[1])
            quantity = int(parts[2]) if len(parts) >= 3 else 1
        except Exception:
            bot.send_message(
                message.chat.id,
                "❌ item_id і quantity мають бути числами.",
                reply_markup=main_kb()
            )
            return

        if quantity < 1:
            quantity = 1

        result = add_item(user_id, item_id, quantity)

        if not result.get("success"):
            bot.send_message(
                message.chat.id,
                result.get("message", "❌ Не вдалося видати предмет."),
                reply_markup=main_kb()
            )
            return

        text = (
            f"✅ DEV: предмет видано.\n\n"
            f"📦 {result.get('name', 'Предмет')} x{result.get('added', 0)}\n"
            f"🎒 Сумка: {result.get('used_slots', 0)}/{result.get('capacity', 20)}"
        )

        if result.get("lost", 0) > 0:
            text += f"\n⚠️ Не влізло: x{result.get('lost', 0)}"

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )

    # ==============================
    # /setlevel N
    # /lvl N
    # /level N
    # ==============================

    @bot.message_handler(commands=["setlevel", "lvl", "level"])
    def set_level(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        parts = message.text.split()

        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                (
                    "❌ Формат:\n"
                    "/setlevel 5\n"
                    "/lvl 5\n"
                    "/level 5"
                ),
                reply_markup=main_kb()
            )
            return

        target_level = parts[1]
        result = set_player_level_for_test(user_id, target_level)

        bot.send_message(
            message.chat.id,
            result["message"],
            reply_markup=main_kb()
        )

    # ==============================
    # /resetlevel
    # ==============================

    @bot.message_handler(commands=["resetlevel"])
    def reset_level(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        result = reset_player_level_for_test(user_id)

        bot.send_message(
            message.chat.id,
            result["message"],
            reply_markup=main_kb()
        )

    # ==============================
    # /resethero CONFIRM
    # ==============================

    @bot.message_handler(commands=["resethero"])
    def reset_hero(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        parts = message.text.split()

        if len(parts) < 2 or parts[1] != "CONFIRM":
            bot.send_message(
                message.chat.id,
                (
                    "⚠️ Повне скидання героя\n\n"
                    "Ця команда видалить:\n"
                    "• рівень і EXP\n"
                    "• золото\n"
                    "• інвентар\n"
                    "• екіпірування\n"
                    "• контракти\n"
                    "• щоденні завдання\n\n"
                    "Щоб підтвердити, введи:\n"
                    "/resethero CONFIRM"
                ),
                reply_markup=main_kb()
            )
            return

        result = reset_hero_for_test(user_id)

        bot.send_message(
            message.chat.id,
            result["message"],
            reply_markup=main_kb()
        )

    # ==============================
    # /progress
    # ==============================

    @bot.message_handler(commands=["progress"])
    def progress(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        progress_data = get_user_progress(user_id)

        if not progress_data:
            bot.send_message(
                message.chat.id,
                "❌ Персонажа не знайдено. Натисни /start.",
                reply_markup=main_kb()
            )
            return

        level = progress_data["level"]
        exp = progress_data["exp"]
        exp_to_next = progress_data["exp_to_next"]
        gold = progress_data["gold"]
        kills = progress_data["kills"]

        energy_data = get_user_energy(user_id)
        energy = energy_data["energy"]
        max_energy = energy_data["max_energy"]

        percent = 0

        if exp_to_next > 0:
            percent = (exp / exp_to_next) * 100

        text = (
            f"📊 DEV Progress\n\n"
            f"🏆 Рівень: {level}\n"
            f"✨ EXP: {exp}/{exp_to_next} ({percent:.2f}%)\n"
            f"🔋 Енергія: {energy}/{max_energy}\n"
            f"🪙 Золото: {gold:.2f}\n"
            f"👹 Вбито мобів: {kills}"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )

    # ==============================
    # /energy N
    # /energy
    # ==============================

    @bot.message_handler(commands=["energy"])
    def set_energy(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        parts = message.text.split()

        if len(parts) < 2:
            energy_data = get_user_energy(user_id)

            bot.send_message(
                message.chat.id,
                (
                    f"🔋 Поточна енергія: "
                    f"{energy_data['energy']}/{energy_data['max_energy']}\n\n"
                    f"Формат:\n"
                    f"/energy 40\n"
                    f"/energy 0"
                ),
                reply_markup=main_kb()
            )
            return

        try:
            amount = int(parts[1])
        except Exception:
            bot.send_message(
                message.chat.id,
                "❌ Формат: /energy 40 або /energy 0",
                reply_markup=main_kb()
            )
            return

        result = restore_energy_for_test(user_id, amount)

        bot.send_message(
            message.chat.id,
            result["message"],
            reply_markup=main_kb()
        )

    # ==============================
    # /gold N
    # ==============================

    @bot.message_handler(commands=["gold"])
    def set_gold(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        parts = message.text.split()

        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                (
                    "❌ Формат:\n"
                    "/gold 100\n"
                    "/gold 0\n"
                    "/gold 1000"
                ),
                reply_markup=main_kb()
            )
            return

        result = set_gold_for_test(user_id, parts[1])

        bot.send_message(
            message.chat.id,
            result["message"],
            reply_markup=main_kb()
        )

    # ==============================
    # /drop rarity level
    # ==============================

    @bot.message_handler(commands=["drop"])
    def generate_drop(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        parts = message.text.split()

        if len(parts) < 3:
            bot.send_message(
                message.chat.id,
                (
                    "❌ Формат:\n"
                    "/drop rarity level\n\n"
                    "Приклади:\n"
                    "/drop common 5\n"
                    "/drop uncommon 7\n"
                    "/drop rare 9\n"
                    "/drop epic 10\n\n"
                    "Також можна:\n"
                    "/drop білий 5\n"
                    "/drop зелений 7\n"
                    "/drop синій 9\n"
                    "/drop фіолетовий 10"
                ),
                reply_markup=main_kb()
            )
            return

        rarity_input = parts[1].lower()
        level_input = parts[2]

        rarity = VALID_DROP_RARITIES.get(rarity_input)

        if not rarity:
            bot.send_message(
                message.chat.id,
                (
                    "❌ Невідома рідкість.\n\n"
                    "Доступні:\n"
                    "common / uncommon / rare / epic\n"
                    "білий / зелений / синій / фіолетовий"
                ),
                reply_markup=main_kb()
            )
            return

        try:
            item_level = int(level_input)
        except Exception:
            bot.send_message(
                message.chat.id,
                "❌ Рівень предмета має бути числом.",
                reply_markup=main_kb()
            )
            return

        if item_level < 1:
            item_level = 1

        if item_level > 30:
            item_level = 30

        result = create_generated_equipment_item(
            user_id=user_id,
            item_level=item_level,
            rarity=rarity
        )

        if not result.get("success"):
            bot.send_message(
                message.chat.id,
                result.get("message", "❌ Не вдалося створити предмет."),
                reply_markup=main_kb()
            )
            return

        rarity_icon = {
            "common": "⚪",
            "uncommon": "🟢",
            "rare": "🔵",
            "epic": "🟣"
        }.get(rarity, "⚪")

        text = (
            f"✅ DEV: згенеровано спорядження.\n\n"
            f"{rarity_icon} Рідкість: {rarity}\n"
            f"🏷 Рівень предмета: {item_level}\n"
            f"📦 Предмет: {result['name']}\n"
            f"🎒 Додано в інвентар."
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )

    # ==============================
    # /myid
    # ==============================

    @bot.message_handler(commands=["myid"])
    def my_id(message):
        if not DEV_MODE:
            return

        bot.send_message(
            message.chat.id,
            f"🆔 Твій Telegram user_id:\n{message.from_user.id}",
            reply_markup=main_kb()
        )

    # ==============================
    # /devhelp
    # ==============================

    @bot.message_handler(commands=["devhelp"])
    def dev_help(message):
        if not DEV_MODE:
            return

        text = (
            "🛠 DEV-команди\n\n"
            "📦 Предмети:\n"
            "/give item_id [quantity]\n"
            "/drop rarity level\n\n"

            "🏆 Рівень:\n"
            "/setlevel N\n"
            "/lvl N\n"
            "/level N\n"
            "/resetlevel\n"
            "/resethero CONFIRM\n\n"

            "📊 Прогрес:\n"
            "/progress\n\n"

            "🔋 Енергія:\n"
            "/energy\n"
            "/energy N\n\n"

            "🪙 Золото:\n"
            "/gold N\n\n"

            "🆔 Інше:\n"
            "/myid\n"
            "/devhelp\n\n"

            "Приклади:\n"
            "/lvl 5\n"
            "/energy 40\n"
            "/gold 100\n"
            "/drop uncommon 7\n"
            "/drop rare 10\n"
            "/resethero CONFIRM"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )