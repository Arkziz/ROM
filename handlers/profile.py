from db import (
    get_player_stats,
    get_attack,
    get_physical_defense,
    get_magic_defense,
    get_max_hp,
    get_current_hp,
    get_user_progress
)

from keyboards import profile_kb
from utils import hp_bar


def register_profile_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "👤 Профіль")
    def profile(message):
        user_id = message.from_user.id

        stats = get_player_stats(user_id)
        progress = get_user_progress(user_id)

        if not stats or not progress:
            bot.send_message(
                message.chat.id,
                "❗ Немає персонажа. Натисни /start",
                reply_markup=profile_kb()
            )
            return

        str_, dex_, int_, wis_, sta_, lvl = stats

        atk = get_attack(user_id)
        current_hp = get_current_hp(user_id)
        max_hp = get_max_hp(user_id)

        pdef = get_physical_defense(user_id)
        mdef = get_magic_defense(user_id)

        exp = progress["exp"]
        exp_to_next = progress["exp_to_next"]
        gold = progress["gold"]
        kills = progress["kills"]

        text = (
            f"👤 Персонаж\n\n"
            f"🏆 Рівень: {lvl}\n\n"

            f"❤️ Здоров’я: {current_hp}/{max_hp}\n"
            f"{hp_bar(current_hp, max_hp)}\n\n"

            f"— Характеристики —\n"
            f"💪 Сила: {str_}\n"
            f"🎯 Спритність: {dex_}\n"
            f"🔮 Інтелект: {int_}\n"
            f"🦉 Мудрість: {wis_}\n"
            f"🛡 Витривалість: {sta_}\n\n"

            f"— Бойові параметри —\n"
            f"⚔️ Атака: {atk}\n"
            f"🛡 Фіз. захист: {pdef}\n"
            f"🔮 Маг. захист: {mdef}\n\n"

            f"— Прогрес —\n"
            f"✨ Досвід: {exp}/{exp_to_next}\n"
            f"👹 Вбито мобів: {kills}\n\n"

            f"— Гаманець —\n"
            f"🪙 Золото: {gold:.2f}\n\n"

            f"Доступні дії персонажа:\n"
            f"🎒 Інвентар"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=profile_kb()
        )