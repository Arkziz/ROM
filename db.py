import sqlite3

# ==============================
# 🔌 ПІДКЛЮЧЕННЯ ДО БАЗИ
# ==============================

conn = sqlite3.connect("game.db", check_same_thread=False)
cursor = conn.cursor()


# ==============================
# ✅ ІНІЦІАЛІЗАЦІЯ БД
# ==============================

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,

        hp INTEGER,
        max_hp INTEGER,
        level INTEGER,
        exp INTEGER,

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
        item_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        type TEXT,
        rarity TEXT,

        bonus_str INTEGER,
        bonus_dex INTEGER,
        bonus_int INTEGER,
        bonus_wis INTEGER,
        bonus_sta INTEGER,

        pdef INTEGER,
        mdef INTEGER
    )
    """)

    conn.commit()


# ==============================
# ✅ СТАРТОВІ ПРЕДМЕТИ
# ==============================

def seed_items():
    items = [
        # id, name, type, rarity, str, dex, int, wis, sta, pdef, mdef

        # WEAPONS
        (1, "⚪ Старий меч", "weapon", "common", 1, 0, 0, 0, 0, 0, 0),
        (2, "🟢 Залізний меч", "weapon", "uncommon", 2, 0, 0, 0, 0, 0, 0),
        (3, "🔵 Меч воїна", "weapon", "rare", 4, 0, 0, 0, 0, 0, 0),
        (4, "🟣 Епічний клинок", "weapon", "epic", 7, 0, 0, 0, 0, 0, 0),

        # ARMOR
        (5, "⚪ Стара броня", "armor", "common", 0, 0, 0, 1, 1, 2, 0),
        (6, "🟢 Шкіряна броня", "armor", "uncommon", 0, 1, 0, 2, 2, 4, 1),
        (7, "🔵 Лицарська броня", "armor", "rare", 0, 2, 0, 3, 4, 8, 2),
    ]

    for item in items:
        try:
            cursor.execute("""
            INSERT INTO items (
                id, name, type, rarity,
                bonus_str, bonus_dex, bonus_int, bonus_wis, bonus_sta,
                pdef, mdef
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, item)
        except:
            pass

    conn.commit()


# ==============================
# ✅ КОРИСТУВАЧ
# ==============================

def create_user(user_id):
    # Стартові параметри:
    # level = 1
    # sta = 10
    # max_hp = 100 + (1 * 20) + (10 * 5) = 170

    cursor.execute("""
    INSERT OR IGNORE INTO users (
        user_id,
        hp,
        max_hp,
        level,
        exp,
        str,
        dex,
        intelligence,
        wis,
        sta,
        equipped_weapon,
        equipped_armor
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        170,
        170,
        1,
        0,
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


# ==============================
# ✅ INVENTORY BASIC
# ==============================

def add_item(user_id, item_id):
    cursor.execute("""
    INSERT INTO inventory (user_id, item_id)
    VALUES (?, ?)
    """, (user_id, item_id))

    conn.commit()


def get_inventory(user_id):
    cursor.execute("""
    SELECT item_id
    FROM inventory
    WHERE user_id=?
    """, (user_id,))

    return cursor.fetchall()


# ==============================
# ✅ INVENTORY DETAILED
# ==============================

def get_inventory_detailed(user_id):
    cursor.execute("""
    SELECT 
        inventory.id,
        inventory.item_id,
        items.name,
        items.type,
        items.rarity,
        items.bonus_str,
        items.bonus_dex,
        items.bonus_int,
        items.bonus_wis,
        items.bonus_sta,
        items.pdef,
        items.mdef
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
        items.bonus_str,
        items.bonus_dex,
        items.bonus_int,
        items.bonus_wis,
        items.bonus_sta,
        items.pdef,
        items.mdef
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

    inv_id, item_id, name, type_, rarity, b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef = item

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


# Старий метод залишаємо для сумісності
def equip_item(user_id, item_id):
    item = get_item(item_id)

    if not item:
        return "❌ Предмет не знайдено"

    _, name, type_, *_ = item

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

    inventory_id = row[0]

    return equip_inventory_item(user_id, inventory_id)


# ==============================
# ✅ BONUSES FROM EQUIPPED ITEMS
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

        _, _, _, _, _, b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef = item

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

        _, _, _, _, _, b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef = item

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

    total_str = base_str + item_str
    total_dex = base_dex + item_dex
    total_int = base_int + item_int
    total_wis = base_wis + item_wis
    total_sta = base_sta + item_sta

    return (
        total_str,
        total_dex,
        total_int,
        total_wis,
        total_sta,
        lvl
    )


# ==============================
# ✅ COMBAT STATS
# ==============================

def get_attack(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 0

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    # Поки фізична атака = Сила
    return total_str


def get_magic_attack(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 0

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    # Поки магічна атака = Інтелект
    return total_int


def get_max_hp(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 100

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    # MaxHP = 100 + (Level * 20) + (STA * 5)
    return 100 + (lvl * 20) + (total_sta * 5)


def get_physical_defense(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 0

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    item_pdef, item_mdef = get_equipped_item_defenses(user_id)

    # PDEF = PDEF_шмоту + STA * 0.2 + заточка
    # Заточки поки немає
    return int(item_pdef + (total_sta * 0.2))


def get_magic_defense(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return 0

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    item_pdef, item_mdef = get_equipped_item_defenses(user_id)

    # MDEF = MDEF_шмоту + WIS * 1 + заточка
    # Заточки поки немає
    return int(item_mdef + (total_wis * 1))


# Старий alias, щоб нічого не зламати
def get_defense(user_id):
    return get_physical_defense(user_id)


# ==============================
# ✅ CURRENT HP
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