# ROM 17.10.1 ITEM QUANTITY DISPLAY FORMAT
from pathlib import Path
from db import (
    add_item,
    set_player_level_for_test,
    reset_player_level_for_test,
    get_user_progress,
    restore_energy_for_test,
    get_user_energy,
    set_gold_for_test,
    create_generated_equipment_item,
    create_dev_armor_item_for_test,
    create_dev_weapon_item_for_test,
    reset_hero_for_test,
    CLASS_RESET_SPHERE_ITEM_ID,
    seed_class_reset_sphere_item
)

from keyboards import main_kb


# ==============================
# DEV CONFIG
# ==============================

import os
from dotenv import load_dotenv

load_dotenv()

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"


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



# ==============================
# ROM 10.4.0 RUNE DEV HELPERS
# ==============================


def parse_dev_rune_request(parts):
    from data.runes import RUNE_LEVELS, RUNE_STATS, get_rune_item_id

    if len(parts) < 3:
        return {
            "success": False,
            "message": (
                "❌ Формат:\n"
                "/dev_rune STAT LEVEL [quantity]\n\n"
                "Доступні характеристики: STR, STA, DEX, INT, WIS\n"
                "Доступні рівні: 1-5"
            ),
        }
    stat = str(parts[1]).strip().upper()
    try:
        level = int(parts[2])
        quantity = int(parts[3]) if len(parts) >= 4 else 1
    except Exception:
        return {
            "success": False,
            "message": "❌ Рівень і кількість мають бути цілими числами.",
        }
    if stat not in RUNE_STATS:
        return {
            "success": False,
            "message": "❌ Невідома характеристика. Доступні: STR, STA, DEX, INT, WIS.",
        }
    if level not in RUNE_LEVELS:
        return {
            "success": False,
            "message": "❌ Рівень руни має бути від 1 до 5.",
        }
    if quantity < 1 or quantity > 999:
        return {
            "success": False,
            "message": "❌ Кількість має бути від 1 до 999.",
        }
    return {
        "success": True,
        "stat": stat,
        "level": level,
        "quantity": quantity,
        "item_id": get_rune_item_id(stat, level),
    }


def parse_dev_quantity_request(parts, default=1, maximum=999):
    try:
        quantity = int(parts[1]) if len(parts) >= 2 else int(default)
    except Exception:
        return {"success": False, "message": "❌ Кількість має бути цілим числом."}
    if quantity < 1 or quantity > int(maximum):
        return {
            "success": False,
            "message": f"❌ Кількість має бути від 1 до {int(maximum)}.",
        }
    return {"success": True, "quantity": quantity}


# ==============================
# ROM 10.11.0 RUNE DROP DEV SIMULATION
# ==============================
def format_rune_drop_simulation(result):
    if not result.get("success"):
        return result.get("message", "❌ Помилка симуляції.")
    levels = result["levels"]; stats = result["stats"]
    return (
        "🎲 DEV: симуляція дропу рун\n\n"
        f"Тип ворога: {result['enemy_type']}\n"
        f"Симуляцій: {result['trials']}\n"
        f"Рун випало: {result['dropped']}\n"
        f"Фактичний шанс: {result['actual_rate'] * 100:.2f}%\n\n"
        "Рівні:\n"
        f"I: {levels[1]}\nII: {levels[2]}\nIII: {levels[3]}\nIV: {levels[4]}\nV: {levels[5]}\n\n"
        "Характеристики:\n"
        f"STR: {stats['STR']}\nSTA: {stats['STA']}\nDEX: {stats['DEX']}\n"
        f"INT: {stats['INT']}\nWIS: {stats['WIS']}"
    )



# ==============================
# ROM 11.8.0 UNIVERSAL DROP SIMULATOR
# ==============================

def parse_dev_drop_sim_request(text):
    parts=str(text or "").split()
    if len(parts)<2:
        return {"success":False,"message":"❌ Формат:\n/dev_drop_sim normal|elite|boss [trials] [all|equipment|trophy|stone|rune|potion|special]"}
    enemy=parts[1].lower()
    if enemy not in ("normal","elite","boss"):
        return {"success":False,"message":"❌ Тип ворога: normal, elite або boss."}
    try: trials=int(parts[2]) if len(parts)>=3 else 10000
    except Exception: return {"success":False,"message":"❌ Кількість симуляцій має бути цілим числом."}
    if trials<1 or trials>1000000: return {"success":False,"message":"❌ Кількість симуляцій: від 1 до 1000000."}
    group=parts[3].lower() if len(parts)>=4 else "all"
    if group not in ("all","equipment","gear","trophy","loot","stone","material","refine","refine_stone","rune","runes","potion","potions","special"):
        return {"success":False,"message":"❌ Група: all, equipment, trophy, stone, rune, potion або special."}
    return {"success":True,"enemy_type":enemy,"trials":trials,"group":group}


def format_universal_drop_simulation(result):
    trials=result["trials"]; counts=result["counts"]
    labels={"equipment":"Спорядження","trophy":"Трофеї","refine_stone":"Камінь Посилення","rune":"Руни","potion":"Зілля","success_rune":"Руна Успіху","simple_extractor":"Простий Екстрактор","perfect_extractor":"Досконалий Екстрактор"}
    lines=["🎲 DEV: універсальна симуляція дропу","",f"Тип ворога: {result['enemy_type']}",f"Симуляцій: {trials}",f"Група: {result['group']}",""]
    for key in ("equipment","trophy","refine_stone","rune","potion","success_rune","simple_extractor","perfect_extractor"):
        if key in counts or result["group"] in ("all","special",key):
            value=counts.get(key,0); lines.append(f"{labels[key]}: {value} ({value/trials*100:.2f}%)")
    if result["equipment_rarity"]:
        lines.extend(("","Рідкість спорядження:")); lines.extend(f"• {k}: {v}" for k,v in sorted(result["equipment_rarity"].items()))
    if result["rune_levels"]:
        lines.extend(("","Рівні рун:")); lines.extend(f"• {k}: {v}" for k,v in sorted(result["rune_levels"].items()))
    if result["rune_stats"]:
        lines.extend(("","Характеристики рун:")); lines.extend(f"• {k}: {v}" for k,v in sorted(result["rune_stats"].items()))
    if result["potion_items"]:
        names={201:"Мале HP",202:"Мале MP",203:"Середнє HP",204:"Середнє MP"}; lines.extend(("","Зілля:")); lines.extend(f"• {names.get(k,k)}: {v}" for k,v in sorted(result["potion_items"].items()))
    lines.extend(("",f"Усього результатів: {result['total_results']}","DB writes: 0","Generated equipment rows: 0"))
    return "\n".join(lines)


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

        if result.get("success"):
            runtime_user_data = getattr(bot, "user_data", None)
            if isinstance(runtime_user_data, dict):
                runtime_user_data.pop(user_id, None)

            from handlers.start import PENDING_CHARACTER_NAME
            PENDING_CHARACTER_NAME.discard(user_id)
            PENDING_CHARACTER_NAME.add(user_id)

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
            f"😴 Втома: {energy}/{max_energy}\n"
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
    # /dev_armor armor_type [slot] [rarity] [level]
    # ==============================

    @bot.message_handler(commands=["dev_armor"])
    def dev_armor(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        parts = message.text.split()

        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                (
                    "❌ Формат:\n"
                    "/dev_armor armor_type [slot] [rarity] [level]\n\n"
                    "armor_type:\n"
                    "cloth, leather, chain, plate\n\n"
                    "slot:\n"
                    "helmet, shoulders, chest, gloves, legs, boots\n\n"
                    "Приклади:\n"
                    "/dev_armor plate\n"
                    "/dev_armor cloth chest rare 5\n"
                    "/dev_armor leather boots uncommon 3"
                ),
                reply_markup=main_kb()
            )
            return

        armor_type = parts[1]
        slot_key = parts[2] if len(parts) >= 3 else "chest"
        rarity = parts[3] if len(parts) >= 4 else "common"
        item_level = parts[4] if len(parts) >= 5 else None

        result = create_dev_armor_item_for_test(
            user_id=user_id,
            armor_type=armor_type,
            slot_key=slot_key,
            item_level=item_level,
            rarity=rarity
        )

        bot.send_message(
            message.chat.id,
            result.get("message", "❌ Не вдалося створити броню."),
            reply_markup=main_kb()
        )

    # ==============================
    # /dev_weapon item_subtype [rarity] [level]
    # ==============================

    @bot.message_handler(commands=["dev_weapon"])
    def dev_weapon(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        parts = message.text.split()

        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                (
                    "❌ Формат:\n"
                    "/dev_weapon item_subtype [rarity] [level]\n\n"
                    "main_hand:\n"
                    "sword_1h, dagger_1h, wand_1h, sword_2h, staff_2h, bow_2h, crossbow_2h\n\n"
                    "off_hand:\n"
                    "shield, talisman, dagger\n\n"
                    "Приклади:\n"
                    "/dev_weapon sword_1h\n"
                    "/dev_weapon dagger_1h rare 5\n"
                    "/dev_weapon shield common 3\n"
                    "/dev_weapon talisman uncommon 4"
                ),
                reply_markup=main_kb()
            )
            return

        item_profile = parts[1]
        rarity = parts[2] if len(parts) >= 3 else "common"
        item_level = parts[3] if len(parts) >= 4 else None

        result = create_dev_weapon_item_for_test(
            user_id=user_id,
            item_profile=item_profile,
            item_level=item_level,
            rarity=rarity
        )

        bot.send_message(
            message.chat.id,
            result.get("message", "❌ Не вдалося створити зброю."),
            reply_markup=main_kb()
        )


    # ==============================
    # ROM 10.4.0 RUNE DEV COMMANDS
    # ==============================

    @bot.message_handler(commands=["dev_rune"])
    def dev_rune(message):
        if not DEV_MODE:
            return
        request = parse_dev_rune_request(message.text.split())
        if not request.get("success"):
            bot.send_message(message.chat.id, request["message"], reply_markup=main_kb())
            return
        result = add_item(
            message.from_user.id,
            request["item_id"],
            request["quantity"],
        )
        bot.send_message(
            message.chat.id,
            result.get("message") if not result.get("success") else (
                "✅ DEV: руну видано.\n\n"
                f"💠 {result.get('name', 'Руна')} ×{result.get('added', 0)}"
            ),
            reply_markup=main_kb(),
        )

    @bot.message_handler(commands=["dev_firius"])
    def dev_firius(message):
        if not DEV_MODE:
            return
        from data.runes import FIRIUS_TOKEN_ITEM_ID
        request = parse_dev_quantity_request(message.text.split(), default=10)
        if not request.get("success"):
            bot.send_message(message.chat.id, request["message"], reply_markup=main_kb())
            return
        result = add_item(
            message.from_user.id,
            FIRIUS_TOKEN_ITEM_ID,
            request["quantity"],
        )
        bot.send_message(
            message.chat.id,
            result.get("message") if not result.get("success") else (
                "✅ DEV: Жетони Фіріуса видано.\n\n"
                f"🪙 Кількість: {result.get('added', 0)}"
            ),
            reply_markup=main_kb(),
        )

    @bot.message_handler(commands=["dev_extractor"])
    def dev_extractor(message):
        if not DEV_MODE:
            return
        from data.runes import RUNE_EXTRACTOR_ITEM_ID
        request = parse_dev_quantity_request(message.text.split(), default=1)
        if not request.get("success"):
            bot.send_message(message.chat.id, request["message"], reply_markup=main_kb())
            return
        result = add_item(message.from_user.id, RUNE_EXTRACTOR_ITEM_ID, request["quantity"])
        bot.send_message(
            message.chat.id,
            result.get("message") if not result.get("success") else (
                "✅ DEV: Екстрактор рун видано.\n\n"
                f"🧰 Кількість: {result.get('added', 0)}"
            ),
            reply_markup=main_kb(),
        )

    @bot.message_handler(commands=["dev_extractor_perfect"])
    def dev_extractor_perfect(message):
        if not DEV_MODE:
            return
        from data.runes import PERFECT_RUNE_EXTRACTOR_ITEM_ID
        request = parse_dev_quantity_request(message.text.split(), default=1)
        if not request.get("success"):
            bot.send_message(message.chat.id, request["message"], reply_markup=main_kb())
            return
        result = add_item(
            message.from_user.id,
            PERFECT_RUNE_EXTRACTOR_ITEM_ID,
            request["quantity"],
        )
        bot.send_message(
            message.chat.id,
            result.get("message") if not result.get("success") else (
                "✅ DEV: Досконалий Екстрактор рун видано.\n\n"
                f"✨ Кількість: {result.get('added', 0)}"
            ),
            reply_markup=main_kb(),
        )


    # ==============================


    # /dev_drop_sim normal|elite|boss [trials] [group]
    @bot.message_handler(commands=["dev_drop_sim"])
    def dev_drop_sim(message):
        if not DEV_MODE:
            return
        parsed=parse_dev_drop_sim_request(message.text)
        if not parsed["success"]:
            bot.send_message(message.chat.id,parsed["message"],reply_markup=main_kb()); return
        from systems.drop_system import simulate_central_drops
        result=simulate_central_drops(parsed["enemy_type"],parsed["trials"],parsed["group"])
        bot.send_message(message.chat.id,format_universal_drop_simulation(result),reply_markup=main_kb())

    # /dev_rune_drop_sim normal|elite|boss [trials]
    # ==============================
    @bot.message_handler(commands=["dev_rune_drop_sim"])
    def dev_rune_drop_sim(message):
        if not DEV_MODE:
            return
        from systems.rune_system import simulate_rune_drops
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id,
                "❌ Формат:\n/dev_rune_drop_sim normal|elite|boss [trials]",
                reply_markup=main_kb()); return
        trials = parts[2] if len(parts) >= 3 else 10000
        result = simulate_rune_drops(parts[1], trials)
        bot.send_message(message.chat.id, format_rune_drop_simulation(result), reply_markup=main_kb())

    # ==============================
    # /devhelp
    # ==============================

    @bot.message_handler(commands=["dev_pvp"])
    def dev_pvp(message):
        if not DEV_MODE: return
        from systems.pvp_balance_simulator import CLASSES,format_matchup,save_report,simulate_matchup
        parts=message.text.split()
        if len(parts)<3 or parts[1] not in CLASSES or parts[2] not in CLASSES:
            bot.send_message(message.chat.id,"❌ Формат: /dev_pvp warrior knight [trials]\nКласи: warrior, knight, scout, rogue, mage, priest"); return
        try: trials=int(parts[3]) if len(parts)>3 else 100
        except ValueError: trials=100
        result=simulate_matchup(parts[1],parts[2],trials)
        save_report(result,Path(__file__).resolve().parents[1]/"tools/pvp_balance_matchup_report.json")
        bot.send_message(message.chat.id,format_matchup(result))

    @bot.message_handler(commands=["dev_pvp_all"])
    def dev_pvp_all(message):
        if not DEV_MODE: return
        from systems.pvp_balance_simulator import LABELS,save_report,simulate_matrix
        parts=message.text.split()
        try: trials=int(parts[1]) if len(parts)>1 else 100
        except ValueError: trials=100
        result=simulate_matrix(trials)
        path=save_report(result,Path(__file__).resolve().parents[1]/"tools/pvp_balance_class_matrix_report.json")
        lines=["📊 <b>PvP матриця 6 × 6</b>",f"\nСимуляцій на matchup: {trials}"]
        for key,row in sorted(result["class_summary"].items(),key=lambda x:x[1]["win_rate"],reverse=True): lines.append(f"{LABELS[key]}: {row['win_rate']}% ({row['wins']}/{row['games']})")
        lines.append(f"\nJSON: {path.name}")
        bot.send_message(message.chat.id,"\n".join(lines),parse_mode="HTML")

    @bot.message_handler(commands=["dev_pvp_audit"])
    def dev_pvp_audit(message):
        if not DEV_MODE: return
        from pathlib import Path
        from systems.pvp_policy_metrics_audit import audit_all_policies,format_summary,save_report
        parts=message.text.split()
        try: trials=int(parts[1]) if len(parts)>1 else 25
        except ValueError: trials=25
        bot.send_message(message.chat.id,"🔬 Запущено PvP policy audit. Зачекайте на результат.")
        result=audit_all_policies(trials)
        path=save_report(result,Path(__file__).resolve().parents[1]/"tools/pvp_policy_metrics_audit_report.json")
        bot.send_message(message.chat.id,format_summary(result)+f"\n\nJSON: {path.name}",parse_mode="HTML")

    @bot.message_handler(commands=["devhelp"])
    def dev_help(message):
        if not DEV_MODE:
            return

        text = (
            "🛠 DEV-команди\n\n"
            "💠 Руни й жетони:\n"
            "/dev_rune STAT LEVEL [quantity]\n"
            "/dev_firius [quantity]  (типово 10)\n"
            "/dev_extractor [quantity]\n"
            "/dev_extractor_perfect [quantity]\n\n"
            "📦 Предмети:\n"
            "/give item_id [quantity]\n"
            "/drop rarity level\n"
            "/dev_armor armor_type [slot] [rarity] [level]\n"
            "/dev_weapon item_subtype [rarity] [level]\n\n"
            "/sphere [quantity]\n"

            "🏆 Рівень:\n"
            "/setlevel N\n"
            "/lvl N\n"
            "/level N\n"
            "/resetlevel\n"
            "/resethero CONFIRM\n\n"

            "📊 Прогрес:\n"
            "/progress\n\n"

            "😴 Втома:\n"
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
            "/dev_armor plate chest rare 5\n"
            "/dev_weapon dagger_1h rare 5\n"
            "/dev_weapon shield common 3\n"
            "/resethero CONFIRM"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )

# ==============================
    # /sphere [quantity]
    # DEV: give class reset sphere
    # ==============================

    @bot.message_handler(commands=["sphere", "classsphere"])
    def give_class_reset_sphere(message):
        if not DEV_MODE:
            return

        user_id = message.from_user.id
        parts = message.text.split()

        quantity = 1

        if len(parts) >= 2:
            try:
                quantity = int(parts[1])
            except Exception:
                quantity = 1

        if quantity < 1:
            quantity = 1

        if quantity > 10:
            quantity = 10

        seed_class_reset_sphere_item()

        result = add_item(
            user_id=user_id,
            item_id=CLASS_RESET_SPHERE_ITEM_ID,
            quantity=quantity
        )

        if not result.get("success"):
            bot.send_message(
                message.chat.id,
                result.get("message", "❌ Не вдалося видати Сферу нового шляху."),
                reply_markup=main_kb()
            )
            return

        text = (
            f"✅ DEV: видано предмет зміни класу.\n\n"
            f"🔮 Сфера нового шляху ×{result.get('added', quantity)}\n"
            f"🎒 Сумка: {result.get('used_slots', 0)}/{result.get('capacity', 40)}"
        )

        if result.get("lost", 0) > 0:
            text += f"\n⚠️ Не влізло: x{result.get('lost', 0)}"

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )

# ROM 14.6.2 PVP PRODUCTION MATRIX AND CALIBRATION SANDBOX

def _register_pvp_production_calibration_handlers_14_6_2(bot):
    @bot.message_handler(commands=["dev_pvp_prod"])
    def dev_pvp_prod_14_6_2(message):
        from systems.pvp_production_calibration import duel,save_report,LABELS
        from pathlib import Path
        parts=(message.text or "").split();
        if len(parts)<3: return bot.reply_to(message,"Формат: /dev_pvp_prod class_a class_b [trials] [level] [rarity]")
        a,b=parts[1].lower(),parts[2].lower(); trials=int(parts[3]) if len(parts)>3 else 50; level=int(parts[4]) if len(parts)>4 else 10; rarity=parts[5].lower() if len(parts)>5 else "rare"
        r=duel(a,b,trials,level,rarity); save_report(r,Path(__file__).resolve().parents[1]/"tools/pvp_production_matchup_report.json")
        bot.reply_to(message,f"⚔️ Production PvP sandbox\n\n{LABELS[a]} проти {LABELS[b]}\nРівень: {level}\nРідкість: {rarity}\nСимуляцій: {trials}\nПеремоги: {r['wins_a']} / {r['wins_b']}\nНічиї: {r['draws']}\nWin rate: {r['win_rate_a']}% / {r['win_rate_b']}%")
    @bot.message_handler(commands=["dev_pvp_prod_all"])
    def dev_pvp_prod_all_14_6_2(message):
        from systems.pvp_production_calibration import matrix,save_report,LABELS
        from pathlib import Path
        p=(message.text or "").split(); trials=int(p[1]) if len(p)>1 else 20; level=int(p[2]) if len(p)>2 else 10; rarity=p[3].lower() if len(p)>3 else "rare"
        r=matrix(trials,level,rarity); save_report(r,Path(__file__).resolve().parents[1]/"tools/pvp_production_class_matrix_report.json")
        lines=["📊 Production PvP матриця 6 × 6","",f"Рівень: {level}",f"Рідкість: {rarity}",f"Симуляцій на matchup: {trials}",""]
        for c,v in sorted(r["class_summary"].items(),key=lambda x:x[1]["non_mirror_win_rate"],reverse=True): lines.append(f"{LABELS[c]}: {v['non_mirror_win_rate']}% non-mirror")
        bot.reply_to(message,"\n".join(lines)+"\n\nJSON: pvp_production_class_matrix_report.json")
    @bot.message_handler(commands=["dev_pvp_calibrate"])
    def dev_pvp_calibrate_14_6_2(message):
        from systems.pvp_production_calibration import calibrate,save_report
        from pathlib import Path
        p=(message.text or "").split(); trials=int(p[1]) if len(p)>1 else 10; level=int(p[2]) if len(p)>2 else 10; rarity=p[3].lower() if len(p)>3 else "rare"
        r=calibrate(trials,level,rarity); save_report(r,Path(__file__).resolve().parents[1]/"tools/pvp_calibration_sandbox_report.json")
        lines=["🧪 PvP calibration sandbox","",f"Перевірено наборів: {r['candidates_tested']}","Найкращі DEV-only варіанти:"]
        for x in r["best"][:5]: lines.append(f"score {x['score']}: healing {x['healing']}, warrior {x['warrior_damage']}, scout {x['scout_damage']}")
        bot.reply_to(message,"\n".join(lines)+"\n\nLive-баланс не змінено. JSON: pvp_calibration_sandbox_report.json")

try:
    _register_dev_handlers_before_pvp_production_14_6_2 = register_dev_handlers
except NameError:
    _register_dev_handlers_before_pvp_production_14_6_2 = None

def register_dev_handlers(bot):
    if _register_dev_handlers_before_pvp_production_14_6_2:
        _register_dev_handlers_before_pvp_production_14_6_2(bot)
    _register_pvp_production_calibration_handlers_14_6_2(bot)


# ROM 14.6.2a PVP PRODUCTION FIXTURE AUDIT

def _register_pvp_fixture_audit_handlers_14_6_2a(bot):
    @bot.message_handler(commands=["dev_pvp_fixture_audit"])
    def dev_pvp_fixture_audit_14_6_2a(message):
        from pathlib import Path
        from systems.pvp_production_fixture_audit import format_summary, run_audit, save_report
        parts=(message.text or "").split()
        try:
            trials=int(parts[1]) if len(parts)>1 else 10
            level=int(parts[2]) if len(parts)>2 else 10
            rarity=parts[3].lower() if len(parts)>3 else "rare"
            bot.reply_to(message,"🔎 Запущено audit усіх 6 класів, 18 навичок і matrix integrity.")
            result=run_audit(trials,level,rarity)
            path=save_report(result,Path(__file__).resolve().parents[1]/"tools/pvp_production_fixture_audit_report.json")
            bot.reply_to(message,format_summary(result)+f"\nJSON: {path.name}",parse_mode="HTML")
        except Exception as error:
            bot.reply_to(message,f"❌ PvP fixture audit: {error}")

try:
    _register_dev_handlers_before_pvp_fixture_audit_14_6_2a=register_dev_handlers
except NameError:
    _register_dev_handlers_before_pvp_fixture_audit_14_6_2a=None

def register_dev_handlers(bot):
    if _register_dev_handlers_before_pvp_fixture_audit_14_6_2a:
        _register_dev_handlers_before_pvp_fixture_audit_14_6_2a(bot)
    _register_pvp_fixture_audit_handlers_14_6_2a(bot)
