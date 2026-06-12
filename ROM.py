import telebot
import random
import sqlite3

TOKEN = "8888701756:AAFzFu1vlQlVKfYS4vEVinodLqyZagSa_Kk"
bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("game.db", check_same_thread=False)
cursor = conn.cursor()

# таблиці
cursor.execute("""
               CREATE TABLE IF NOT EXISTS users
               (
                   user_id
                   INTEGER
                   PRIMARY
                   KEY,
                   hp
                   INTEGER,
                   base_attack
                   INTEGER,
                   level
                   INTEGER
               )
               """)

cursor.execute("""
               CREATE TABLE IF NOT EXISTS inventory
               (
                   id
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,
                   user_id
                   INTEGER,
                   item_name
                   TEXT,
                   bonus
                   INTEGER,
                   item_type
                   TEXT
               )
               """)

# додаткові колонки
for column in [
    "exp INTEGER DEFAULT 0",
    "in_fight INTEGER DEFAULT 0",
    "mob_hp INTEGER DEFAULT 0",
    "mob_attack INTEGER DEFAULT 0",
    "equipped_weapon INTEGER DEFAULT 0",
    "equipped_armor INTEGER DEFAULT 0"
]:
    try:
        cursor.execute(f"ALTER TABLE users ADD COLUMN {column}")
    except:
        pass

conn.commit()

from telebot import types


# 🔧 допоміжні функції
def get_item_bonus(item_id):
    if not item_id:
        return ("Немає", 0)
    cursor.execute("SELECT item_name, bonus FROM inventory WHERE id=?", (item_id,))
    row = cursor.fetchone()
    return row if row else ("Немає", 0)


def get_total_attack(user_id):
    cursor.execute("""
                   SELECT base_attack, equipped_weapon, equipped_armor
                   FROM users
                   WHERE user_id = ?
                   """, (user_id,))
    base, w_id, a_id = cursor.fetchone()

    w_name, w_bonus = get_item_bonus(w_id)
    a_name, a_bonus = get_item_bonus(a_id)

    return base + w_bonus + a_bonus


# 🎛 кнопки
def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔎 Пошук", "🎒 Інвентар", "👤 Профіль")
    kb.add("❤️ Відновитись")
    return kb


def fight_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⚔️ Атакувати")
    return kb


# 🚀 старт
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("""
                       INSERT INTO users
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """, (user_id, 100, 10, 1, 0, 0, 0, 0, 0, 0))
        conn.commit()

    bot.send_message(message.chat.id, "👋 Старт гри", reply_markup=main_kb())


# 👤 профіль (норм UX)
@bot.message_handler(func=lambda m: m.text and "проф" in m.text.lower())
def profile(message):
    user_id = message.from_user.id

    cursor.execute("""
                   SELECT hp, base_attack, level, exp, equipped_weapon, equipped_armor
                   FROM users
                   WHERE user_id = ?
                   """, (user_id,))

    hp, base, lvl, exp, w_id, a_id = cursor.fetchone()

    w_name, w_bonus = get_item_bonus(w_id)
    a_name, a_bonus = get_item_bonus(a_id)

    total = base + w_bonus + a_bonus

    bot.send_message(message.chat.id,
                     f"👤 Профіль\n\n"
                     f"❤️ HP: {hp}\n"
                     f"⚔️ Атака: {total}\n\n"
                     f"🔹 База: {base}\n"
                     f"🗡️ {w_name}: +{w_bonus}\n"
                     f"🛡 {a_name}: +{a_bonus}\n\n"
                     f"🏆 Level: {lvl}\n"
                     f"📈 EXP: {exp}"
                     )


# 🎒 інвентар
@bot.message_handler(func=lambda m: m.text and "інв" in m.text.lower())
def inventory(message):
    user_id = message.from_user.id

    cursor.execute("""
                   SELECT id, item_name, bonus, item_type
                   FROM inventory
                   WHERE user_id = ?
                   """, (user_id,))
    items = cursor.fetchall()

    if not items:
        bot.send_message(message.chat.id, "🎒 Порожньо")
        return

    cursor.execute("""
                   SELECT equipped_weapon, equipped_armor
                   FROM users
                   WHERE user_id = ?
                   """, (user_id,))
    eq_w, eq_a = cursor.fetchone()

    kb = types.InlineKeyboardMarkup()

    for item in items:
        item_id, name, bonus, t = item

        emoji = "🗡️" if t == "weapon" else "🛡"

        is_equipped = (
                (t == "weapon" and item_id == eq_w) or
                (t == "armor" and item_id == eq_a)
        )

        label = f"{emoji} {name} (+{bonus})"
        if is_equipped:
            label += " ✅"

        kb.add(types.InlineKeyboardButton(
            text=label,
            callback_data=f"equip_{item_id}"
        ))

    bot.send_message(message.chat.id, "🎒 Інвентар:", reply_markup=kb)


# ⚔️ екіп
@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_"))
def equip(call):
    user_id = call.from_user.id
    item_id = int(call.data.split("_")[1])

    cursor.execute("""
                   SELECT item_type
                   FROM inventory
                   WHERE id = ?
                     AND user_id = ?
                   """, (item_id, user_id))
    row = cursor.fetchone()

    if not row:
        return

    item_type = row[0]

    if item_type == "weapon":
        cursor.execute("UPDATE users SET equipped_weapon=? WHERE user_id=?", (item_id, user_id))
        text = "🗡️ Зброя одягнута"

    elif item_type == "armor":
        cursor.execute("UPDATE users SET equipped_armor=? WHERE user_id=?", (item_id, user_id))
        text = "🛡 Броня одягнута"
    else:
        return

    conn.commit()

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, text)


# ❤️ лікування
@bot.message_handler(func=lambda m: m.text and "віднов" in m.text.lower())
def heal(message):
    cursor.execute("UPDATE users SET hp=100 WHERE user_id=?", (message.from_user.id,))
    conn.commit()

    bot.send_message(message.chat.id, "❤️ HP відновлено", reply_markup=main_kb())


# 🔎 пошук
@bot.message_handler(func=lambda m: m.text and "пошук" in m.text.lower())
def search(message):
    user_id = message.from_user.id

    mob_hp = random.randint(30, 60)
    mob_attack = random.randint(5, 15)

    cursor.execute("""
                   UPDATE users
                   SET in_fight=1,
                       mob_hp=?,
                       mob_attack=?
                   WHERE user_id = ?
                   """, (mob_hp, mob_attack, user_id))
    conn.commit()

    cursor.execute("SELECT hp FROM users WHERE user_id=?", (user_id,))
    hp = cursor.fetchone()[0]

    atk = get_total_attack(user_id)

    bot.send_message(message.chat.id,
                     f"🔎 Ти знайшов монстра!\n\n"
                     f"👤 Ти:\n❤️ {hp} HP\n⚔️ {atk}\n\n"
                     f"👹 Монстр:\n❤️ {mob_hp} HP\n⚔️ {mob_attack}",
                     reply_markup=fight_kb()
                     )


# ⚔️ БІЙ (ПОВЕРНУТО І ВИПРАВЛЕНО)
@bot.message_handler(func=lambda m: m.text and "атак" in m.text.lower())
def attack(message):
    user_id = message.from_user.id

    cursor.execute("""
                   SELECT hp, level, exp, mob_hp, mob_attack, in_fight
                   FROM users
                   WHERE user_id = ?
                   """, (user_id,))
    data = cursor.fetchone()

    if not data:
        return

    hp, lvl, exp, mob_hp, mob_attack, in_fight = data

    if not in_fight:
        bot.send_message(message.chat.id, "❗ Спочатку натисни Пошук")
        return

    player_attack = get_total_attack(user_id)

    dmg = max(1, random.randint(player_attack - 2, player_attack + 5))
    mob_hp -= dmg

    if mob_hp <= 0:
        exp_gain = random.randint(15, 30)
        exp += exp_gain

        text = f"🗡️ Ти вдарив: {dmg}\n\n🎉 Перемога! +{exp_gain} EXP\n"

        if random.randint(1, 100) <= 50:
            t = random.choice(["weapon", "armor"])
            bonus = random.randint(1, 5)

            cursor.execute("""
                           INSERT INTO inventory (user_id, item_name, bonus, item_type)
                           VALUES (?, ?, ?, ?)
                           """, (user_id, t, bonus, t))

            text += f"📦 Новий {t} +{bonus}\n"

        if exp >= lvl * 50:
            exp = 0
            lvl += 1
            cursor.execute("UPDATE users SET base_attack = base_attack + 2 WHERE user_id=?", (user_id,))
            text += f"\n🏆 Level {lvl}"

        cursor.execute("""
                       UPDATE users
                       SET exp=?,
                           level=?,
                           in_fight=0
                       WHERE user_id = ?
                       """, (exp, lvl, user_id))

        conn.commit()

        bot.send_message(message.chat.id, text, reply_markup=main_kb())
        return

    mob_dmg = max(1, random.randint(mob_attack - 2, mob_attack + 3))
    hp -= mob_dmg

    text = (
        f"🗡️ Ти вдарив: {dmg}\n"
        f"👹 Монстр вдарив: {mob_dmg}\n\n"
        f"❤️ Твоє HP: {hp}\n"
        f"👹 HP монстра: {mob_hp}"
    )

    if hp <= 0:
        cursor.execute("UPDATE users SET hp=100, in_fight=0 WHERE user_id=?", (user_id,))
        conn.commit()

        bot.send_message(message.chat.id, "💀 Ти помер", reply_markup=main_kb())
        return

    cursor.execute("""
                   UPDATE users
                   SET hp=?,
                       mob_hp=?
                   WHERE user_id = ?
                   """, (hp, mob_hp, user_id))
    conn.commit()

    bot.send_message(message.chat.id, text, reply_markup=fight_kb())


print("✅ BOT STARTED")
bot.infinity_polling()
