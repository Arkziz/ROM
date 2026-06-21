from telebot import types

from db import (
    get_inventory_detailed,
    get_equipped_inventory_ids,
    equip_inventory_item
)

from keyboards import profile_kb


def register_inventory_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🎒 Інвентар")
    def show_inventory(message):
        user_id = message.from_user.id

        items = get_inventory_detailed(user_id)

        if not items:
            bot.send_message(
                message.chat.id,
                "🎒 Інвентар порожній",
                reply_markup=profile_kb()
            )
            return

        eq_weapon, eq_armor = get_equipped_inventory_ids(user_id)

        kb = types.InlineKeyboardMarkup()

        text = "🎒 Інвентар:\n\n"

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

            equipped = (
                (type_ == "weapon" and inv_id == eq_weapon) or
                (type_ == "armor" and inv_id == eq_armor)
            )

            label = name

            if max_stack > 1:
                label += f" x{quantity}"

            bonuses = []

            if b_str:
                bonuses.append(f"Сила +{b_str}")
            if b_dex:
                bonuses.append(f"Спритність +{b_dex}")
            if b_int:
                bonuses.append(f"Інтелект +{b_int}")
            if b_wis:
                bonuses.append(f"Мудрість +{b_wis}")
            if b_sta:
                bonuses.append(f"Витривалість +{b_sta}")
            if pdef:
                bonuses.append(f"Фіз. захист +{pdef}")
            if mdef:
                bonuses.append(f"Маг. захист +{mdef}")

            if bonuses:
                label += " | " + ", ".join(bonuses)

            if equipped:
                label += " ✅"

            text += f"• {label}\n"

            if category == "equipment":
                kb.add(types.InlineKeyboardButton(
                    text=label,
                    callback_data=f"equip_{inv_id}"
                ))

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb if kb.keyboard else None
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
            reply_markup=profile_kb()
        )