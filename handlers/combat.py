from db import (
    get_player_stats,
    get_attack,
    get_physical_defense,
    get_magic_defense,
    get_max_hp,
    get_current_hp,
    set_current_hp
)

from keyboards import main_kb, fight_kb
from utils import hp_bar

from systems.combat_system import (
    generate_mob,
    calculate_player_attack,
    calculate_mob_attack
)


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

        mob = generate_mob()
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
        # 🗡️ УДАР ГРАВЦЯ
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
        player_crit_chance = player_attack_result["crit_chance"]

        mob["hp"] -= dmg

        # ==============================
        # 🎉 ПЕРЕМОГА
        # ==============================

        if mob["hp"] <= 0:
            del bot.user_data[user_id]

            text = "🎉 Перемога!\n\n"

            if is_player_crit:
                text += f"💥 Завершальний критичний удар: {dmg}\n"
            else:
                text += "👹 Ворог переможений\n"

            text += f"\n🎯 Шанс криту: {player_crit_chance}%"

            bot.send_message(
                message.chat.id,
                text,
                reply_markup=main_kb()
            )
            return

        # ==============================
        # 👹 УДАР МОБА
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
        dodge_chance = mob_attack_result["dodge_chance"]
        mob_crit_chance = mob_attack_result["crit_chance"]

        player_hp -= mob_dmg

        # ==============================
        # 💀 СМЕРТЬ
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
        # ✅ ЗБЕРЕГТИ HP
        # ==============================

        set_current_hp(user_id, player_hp)

        # ==============================
        # 📜 ТЕКСТ БОЮ
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
            f"{hp_bar(mob['hp'], mob['max_hp'])}\n\n"
            f"— Шанси —\n"
            f"🎯 Твій крит: {player_crit_chance}%\n"
            f"💨 Твій ухил: {dodge_chance}%\n"
            f"💥 Крит ворога: {mob_crit_chance}%"
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