from telebot import types

from data.locations import LOCATIONS

from db import (
    get_player_stats,
    get_player_attack_profile,
    get_physical_defense,
    get_magic_defense,
    get_max_hp,
    get_current_hp,
    set_current_hp,
    get_current_location,
    get_inventory_detailed,
    get_item_by_inventory_id_full,
    damage_equipped_items_on_death,
    apply_random_durability_wear_on_victory,
    process_contract_progress_on_kill,
    process_daily_quest_progress_on_kill,
    consume_energy_for_hunt
)

from keyboards import main_kb, fight_kb
from utils import hp_bar

from systems.combat_system import (
    generate_mob,
    calculate_player_attack,
    calculate_mob_attack
)

from systems.reward_system import process_victory_reward
from systems.potion_system import use_potion_from_inventory


# ==============================
# 🧪 POTION COOLDOWN
# ==============================

def get_potion_cooldown_turns_by_inventory_id(inventory_id):
    item = get_item_by_inventory_id_full(inventory_id)

    if not item:
        return 3

    (
        inv_id,
        item_id,
        name,
        type_,
        rarity,
        category,
        slot_key,
        weapon_hands,
        quantity,
        max_stack,
        durability,
        b_str,
        b_dex,
        b_int,
        b_wis,
        b_sta,
        pdef,
        mdef,
        sell_price
    ) = item

    if type_ == "potion_hp_medium":
        return 5

    if type_ == "potion_hp":
        return 3

    return 3


# ==============================
# 🧪 POTION SELECT IN COMBAT
# ==============================

def build_combat_potion_kb(user_id):
    items = get_inventory_detailed(user_id)

    kb = types.InlineKeyboardMarkup()
    found = False

    for item in items:
        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            quantity,
            max_stack,
            durability,
            b_str,
            b_dex,
            b_int,
            b_wis,
            b_sta,
            pdef,
            mdef,
            sell_price
        ) = item

        if category == "potion" and type_ in ["potion_hp", "potion_hp_medium"]:
            found = True

            cooldown = 3

            if type_ == "potion_hp_medium":
                cooldown = 5

            kb.add(types.InlineKeyboardButton(
                text=f"{name} x{quantity} — cooldown {cooldown} ход.",
                callback_data=f"combat_potion_{inv_id}"
            ))

    if not found:
        return None

    kb.add(types.InlineKeyboardButton(
        text="⬅️ Назад до бою",
        callback_data="combat_back"
    ))

    return kb


def build_death_text(durability_damage):
    text = (
        "💀 ТИ ЗАГИНУВ\n"
        "❤️ Здоров’я відновлено\n"
        "🧱 Одягнене спорядження втратило 5 міцності\n"
    )

    if durability_damage:
        text += "\n📉 Стан спорядження:\n"

        for item in durability_damage:
            broken_text = " ⚠️ ЗЛАМАНО" if item["broken"] else ""
            text += f"• {item['name']}: {item['old']} → {item['new']}/100{broken_text}\n"

    return text


def register_combat_handlers(bot):

    # ==============================
    # 🔎 HUNT
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🔎 Полювання")
    def hunt(message):
        user_id = message.from_user.id

        stats = get_player_stats(user_id)

        if not stats:
            bot.send_message(
                message.chat.id,
                "❗ Спочатку натисни /start",
                reply_markup=main_kb()
            )
            return

        str_, dex_, int_, wis_, sta_, lvl = stats

        current_hp = get_current_hp(user_id)
        max_hp = get_max_hp(user_id)

        hp_percent = 0

        if max_hp > 0:
            hp_percent = (current_hp / max_hp) * 100

        if hp_percent <= 25:
            bot.send_message(
                message.chat.id,
                (
                    "😴 Ви занадто слабкі для полювання.\n\n"
                    f"❤️ Здоров’я: {current_hp}/{max_hp} ({hp_percent:.1f}%)\n"
                    "Ваше здоров’я нижче або дорівнює 25%.\n\n"
                    "Відпочиньте або використайте зілля!"
                ),
                reply_markup=main_kb()
            )
            return

        energy_result = consume_energy_for_hunt(user_id)

        if not energy_result["success"]:
            bot.send_message(
                message.chat.id,
                energy_result["message"],
                reply_markup=main_kb()
            )
            return

        location_id = get_current_location(user_id)
        location = LOCATIONS.get(location_id, LOCATIONS["start_path"])

        mob = generate_mob(player_level=lvl, location_id=location_id)
        mob["max_hp"] = mob["hp"]
        mob["potion_cooldown"] = 0

        bot.user_data = getattr(bot, "user_data", {})
        bot.user_data[user_id] = mob

        attack_profile = get_player_attack_profile(user_id)

        player_pdef = get_physical_defense(user_id)
        player_mdef = get_magic_defense(user_id)

        attack_type_text = "Фізична" if mob["attack_type"] == "physical" else "Магічна"
        player_attack_type_text = "Фізична" if attack_profile["attack_type"] == "physical" else "Магічна"

        elite_text = ""

        if mob.get("is_elite"):
            elite_text = (
                "⭐ ЕЛІТНИЙ ВОРОГ!\n"
                "Ця істота значно сильніша за звичайну.\n\n"
            )

        weapon_text = attack_profile.get("weapon_text") or "Без зброї"

        text = (
            f"📍 Мапа: {location['name']}\n"
            f"🔎 Ти зустрів {mob['name']}\n\n"
            f"{elite_text}"
            f"🔋 Енергія: {energy_result['energy']}/{energy_result['max_energy']}\n\n"

            f"======================\n\n"

            f"👤 ТИ\n"
            f"❤️ Здоров’я: {current_hp}/{max_hp}\n"
            f"{hp_bar(current_hp, max_hp)}\n"
            f"⚔️ Тип атаки: {player_attack_type_text}\n"
            f"🗡️ Зброя: {weapon_text}\n"
            f"💥 Атака: {attack_profile['display_attack']}\n"
            f"🛡 Фіз. захист: {player_pdef}\n"
            f"🔮 Маг. захист: {player_mdef}\n\n"

            f"----------------------\n\n"

            f"👹 ВОРОГ\n"
            f"🏷 Рівень: {mob['level']}\n"
            f"❤️ Здоров’я: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}\n"
            f"⚔️ Атака: {mob['attack']}\n"
            f"🛡 Фіз. захист: {mob.get('pdef', mob.get('def', 0))}\n"
            f"🔮 Маг. захист: {mob.get('mdef', mob.get('def', 0))}\n"
            f"🎯 Тип атаки: {attack_type_text}\n\n"

            f"⚔️ Бій починається!"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=fight_kb()
        )

    # ==============================
    # ⚔️ ATTACK
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "⚔️ Атакувати")
    def attack(message):
        user_id = message.from_user.id

        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.send_message(
                message.chat.id,
                "❗ Спочатку почни полювання",
                reply_markup=main_kb()
            )
            return

        mob = bot.user_data[user_id]

        stats = get_player_stats(user_id)

        if not stats:
            bot.send_message(
                message.chat.id,
                "❗ Персонажа не знайдено",
                reply_markup=main_kb()
            )
            return

        str_, dex_, int_, wis_, sta_, lvl = stats

        attack_profile = get_player_attack_profile(user_id)

        player_pdef = get_physical_defense(user_id)
        player_mdef = get_magic_defense(user_id)

        player_hp = get_current_hp(user_id)
        player_max_hp = get_max_hp(user_id)

        if "max_hp" not in mob:
            mob["max_hp"] = mob["hp"]

        player_attack_result = calculate_player_attack(
            player_stat_attack=attack_profile["stat_attack"],
            mob_def=(
                mob.get("mdef", mob.get("def", 0))
                if attack_profile["attack_type"] == "magical"
                else mob.get("pdef", mob.get("def", 0))
            ),
            dex=dex_,
            wis=wis_,
            level=lvl,
            attack_type=attack_profile["attack_type"],
            weapon_min_damage=attack_profile["weapon_min_damage"],
            weapon_max_damage=attack_profile["weapon_max_damage"]
        )

        dmg = player_attack_result["damage"]
        is_player_crit = player_attack_result["is_crit"]
        weapon_damage = player_attack_result.get("weapon_damage", 0)

        mob["hp"] -= dmg

        # ==============================
        # VICTORY
        # ==============================

        if mob["hp"] <= 0:
            del bot.user_data[user_id]

            reward = process_victory_reward(
                user_id=user_id,
                player_level=lvl,
                mob=mob
            )

            wear_result = apply_random_durability_wear_on_victory(
                user_id=user_id,
                chance_percent=25
            )

            contract_result = process_contract_progress_on_kill(
                user_id=user_id,
                mob=mob
            )

            daily_result = process_daily_quest_progress_on_kill(
                user_id=user_id,
                mob=mob
            )

            exp_result = reward["exp_result"]

            victory_title = "🏆 ВИ ПЕРЕМОГЛИ!"

            if mob.get("is_elite"):
                victory_title = "🏆 ВИ ПЕРЕМОГЛИ ЕЛІТНОГО ВОРОГА!"

            text = (
                f"{victory_title}\n\n"
                f"{mob['name']} повалений на землю.\n\n"
                f"📈 Нагорода:\n"
                f"✨ Досвід: +{reward['exp']} EXP"
            )

            if exp_result:
                text += f" ({exp_result['exp']}/{exp_result['exp_to_next']})"

                if exp_result["level_ups"] > 0:
                    text += f"\n🏆 Новий рівень: {exp_result['level']}!"

            text += f"\n🪙 Чисте золото: +{reward['gold']}\n"

            if reward["loot_messages"]:
                text += "\n🎒 Знайдений лут:\n"

                for loot in reward["loot_messages"]:
                    text += f"• {loot}\n"
            else:
                text += "\n🎒 Лут не знайдено.\n"

            if wear_result and wear_result.get("triggered"):
                text += f"\n{wear_result['message']}\n"

            if contract_result and contract_result.get("message"):
                text += f"\n{contract_result['message']}\n"

            if daily_result and daily_result.get("message"):
                text += f"\n{daily_result['message']}\n"

            text += f"\n🎒 Сумка: {reward['used_slots']}/{reward['capacity']} слотів"

            bot.send_message(
                message.chat.id,
                text,
                reply_markup=main_kb()
            )
            return

        # ==============================
        # MOB ATTACK
        # ==============================

        mob_attack_result = calculate_mob_attack(
            mob_attack=mob["attack"],
            player_pdef=player_pdef,
            player_mdef=player_mdef,
            player_dex=dex_,
            mob_dex=mob["dex"],
            sta=sta_,
            level=lvl,
            attack_type=mob["attack_type"]
        )

        mob_dmg = mob_attack_result["damage"]
        is_mob_crit = mob_attack_result["is_crit"]
        is_dodge = mob_attack_result["is_dodge"]

        player_hp -= mob_dmg

        if player_hp <= 0:
            durability_damage = damage_equipped_items_on_death(
                user_id=user_id,
                amount=5
            )

            set_current_hp(user_id, player_max_hp)

            if user_id in bot.user_data:
                del bot.user_data[user_id]

            text = build_death_text(durability_damage)

            bot.send_message(
                message.chat.id,
                text,
                reply_markup=main_kb()
            )
            return

        set_current_hp(user_id, player_hp)

        # cooldown зілля зменшується тільки після реального бойового ходу
        if mob.get("potion_cooldown", 0) > 0:
            mob["potion_cooldown"] -= 1

        text = "⚔️ БІЙ\n\n"

        if is_player_crit:
            text += f"💥 КРИТ! Ти завдав {dmg} шкоди"
        else:
            text += f"🗡️ Ти завдав {dmg} шкоди"

        if weapon_damage > 0:
            text += f" (зброя: {weapon_damage})"

        text += "\n"

        if is_dodge:
            text += "💨 УХИЛ! Ти уникнув атаки ворога\n\n"
        elif is_mob_crit:
            text += f"💥 КРИТ ВОРОГА! Ти отримав {mob_dmg} шкоди\n\n"
        else:
            text += f"👹 Ворог завдав {mob_dmg} шкоди\n\n"

        text += (
            f"❤️ Твоє здоров’я: {player_hp}/{player_max_hp}\n"
            f"{hp_bar(player_hp, player_max_hp)}\n\n"
            f"👹 Здоров’я ворога: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )

        if mob.get("potion_cooldown", 0) > 0:
            text += f"\n\n🔴 Повний шлунок: {mob['potion_cooldown']} ход."

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=fight_kb()
        )

    # ==============================
    # 🧪 POTION BUTTON
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🧪 Зілля")
    def choose_potion_in_combat(message):
        user_id = message.from_user.id

        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.send_message(
                message.chat.id,
                "❗ Ти не в бою",
                reply_markup=main_kb()
            )
            return

        mob = bot.user_data[user_id]

        cooldown = mob.get("potion_cooldown", 0)

        if cooldown > 0:
            bot.send_message(
                message.chat.id,
                f"🔴 Повний шлунок: зілля можна буде випити через {cooldown} ход.",
                reply_markup=fight_kb()
            )
            return

        kb = build_combat_potion_kb(user_id)

        if not kb:
            bot.send_message(
                message.chat.id,
                "❌ У тебе немає зілля здоров’я",
                reply_markup=fight_kb()
            )
            return

        bot.send_message(
            message.chat.id,
            "🧪 Обери зілля, яке хочеш випити:",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "combat_back")
    def combat_back(call):
        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "⚔️ Повернення до бою",
            reply_markup=fight_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("combat_potion_"))
    def use_selected_potion_in_combat(call):
        user_id = call.from_user.id

        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "❗ Бій уже завершено",
                reply_markup=main_kb()
            )
            return

        mob = bot.user_data[user_id]

        cooldown = mob.get("potion_cooldown", 0)

        if cooldown > 0:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                f"🔴 Повний шлунок: зілля можна буде випити через {cooldown} ход.",
                reply_markup=fight_kb()
            )
            return

        inventory_id = int(call.data.split("_")[2])
        cooldown_turns = get_potion_cooldown_turns_by_inventory_id(inventory_id)

        potion_result = use_potion_from_inventory(user_id, inventory_id)

        if not potion_result["success"]:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                potion_result["message"],
                reply_markup=fight_kb()
            )
            return

        bot.answer_callback_query(call.id)

        # ВАЖЛИВО:
        # Зілля більше НЕ витрачає хід.
        # Ворог НЕ атакує після використання зілля.
        mob["potion_cooldown"] = cooldown_turns

        player_hp = potion_result["new_hp"]
        player_max_hp = potion_result["max_hp"]

        text = (
            f"🧪 ЗІЛЛЯ\n\n"
            f"{potion_result['message']}\n\n"
            f"✅ Хід не витрачено — ворог не атакує після використання зілля.\n"
            f"🔴 Повний шлунок: {cooldown_turns} ход.\n\n"
            f"❤️ Твоє здоров’я: {player_hp}/{player_max_hp}\n"
            f"{hp_bar(player_hp, player_max_hp)}\n\n"
            f"👹 Здоров’я ворога: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=fight_kb()
        )

    # ==============================
    # 🏃 ESCAPE CONFIRM
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🏃 Втекти")
    def escape(message):
        user_id = message.from_user.id

        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.send_message(
                message.chat.id,
                "❗ Ти не в бою",
                reply_markup=main_kb()
            )
            return

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton(
                text="✅ Так, втекти",
                callback_data="escape_yes"
            ),
            types.InlineKeyboardButton(
                text="❌ Ні, залишитись",
                callback_data="escape_no"
            )
        )

        bot.send_message(
            message.chat.id,
            "🏃 Ти точно хочеш втекти з бою?",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "escape_yes")
    def escape_yes(call):
        user_id = call.from_user.id

        if hasattr(bot, "user_data") and user_id in bot.user_data:
            del bot.user_data[user_id]

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "🏃 Ти втік з бою",
            reply_markup=main_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "escape_no")
    def escape_no(call):
        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "⚔️ Ти залишився в бою",
            reply_markup=fight_kb()
        )