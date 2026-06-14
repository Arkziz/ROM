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

#отримати статси з предметів
def get_equipped_items(user_id):
    cursor.execute("""
    SELECT equipped_weapon, equipped_armor FROM users
    WHERE user_id=?
    """, (user_id,))
    return cursor.fetchone()

#бонуси від екіпу
def get_item_bonuses(user_id):
    eq = get_equipped_items(user_id)

    total_str = 0
    total_dex = 0
    total_int = 0
    total_wis = 0

    for item_id in eq:
        if not item_id:
            continue

        item = get_item(item_id)
        if not item:
            continue

        _, _, _, _, b_str, b_dex, b_int, b_wis = item

        total_str += b_str or 0
        total_dex += b_dex or 0
        total_int += b_int or 0
        total_wis += b_wis or 0

    return total_str, total_dex, total_int, total_wis

#отримати повні статси
def get_player_stats(user_id):
    cursor.execute("""
    SELECT str, dex, int, wis FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return None

    base_str, base_dex, base_int, base_wis = row

    item_str, item_dex, item_int, item_wis = get_item_bonuses(user_id)

    total_str = base_str + item_str
    total_dex = base_dex + item_dex
    total_int = base_int + item_int
    total_wis = base_wis + item_wis

    return total_str, total_dex, total_int, total_wis

#атака з урахуванням предметів
def get_attack(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 0

    total_str = stats[0]

    # поки проста формула
    return total_str

#створення персонажа
def create_user(user_id):
    cursor.execute("""
    INSERT OR IGNORE INTO users
    (user_id, hp, max_hp, level, exp, str, dex, int, wis, equipped_weapon, equipped_armor)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        100, 100,   # hp
        1, 0,       # level, exp
        10, 10, 10, 10,  # стати
        None, None
    ))
    conn.commit()