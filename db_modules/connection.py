# ROM 17.19.1 MANA POTION PRICE BALANCE
"""
Database connection and initialization module.
"""

import sqlite3

# ==============================
# 🔌 ПІДКЛЮЧЕННЯ ДО БАЗИ
# ==============================

conn = sqlite3.connect("game.db", check_same_thread=False)
cursor = conn.cursor()


# ==============================
# ✅ EQUIPMENT CONFIG
# ==============================

DEFAULT_BAG_SLOTS = 60  # ROM 17.8.1 BASE BAG CAPACITY 60

SLOT_ORDER = [
    "main_hand",
    "off_hand",
    "helmet",
    "shoulders",
    "chest",
    "gloves",
    "legs",
    "boots",
    "necklace",
    "ring"
]


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
    ,
        refine_level INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        type TEXT,
        rarity TEXT,
        category TEXT,

        slot_key TEXT,
        weapon_hands INTEGER,

        max_stack INTEGER,
        sell_price REAL,

        bonus_str INTEGER,
        bonus_dex INTEGER,
        bonus_int INTEGER,
        bonus_wis INTEGER,
        bonus_sta INTEGER,

        pdef INTEGER,
        mdef INTEGER
    ,
        item_subtype TEXT DEFAULT ''
    ,
        armor_type TEXT DEFAULT ''
    ,
        weapon_min_damage INTEGER DEFAULT 0
    ,
        weapon_max_damage INTEGER DEFAULT 0
    ,
        weapon_min_magic_damage INTEGER DEFAULT 0
    ,
        weapon_max_magic_damage INTEGER DEFAULT 0
    ,
        weapon_attack_type TEXT DEFAULT ''
    ,
        shop_preview_owner INTEGER DEFAULT NULL
    ,
        shop_preview_price INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment_slots (
        user_id INTEGER,
        slot_key TEXT,
        inventory_id INTEGER,
        PRIMARY KEY (user_id, slot_key)
    )
    """)

    migrations = [
        ("users", "gold", "REAL DEFAULT 0"),
        ("users", "kills", "INTEGER DEFAULT 0"),
        ("users", "bag_slots", "INTEGER DEFAULT 60"),
        ("users", "current_location", "TEXT DEFAULT 'city'"),

        ("inventory", "quantity", "INTEGER DEFAULT 1"),
        ("inventory", "durability", "INTEGER DEFAULT NULL"),

        ("items", "category", "TEXT DEFAULT 'equipment'"),
        ("items", "slot_key", "TEXT DEFAULT NULL"),
        ("items", "weapon_hands", "INTEGER DEFAULT 1"),
        ("items", "max_stack", "INTEGER DEFAULT 1"),
        ("items", "sell_price", "REAL DEFAULT 0"),
        ("items", "bonus_sta", "INTEGER DEFAULT 0"),
        ("items", "pdef", "INTEGER DEFAULT 0"),
        ("items", "mdef", "INTEGER DEFAULT 0"),
        ("items", "item_level", "INTEGER DEFAULT 1"),
        ("items", "is_generated", "INTEGER DEFAULT 0"),

        ("users", "daily_contracts_completed", "INTEGER DEFAULT 0"),
        ("users", "daily_contract_date", "TEXT DEFAULT ''"),

        ("users", "energy", "INTEGER DEFAULT 0"),
        ("users", "last_energy_update", "TEXT DEFAULT ''"),
        ("users", "energy_full_notified", "INTEGER DEFAULT 1"),

        ("users", "last_hp_regen_update", "TEXT DEFAULT ''"),
        ("users", "hp_full_notified", "INTEGER DEFAULT 1"),
        ("users", "daily_hunts", "INTEGER DEFAULT 0"),
        ("users", "daily_hunts_date", "TEXT DEFAULT ''"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    cursor.execute("UPDATE users SET gold = 0 WHERE gold IS NULL")
    cursor.execute("UPDATE users SET kills = 0 WHERE kills IS NULL")
    cursor.execute(
        "UPDATE users SET bag_slots = ? WHERE bag_slots IS NULL",
        (DEFAULT_BAG_SLOTS,),
    )  # ROM 17.8.1.1 PARAMETERIZED BAG DEFAULT

    cursor.execute("""
    UPDATE users
    SET current_location = 'city'
    WHERE current_location IS NULL OR current_location = ''
    """)

    cursor.execute("UPDATE inventory SET quantity = 1 WHERE quantity IS NULL")

    cursor.execute("""
    UPDATE inventory
    SET durability = 100
    WHERE durability IS NULL
      AND item_id IN (
          SELECT id FROM items WHERE category = 'equipment'
      )
    """)

    conn.commit()


# ==============================
# ✅ SEED ITEMS
# ==============================

def seed_items():
    """Seed active consumables only.

    Legacy static equipment 1-26, legacy trash 101-106, and the obsolete
    Rune of Strength definition for ID 301 were retired in ROM 9.0.13b.
    """
    items = [
        (401, "🔴 Мале зілля здоров'я", "potion_hp", "common", "potion", None, 1, 10, 1.00, 0, 0, 0, 0, 0, 0, 0),
        (402, "🔵 Мале зілля мани", "potion_mp", "common", "potion", None, 1, 10, 0.80, 0, 0, 0, 0, 0, 0, 0),
        (403, "🔴 Середнє зілля здоров'я", "potion_hp_medium", "common", "potion", None, 1, 10, 3.00, 0, 0, 0, 0, 0, 0, 0),
        (404, "🔵 Середнє зілля мани", "potion_mp_medium", "common", "potion", None, 1, 10, 2.50, 0, 0, 0, 0, 0, 0, 0),
    ]

    for item in items:
        cursor.execute("""
        INSERT INTO items (
            id, name, type, rarity, category,
            slot_key, weapon_hands,
            max_stack, sell_price,
            bonus_str, bonus_dex, bonus_int, bonus_wis, bonus_sta,
            pdef, mdef
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            type=excluded.type,
            rarity=excluded.rarity,
            category=excluded.category,
            slot_key=excluded.slot_key,
            weapon_hands=excluded.weapon_hands,
            max_stack=excluded.max_stack,
            sell_price=excluded.sell_price,
            bonus_str=excluded.bonus_str,
            bonus_dex=excluded.bonus_dex,
            bonus_int=excluded.bonus_int,
            bonus_wis=excluded.bonus_wis,
            bonus_sta=excluded.bonus_sta,
            pdef=excluded.pdef,
            mdef=excluded.mdef
        """, item)

    conn.commit()
