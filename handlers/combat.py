from data.locations import LOCATIONS

from db import (
    get_player_stats,
    get_attack,
    get_physical_defense,
    get_magic_defense,
    get_max_hp,
    get_current_hp,
    set_current_hp,
    get_current_location
)

from keyboards import main_kb, fight_kb
from utils import hp_bar

from systems.combat_system import (
    generate_mob,
    calculate_player_attack,
    calculate_mob_attack
)

from systems.reward_system import process_victory_reward


def register_combat_handlers(bot):

    # ==============================
    # 🔎 ПОЛЮВАННЯ
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

        location_id = get_current_location(user_id)
        location = LOCATIONS.get(location_id, LOCATIONS["start_path"])

        mob = generate_mob(player_level=lvl, location_id=location_id)
        mob["max_hp"] = mob["hp"]

        bot.user_data = getattr(bot, "user_data", {})
        bot.user_data[user_id] = mob

        atk = get_attack(user_id)
        current_hp = get_current_hp(user_id)
        max_hp = get_max_hp(user_id)
        player_pdef = get_physical_defense(user_id)
        player_mdef = get_magic_defense(user_id)

        attack_type_text = "Фізична" if mob["attack_type"] == "physical" else "Магічна"

        text = (
            f"📍 Мапа: {location['name']}\n"
            f"🔎 Ти зустрів {mob['name']}\n\n"

            f"======================\n\n"

            f"👤 ТИ\n"
            f"❤️ Здоров’я: {current_hp}/{max_hp}\n"
            f"{hp_bar(current_hp, max_hp)}\n"
            f"⚔️ Атака: {atk}\n"
            f"🛡 Фіз. захист: {player_pdef}\n"
            f"🔮 Маг. захист: {player_mdef}\n\n"

            f"----------------------\n\n"

            f"👹 ВОРОГ\n"
            f"🏷 Рівень: {mob['level']}\n"
            f"❤️ Здоров’я: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}\n"
            f"⚔️ Атака: {mob['attack']}\n"
            f"🛡 Захист: {mob['def']}\n"
            f"🎯 Тип атаки: {attack_type_text}\n\n"

            f"⚔️ Бій починається!"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=fight_kb()
        )

    # ==============================
    # ⚔️ АТАКА
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

        player_atk = get_attack(user_id)
        player_pdef = get_physical_defense(user_id)
        player_mdef = get_magic_defense(user_id)

        player_hp = get_current_hp(user_id)
        player_max_hp = get_max_hp(user_id)

        if "max_hp" not in mob:
            mob["max_hp"] = mob["hp"]

        # ==============================
        # УДАР ГРАВЦЯ
        # ==============================

        player_attack_result = calculate_player_attack(
            player_atk=player_atk,
            mob_def=mob["def"],
            dex=dex_,
            wis=wis_,
            level=lvl,
            attack_type="physical"
        )

        dmg = player_attack_result["damage"]
        is_player_crit = player_attack_result["is_crit"]

        mob["hp"] -= dmg

        # ==============================
        # ПЕРЕМОГА
        # ==============================

        if mob["hp"] <= 0:
            del bot.user_data[user_id]

            reward = process_victory_reward(
                user_id=user_id,
                player_level=lvl,
                mob=mob
            )

            exp_result = reward["exp_result"]

            text = (
                f"🏆 ВИ ПЕРЕМОГЛИ!\n\n"
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

            text += f"\n🎒 Сумка: {reward['used_slots']}/{reward['capacity']} слотів"

            bot.send_message(
                message.chat.id,
                text,
                reply_markup=main_kb()
            )
            return

        # ==============================
        # УДАР МОБА
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

        # ==============================
        # СМЕРТЬ
        # ==============================

        if player_hp <= 0:
            set_current_hp(user_id, player_max_hp)

            del bot.user_data[user_id]

            bot.send_message(
                message.chat.id,
                "💀 ТИ ЗАГИНУВ\n❤️ Здоров’я відновлено",
                reply_markup=main_kb()
            )
            return

        # ==============================
        # ЗБЕРЕГТИ HP
        # ==============================

        set_current_hp(user_id, player_hp)

        # ==============================
        # ТЕКСТ БОЮ
        # ==============================

        text = "⚔️ БІЙ\n\n"

        if is_player_crit:
            text += f"💥 КРИТ! Ти завдав {dmg} шкоди\n"
        else:
            text += f"🗡️ Ти завдав {dmg} шкоди\n"

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

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=fight_kb()
        )

    # ==============================
    # 🏃 ВТЕЧА
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🏃 Втекти")
    def escape(message):
        user_id = message.from_user.id

        if hasattr(bot, "user_data") and user_id in bot.user_data:
            del bot.user_data[user_id]

        bot.send_message(
            message.chat.id,
            "🏃 Ти втік з бою",
            reply_markup=main_kb()
        )