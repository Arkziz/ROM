import sqlite3

# ==============================
# 🔌 ПІДКЛЮЧЕННЯ ДО БАЗИ
# ==============================

conn = sqlite3.connect("game.db", check_same_thread=False)
cursor = conn.cursor()


# ==============================
# ✅ DB INIT
# ==============================

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,

        hp INTEGER,
        max_hp INTEGER,
        level INTEGER,
        exp INTEGER,
        gold REAL,
        kills INTEGER,
        bag_slots INTEGER,
        current_location TEXT,

        str INTEGER,
        dex INTEGER,
        intelligence INTEGER,
        wis INTEGER,
        sta INTEGER,

        equipped_weapon INTEGER,
        equipped_armor INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        quantity INTEGER,
        durability INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        type TEXT,
        rarity TEXT,
        category TEXT,

        max_stack INTEGER,
        sell_price REAL,

        bonus_str INTEGER,
        bonus_dex INTEGER,
        bonus_int INTEGER,
        bonus_wis INTEGER,
        bonus_sta INTEGER,

        pdef INTEGER,
        mdef INTEGER
    )
    """)

    migrations = [
        ("users", "gold", "REAL DEFAULT 0"),
        ("users", "kills", "INTEGER DEFAULT 0"),
        ("users", "bag_slots", "INTEGER DEFAULT 20"),
        ("users", "current_location", "TEXT DEFAULT 'start_path'"),

        ("inventory", "quantity", "INTEGER DEFAULT 1"),
        ("inventory", "durability", "INTEGER DEFAULT NULL"),

        ("items", "category", "TEXT DEFAULT 'equipment'"),
        ("items", "max_stack", "INTEGER DEFAULT 1"),
        ("items", "sell_price", "REAL DEFAULT 0"),
        ("items", "bonus_sta", "INTEGER DEFAULT 0"),
        ("items", "pdef", "INTEGER DEFAULT 0"),
        ("items", "mdef", "INTEGER DEFAULT 0"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    # repair старих користувачів
    cursor.execute("UPDATE users SET gold = 0 WHERE gold IS NULL")
    cursor.execute("UPDATE users SET kills = 0 WHERE kills IS NULL")
    cursor.execute("UPDATE users SET bag_slots = 20 WHERE bag_slots IS NULL")
    cursor.execute("""
    UPDATE users
    SET current_location = 'start_path'
    WHERE current_location IS NULL OR current_location = ''
    """)

    # repair старого інвентаря
    cursor.execute("UPDATE inventory SET quantity = 1 WHERE quantity IS NULL")
    cursor.execute("""
    UPDATE inventory
    SET durability = 100
    WHERE durability IS NULL
      AND item_id IN (SELECT id FROM items WHERE category = 'equipment')
    """)

    conn.commit()


# ==============================
# ✅ SEED ITEMS
# ==============================

def seed_items():
    items = [
        # id, name, type, rarity, category, max_stack, sell_price,
        # str, dex, int, wis, sta, pdef, mdef

        # WEAPONS
        (1, "⚪ Старий меч", "weapon", "common", "equipment", 1, 1.00, 1, 0, 0, 0, 0, 0, 0),
        (2, "🟢 Залізний меч", "weapon", "uncommon", "equipment", 1, 3.00, 2, 0, 0, 0, 0, 0, 0),
        (3, "🔵 Меч воїна", "weapon", "rare", "equipment", 1, 8.00, 4, 0, 0, 0, 0, 0, 0),
        (4, "🟣 Епічний клинок", "weapon", "epic", "equipment", 1, 25.00, 7, 0, 0, 0, 0, 0, 0),

        # ARMOR
        (5, "⚪ Стара броня", "armor", "common", "equipment", 1, 1.00, 0, 0, 0, 1, 1, 2, 0),
        (6, "🟢 Шкіряна броня", "armor", "uncommon", "equipment", 1, 3.00, 0, 1, 0, 2, 2, 4, 1),
        (7, "🔵 Лицарська броня", "armor", "rare", "equipment", 1, 8.00, 0, 2, 0, 3, 4, 8, 2),

        # TRASH
        (101, "🐾 Густа вовча шкура", "trash", "grey", "trash", 20, 0.50, 0, 0, 0, 0, 0, 0, 0),
        (102, "🐗 Жорстка щетина", "trash", "grey", "trash", 20, 0.15, 0, 0, 0, 0, 0, 0, 0),
        (103, "🦡 Борсучий жир", "trash", "grey", "trash", 20, 0.25, 0, 0, 0, 0, 0, 0, 0),
        (104, "👹 Гоблінська сережка", "trash", "grey", "trash", 20, 0.35, 0, 0, 0, 0, 0, 0, 0),
        (105, "🕷️ Липка павутина", "trash", "grey", "trash", 20, 0.60, 0, 0, 0, 0, 0, 0, 0),
        (106, "💎 Тріснутий рунічний уламок", "trash", "grey", "trash", 20, 0.75, 0, 0, 0, 0, 0, 0, 0),

        # POTIONS
        (201, "🧪 Мале зілля здоров’я", "potion_hp", "common", "potion", 10, 0.50, 0, 0, 0, 0, 0, 0, 0),
        (202, "🔵 Мале зілля мани", "potion_mp", "common", "potion", 10, 0.50, 0, 0, 0, 0, 0, 0, 0),

        # RUNES
        (301, "💎 Руна Сили I", "rune_str", "common", "rune", 5, 1.00, 1, 0, 0, 0, 0, 0, 0),
    ]

    for item in items:
        cursor.execute("""
        INSERT OR REPLACE INTO items (
            id, name, type, rarity, category,
            max_stack, sell_price,
            bonus_str, bonus_dex, bonus_int, bonus_wis, bonus_sta,
            pdef, mdef
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)

    conn.commit()


# ==============================
# ✅ USER
# ==============================

def create_user(user_id):
    cursor.execute("""
    INSERT OR IGNORE INTO users (
        user_id,
        hp,
        max_hp,
        level,
        exp,
        gold,
        kills,
        bag_slots,
        current_location,
        str,
        dex,
        intelligence,
        wis,
        sta,
        equipped_weapon,
        equipped_armor
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        170,
        170,
        1,
        0,
        0.0,
        0,
        20,
        "start_path",
        10,
        10,
        10,
        10,
        10,
        None,
        None
    ))

    conn.commit()


# ==============================
# ✅ LOCATION
# ==============================

def get_current_location(user_id):
    cursor.execute("""
    SELECT current_location
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return "start_path"

    if row[0] is None or row[0] == "":
        return "start_path"

    return row[0]


def set_current_location(user_id, location_id):
    cursor.execute("""
    UPDATE users
    SET current_location=?
    WHERE user_id=?
    """, (location_id, user_id))

    conn.commit()


# ==============================
# ✅ ITEMS
# ==============================

def get_item(item_id):
    cursor.execute("""
    SELECT
        id,
        name,
        type,
        rarity,
        bonus_str,
        bonus_dex,
        bonus_int,
        bonus_wis,
        bonus_sta,
        pdef,
        mdef
    FROM items
    WHERE id=?
    """, (item_id,))

    return cursor.fetchone()


def get_item_full(item_id):
    cursor.execute("""
    SELECT
        id,
        name,
        type,
        rarity,
        category,
        max_stack,
        sell_price,
        bonus_str,
        bonus_dex,
        bonus_int,
        bonus_wis,
        bonus_sta,
        pdef,
        mdef
    FROM items
    WHERE id=?
    """, (item_id,))

    return cursor.fetchone()


# ==============================
# ✅ INVENTORY CAPACITY
# ==============================

def get_bag_capacity(user_id):
    cursor.execute("""
    SELECT bag_slots
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return 20

    if row[0] is None:
        return 20

    return row[0]


def get_inventory_used_slots(user_id):
    cursor.execute("""
    SELECT COUNT(*)
    FROM inventory
    WHERE user_id=?
    """, (user_id,))

    return cursor.fetchone()[0]


# ==============================
# ✅ ADD ITEM WITH STACKING
# ==============================

def add_item(user_id, item_id, quantity=1):
    item = get_item_full(item_id)

    if not item:
        return {
            "success": False,
            "added": 0,
            "lost": quantity,
            "message": "❌ Предмет не знайдено"
        }

    (
        _,
        name,
        type_,
        rarity,
        category,
        max_stack,
        sell_price,
        b_str,
        b_dex,
        b_int,
        b_wis,
        b_sta,
        pdef,
        mdef
    ) = item

    capacity = get_bag_capacity(user_id)
    added = 0
    lost = 0

    # НЕ СТАКУЄТЬСЯ
    if max_stack <= 1:
        for _ in range(quantity):
            used = get_inventory_used_slots(user_id)

            if used >= capacity:
                lost += 1
                continue

            cursor.execute("""
            INSERT INTO inventory (user_id, item_id, quantity, durability)
            VALUES (?, ?, ?, ?)
            """, (user_id, item_id, 1, 100))

            added += 1

        conn.commit()

        return {
            "success": added > 0,
            "added": added,
            "lost": lost,
            "name": name,
            "used_slots": get_inventory_used_slots(user_id),
            "capacity": capacity
        }

    # СТАКУЄТЬСЯ
    remaining = quantity

    cursor.execute("""
    SELECT id, quantity
    FROM inventory
    WHERE user_id=? AND item_id=? AND quantity < ?
    ORDER BY id ASC
    """, (user_id, item_id, max_stack))

    stacks = cursor.fetchall()

    for inv_id, current_qty in stacks:
        if remaining <= 0:
            break

        space = max_stack - current_qty
        to_add = min(space, remaining)

        cursor.execute("""
        UPDATE inventory
        SET quantity = quantity + ?
        WHERE id=?
        """, (to_add, inv_id))

        remaining -= to_add
        added += to_add

    while remaining > 0:
        used = get_inventory_used_slots(user_id)

        if used >= capacity:
            lost += remaining
            remaining = 0
            break

        to_add = min(max_stack, remaining)

        cursor.execute("""
        INSERT INTO inventory (user_id, item_id, quantity, durability)
        VALUES (?, ?, ?, ?)
        """, (user_id, item_id, to_add, None))

        remaining -= to_add
        added += to_add

    conn.commit()

    return {
        "success": added > 0,
        "added": added,
        "lost": lost,
        "name": name,
        "used_slots": get_inventory_used_slots(user_id),
        "capacity": capacity
    }


# ==============================
# ✅ INVENTORY READ
# ==============================

def get_inventory(user_id):
    cursor.execute("""
    SELECT item_id
    FROM inventory
    WHERE user_id=?
    """, (user_id,))

    return cursor.fetchall()


def get_inventory_detailed(user_id):
    cursor.execute("""
    SELECT
        inventory.id,
        inventory.item_id,
        items.name,
        items.type,
        items.rarity,
        items.category,
        inventory.quantity,
        items.max_stack,
        inventory.durability,
        items.bonus_str,
        items.bonus_dex,
        items.bonus_int,
        items.bonus_wis,
        items.bonus_sta,
        items.pdef,
        items.mdef,
        items.sell_price
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.user_id=?
    ORDER BY inventory.id ASC
    """, (user_id,))

    return cursor.fetchall()


def get_item_by_inventory_id(inventory_id):
    cursor.execute("""
    SELECT
        inventory.id,
        inventory.item_id,
        items.name,
        items.type,
        items.rarity,
        items.category,
        inventory.quantity,
        items.max_stack,
        inventory.durability,
        items.bonus_str,
        items.bonus_dex,
        items.bonus_int,
        items.bonus_wis,
        items.bonus_sta,
        items.pdef,
        items.mdef,
        items.sell_price
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.id=?
    """, (inventory_id,))

    return cursor.fetchone()


# ==============================
# ✅ EQUIPMENT
# ==============================

def get_equipped_inventory_ids(user_id):
    cursor.execute("""
    SELECT equipped_weapon, equipped_armor
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return None, None

    return row[0], row[1]


def equip_inventory_item(user_id, inventory_id):
    item = get_item_by_inventory_id(inventory_id)

    if not item:
        return "❌ Предмет не знайдено"

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

    if category != "equipment":
        return "❌ Цей предмет не можна одягти"

    if type_ == "weapon":
        cursor.execute("""
        UPDATE users
        SET equipped_weapon=?
        WHERE user_id=?
        """, (inventory_id, user_id))

    elif type_ == "armor":
        cursor.execute("""
        UPDATE users
        SET equipped_armor=?
        WHERE user_id=?
        """, (inventory_id, user_id))

    else:
        return "❌ Цей предмет не можна одягти"

    conn.commit()

    return f"✅ Одягнуто: {name}"


def equip_item(user_id, item_id):
    cursor.execute("""
    SELECT id
    FROM inventory
    WHERE user_id=? AND item_id=?
    ORDER BY id ASC
    LIMIT 1
    """, (user_id, item_id))

    row = cursor.fetchone()

    if not row:
        return "❌ Такого предмета немає в інвентарі"

    return equip_inventory_item(user_id, row[0])


# ==============================
# ✅ BONUSES
# ==============================

def get_item_bonuses(user_id):
    equipped_weapon, equipped_armor = get_equipped_inventory_ids(user_id)

    total_str = 0
    total_dex = 0
    total_int = 0
    total_wis = 0
    total_sta = 0

    for inventory_id in [equipped_weapon, equipped_armor]:
        if not inventory_id:
            continue

        item = get_item_by_inventory_id(inventory_id)

        if not item:
            continue

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

        total_str += b_str or 0
        total_dex += b_dex or 0
        total_int += b_int or 0
        total_wis += b_wis or 0
        total_sta += b_sta or 0

    return total_str, total_dex, total_int, total_wis, total_sta


def get_equipped_item_defenses(user_id):
    equipped_weapon, equipped_armor = get_equipped_inventory_ids(user_id)

    total_pdef = 0
    total_mdef = 0

    for inventory_id in [equipped_weapon, equipped_armor]:
        if not inventory_id:
            continue

        item = get_item_by_inventory_id(inventory_id)

        if not item:
            continue

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

        total_pdef += pdef or 0
        total_mdef += mdef or 0

    return total_pdef, total_mdef


# ==============================
# ✅ PLAYER STATS
# ==============================

def get_player_stats(user_id):
    cursor.execute("""
    SELECT
        str,
        dex,
        intelligence,
        wis,
        sta,
        level
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return None

    base_str, base_dex, base_int, base_wis, base_sta, lvl = row

    item_str, item_dex, item_int, item_wis, item_sta = get_item_bonuses(user_id)

    return (
        base_str + item_str,
        base_dex + item_dex,
        base_int + item_int,
        base_wis + item_wis,
        base_sta + item_sta,
        lvl
    )


# ==============================
# ✅ EXP / GOLD
# ==============================

def get_exp_to_next_level(level):
    exp_table = {
        1: 500,
        2: 900,
        3: 1500,
        4: 2400,
        5: 3600,
        6: 5200,
        7: 7500,
        8: 10500,
        9: 14500,
        10: 20000
    }

    if level in exp_table:
        return exp_table[level]

    return int(20000 * (1.35 ** (level - 10)))


def add_exp(user_id, amount):
    cursor.execute("""
    SELECT level, exp
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return None

    level, exp = row
    exp += int(amount)

    level_ups = 0

    while exp >= get_exp_to_next_level(level):
        exp -= get_exp_to_next_level(level)
        level += 1
        level_ups += 1

        cursor.execute("""
        UPDATE users
        SET
            str = str + 1,
            dex = dex + 1,
            intelligence = intelligence + 1,
            wis = wis + 1,
            sta = sta + 1
        WHERE user_id=?
        """, (user_id,))

    cursor.execute("""
    UPDATE users
    SET level=?, exp=?
    WHERE user_id=?
    """, (level, exp, user_id))

    conn.commit()

    max_hp = get_max_hp(user_id)

    cursor.execute("""
    UPDATE users
    SET max_hp=?
    WHERE user_id=?
    """, (max_hp, user_id))

    conn.commit()

    return {
        "level": level,
        "exp": exp,
        "exp_to_next": get_exp_to_next_level(level),
        "level_ups": level_ups
    }


def add_gold(user_id, amount):
    cursor.execute("""
    UPDATE users
    SET gold = gold + ?
    WHERE user_id=?
    """, (float(amount), user_id))

    conn.commit()


def add_kill(user_id):
    cursor.execute("""
    UPDATE users
    SET kills = kills + 1
    WHERE user_id=?
    """, (user_id,))

    conn.commit()


def get_wallet(user_id):
    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return 0.0

    return row[0]


def get_user_progress(user_id):
    cursor.execute("""
    SELECT level, exp, gold, kills
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return None

    level, exp, gold, kills = row

    return {
        "level": level,
        "exp": exp,
        "exp_to_next": get_exp_to_next_level(level),
        "gold": gold,
        "kills": kills
    }


# ==============================
# ✅ SELL TRASH
# ==============================

def sell_all_trash(user_id):
    cursor.execute("""
    SELECT
        inventory.id,
        items.name,
        inventory.quantity,
        items.sell_price
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.user_id=?
      AND items.category='trash'
    """, (user_id,))

    rows = cursor.fetchall()

    if not rows:
        return {
            "sold_items_count": 0,
            "gold_earned": 0.0,
            "freed_slots": 0,
            "details": []
        }

    total_gold = 0.0
    freed_slots = 0
    details = []

    for inv_id, name, quantity, sell_price in rows:
        quantity = quantity or 1
        sell_price = sell_price or 0

        earned = quantity * sell_price
        total_gold += earned
        freed_slots += 1

        details.append(f"{name} x{quantity} = {earned:.2f} золота")

        cursor.execute("""
        DELETE FROM inventory
        WHERE id=?
        """, (inv_id,))

    cursor.execute("""
    UPDATE users
    SET gold = gold + ?
    WHERE user_id=?
    """, (total_gold, user_id))

    conn.commit()

    return {
        "sold_items_count": len(rows),
        "gold_earned": total_gold,
        "freed_slots": freed_slots,
        "details": details
    }


# ==============================
# ✅ COMBAT STATS
# ==============================

def get_attack(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 0

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    return total_str


def get_magic_attack(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 0

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    return total_int


def get_max_hp(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 100

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    return 100 + (lvl * 20) + (total_sta * 5)


def get_physical_defense(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 0

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats
    item_pdef, item_mdef = get_equipped_item_defenses(user_id)

    return int(item_pdef + (total_sta * 0.2))


def get_magic_defense(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 0

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats
    item_pdef, item_mdef = get_equipped_item_defenses(user_id)

    return int(item_mdef + (total_wis * 1))


def get_defense(user_id):
    return get_physical_defense(user_id)


# ==============================
# ✅ HP
# ==============================

def get_current_hp(user_id):
    cursor.execute("""
    SELECT hp
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return 0

    return row[0]


def set_current_hp(user_id, hp):
    cursor.execute("""
    UPDATE users
    SET hp=?
    WHERE user_id=?
    """, (hp, user_id))

    conn.commit()