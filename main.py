import telebot
from config import TOKEN
#from db import init_db, seed_items
from db import get_inventory, get_item
from db import init_db, seed_items, equip_item
from db import equip_item

bot = telebot.TeleBot(TOKEN)

# ініціалізація БД
init_db()
seed_items()

@bot.message_handler(commands=['inv'])
def show_inventory(message):
    user_id = message.from_user.id

    items = get_inventory(user_id)

    if not items:
        bot.send_message(message.chat.id, "🎒 Інвентар порожній")
        return

    text = "🎒 Інвентар:\n\n"

    for row in items:
        item_id = row[0]
        item = get_item(item_id)

        if not item:
            continue

        _, name, type_, rarity, b_str, b_dex, b_int, b_wis = item

        bonus = ""
        if b_str: bonus += f"+STR {b_str} "
        if b_dex: bonus += f"+DEX {b_dex} "
        if b_int: bonus += f"+INT {b_int} "
        if b_wis: bonus += f"+WIS {b_wis} "

        text += f"{name} ({type_}) {bonus}\n"

    bot.send_message(message.chat.id, text)



#temp
from db import add_item
import random

@bot.message_handler(commands=['give'])
def give_item(message):
    user_id = message.from_user.id

    item_id = random.randint(1, 7)
    add_item(user_id, item_id)

    bot.send_message(message.chat.id, f"🎁 отримав item_id {item_id}")


#new
@bot.message_handler(commands=['equip'])
def equip(message):
    user_id = message.from_user.id

    parts = message.text.split()

    if len(parts) < 2:
        bot.send_message(message.chat.id, "❗ /equip ID")
        return

    try:
        item_id = int(parts[1])
    except:
        bot.send_message(message.chat.id, "❗ неправильний ID")
        return

    result = equip_item(user_id, item_id)

    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот працює")


print("✅ BOT STARTED")
bot.infinity_polling()