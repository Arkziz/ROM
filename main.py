
import telebot
from telebot import types
import random

from config import TOKEN

from db import (
    init_db, seed_items,
    add_item,
    get_player_stats,
    get_attack, get_defense, get_max_hp,
    create_user,
    cursor, conn,
    get_inventory_detailed,
    get_equipped_inventory_ids,
    equip_inventory_item
)

bot = telebot.TeleBot(TOKEN)

init_db()
seed_items()


# ==================
# UI
# ==================

def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔎 Полювання", "🎒 Інвентар")
    kb.add("👤 Профіль")
    return kb


def fight_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⚔️ Атакувати")
    kb.add("🏃 Втекти")
    return kb


# ==================
# HP BAR
# ==================

def hp_bar(current_hp, max_hp, size=10):
    if max_hp <= 0:
        return "░" * size + " 0%"

    current_hp = max(0, min(current_hp, max_hp))
    percent = int((current_hp / max_hp) * 100)
    filled = round((current_hp / max_hp) * size)

    bar = "█" * filled + "░" * (size - filled)
    return f"{bar} {percent}%"


def get_current_hp(user_id):
    cursor.execute("SELECT hp FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    if not row:
        return 0

    return row[0]


# ==================
# START
# ==================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    create_user(user_id)

    bot.send_message(
        message.chat.id,
        "👤 Персонаж створено ✅",
        reply_markup=main_kb()
    )


# ==================
# PROFILE
# ==================

@bot.message_handler(func=lambda m: m.text == "👤 Профіль")
def profile(message):
    user_id = message.from_user.id

    stats = get_player_stats(user_id)

    if not stats:
        bot.send_message(message.chat.id, "❗ Немає персонажа", reply_markup=main_kb())
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

    bot.send_message(message.chat.id, text, reply_markup=main_kb())


# ==================
# GIVE TEST ITEM
# ==================

@bot.message_handler(commands=['give'])
def give_item(message):
    user_id = message.from_user.id

    item_id = random.randint(1, 7)
    add_item(user_id, item_id)

    bot.send_message(
        message.chat.id,
        f"🎁 Отримано тестовий предмет item_id {item_id}",
        reply_markup=main_kb()
    )


# ==================
# INVENTORY
# ==================

@bot.message_handler(func=lambda m: m.text == "🎒 Інвентар")
def show_inventory(message):
    user_id = message.from_user.id

    items = get_inventory_detailed(user_id)

    if not items:
        bot.send_message(message.chat.id, "🎒 Інвентар порожній", reply_markup=main_kb())
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

    bot.send_message(message.chat.id, "🎒 Обери предмет:", reply_markup=kb)


# ==================
# EQUIP CALLBACK
# ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def handle_equip(call):
    user_id = call.from_user.id
    inventory_id = int(call.data.split("_")[1])

    result = equip_inventory_item(user_id, inventory_id)

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, result, reply_markup=main_kb())


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
# HUNT
# ==================

@bot.message_handler(func=lambda m: m.text == "🔎 Полювання")
def hunt(message):
    user_id = message.from_user.id

    stats = get_player_stats(user_id)

    if not stats:
        bot.send_message(message.chat.id, "❗ Спочатку натисни /start", reply_markup=main_kb())
        return

    mob = generate_mob()

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
        f"❤️ HP: {mob['hp']}\n"
        f"{hp_bar(mob['hp'], mob['hp'])}\n"
        f"⚔️ Атака: {mob['attack']}\n"
        f"🛡 Захист: {mob['def']}\n\n"
        f"⚔️ Бій починається!"
    )

    bot.send_message(message.chat.id, text, reply_markup=fight_kb())


# ==================
# ATTACK
# ==================

@bot.message_handler(func=lambda m: m.text == "⚔️ Атакувати")
def attack(message):
    user_id = message.from_user.id

    if not hasattr(bot, "user_data") or user_id not in bot.user_data:
        bot.send_message(message.chat.id, "❗ Спочатку почни полювання", reply_markup=main_kb())
        return

    mob = bot.user_data[user_id]

    stats = get_player_stats(user_id)

    if not stats:
        bot.send_message(message.chat.id, "❗ Персонажа не знайдено", reply_markup=main_kb())
        return

    str_, dex_, int_, wis_, sta_, lvl = stats

    player_atk = get_attack(user_id)
    player_def = get_defense(user_id)

    player_hp = get_current_hp(user_id)
    player_max_hp = get_max_hp(user_id)

    mob_max_hp = mob.get("max_hp")
    if not mob_max_hp:
        mob["max_hp"] = mob["hp"]
        mob_max_hp = mob["max_hp"]

    # ==================
    # PLAYER ATTACK
    # ==================

    crit_chance = dex_ * 0.5
    is_crit = random.randint(1, 100) <= crit_chance

    dmg = max(1, player_atk - mob["def"] + random.randint(-2, 3))

    if is_crit:
        dmg *= 2

    mob["hp"] -= dmg

    # ==================
    # VICTORY
    # ==================

    if mob["hp"] <= 0:
        del bot.user_data[user_id]

        text = "🎉 Перемога!\n\n"

        if is_crit:
            text += f"💥 Завершальний критичний удар: {dmg}\n"
        else:
            text += "👹 Ворог переможений"

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_kb()
        )
        return

    # ==================
    # DODGE
    # ==================

    dodge_chance = dex_ * 0.4
    is_dodge = random.randint(1, 100) <= dodge_chance

    # ==================
    # MOB CRIT
    # ==================

    anti_crit = sta_ // 25
    mob_crit_chance = max(0, 10 - anti_crit)

    mob_is_crit = random.randint(1, 100) <= mob_crit_chance

    if is_dodge:
        mob_dmg = 0
    else:
        mob_dmg = max(1, mob["attack"] - player_def + random.randint(-2, 2))

        if mob_is_crit:
            mob_dmg *= 2

    player_hp -= mob_dmg

    # ==================
    # DEATH
    # ==================

    if player_hp <= 0:
        cursor.execute(
            "UPDATE users SET hp=? WHERE user_id=?",
            (player_max_hp, user_id)
        )
        conn.commit()

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

    cursor.execute(
        "UPDATE users SET hp=? WHERE user_id=?",
        (player_hp, user_id)
    )
    conn.commit()

    # ==================
    # BATTLE TEXT
    # ==================

    text = "⚔️ БІЙ\n\n"

    if is_crit:
        text += f"💥 КРИТ! Ти завдав {dmg} шкоди\n"
    else:
        text += f"🗡️ Ти завдав {dmg} шкоди\n"

    if is_dodge:
        text += "💨 УХИЛ! Ти уникнув атаки ворога\n\n"
    elif mob_is_crit:
        text += f"💥 КРИТ ВОРОГА! Ти отримав {mob_dmg} шкоди\n\n"
    else:
        text += f"👹 Ворог завдав {mob_dmg} шкоди\n\n"

    text += (
        f"❤️ Твоє HP: {player_hp}/{player_max_hp}\n"
        f"{hp_bar(player_hp, player_max_hp)}\n\n"
        f"👹 HP ворога: {mob['hp']}/{mob_max_hp}\n"
        f"{hp_bar(mob['hp'], mob_max_hp)}"
    )

    bot.send_message(message.chat.id, text, reply_markup=fight_kb())


# ==================
# ESCAPE
# ==================

@bot.message_handler(func=lambda m: m.text == "🏃 Втекти")
def escape(message):
    user_id = message.from_user.id

    if hasattr(bot, "user_data") and user_id in bot.user_data:
        del bot.user_data[user_id]

    bot.send_message(message.chat.id, "🏃 Ти втік з бою", reply_markup=main_kb())


print("✅ BOT STARTED")
bot.infinity_polling()
