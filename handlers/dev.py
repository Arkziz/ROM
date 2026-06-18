import random

from db import add_item, get_item
from keyboards import main_kb


def register_dev_handlers(bot):

    @bot.message_handler(commands=['give'])
    def give_item(message):
        user_id = message.from_user.id

        # Якщо написати /give 3 — дасть конкретний item_id 3
        parts = message.text.split()

        if len(parts) >= 2:
            try:
                item_id = int(parts[1])
            except:
                bot.send_message(
                    message.chat.id,
                    "❗ Використання: /give або /give ID",
                    reply_markup=main_kb()
                )
                return
        else:
            # Випадковий предмет із тестових 1–7
            item_id = random.randint(1, 7)

        item = get_item(item_id)

        if not item:
            bot.send_message(
                message.chat.id,
                f"❌ Предмет з ID {item_id} не знайдено",
                reply_markup=main_kb()
            )
            return

        add_item(user_id, item_id)

        (
            _,
            name,
            type_,
            rarity,
            b_str,
            b_dex,
            b_int,
            b_wis,
            b_sta,
            pdef,
            mdef
        ) = item

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

        bonus_text = ""
        if bonuses:
            bonus_text = "\n📊 " + ", ".join(bonuses)

        text = (
            f"🎁 Тестовий предмет додано!\n\n"
            f"{name}"
            f"{bonus_text}"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )