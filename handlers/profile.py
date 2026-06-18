from db import get_player_stats, get_attack, get_defense, get_max_hp, get_current_hp
from keyboards import main_kb
from utils import hp_bar


def register_profile_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "👤 Профіль")
    def profile(message):
        user_id = message.from_user.id

        stats = get_player_stats(user_id)

        if not stats:
            bot.send_message(
                message.chat.id,
                "❗ Немає персонажа. Натисни /start",
                reply_markup=main_kb()
            )
            return

        str_, dex_, int_, wis_, sta_, lvl = stats

        atk = get_attack(user_id)
        current_hp = get_current_hp(user_id)
        max_hp = get_max_hp(user_id)
        pdef = get_defense(user_id)

        text = (
            f"👤 Персонаж\n\n"
            f"🏆 Рівень: {lvl}\n\n"
            f"💪 STR: {str_}\n"
            f"🎯 DEX: {dex_}\n"
            f"🔮 INT: {int_}\n"
            f"🦉 WIS: {wis_}\n"
            f"🛡 STA: {sta_}\n\n"
            f"❤️ HP: {current_hp}/{max_hp}\n"
            f"{hp_bar(current_hp, max_hp)}\n\n"
            f"🛡 DEF: {pdef}\n"
            f"⚔️ Атака: {atk}"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )