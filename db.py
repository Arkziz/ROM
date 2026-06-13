import sqlite3



#@bot.message_handler(commands=['equip']) delete
def equip(message):
    user_id = message.from_user.id

    parts = message.text.split()

    if len(parts) < 2:
        bot.send_message(message.chat.id, "❗ /equip ID")
        return

    item_id = int(parts[1])

    result = equip_item(user_id, item_id)

    bot.send_message(message.chat.id, result)

# підключення
conn = sqlite3.connect("game.db", check_same_thread=False)
cursor = conn.cursor()


def init_db():
    # 👤 USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        hp INTEGER,
        max_hp INTEGER,
        level INTEGER,
        exp INTEGER,

        str INTEGER,
        dex INTEGER,
        int INTEGER,
        wis INTEGER,

        equipped_weapon INTEGER,
        equipped_armor INTEGER
    )
    """)

    # 🎒 INVENTORY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER
    )
    """)

    # 🧱 ITEMS (найважливіша таблиця)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        type TEXT,
        rarity TEXT,

        bonus_str INTEGER,
        bonus_dex INTEGER,
        bonus_int INTEGER,
        bonus_wis INTEGER
    )
    """)

    conn.commit()


def seed_items():
    items = [
        (1, "⚪ Старий меч", "weapon", "common", 1, 0, 0, 0),
        (2, "🟢 Залізний меч", "weapon", "uncommon", 2, 0, 0, 0),
        (3, "🔵 Меч воїна", "weapon", "rare", 4, 0, 0, 0),
        (4, "🟣 Епічний клинок", "weapon", "epic", 7, 0, 0, 0),

        (5, "⚪ Стара броня", "armor", "common", 0, 0, 0, 1),
        (6, "🟢 Шкіряна броня", "armor", "uncommon", 0, 1, 0, 2),
        (7, "🔵 Лицарська броня", "armor", "rare", 0, 2, 0, 3),
    ]

    for item in items:
        try:
            cursor.execute("""
            INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, item)
        except:
            pass

    conn.commit()

def get_inventory(user_id):
    cursor.execute("""
    SELECT item_id FROM inventory WHERE user_id=?
    """, (user_id,))
    return cursor.fetchall()

def get_item(item_id):
    cursor.execute("""
    SELECT id, name, type, rarity,
           bonus_str, bonus_dex, bonus_int, bonus_wis
    FROM items WHERE id=?
    """, (item_id,))
    return cursor.fetchone()

def add_item(user_id, item_id):
    cursor.execute("""
    INSERT INTO inventory (user_id, item_id)
    VALUES (?, ?)
    """, (user_id, item_id))
    conn.commit()


def equip_item(user_id, item_id):
    item = get_item(item_id)

    if not item:
        return "❌ Предмет не знайдено"

    _, name, type_, *_ = item

    if type_ == "weapon":
        cursor.execute("""
        UPDATE users SET equipped_weapon=?
        WHERE user_id=?
        """, (item_id, user_id))

    elif type_ == "armor":
        cursor.execute("""
        UPDATE users SET equipped_armor=?
        WHERE user_id=?
        """, (item_id, user_id))
    else:
        return "❌ Не можна одягти"

    conn.commit()
    return f"✅ Одягнув {name}"