import telebot
from config import TOKEN
#from db import init_db, seed_items
from db import get_inventory, get_item
from db import init_db, seed_items, equip_item
from db import equip_item
from telebot import types
from db import get_player_stats, get_attack
from db import create_user

bot = telebot.TeleBot(TOKEN)

# ініціалізація БД
init_db()
seed_items()

from db import get_inventory, get_item

@bot.message_handler(commands=['inv'])
def show_inventory(message):
    user_id = message.from_user.id

    items = get_inventory(user_id)

    if not items:
        bot.send_message(message.chat.id, "🎒 Інвентар порожній")
        return

    kb = types.InlineKeyboardMarkup()

    text = "🎒 Обери предмет:\n\n"

    for row in items:
        item_id = row[0]
        item = get_item(item_id)

        if not item:
            continue

        _, name, type_, rarity, *_ = item

        kb.add(types.InlineKeyboardButton(
            text=name,
            callback_data=f"equip_{item_id}"
        ))

    bot.send_message(message.chat.id, text, reply_markup=kb)


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


#callback (обробка кліку)
@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def handle_equip(call):
    user_id = call.from_user.id

    item_id = int(call.data.split("_")[1])

    result = equip_item(user_id, item_id)

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, result)

#ПРОФІЛЬ з реальними статами
@bot.message_handler(commands=['me'])
def profile(message):
    user_id = message.from_user.id

    stats = get_player_stats(user_id)

    if not stats:
        bot.send_message(message.chat.id, "❗ немає персонажа")
        return

    str_, dex_, int_, wis_ = stats
    atk = get_attack(user_id)

    text = (
        f"👤 Персонаж\n\n"
        f"💪 STR: {str_}\n"
        f"🎯 DEX: {dex_}\n"
        f"🔮 INT: {int_}\n"
        f"🦉 WIS: {wis_}\n\n"
        f"⚔️ Атака: {atk}"
    )

    bot.send_message(message.chat.id, text)
#Створеня персонажа
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    create_user(user_id)

    bot.send_message(message.chat.id, "👤 Персонаж створено ✅")

#пошук (оновлений)
@bot.message_handler(commands=['hunt'])
def hunt(message):
    user_id = message.from_user.id

    mob = generate_mob()

    # зберігаємо моба у памʼять (простий варіант)
    bot.user_data = getattr(bot, "user_data", {})
    bot.user_data[user_id] = mob

    atk = get_attack(user_id)

    text = (
        f"🔎 Ти зустрів {mob['name']}\n\n"
        f"👤 ТИ\n⚔️ {atk}\n\n"
        f"👹 ВОРОГ\n❤️ {mob['hp']}\n⚔️ {mob['attack']}\n🛡 {mob['def']}\n\n"
        f"⚔️ В атаку!"
    )

    bot.send_message(message.chat.id, text)

# тимчасово - ДОДАЄМО МОБІВ (простий варіант)
import random

def generate_mob():
    return {
        "name": random.choice(["🐺 Вовк", "🐗 Кабан", "👹 Гоблін"]),
        "hp": random.randint(30, 50),
        "attack": random.randint(5, 10),
        "def": random.randint(2, 5)
    }

#БІЙ З НОРМ ФОРМУЛОЮ
@bot.message_handler(commands=['attack'])
def attack(message):
    user_id = message.from_user.id

    if not hasattr(bot, "user_data") or user_id not in bot.user_data:
        bot.send_message(message.chat.id, "❗ Спочатку /hunt")
        return

    mob = bot.user_data[user_id]

    player_atk = get_attack(user_id)

    # ✅ ГОЛОВНА ФОРМУЛА
    damage = max(1, player_atk - mob["def"])

    # трохи рандому
    damage += random.randint(-2, 3)

    mob["hp"] -= damage

    # ✅ якщо перемога
    if mob["hp"] <= 0:
        bot.send_message(
            message.chat.id,
            f"🎉 Ти вбив {mob['name']}\n\n💥 Урон: {damage}"
        )

        del bot.user_data[user_id]
        return

    # моб б'є у відповідь
    mob_damage = max(1, mob["attack"] - 2)

    text = (
        f"⚔️ БІЙ\n\n"
        f"🗡️ Ти вдарив на {damage}\n"
        f"👹 Ворог вдарив на {mob_damage}\n\n"
        f"❤️ Ворог: {mob['hp']}"
    )

    bot.send_message(message.chat.id, text)
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот працює")


print("✅ BOT STARTED")
bot.infinity_polling()