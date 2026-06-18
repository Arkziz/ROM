from telebot import types

from db import (
    get_inventory_detailed,
    get_equipped_inventory_ids,
    equip_inventory_item
)

from keyboards import main_kb


def register_inventory_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🎒 Інвентар")
    def show_inventory(message):
        user_id = message.from_user.id

        items = get_inventory_detailed(user_id)

        if not items:
            bot.send_message(
                message.chat.id,
                "🎒 Інвентар порожній",
                reply_markup=main_kb()
            )
            return

        eq_weapon, eq_armor = get_equipped_inventory_ids(user_id)

        kb = types.InlineKeyboardMarkup()

        for item in items:
            inv_id, item_id, name, type_, rarity, b_str, b_dex, b_int, b_wis = item

            equipped = (
                (type_ == "weapon" and inv_id == eq_weapon) or
                (type_ == "armor" and inv_id == eq_armor)
            )

            label = name

            bonuses = []

            if b_str:
                bonuses.append(f"STR+{b_str}")
            if b_dex:
                bonuses.append(f"DEX+{b_dex}")
            if b_int:
                bonuses.append(f"INT+{b_int}")
            if b_wis:
                bonuses.append(f"WIS+{b_wis}")

            if bonuses:
                label += " | " + ", ".join(bonuses)

            if equipped:
                label += " ✅"

            kb.add(types.InlineKeyboardButton(
                text=label,
                callback_data=f"equip_{inv_id}"
            ))

        bot.send_message(
            message.chat.id,
            "🎒 Обери предмет:",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
    def handle_equip(call):
        user_id = call.from_user.id
        inventory_id = int(call.data.split("_")[1])

        result = equip_inventory_item(user_id, inventory_id)

        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            result,
            reply_markup=main_kb()
        )