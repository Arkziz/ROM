import telebot
from telebot import types
import random

from config import TOKEN

from db import (
    init_db, seed_items,
    get_inventory, get_item,
    equip_item, add_item,
    get_player_stats,
    get_attack, get_defense, get_max_hp,
    create_user,
    cursor, conn
)

bot = telebot.TeleBot(TOKEN)

init_db()
seed_items()


# ==================
# START
# ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    create_user(user_id)
    bot.send_message(message.chat.id, "👤 Персонаж створено ✅")


# ==================
# PROFILE
# ==================
@bot.message_handler(commands=['me'])
def profile(message):
    user_id = message.from_user.id

    stats = get_player_stats(user_id)

    if not stats:
        bot.send_message(message.chat.id, "❗ немає персонажа")
        return

    str_, dex_, int_, wis_, sta_, lvl = stats

    atk = get_attack(user_id)
    hp = get_max_hp(user_id)
    pdef = get_defense(user_id)

    text = (
        f"👤 Персонаж\n\n"
        f"🏆 Рівень: {lvl}\n\n"
        f"💪 STR: {str_}\n"
        f"🎯 DEX: {dex_}\n"
        f"🔮 INT: {int_}\n"
        f"🦉 WIS: {wis_}\n"
        f"🛡 STA: {sta_}\n\n"
        f"❤️ HP: {hp}\n"
        f"🛡 DEF: {pdef}\n"
        f"⚔️ Атака: {atk}"
    )

    bot.send_message(message.chat.id, text)


# ==================
# GIVE ITEM
# ==================
@bot.message_handler(commands=['give'])
def give_item(message):
    user_id = message.from_user.id

    item_id = random.randint(1, 7)
    add_item(user_id, item_id)

    bot.send_message(message.chat.id, f"🎁 отримав {item_id}")


# ==================
# INVENTORY
# ==================
@bot.message_handler(commands=['inv'])
def show_inventory(message):
    user_id = message.from_user.id

    items = get_inventory(user_id)

    if not items:
        bot.send_message(message.chat.id, "🎒 Інвентар порожній")
        return

    kb = types.InlineKeyboardMarkup()

    for row in items:
        item_id = row[0]
        item = get_item(item_id)

        if not item:
            continue

        _, name, *_ = item

        kb.add(types.InlineKeyboardButton(
            text=name,
            callback_data=f"equip_{item_id}"
        ))

    bot.send_message(message.chat.id, "🎒 Обери предмет:", reply_markup=kb)


# ==================
# EQUIP
# ==================
@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def handle_equip(call):
    user_id = call.from_user.id
    item_id = int(call.data.split("_")[1])

    result = equip_item(user_id, item_id)

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, result)


# ==================
# MOB
# ==================
def generate_mob():
    return {
        "name": random.choice(["🐺 Вовк", "🐗 Кабан", "👹 Гоблін"]),
        "hp": random.randint(30, 50),
        "attack": random.randint(5, 10),
        "def": random.randint(2, 5)
    }


# ==================
# HUNT (з норм UI)
# ==================
@bot.message_handler(commands=['hunt'])
def hunt(message):
    user_id = message.from_user.id

    mob = generate_mob()

    bot.user_data = getattr(bot, "user_data", {})
    bot.user_data[user_id] = mob

    stats = get_player_stats(user_id)
    str_, dex_, int_, wis_, sta_, lvl = stats

    atk = get_attack(user_id)
    hp = get_max_hp(user_id)
    pdef = get_defense(user_id)

    text = (
        f"🔎 Ти зустрів {mob['name']}\n\n"
        f"======================\n\n"
        f"👤 ТИ\n"
        f"❤️ HP: {hp}\n"
        f"⚔️ Атака: {atk}\n"
        f"🛡 Захист: {pdef}\n\n"
        f"💪 STR {str_} | 🎯 DEX {dex_}\n"
        f"🔮 INT {int_} | 🦉 WIS {wis_}\n"
        f"🛡 STA {sta_}\n\n"
        f"----------------------\n\n"
        f"👹 ВОРОГ\n"
        f"❤️ HP: {mob['hp']}\n"
        f"⚔️ Атака: {mob['attack']}\n"
        f"🛡 Захист: {mob['def']}\n\n"
        f"⚔️ Бій починається!"
    )

    bot.send_message(message.chat.id, text)


# ==================
# ATTACK (FIXED + CRIT)
# ==================
@bot.message_handler(commands=['attack'])
def attack(message):
    user_id = message.from_user.id

    if not hasattr(bot, "user_data") or user_id not in bot.user_data:
        bot.send_message(message.chat.id, "❗ Спочатку /hunt")
        return

    mob = bot.user_data[user_id]

    # ✅ ВАЖЛИВО — тепер беремо stats
    stats = get_player_stats(user_id)
    str_, dex_, int_, wis_, sta_, lvl = stats

    player_atk = get_attack(user_id)
    player_def = get_defense(user_id)

    cursor.execute("SELECT hp FROM users WHERE user_id=?", (user_id,))
    player_hp = cursor.fetchone()[0]

    # 🎯 CRIT
    crit_chance = dex_ * 0.5
    is_crit = random.randint(1, 100) <= crit_chance

    dmg = max(1, player_atk - mob["def"] + random.randint(-2, 3))

    if is_crit:
        dmg *= 2

    mob["hp"] -= dmg

    if mob["hp"] <= 0:
        bot.send_message(message.chat.id,
            f"🎉 Перемога!\n{'💥 КРИТ!\n' if is_crit else ''}Урон: {dmg}")
        del bot.user_data[user_id]
        return

    # 👹 анти-крит
    anti_crit = sta_ // 25
    mob_crit_chance = max(0, 10 - anti_crit)

    mob_is_crit = random.randint(1, 100) <= mob_crit_chance

    mob_dmg = max(1, mob["attack"] - player_def + random.randint(-2, 2))

    if mob_is_crit:
        mob_dmg *= 2

    player_hp -= mob_dmg

    if player_hp <= 0:
        cursor.execute(
            "UPDATE users SET hp=? WHERE user_id=?",
            (get_max_hp(user_id), user_id)
        )
        conn.commit()

        del bot.user_data[user_id]

        bot.send_message(message.chat.id,
            "💀 ТИ ЗАГИНУВ\n❤️ HP відновлено")
        return

    cursor.execute(
        "UPDATE users SET hp=? WHERE user_id=?",
        (player_hp, user_id)
    )
    conn.commit()

    text = "⚔️ БІЙ\n\n"

    text += f"{'💥 КРИТ! ' if is_crit else ''}🗡️ Ти: {dmg}\n"
    text += f"{'💥 КРИТ ВОРОГА! ' if mob_is_crit else ''}👹 Ворог: {mob_dmg}\n\n"

    text += (
        f"❤️ Твоє HP: {player_hp}\n"
        f"👹 HP ворога: {mob['hp']}"
    )

    bot.send_message(message.chat.id, text)


print("✅ BOT STARTED")
bot.infinity_polling()