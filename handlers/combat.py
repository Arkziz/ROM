from db import (
    get_player_stats,
    get_attack,
    get_defense,
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
        pdef = get_defense(user_id)

        text = (
            f"🔎 Ти зустрів {mob['name']}\n\n"
            f"======================\n\n"
            f"👤 ТИ\n"
            f"❤️ HP: {current_hp}/{max_hp}\n"
            f"{hp_bar(current_hp, max_hp)}\n"
            f"⚔️ Атака: {atk}\n"
            f"🛡 Захист: {pdef}\n\n"
            f"----------------------\n\n"
            f"👹 ВОРОГ\n"
            f"❤️ HP: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}\n"
            f"⚔️ Атака: {mob['attack']}\n"
            f"🛡 Захист: {mob['def']}\n\n"
            f"⚔️ Бій починається!"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=fight_kb()
        )

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
        player_def = get_defense(user_id)

        player_hp = get_current_hp(user_id)
        player_max_hp = get_max_hp(user_id)

        # ==================
        # PLAYER ATTACK
        # ==================

        dmg, is_player_crit = calculate_player_attack(
            player_atk=player_atk,
            mob_def=mob["def"],
            dex=dex_
        )

        mob["hp"] -= dmg

        # ==================
        # VICTORY
        # ==================

        if mob["hp"] <= 0:
            del bot.user_data[user_id]

            text = "🎉 Перемога!\n\n"

            if is_player_crit:
                text += f"💥 Завершальний критичний удар: {dmg}"
            else:
                text += "👹 Ворог переможений"

            bot.send_message(
                message.chat.id,
                text,
                reply_markup=main_kb()
            )
            return

        # ==================
        # MOB ATTACK
        # ==================

        mob_dmg, is_mob_crit, is_dodge = calculate_mob_attack(
            mob_attack=mob["attack"],
            player_def=player_def,
            dex=dex_,
            sta=sta_
        )

        player_hp -= mob_dmg

        # ==================
        # DEATH
        # ==================

        if player_hp <= 0:
            set_current_hp(user_id, player_max_hp)

            del bot.user_data[user_id]

            bot.send_message(
                message.chat.id,
                "💀 ТИ ЗАГИНУВ\n❤️ HP відновлено",
                reply_markup=main_kb()
            )
            return

        # ==================
        # SAVE HP
        # ==================

        set_current_hp(user_id, player_hp)

        # ==================
        # TEXT
        # ==================

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
            f"❤️ Твоє HP: {player_hp}/{player_max_hp}\n"
            f"{hp_bar(player_hp, player_max_hp)}\n\n"
            f"👹 HP ворога: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=fight_kb()
        )

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