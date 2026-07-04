import sqlite3
import random

# ==============================
# 🔌 ПІДКЛЮЧЕННЯ ДО БАЗИ
# ==============================

conn = sqlite3.connect("game.db", check_same_thread=False)
cursor = conn.cursor()


# ==============================
# ✅ EQUIPMENT CONFIG
# ==============================

EQUIPMENT_SLOTS = {
    "main_hand": "🗡️ Зброя",
    "off_hand": "🛡️ Друга рука",
    "helmet": "🪖 Голова",
    "shoulders": "🦾 Плечі",
    "chest": "🥋 Тіло",
    "gloves": "🧤 Руки",
    "legs": "👖 Ноги",
    "boots": "👟 Взуття",
    "necklace": "📿 Шия",
    "ring": "💍 Кільце"
}


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


RARITY_REPAIR_MULTIPLIERS = {
    "common": 1.0,
    "uncommon": 2.5,
    "rare": 7.0,
    "epic": 18.0
}


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
        ("users", "bag_slots", "INTEGER DEFAULT 20"),
        ("users", "current_location", "TEXT DEFAULT 'start_path'"),

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

        ("users", "energy", "INTEGER DEFAULT 40"),
        ("users", "last_energy_update", "TEXT DEFAULT ''"),
        ("users", "energy_full_notified", "INTEGER DEFAULT 1"),

        ("users", "last_hp_regen_update", "TEXT DEFAULT ''"),
        ("users", "hp_full_notified", "INTEGER DEFAULT 1"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    cursor.execute("UPDATE users SET gold = 0 WHERE gold IS NULL")
    cursor.execute("UPDATE users SET kills = 0 WHERE kills IS NULL")
    cursor.execute("UPDATE users SET bag_slots = 20 WHERE bag_slots IS NULL")

    cursor.execute("""
    UPDATE users
    SET current_location = 'start_path'
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
    items = [
        (1, "⚪ Старий меч", "weapon", "common", "equipment", "main_hand", 1, 1, 1.00, 1, 0, 0, 0, 0, 0, 0),
        (2, "🟢 Залізний меч", "weapon", "uncommon", "equipment", "main_hand", 1, 1, 3.00, 2, 0, 0, 0, 0, 0, 0),
        (3, "🔵 Меч воїна", "weapon", "rare", "equipment", "main_hand", 1, 1, 8.00, 4, 0, 0, 0, 0, 0, 0),
        (4, "🟣 Епічний клинок", "weapon", "epic", "equipment", "main_hand", 2, 1, 25.00, 7, 0, 0, 0, 0, 0, 0),

        (8, "⚪ Деревʼяний щит", "offhand", "common", "equipment", "off_hand", 1, 1, 1.00, 0, 0, 0, 0, 1, 2, 0),
        (9, "🟢 Малий круглий щит", "offhand", "uncommon", "equipment", "off_hand", 1, 1, 3.00, 0, 0, 0, 0, 2, 4, 0),
        (10, "🔵 Рунічна сфера", "offhand", "rare", "equipment", "off_hand", 1, 1, 8.00, 0, 0, 1, 3, 0, 0, 5),

        (11, "⚪ Старий шолом", "helmet", "common", "equipment", "helmet", 1, 1, 1.00, 0, 0, 0, 0, 1, 2, 0),
        (12, "🟢 Шкіряний капюшон", "helmet", "uncommon", "equipment", "helmet", 1, 1, 3.00, 0, 1, 0, 1, 1, 3, 1),

        (13, "⚪ Потерті наплічники", "shoulders", "common", "equipment", "shoulders", 1, 1, 1.00, 0, 0, 0, 0, 1, 2, 0),
        (14, "🟢 Наплічники слідопита", "shoulders", "uncommon", "equipment", "shoulders", 1, 1, 3.00, 0, 1, 0, 0, 2, 4, 0),

        (5, "⚪ Стара броня", "armor", "common", "equipment", "chest", 1, 1, 1.00, 0, 0, 0, 1, 1, 2, 0),
        (6, "🟢 Шкіряна броня", "armor", "uncommon", "equipment", "chest", 1, 1, 3.00, 0, 1, 0, 2, 2, 4, 1),
        (7, "🔵 Лицарська броня", "armor", "rare", "equipment", "chest", 1, 1, 8.00, 0, 2, 0, 3, 4, 8, 2),

        (15, "⚪ Старі рукавиці", "gloves", "common", "equipment", "gloves", 1, 1, 1.00, 0, 0, 0, 0, 1, 1, 0),
        (16, "🟢 Рукавиці мисливця", "gloves", "uncommon", "equipment", "gloves", 1, 1, 3.00, 1, 1, 0, 0, 1, 2, 0),

        (17, "⚪ Старі поножі", "legs", "common", "equipment", "legs", 1, 1, 1.00, 0, 0, 0, 0, 1, 2, 0),
        (18, "🟢 Шкіряні поножі", "legs", "uncommon", "equipment", "legs", 1, 1, 3.00, 0, 1, 0, 0, 2, 4, 0),

        (19, "⚪ Старі чоботи", "boots", "common", "equipment", "boots", 1, 1, 1.00, 0, 1, 0, 0, 0, 1, 0),
        (20, "🟢 Чоботи слідопита", "boots", "uncommon", "equipment", "boots", 1, 1, 3.00, 0, 2, 0, 0, 1, 2, 0),

        (21, "⚪ Простий амулет", "necklace", "common", "equipment", "necklace", 1, 1, 1.00, 0, 0, 0, 1, 0, 0, 2),
        (22, "🟢 Амулет мудрості", "necklace", "uncommon", "equipment", "necklace", 1, 1, 3.00, 0, 0, 0, 3, 0, 0, 5),
        (23, "🔵 Рунічне намисто", "necklace", "rare", "equipment", "necklace", 1, 1, 8.00, 0, 0, 1, 5, 0, 0, 10),

        (24, "⚪ Мідне кільце", "ring", "common", "equipment", "ring", 1, 1, 1.00, 1, 0, 0, 0, 0, 0, 0),
        (25, "🟢 Перстень спритності", "ring", "uncommon", "equipment", "ring", 1, 1, 3.00, 0, 3, 0, 0, 0, 0, 0),
        (26, "🔵 Перстень сили", "ring", "rare", "equipment", "ring", 1, 1, 8.00, 5, 0, 0, 0, 0, 0, 0),

        (101, "🐾 Густа вовча шкура", "trash", "grey", "trash", None, 1, 20, 0.50, 0, 0, 0, 0, 0, 0, 0),
        (102, "🐗 Жорстка щетина", "trash", "grey", "trash", None, 1, 20, 0.15, 0, 0, 0, 0, 0, 0, 0),
        (103, "🦡 Борсучий жир", "trash", "grey", "trash", None, 1, 20, 0.25, 0, 0, 0, 0, 0, 0, 0),
        (104, "👹 Гоблінська сережка", "trash", "grey", "trash", None, 1, 20, 0.35, 0, 0, 0, 0, 0, 0, 0),
        (105, "🕷️ Липка павутина", "trash", "grey", "trash", None, 1, 20, 0.60, 0, 0, 0, 0, 0, 0, 0),
        (106, "💎 Тріснутий рунічний уламок", "trash", "grey", "trash", None, 1, 20, 0.75, 0, 0, 0, 0, 0, 0, 0),

        (201, "🔴 Мале зілля здоров’я", "potion_hp", "common", "potion", None, 1, 10, 1.00, 0, 0, 0, 0, 0, 0, 0),
        (202, "🔵 Мале зілля мани", "potion_mp", "common", "potion", None, 1, 10, 1.20, 0, 0, 0, 0, 0, 0, 0),
        (203, "🔴 Середнє зілля здоров’я", "potion_hp_medium", "common", "potion", None, 1, 10, 3.00, 0, 0, 0, 0, 0, 0, 0),
        (204, "🔵 Середнє зілля мани", "potion_mp_medium", "common", "potion", None, 1, 10, 3.60, 0, 0, 0, 0, 0, 0, 0),

        (301, "💎 Руна Сили I", "rune_str", "common", "rune", None, 1, 5, 1.00, 1, 0, 0, 0, 0, 0, 0),
    ]

    for item in items:
        cursor.execute("""
        INSERT OR REPLACE INTO items (
            id, name, type, rarity, category,
            slot_key, weapon_hands,
            max_stack, sell_price,
            bonus_str, bonus_dex, bonus_int, bonus_wis, bonus_sta,
            pdef, mdef
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

    ensure_equipment_slots(user_id)
    migrate_legacy_equipment_to_slots(user_id)


# ==============================
# ✅ EQUIPMENT SLOTS CORE
# ==============================

def ensure_equipment_slots(user_id):
    for slot_key in SLOT_ORDER:
        cursor.execute("""
        INSERT OR IGNORE INTO equipment_slots (
            user_id,
            slot_key,
            inventory_id
        )
        VALUES (?, ?, NULL)
        """, (user_id, slot_key))

    conn.commit()


def migrate_legacy_equipment_to_slots(user_id):
    cursor.execute("""
    SELECT equipped_weapon, equipped_armor
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return

    equipped_weapon, equipped_armor = row

    if equipped_weapon:
        cursor.execute("""
        UPDATE equipment_slots
        SET inventory_id=?
        WHERE user_id=? AND slot_key='main_hand'
        """, (equipped_weapon, user_id))

    if equipped_armor:
        cursor.execute("""
        UPDATE equipment_slots
        SET inventory_id=?
        WHERE user_id=? AND slot_key='chest'
        """, (equipped_armor, user_id))

    conn.commit()


def get_equipped_slot(user_id, slot_key):
    ensure_equipment_slots(user_id)

    cursor.execute("""
    SELECT inventory_id
    FROM equipment_slots
    WHERE user_id=? AND slot_key=?
    """, (user_id, slot_key))

    row = cursor.fetchone()

    if not row:
        return None

    return row[0]


def set_equipped_slot(user_id, slot_key, inventory_id):
    ensure_equipment_slots(user_id)

    cursor.execute("""
    UPDATE equipment_slots
    SET inventory_id=?
    WHERE user_id=? AND slot_key=?
    """, (inventory_id, user_id, slot_key))

    if slot_key == "main_hand":
        cursor.execute("""
        UPDATE users
        SET equipped_weapon=?
        WHERE user_id=?
        """, (inventory_id, user_id))

    if slot_key == "chest":
        cursor.execute("""
        UPDATE users
        SET equipped_armor=?
        WHERE user_id=?
        """, (inventory_id, user_id))

    conn.commit()


def unequip_slot(user_id, slot_key):
    ensure_equipment_slots(user_id)

    cursor.execute("""
    UPDATE equipment_slots
    SET inventory_id=NULL
    WHERE user_id=? AND slot_key=?
    """, (user_id, slot_key))

    if slot_key == "main_hand":
        cursor.execute("""
        UPDATE users
        SET equipped_weapon=NULL
        WHERE user_id=?
        """, (user_id,))

    if slot_key == "chest":
        cursor.execute("""
        UPDATE users
        SET equipped_armor=NULL
        WHERE user_id=?
        """, (user_id,))

    conn.commit()


def get_all_equipped_slots(user_id):
    ensure_equipment_slots(user_id)

    cursor.execute("""
    SELECT slot_key, inventory_id
    FROM equipment_slots
    WHERE user_id=?
    """, (user_id,))

    rows = cursor.fetchall()
    result = {}

    for slot_key, inventory_id in rows:
        result[slot_key] = inventory_id

    for slot_key in SLOT_ORDER:
        result.setdefault(slot_key, None)

    return result


def get_all_equipped_items(user_id):
    equipped_slots = get_all_equipped_slots(user_id)
    result = []

    for slot_key in SLOT_ORDER:
        inventory_id = equipped_slots.get(slot_key)

        item = None

        if inventory_id:
            item = get_item_by_inventory_id_full(inventory_id)

        result.append({
            "slot_key": slot_key,
            "slot_name": EQUIPMENT_SLOTS[slot_key],
            "inventory_id": inventory_id,
            "item": item
        })

    return result


def get_equipped_inventory_ids(user_id):
    main_hand = get_equipped_slot(user_id, "main_hand")
    chest = get_equipped_slot(user_id, "chest")
    return main_hand, chest


def is_inventory_item_equipped(user_id, inventory_id):
    equipped_slots = get_all_equipped_slots(user_id)
    return inventory_id in equipped_slots.values()


def find_equipped_slot_by_inventory_id(user_id, inventory_id):
    equipped_slots = get_all_equipped_slots(user_id)

    for slot_key, equipped_inventory_id in equipped_slots.items():
        if equipped_inventory_id == inventory_id:
            return slot_key

    return None


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
        slot_key,
        weapon_hands,
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

    if not row or row[0] is None:
        return 20

    return row[0]


def get_inventory_used_slots(user_id):
    cursor.execute("""
    SELECT COUNT(*)
    FROM inventory
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return 0

    return row[0]


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
        slot_key,
        weapon_hands,
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

    max_stack = max_stack or 1
    capacity = get_bag_capacity(user_id)
    added = 0
    lost = 0

    if max_stack <= 1:
        for _ in range(quantity):
            used = get_inventory_used_slots(user_id)

            if used >= capacity:
                lost += 1
                continue

            durability = 100 if category == "equipment" else None

            cursor.execute("""
            INSERT INTO inventory (user_id, item_id, quantity, durability)
            VALUES (?, ?, ?, ?)
            """, (user_id, item_id, 1, durability))

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

        current_qty = current_qty or 0
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


def get_item_by_inventory_id_full(inventory_id):
    cursor.execute("""
    SELECT
        inventory.id,
        inventory.item_id,
        items.name,
        items.type,
        items.rarity,
        items.category,
        items.slot_key,
        items.weapon_hands,
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


def get_inventory_entry(user_id, inventory_id):
    cursor.execute("""
    SELECT
        inventory.id,
        inventory.item_id,
        items.name,
        items.type,
        items.category,
        inventory.quantity
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.id=? AND inventory.user_id=?
    """, (inventory_id, user_id))

    return cursor.fetchone()


def consume_inventory_item(user_id, inventory_id, quantity=1):
    entry = get_inventory_entry(user_id, inventory_id)

    if not entry:
        return False

    inv_id, item_id, name, type_, category, current_quantity = entry

    if current_quantity is None:
        current_quantity = 1

    if current_quantity < quantity:
        return False

    new_quantity = current_quantity - quantity

    if new_quantity <= 0:
        cursor.execute("""
        DELETE FROM inventory
        WHERE id=? AND user_id=?
        """, (inventory_id, user_id))
    else:
        cursor.execute("""
        UPDATE inventory
        SET quantity=?
        WHERE id=? AND user_id=?
        """, (new_quantity, inventory_id, user_id))

    conn.commit()
    return True


def find_first_item_stack_by_type(user_id, item_type):
    cursor.execute("""
    SELECT inventory.id
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.user_id=?
      AND items.type=?
      AND inventory.quantity > 0
    ORDER BY inventory.id ASC
    LIMIT 1
    """, (user_id, item_type))

    row = cursor.fetchone()

    if not row:
        return None

    return row[0]


# ==============================
# ✅ ITEM LEVEL REQUIREMENT
# ==============================

def get_player_level(user_id):
    cursor.execute("""
    SELECT level
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return 1

    return row[0] or 1


def get_item_required_level_by_inventory_id(inventory_id):
    try:
        init_dynamic_equipment_system()
    except Exception:
        pass

    try:
        cursor.execute("""
        SELECT items.item_level
        FROM inventory
        JOIN items ON inventory.item_id = items.id
        WHERE inventory.id=?
        """, (inventory_id,))

        row = cursor.fetchone()

        if not row:
            return 1

        return row[0] or 1

    except Exception:
        return 1


# ==============================
# ✅ EQUIPMENT
# ==============================

def get_main_hand_item(user_id):
    main_hand_id = get_equipped_slot(user_id, "main_hand")

    if not main_hand_id:
        return None

    return get_item_by_inventory_id_full(main_hand_id)


def is_main_hand_two_handed(user_id):
    item = get_main_hand_item(user_id)

    if not item:
        return False

    weapon_hands = item[7]

    return weapon_hands == 2


def equip_inventory_item(user_id, inventory_id):
    item = get_item_by_inventory_id_full(inventory_id)

    if not item:
        return "❌ Предмет не знайдено"

    (
        inv_id,
        item_id,
        name,
        type_,
        rarity,
        category,
        slot_key,
        weapon_hands,
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

    player_level = get_player_level(user_id)
    required_level = get_item_required_level_by_inventory_id(inventory_id)

    if player_level < required_level:
        return (
            f"🔒 Ти ще не можеш одягти цей предмет.\n\n"
            f"📦 Предмет: {name}\n"
            f"🏷 Потрібний рівень: {required_level}\n"
            f"👤 Твій рівень: {player_level}"
        )

    if not slot_key:
        return "❌ Для цього предмета не вказано слот"

    if slot_key not in EQUIPMENT_SLOTS:
        return "❌ Невідомий слот екіпірування"

    if slot_key == "off_hand" and is_main_hand_two_handed(user_id):
        return "❌ Неможливо: дворучна зброя блокує другу руку"

    if slot_key == "main_hand" and weapon_hands == 2:
        unequip_slot(user_id, "off_hand")

    set_equipped_slot(user_id, slot_key, inventory_id)

    return f"✅ Одягнуто: {name}"


def unequip_inventory_item(user_id, inventory_id):
    slot_key = find_equipped_slot_by_inventory_id(user_id, inventory_id)

    if not slot_key:
        return "❌ Цей предмет не вдягнений"

    unequip_slot(user_id, slot_key)

    return f"✅ Знято зі слота: {EQUIPMENT_SLOTS.get(slot_key, slot_key)}"


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
    equipped_items = get_all_equipped_items(user_id)

    total_str = 0
    total_dex = 0
    total_int = 0
    total_wis = 0
    total_sta = 0

    for equipped in equipped_items:
        item = equipped["item"]

        if not item:
            continue

        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            slot_key,
            weapon_hands,
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

        if durability is not None and durability <= 0:
            continue

        total_str += b_str or 0
        total_dex += b_dex or 0
        total_int += b_int or 0
        total_wis += b_wis or 0
        total_sta += b_sta or 0

    return total_str, total_dex, total_int, total_wis, total_sta


def get_equipped_item_defenses(user_id):
    equipped_items = get_all_equipped_items(user_id)

    total_pdef = 0
    total_mdef = 0

    for equipped in equipped_items:
        item = equipped["item"]

        if not item:
            continue

        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            slot_key,
            weapon_hands,
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

        if durability is not None and durability <= 0:
            continue

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

BASE_EXP_BY_LEVEL = {
    1: 10,
    2: 12,
    3: 15,
    4: 18,
    5: 25,
    6: 30,
    7: 35,
    8: 45,
    9: 60,
    10: 65,
    11: 75,
    12: 85,
    13: 95,
    14: 110,
    15: 120,
    16: 135,
    17: 150,
    18: 170,
    19: 190,
    20: 220,
    21: 240,
    22: 270,
    23: 300,
    24: 340,
    25: 380,
    26: 420,
    27: 460,
    28: 520,
    29: 600,
    30: 600
}


CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL = {
    1: 50,
    2: 150,
    3: 300,
    4: 500,
    5: 1200,
    6: 1800,
    7: 2500,
    8: 3500,
    9: 4500,
    10: 5000,
    11: 5500,
    12: 6000,
    13: 6000,
    14: 6000,
    15: 7000,
    16: 7000,
    17: 7000,
    18: 8000,
    19: 8000,
    20: 8500,
    21: 8500,
    22: 9500,
    23: 9500,
    24: 9500,
    25: 10500,
    26: 10500,
    27: 10500,
    28: 12000,
    29: 12000,
    30: 14000
}


CONTRACT_MOBS_EQUIVALENT = 20


def get_base_exp_for_level(level):
    level = int(level)

    if level in BASE_EXP_BY_LEVEL:
        return BASE_EXP_BY_LEVEL[level]

    if level > 30:
        return int(BASE_EXP_BY_LEVEL[30] * (1.12 ** (level - 30)))

    return BASE_EXP_BY_LEVEL[1]


def get_contract_exp_for_level(level):
    return get_base_exp_for_level(level) * CONTRACT_MOBS_EQUIVALENT


def get_exp_to_next_level(level):
    level = int(level)
    base_exp = get_base_exp_for_level(level)

    if level in CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL:
        mobs_required = CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL[level]
        return int(base_exp * mobs_required)

    mobs_required = int(CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL[30] * (1.10 ** (level - 30)))
    return int(base_exp * mobs_required)


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
# ✅ BUY ITEM FOR GOLD
# ==============================

def buy_item_for_gold(user_id, item_id, price, quantity=1):
    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено"
        }

    gold = row[0] or 0
    total_price = float(price) * quantity

    if gold < total_price:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо золота.\n"
                f"Потрібно: {total_price:.2f}\n"
                f"У тебе: {gold:.2f}"
            )
        }

    add_result = add_item(user_id, item_id, quantity)

    added = add_result.get("added", 0)
    lost = add_result.get("lost", 0)
    name = add_result.get("name", "Предмет")

    if added <= 0:
        return {
            "success": False,
            "message": "🎒 Сумка переповнена. Предмет не куплено."
        }

    actual_price = float(price) * added

    cursor.execute("""
    UPDATE users
    SET gold = gold - ?
    WHERE user_id=?
    """, (actual_price, user_id))

    conn.commit()

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    new_gold_row = cursor.fetchone()
    new_gold = new_gold_row[0] if new_gold_row else 0

    message = (
        f"✅ Куплено: {name} x{added}\n"
        f"🪙 Витрачено: {actual_price:.2f}\n"
        f"🪙 Залишилось золота: {new_gold:.2f}"
    )

    if lost > 0:
        message += f"\n⚠️ Не влізло в сумку: x{lost}"

    return {
        "success": True,
        "message": message,
        "added": added,
        "lost": lost,
        "gold_left": new_gold
    }


# ==============================
# ✅ BLACKSMITH / REPAIR SYSTEM
# ==============================

def get_rarity_repair_multiplier(rarity):
    return RARITY_REPAIR_MULTIPLIERS.get(rarity, 1.0)


def calculate_repair_cost(durability, rarity):
    if durability is None:
        durability = 100

    durability = max(0, min(100, durability))

    if durability >= 100:
        return 0.0

    multiplier = get_rarity_repair_multiplier(rarity)

    return round((100 - durability) * multiplier * 0.05, 2)


def get_equipped_items_for_repair(user_id):
    equipped_items = get_all_equipped_items(user_id)
    result = []

    for equipped in equipped_items:
        slot_key = equipped["slot_key"]
        slot_name = equipped["slot_name"]
        inventory_id = equipped["inventory_id"]
        item = equipped["item"]

        if not inventory_id:
            result.append({
                "slot": slot_name,
                "slot_key": slot_key,
                "inventory_id": None,
                "name": "Порожньо",
                "rarity": None,
                "durability": None,
                "repair_cost": 0.0,
                "is_broken": False
            })
            continue

        if not item:
            result.append({
                "slot": slot_name,
                "slot_key": slot_key,
                "inventory_id": inventory_id,
                "name": "Предмет не знайдено",
                "rarity": None,
                "durability": None,
                "repair_cost": 0.0,
                "is_broken": False
            })
            continue

        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            item_slot_key,
            weapon_hands,
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

        if durability is None:
            durability = 100

        repair_cost = calculate_repair_cost(durability, rarity)

        result.append({
            "slot": slot_name,
            "slot_key": slot_key,
            "inventory_id": inv_id,
            "name": name,
            "rarity": rarity,
            "durability": durability,
            "repair_cost": repair_cost,
            "is_broken": durability <= 0
        })

    return result


def get_total_repair_cost(user_id):
    equipped_items = get_equipped_items_for_repair(user_id)
    total = 0.0

    for item in equipped_items:
        total += item["repair_cost"]

    return round(total, 2)


def repair_equipped_item(user_id, inventory_id):
    if not is_inventory_item_equipped(user_id, inventory_id):
        return {
            "success": False,
            "message": "❌ Цей предмет не вдягнений."
        }

    item = get_item_by_inventory_id_full(inventory_id)

    if not item:
        return {
            "success": False,
            "message": "❌ Предмет не знайдено."
        }

    (
        inv_id,
        item_id,
        name,
        type_,
        rarity,
        category,
        slot_key,
        weapon_hands,
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
        return {
            "success": False,
            "message": "❌ Цей предмет не є спорядженням."
        }

    if durability is None:
        durability = 100

    repair_cost = calculate_repair_cost(durability, rarity)

    if repair_cost <= 0:
        return {
            "success": False,
            "message": f"🛠️ {name} вже має повну міцність."
        }

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено."
        }

    gold = row[0] or 0.0

    if gold < repair_cost:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо золота для ремонту.\n\n"
                f"📦 Предмет: {name}\n"
                f"💳 Потрібно: {repair_cost:.2f} 🪙\n"
                f"💰 У тебе: {gold:.2f} 🪙"
            )
        }

    cursor.execute("""
    UPDATE inventory
    SET durability=100
    WHERE id=?
    """, (inventory_id,))

    cursor.execute("""
    UPDATE users
    SET gold = gold - ?
    WHERE user_id=?
    """, (repair_cost, user_id))

    conn.commit()

    return {
        "success": True,
        "message": (
            f"✅ Предмет відремонтовано.\n\n"
            f"📦 {name}\n"
            f"🛠️ Міцність: {durability}/100 → 100/100\n"
            f"💳 Сплачено: {repair_cost:.2f} 🪙"
        ),
        "repair_cost": repair_cost
    }


def repair_all_equipped(user_id):
    equipped_items = get_equipped_items_for_repair(user_id)
    total_cost = get_total_repair_cost(user_id)

    if total_cost <= 0:
        return {
            "success": False,
            "message": "🛠️ Усе спорядження вже має повну міцність.",
            "total_cost": 0.0
        }

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено.",
            "total_cost": total_cost
        }

    gold = row[0] or 0.0

    if gold < total_cost:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо золота для повного ремонту.\n\n"
                f"💳 Потрібно: {total_cost:.2f} 🪙\n"
                f"💰 У тебе: {gold:.2f} 🪙\n\n"
                f"ℹ️ Можеш відремонтувати окремі речі нижче."
            ),
            "total_cost": total_cost
        }

    repaired_count = 0

    for item in equipped_items:
        inventory_id = item["inventory_id"]

        if not inventory_id:
            continue

        if item["repair_cost"] <= 0:
            continue

        cursor.execute("""
        UPDATE inventory
        SET durability=100
        WHERE id=?
        """, (inventory_id,))

        repaired_count += 1

    cursor.execute("""
    UPDATE users
    SET gold = gold - ?
    WHERE user_id=?
    """, (total_cost, user_id))

    conn.commit()

    return {
        "success": True,
        "message": (
            f"✅ Спорядження відремонтовано.\n"
            f"🛠️ Відремонтовано речей: {repaired_count}\n"
            f"💳 Сплачено: {total_cost:.2f} 🪙"
        ),
        "total_cost": total_cost,
        "repaired_count": repaired_count
    }


def damage_equipped_items_on_death(user_id, amount=5):
    equipped_items = get_all_equipped_items(user_id)
    damaged = []

    for equipped in equipped_items:
        inventory_id = equipped["inventory_id"]
        item = equipped["item"]

        if not inventory_id or not item:
            continue

        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            slot_key,
            weapon_hands,
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

        if durability is None:
            durability = 100

        new_durability = max(0, durability - amount)

        cursor.execute("""
        UPDATE inventory
        SET durability=?
        WHERE id=?
        """, (new_durability, inventory_id))

        damaged.append({
            "name": name,
            "old": durability,
            "new": new_durability,
            "broken": new_durability <= 0
        })

    conn.commit()

    return damaged


# ==============================
# ✅ NATURAL DURABILITY WEAR ON VICTORY
# ==============================

def apply_random_durability_wear_on_victory(user_id, chance_percent=25):
    roll = random.randint(1, 100)

    if roll > chance_percent:
        return {
            "triggered": False,
            "message": None
        }

    equipped_items = get_all_equipped_items(user_id)
    candidates = []

    for equipped in equipped_items:
        inventory_id = equipped["inventory_id"]
        item = equipped["item"]
        slot_name = equipped["slot_name"]

        if not inventory_id or not item:
            continue

        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            slot_key,
            weapon_hands,
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
            continue

        if durability is None:
            durability = 100

        if durability <= 1:
            continue

        candidates.append({
            "inventory_id": inventory_id,
            "slot_name": slot_name,
            "name": name,
            "old_durability": durability
        })

    if not candidates:
        return {
            "triggered": False,
            "message": None
        }

    selected = random.choice(candidates)

    old_durability = selected["old_durability"]
    new_durability = max(1, old_durability - 1)

    cursor.execute("""
    UPDATE inventory
    SET durability=?
    WHERE id=?
    """, (new_durability, selected["inventory_id"]))

    conn.commit()

    return {
        "triggered": True,
        "slot_name": selected["slot_name"],
        "name": selected["name"],
        "old_durability": old_durability,
        "new_durability": new_durability,
        "message": (
            f"🧱 Знос спорядження:\n"
            f"• {selected['slot_name']}: {selected['name']} "
            f"{old_durability} → {new_durability}/100"
        )
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
# ✅ DYNAMIC EQUIPMENT GENERATOR
# ==============================

DYNAMIC_RARITY_ICONS = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣"
}


DYNAMIC_RARITY_NAMES = {
    "common": "Звичайний",
    "uncommon": "Незвичайний",
    "rare": "Рідкісний",
    "epic": "Епічний"
}


DYNAMIC_STAT_MULTIPLIERS = {
    "common": 1.0,
    "uncommon": 1.35,
    "rare": 1.85,
    "epic": 2.60
}


DYNAMIC_SELL_MULTIPLIERS = {
    "common": 0.30,
    "uncommon": 0.90,
    "rare": 2.25,
    "epic": 6.00
}


DYNAMIC_SLOT_NAMES = {
    "main_hand": "Зброя",
    "off_hand": "Друга рука",
    "helmet": "Шолом",
    "shoulders": "Наплічники",
    "chest": "Обладунок",
    "gloves": "Рукавиці",
    "legs": "Поножі",
    "boots": "Чоботи",
    "necklace": "Амулет",
    "ring": "Кільце"
}


def init_dynamic_equipment_system():
    migrations = [
        ("items", "item_level", "INTEGER DEFAULT 1"),
        ("items", "is_generated", "INTEGER DEFAULT 0"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()


def get_dynamic_slot_key():
    return random.choice(SLOT_ORDER)


def get_dynamic_stat_value(item_level, rarity, base=1.0):
    multiplier = DYNAMIC_STAT_MULTIPLIERS.get(rarity, 1.0)
    value = int(round(item_level * base * multiplier))

    return max(1, value)


def get_dynamic_sell_price(item_level, rarity):
    multiplier = DYNAMIC_SELL_MULTIPLIERS.get(rarity, 0.30)

    return round(max(0.10, item_level * multiplier), 2)


def get_dynamic_weapon_name(slot_key, rarity, weapon_hands):
    icon = DYNAMIC_RARITY_ICONS.get(rarity, "⚪")

    if slot_key == "main_hand":
        variants_1h = [
            "Одноручний меч",
            "Одноручний посох"
        ]

        variants_2h = [
            "Дворучний меч",
            "Дворучний посох",
            "Лук",
            "Арбалет"
        ]

        if weapon_hands == 2:
            base_name = random.choice(variants_2h)
        else:
            base_name = random.choice(variants_1h)

        return f"{icon} {base_name}"

    if slot_key == "off_hand":
        variants = [
            "Щит",
            "Магічний талісман",
            "Кинджал для другої руки"
        ]

        return f"{icon} {random.choice(variants)}"

    return f"{icon} Зброя"


def get_dynamic_armor_name(slot_key, rarity):
    icon = DYNAMIC_RARITY_ICONS.get(rarity, "⚪")
    base_name = DYNAMIC_SLOT_NAMES.get(slot_key, "Річ")

    return f"{icon} {base_name}"


def generate_dynamic_equipment_stats(slot_key, item_level, rarity, weapon_hands=1):
    b_str = 0
    b_dex = 0
    b_int = 0
    b_wis = 0
    b_sta = 0
    pdef = 0
    mdef = 0

    if slot_key == "main_hand":
        if random.random() < 0.55:
            b_str = get_dynamic_stat_value(item_level, rarity, 1.00)

            if weapon_hands == 2:
                b_str = int(round(b_str * 1.35))
        else:
            b_int = get_dynamic_stat_value(item_level, rarity, 1.00)

            if weapon_hands == 2:
                b_int = int(round(b_int * 1.35))

    elif slot_key == "off_hand":
        choice = random.choice(["shield", "talisman", "dagger"])

        if choice == "shield":
            pdef = get_dynamic_stat_value(item_level, rarity, 1.30)
            b_sta = get_dynamic_stat_value(item_level, rarity, 0.45)

        elif choice == "talisman":
            mdef = get_dynamic_stat_value(item_level, rarity, 1.30)
            b_wis = get_dynamic_stat_value(item_level, rarity, 0.55)

        else:
            b_dex = get_dynamic_stat_value(item_level, rarity, 0.90)

    elif slot_key == "helmet":
        pdef = get_dynamic_stat_value(item_level, rarity, 0.80)
        mdef = get_dynamic_stat_value(item_level, rarity, 0.40)

        bonus = random.choice(["sta", "wis", "dex"])
        value = get_dynamic_stat_value(item_level, rarity, 0.25)

        if bonus == "sta":
            b_sta += value
        elif bonus == "wis":
            b_wis += value
        else:
            b_dex += value

    elif slot_key == "shoulders":
        pdef = get_dynamic_stat_value(item_level, rarity, 1.00)
        mdef = get_dynamic_stat_value(item_level, rarity, 0.25)

    elif slot_key == "chest":
        pdef = get_dynamic_stat_value(item_level, rarity, 1.60)
        mdef = get_dynamic_stat_value(item_level, rarity, 0.35)
        b_sta = get_dynamic_stat_value(item_level, rarity, 0.55)

    elif slot_key == "gloves":
        pdef = get_dynamic_stat_value(item_level, rarity, 0.55)
        mdef = get_dynamic_stat_value(item_level, rarity, 0.20)
        b_dex = get_dynamic_stat_value(item_level, rarity, 0.60)

    elif slot_key == "legs":
        pdef = get_dynamic_stat_value(item_level, rarity, 1.20)
        mdef = get_dynamic_stat_value(item_level, rarity, 0.30)
        b_sta = get_dynamic_stat_value(item_level, rarity, 0.45)

    elif slot_key == "boots":
        pdef = get_dynamic_stat_value(item_level, rarity, 0.45)
        mdef = get_dynamic_stat_value(item_level, rarity, 0.20)
        b_dex = get_dynamic_stat_value(item_level, rarity, 0.80)

    elif slot_key == "necklace":
        mdef = get_dynamic_stat_value(item_level, rarity, 1.30)
        b_wis = get_dynamic_stat_value(item_level, rarity, 0.80)

    elif slot_key == "ring":
        stat_choice = random.choice(["str", "dex", "int", "wis", "sta"])
        value = get_dynamic_stat_value(item_level, rarity, 0.90)

        if stat_choice == "str":
            b_str = value
        elif stat_choice == "dex":
            b_dex = value
        elif stat_choice == "int":
            b_int = value
        elif stat_choice == "wis":
            b_wis = value
        elif stat_choice == "sta":
            b_sta = value

    if rarity in ["uncommon", "rare", "epic"]:
        bonus_count = 1
        min_bonus = 2

        if rarity == "rare":
            bonus_count = 2
            min_bonus = 3

        if rarity == "epic":
            bonus_count = 3
            min_bonus = 4

        for _ in range(bonus_count):
            bonus_type = random.choice(["str", "dex", "int", "wis", "sta"])

            bonus_value = get_dynamic_stat_value(item_level, rarity, 0.30)
            bonus_value = max(min_bonus, bonus_value)

            if bonus_type == "str":
                b_str += bonus_value
            elif bonus_type == "dex":
                b_dex += bonus_value
            elif bonus_type == "int":
                b_int += bonus_value
            elif bonus_type == "wis":
                b_wis += bonus_value
            elif bonus_type == "sta":
                b_sta += bonus_value

    return {
        "bonus_str": b_str,
        "bonus_dex": b_dex,
        "bonus_int": b_int,
        "bonus_wis": b_wis,
        "bonus_sta": b_sta,
        "pdef": pdef,
        "mdef": mdef
    }


def create_generated_equipment_item(user_id, item_level, rarity):
    init_dynamic_equipment_system()

    item_level = int(item_level)
    item_level = max(1, item_level)

    if rarity not in ["common", "uncommon", "rare", "epic"]:
        rarity = "common"

    capacity = get_bag_capacity(user_id)
    used_slots = get_inventory_used_slots(user_id)

    if used_slots >= capacity:
        return {
            "success": False,
            "lost": 1,
            "message": "🎒 Сумка переповнена. Екіпірування не влізло."
        }

    slot_key = get_dynamic_slot_key()
    weapon_hands = 1

    if slot_key == "main_hand":
        weapon_hands = 2 if random.random() < 0.45 else 1
        name = get_dynamic_weapon_name(slot_key, rarity, weapon_hands)
        type_ = "weapon"

    elif slot_key == "off_hand":
        name = get_dynamic_weapon_name(slot_key, rarity, weapon_hands)
        type_ = "offhand"

    else:
        name = get_dynamic_armor_name(slot_key, rarity)
        type_ = slot_key

    rarity_name = DYNAMIC_RARITY_NAMES.get(rarity, "Звичайний")
    name = f"{name} {item_level} рівня"

    stats = generate_dynamic_equipment_stats(
        slot_key=slot_key,
        item_level=item_level,
        rarity=rarity,
        weapon_hands=weapon_hands
    )

    sell_price = get_dynamic_sell_price(item_level, rarity)

    cursor.execute("""
    INSERT INTO items (
        name,
        type,
        rarity,
        category,
        slot_key,
        weapon_hands,
        max_stack,
        sell_price,
        bonus_str,
        bonus_dex,
        bonus_int,
        bonus_wis,
        bonus_sta,
        pdef,
        mdef,
        item_level,
        is_generated
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        type_,
        rarity,
        "equipment",
        slot_key,
        weapon_hands,
        1,
        sell_price,
        stats["bonus_str"],
        stats["bonus_dex"],
        stats["bonus_int"],
        stats["bonus_wis"],
        stats["bonus_sta"],
        stats["pdef"],
        stats["mdef"],
        item_level,
        1
    ))

    item_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO inventory (
        user_id,
        item_id,
        quantity,
        durability
    )
    VALUES (?, ?, ?, ?)
    """, (
        user_id,
        item_id,
        1,
        100
    ))

    inventory_id = cursor.lastrowid

    conn.commit()

    return {
        "success": True,
        "lost": 0,
        "name": name,
        "rarity": rarity,
        "rarity_name": rarity_name,
        "slot_key": slot_key,
        "item_id": item_id,
        "inventory_id": inventory_id,
        "message": f"{name}"
    }


# ==============================
# ✅ COMMON EQUIPMENT TRADER SHOP
# ==============================

COMMON_SHOP_PRICE_MULTIPLIERS = {
    "main_hand": 3.0,
    "off_hand": 2.5,
    "helmet": 1.5,
    "shoulders": 1.5,
    "chest": 2.5,
    "gloves": 1.3,
    "legs": 1.8,
    "boots": 1.3,
    "necklace": 2.0,
    "ring": 2.0
}


def get_common_equipment_price_for_slot(item_level, slot_key):
    multiplier = COMMON_SHOP_PRICE_MULTIPLIERS.get(slot_key, 1.5)

    return round(max(1.0, item_level * multiplier), 2)


def create_generated_equipment_item_for_slot(user_id, item_level, rarity, slot_key):
    init_dynamic_equipment_system()

    if slot_key not in SLOT_ORDER:
        return {
            "success": False,
            "message": "❌ Невідомий слот спорядження."
        }

    item_level = int(item_level)
    item_level = max(1, item_level)

    if rarity not in ["common", "uncommon", "rare", "epic"]:
        rarity = "common"

    capacity = get_bag_capacity(user_id)
    used_slots = get_inventory_used_slots(user_id)

    if used_slots >= capacity:
        return {
            "success": False,
            "lost": 1,
            "message": "🎒 Сумка переповнена. Предмет не куплено."
        }

    weapon_hands = 1

    if slot_key == "main_hand":
        weapon_hands = 2 if random.random() < 0.35 else 1
        name = get_dynamic_weapon_name(slot_key, rarity, weapon_hands)
        type_ = "weapon"

    elif slot_key == "off_hand":
        weapon_hands = 1
        name = get_dynamic_weapon_name(slot_key, rarity, weapon_hands)
        type_ = "offhand"

    else:
        weapon_hands = 1
        name = get_dynamic_armor_name(slot_key, rarity)
        type_ = slot_key

    name = f"{name} {item_level} рівня"

    stats = generate_dynamic_equipment_stats(
        slot_key=slot_key,
        item_level=item_level,
        rarity=rarity,
        weapon_hands=weapon_hands
    )

    sell_price = get_dynamic_sell_price(item_level, rarity)

    cursor.execute("""
    INSERT INTO items (
        name,
        type,
        rarity,
        category,
        slot_key,
        weapon_hands,
        max_stack,
        sell_price,
        bonus_str,
        bonus_dex,
        bonus_int,
        bonus_wis,
        bonus_sta,
        pdef,
        mdef,
        item_level,
        is_generated
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        type_,
        rarity,
        "equipment",
        slot_key,
        weapon_hands,
        1,
        sell_price,
        stats["bonus_str"],
        stats["bonus_dex"],
        stats["bonus_int"],
        stats["bonus_wis"],
        stats["bonus_sta"],
        stats["pdef"],
        stats["mdef"],
        item_level,
        1
    ))

    item_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO inventory (
        user_id,
        item_id,
        quantity,
        durability
    )
    VALUES (?, ?, ?, ?)
    """, (
        user_id,
        item_id,
        1,
        100
    ))

    inventory_id = cursor.lastrowid

    conn.commit()

    return {
        "success": True,
        "name": name,
        "item_id": item_id,
        "inventory_id": inventory_id,
        "slot_key": slot_key,
        "item_level": item_level
    }


def get_common_equipment_shop_offer(user_id):
    player_level = get_player_level(user_id)
    offers = []

    for slot_key in SLOT_ORDER:
        slot_name = EQUIPMENT_SLOTS.get(slot_key, slot_key)
        price = get_common_equipment_price_for_slot(player_level, slot_key)

        offers.append({
            "slot_key": slot_key,
            "slot_name": slot_name,
            "item_level": player_level,
            "price": price
        })

    return offers


def buy_common_equipment_from_trader(user_id, slot_key):
    if slot_key not in SLOT_ORDER:
        return {
            "success": False,
            "message": "❌ Невідомий слот спорядження."
        }

    player_level = get_player_level(user_id)
    price = get_common_equipment_price_for_slot(player_level, slot_key)

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено."
        }

    gold = row[0] or 0.0

    if gold < price:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо золота.\n\n"
                f"💳 Потрібно: {price:.2f} 🪙\n"
                f"💰 У тебе: {gold:.2f} 🪙"
            )
        }

    result = create_generated_equipment_item_for_slot(
        user_id=user_id,
        item_level=player_level,
        rarity="common",
        slot_key=slot_key
    )

    if not result.get("success"):
        return result

    cursor.execute("""
    UPDATE users
    SET gold = gold - ?
    WHERE user_id=?
    """, (price, user_id))

    conn.commit()

    return {
        "success": True,
        "message": (
            f"✅ Куплено базове спорядження.\n\n"
            f"📦 {result['name']}\n"
            f"🏷 Рівень предмета: {player_level}\n"
            f"💳 Сплачено: {price:.2f} 🪙"
        )
    }


# ==============================
# ✅ SELL EQUIPMENT TO TRADER
# ==============================

def get_sellable_equipment_items(user_id):
    equipped_slots = get_all_equipped_slots(user_id)
    equipped_inventory_ids = set()

    for slot_key, inventory_id in equipped_slots.items():
        if inventory_id:
            equipped_inventory_ids.add(inventory_id)

    cursor.execute("""
    SELECT
        inventory.id,
        inventory.item_id,
        items.name,
        items.type,
        items.rarity,
        items.category,
        items.slot_key,
        items.weapon_hands,
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
      AND items.category='equipment'
    ORDER BY inventory.id ASC
    """, (user_id,))

    rows = cursor.fetchall()
    result = []

    for row in rows:
        inventory_id = row[0]

        if inventory_id in equipped_inventory_ids:
            continue

        result.append(row)

    return result


def sell_inventory_item_to_trader(user_id, inventory_id):
    if is_inventory_item_equipped(user_id, inventory_id):
        return {
            "success": False,
            "message": (
                "❌ Неможливо продати вдягнений предмет.\n\n"
                "Спочатку зніми його з персонажа."
            )
        }

    cursor.execute("""
    SELECT
        inventory.id,
        inventory.item_id,
        items.name,
        items.category,
        inventory.quantity,
        items.sell_price
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.id=? AND inventory.user_id=?
    """, (inventory_id, user_id))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Предмет не знайдено в інвентарі."
        }

    inv_id, item_id, name, category, quantity, sell_price = row

    quantity = quantity or 1
    sell_price = sell_price or 0

    if category != "equipment":
        return {
            "success": False,
            "message": "❌ Через це меню можна продавати тільки спорядження."
        }

    if sell_price <= 0:
        return {
            "success": False,
            "message": "❌ Цей предмет не має ціни продажу."
        }

    total_gold = round(quantity * sell_price, 2)

    cursor.execute("""
    DELETE FROM inventory
    WHERE id=? AND user_id=?
    """, (inventory_id, user_id))

    cursor.execute("""
    UPDATE users
    SET gold = gold + ?
    WHERE user_id=?
    """, (total_gold, user_id))

    conn.commit()

    return {
        "success": True,
        "message": (
            f"🪙 Спорядження продано торговцю.\n\n"
            f"📦 {name} x{quantity}\n"
            f"💰 Отримано: {total_gold:.2f} 🪙"
        ),
        "gold_earned": total_gold
    }


# ==============================
# ✅ MERCENARY CONTRACTS SYSTEM
# ==============================

CONTRACTS_UNLOCK_LEVEL = 5
DAILY_CONTRACT_LIMIT = 5
CONTRACT_TARGET_KILLS = 10
CONTRACT_MOBS_EQUIVALENT = 20


def get_today_str():
    from datetime import date
    return date.today().isoformat()


def init_contract_system():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_active_contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        created_date TEXT,
        player_level INTEGER,

        target_mob_name TEXT,
        target_mob_level INTEGER,

        target_min_level INTEGER,
        target_max_level INTEGER,

        target_kills INTEGER,
        current_kills INTEGER,
        reward_exp INTEGER,

        completed INTEGER DEFAULT 0,
        reward_claimed INTEGER DEFAULT 0
    )
    """)

    migrations = [
        ("users", "daily_contracts_completed", "INTEGER DEFAULT 0"),
        ("users", "daily_contract_date", "TEXT DEFAULT ''"),

        ("user_active_contracts", "target_mob_name", "TEXT DEFAULT ''"),
        ("user_active_contracts", "target_mob_level", "INTEGER DEFAULT 0"),
        ("user_active_contracts", "target_min_level", "INTEGER DEFAULT 0"),
        ("user_active_contracts", "target_max_level", "INTEGER DEFAULT 0"),
        ("user_active_contracts", "completed", "INTEGER DEFAULT 0"),
        ("user_active_contracts", "reward_claimed", "INTEGER DEFAULT 0"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    try:
        cursor.execute("""
        DELETE FROM user_active_contracts
        WHERE target_mob_name IS NULL OR target_mob_name = ''
        """)
    except Exception:
        pass

    conn.commit()


def reset_daily_contracts_if_needed(user_id):
    init_contract_system()

    today = get_today_str()

    cursor.execute("""
    SELECT daily_contract_date
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return

    current_date = row[0] or ""

    if current_date != today:
        cursor.execute("""
        UPDATE users
        SET daily_contracts_completed=0,
            daily_contract_date=?
        WHERE user_id=?
        """, (today, user_id))

        cursor.execute("""
        DELETE FROM user_active_contracts
        WHERE user_id=?
        """, (user_id,))

        conn.commit()


def get_active_contract(user_id):
    reset_daily_contracts_if_needed(user_id)

    cursor.execute("""
    SELECT
        id,
        user_id,
        created_date,
        player_level,
        target_mob_name,
        target_mob_level,
        target_min_level,
        target_max_level,
        target_kills,
        current_kills,
        reward_exp,
        completed,
        reward_claimed
    FROM user_active_contracts
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 1
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return None

    (
        contract_id,
        row_user_id,
        created_date,
        player_level,
        target_mob_name,
        target_mob_level,
        target_min_level,
        target_max_level,
        target_kills,
        current_kills,
        reward_exp,
        completed,
        reward_claimed
    ) = row

    if not target_mob_name:
        return None

    return {
        "id": contract_id,
        "user_id": row_user_id,
        "created_date": created_date,
        "player_level": player_level,
        "target_mob_name": target_mob_name,
        "target_mob_level": target_mob_level,
        "target_min_level": target_min_level,
        "target_max_level": target_max_level,
        "target_kills": target_kills,
        "current_kills": current_kills,
        "reward_exp": reward_exp,
        "completed": bool(completed),
        "reward_claimed": bool(reward_claimed)
    }


def get_contract_status(user_id):
    reset_daily_contracts_if_needed(user_id)

    cursor.execute("""
    SELECT level, daily_contracts_completed
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "exists": False,
            "message": "❌ Персонажа не знайдено"
        }

    level, completed_today = row
    completed_today = completed_today or 0

    active_contract = get_active_contract(user_id)

    return {
        "exists": True,
        "level": level,
        "unlocked": level >= CONTRACTS_UNLOCK_LEVEL,
        "completed_today": completed_today,
        "daily_limit": DAILY_CONTRACT_LIMIT,
        "active_contract": active_contract
    }


def create_daily_contract(
    user_id,
    target_mob_name,
    target_mob_level,
    target_kills=CONTRACT_TARGET_KILLS
):
    reset_daily_contracts_if_needed(user_id)

    status = get_contract_status(user_id)

    if not status["exists"]:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено"
        }

    level = status["level"]

    if level < CONTRACTS_UNLOCK_LEVEL:
        return {
            "success": False,
            "message": (
                f"🔒 Контракти відкриються з {CONTRACTS_UNLOCK_LEVEL} рівня.\n"
                f"Твій рівень: {level}"
            )
        }

    if status["completed_today"] >= DAILY_CONTRACT_LIMIT:
        return {
            "success": False,
            "message": (
                f"📜 Ліміт контрактів на сьогодні виконано.\n"
                f"✅ Виконано: {status['completed_today']}/{DAILY_CONTRACT_LIMIT}"
            )
        }

    if status["active_contract"]:
        active = status["active_contract"]

        if active.get("completed"):
            return {
                "success": False,
                "message": (
                    "📜 У тебе вже є виконаний контракт.\n\n"
                    "Повернися до Гільдії Найманців і здай його, "
                    "щоб отримати нагороду."
                )
            }

        return {
            "success": False,
            "message": "📜 У тебе вже є активний контракт."
        }

    reward_exp = get_contract_exp_for_level(level)

    target_min_level = max(1, level - 1)
    target_max_level = level + 1

    cursor.execute("""
    INSERT INTO user_active_contracts (
        user_id,
        created_date,
        player_level,
        target_mob_name,
        target_mob_level,
        target_min_level,
        target_max_level,
        target_kills,
        current_kills,
        reward_exp,
        completed,
        reward_claimed
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        get_today_str(),
        level,
        target_mob_name,
        int(target_mob_level),
        target_min_level,
        target_max_level,
        int(target_kills),
        0,
        reward_exp,
        0,
        0
    ))

    conn.commit()

    return {
        "success": True,
        "message": (
            f"📜 Контракт прийнято!\n\n"
            f"🎯 Завдання:\n"
            f"Вбий {target_kills} × {target_mob_name} "
            f"(рівень {target_mob_level}).\n\n"
            f"✨ Нагорода після здачі: {reward_exp} EXP"
        )
    }


def abandon_active_contract(user_id):
    reset_daily_contracts_if_needed(user_id)

    active_contract = get_active_contract(user_id)

    if not active_contract:
        return {
            "success": False,
            "message": "📜 У тебе немає активного контракту."
        }

    cursor.execute("""
    DELETE FROM user_active_contracts
    WHERE user_id=?
    """, (user_id,))

    conn.commit()

    return {
        "success": True,
        "message": "📜 Активний контракт скасовано."
    }


def process_contract_progress_on_kill(user_id, mob):
    reset_daily_contracts_if_needed(user_id)

    active_contract = get_active_contract(user_id)

    if not active_contract:
        return {
            "updated": False,
            "completed": False,
            "message": None
        }

    if active_contract.get("reward_claimed"):
        return {
            "updated": False,
            "completed": False,
            "message": None
        }

    if active_contract.get("completed"):
        return {
            "updated": False,
            "completed": True,
            "message": None
        }

    mob_name = mob.get("name", "")
    mob_base_name = mob.get("base_name", mob_name)
    mob_level = int(mob.get("level", active_contract["target_mob_level"]))

    target_name = active_contract["target_mob_name"]
    target_level = int(active_contract["target_mob_level"])

    if mob_base_name != target_name or mob_level != target_level:
        return {
            "updated": False,
            "completed": False,
            "message": None
        }

    new_progress = active_contract["current_kills"] + 1

    if new_progress >= active_contract["target_kills"]:
        cursor.execute("""
        UPDATE user_active_contracts
        SET current_kills=?,
            completed=1
        WHERE id=?
        """, (
            active_contract["target_kills"],
            active_contract["id"]
        ))

        conn.commit()

        return {
            "updated": True,
            "completed": True,
            "message": (
                f"📜 Контракт виконано!\n"
                f"🎯 Ціль: {target_name}\n"
                f"✅ Прогрес: {active_contract['target_kills']}/{active_contract['target_kills']}\n"
                f"🏛️ Поверніться до Гільдії Найманців, щоб здати контракт і отримати нагороду."
            )
        }

    cursor.execute("""
    UPDATE user_active_contracts
    SET current_kills=?
    WHERE id=?
    """, (new_progress, active_contract["id"]))

    conn.commit()

    elite_note = ""

    if mob.get("is_elite"):
        elite_note = " ⭐ Елітна ціль зарахована!"

    return {
        "updated": True,
        "completed": False,
        "message": (
            f"📜 Контракт: {target_name} "
            f"{new_progress}/{active_contract['target_kills']}"
            f"{elite_note}"
        )
    }


def claim_contract_reward(user_id):
    reset_daily_contracts_if_needed(user_id)

    active_contract = get_active_contract(user_id)

    if not active_contract:
        return {
            "success": False,
            "message": "📜 У тебе немає контракту для здачі."
        }

    if not active_contract.get("completed"):
        return {
            "success": False,
            "message": (
                "❌ Контракт ще не виконано.\n\n"
                f"🎯 Ціль: {active_contract['target_mob_name']}\n"
                f"📈 Прогрес: {active_contract['current_kills']}/{active_contract['target_kills']}"
            )
        }

    if active_contract.get("reward_claimed"):
        return {
            "success": False,
            "message": "✅ Нагороду за цей контракт уже отримано."
        }

    reward_exp = active_contract["reward_exp"]

    exp_result = add_exp(user_id, reward_exp)

    cursor.execute("""
    UPDATE users
    SET daily_contracts_completed = daily_contracts_completed + 1
    WHERE user_id=?
    """, (user_id,))

    cursor.execute("""
    UPDATE user_active_contracts
    SET reward_claimed=1
    WHERE id=?
    """, (active_contract["id"],))

    cursor.execute("""
    DELETE FROM user_active_contracts
    WHERE id=?
    """, (active_contract["id"],))

    conn.commit()

    message = (
        f"🎁 Контракт здано!\n\n"
        f"🎯 Ціль: {active_contract['target_mob_name']}\n"
        f"✨ Нагорода: +{reward_exp} EXP"
    )

    if exp_result and exp_result.get("level_ups", 0) > 0:
        message += f"\n🏆 Новий рівень: {exp_result['level']}!"

    return {
        "success": True,
        "message": message,
        "reward_exp": reward_exp,
        "exp_result": exp_result
    }

# ==============================
# ✅ ENERGY SYSTEM
# ==============================

ENERGY_MAX = 40
ENERGY_REGEN_MINUTES = 5


def init_energy_system():
    migrations = [
        ("users", "energy", "INTEGER DEFAULT 40"),
        ("users", "last_energy_update", "TEXT DEFAULT ''"),
        ("users", "energy_full_notified", "INTEGER DEFAULT 1"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    cursor.execute("""
    UPDATE users
    SET energy_full_notified = 1
    WHERE energy IS NULL OR energy >= ?
    """, (ENERGY_MAX,))

    cursor.execute("""
    UPDATE users
    SET energy = ?
    WHERE energy IS NULL OR energy > ?
    """, (ENERGY_MAX, ENERGY_MAX))

    conn.commit()


def get_user_energy(user_id):
    from datetime import datetime, timedelta

    init_energy_system()

    cursor.execute("""
    SELECT energy, last_energy_update
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "energy": 0,
            "max_energy": ENERGY_MAX,
            "next_energy_minutes": ENERGY_REGEN_MINUTES
        }

    energy, last_update = row

    if energy is None:
        energy = ENERGY_MAX

    now = datetime.now()

    if not last_update:
        last_update_dt = now
    else:
        try:
            last_update_dt = datetime.fromisoformat(last_update)
        except Exception:
            last_update_dt = now

    if energy < ENERGY_MAX:
        diff_seconds = (now - last_update_dt).total_seconds()
        regen_units = int(diff_seconds // (ENERGY_REGEN_MINUTES * 60))

        if regen_units > 0:
            energy = min(ENERGY_MAX, energy + regen_units)
            last_update_dt = last_update_dt + timedelta(
                minutes=regen_units * ENERGY_REGEN_MINUTES
            )

            cursor.execute("""
            UPDATE users
            SET energy=?, last_energy_update=?
            WHERE user_id=?
            """, (energy, last_update_dt.isoformat(), user_id))

            conn.commit()

    else:
        cursor.execute("""
        UPDATE users
        SET energy=?, last_energy_update=?
        WHERE user_id=?
        """, (ENERGY_MAX, now.isoformat(), user_id))

        conn.commit()

    next_energy_minutes = ENERGY_REGEN_MINUTES

    if energy < ENERGY_MAX:
        elapsed_seconds = (now - last_update_dt).total_seconds()
        remaining_seconds = (ENERGY_REGEN_MINUTES * 60) - elapsed_seconds
        next_energy_minutes = max(1, int(remaining_seconds // 60) + 1)

    return {
        "energy": energy,
        "max_energy": ENERGY_MAX,
        "next_energy_minutes": next_energy_minutes
    }


def consume_energy_for_hunt(user_id):
    from datetime import datetime

    energy_data = get_user_energy(user_id)
    energy = energy_data["energy"]

    if energy <= 0:
        return {
            "success": False,
            "energy": 0,
            "max_energy": ENERGY_MAX,
            "message": (
                "😴 Герой виснажений і не може полювати.\n\n"
                "Потрібно відпочити та дочекатися відновлення енергії.\n"
                f"⏳ Наступна енергія приблизно через: "
                f"{energy_data['next_energy_minutes']} хв."
            )
        }

    new_energy = energy - 1

    cursor.execute("""
    UPDATE users
    SET energy=?,
        last_energy_update=?,
        energy_full_notified=0
    WHERE user_id=?
    """, (new_energy, datetime.now().isoformat(), user_id))

    conn.commit()

    return {
        "success": True,
        "energy": new_energy,
        "max_energy": ENERGY_MAX,
        "message": None
    }


def restore_energy_for_test(user_id, amount=ENERGY_MAX):
    from datetime import datetime

    init_energy_system()

    try:
        amount = int(amount)
    except Exception:
        amount = ENERGY_MAX

    amount = max(0, min(ENERGY_MAX, amount))
    notified = 0

    cursor.execute("""
    UPDATE users
    SET energy=?,
        last_energy_update=?,
        energy_full_notified=?
    WHERE user_id=?
    """, (amount, datetime.now().isoformat(), notified, user_id))

    conn.commit()

    return {
        "success": True,
        "energy": amount,
        "max_energy": ENERGY_MAX,
        "message": f"✅ DEV: енергію встановлено {amount}/{ENERGY_MAX}"
    }


def get_users_for_energy_full_notification():
    init_energy_system()

    cursor.execute("""
    SELECT user_id
    FROM users
    """)

    users = cursor.fetchall()
    notify_users = []

    for row in users:
        user_id = row[0]

        energy_data = get_user_energy(user_id)
        energy = energy_data["energy"]
        max_energy = energy_data["max_energy"]

        cursor.execute("""
        SELECT energy_full_notified
        FROM users
        WHERE user_id=?
        """, (user_id,))

        notified_row = cursor.fetchone()
        notified = notified_row[0] if notified_row else 0

        if energy >= max_energy and not notified:
            notify_users.append(user_id)

            cursor.execute("""
            UPDATE users
            SET energy_full_notified=1
            WHERE user_id=?
            """, (user_id,))

        elif energy < max_energy and notified:
            cursor.execute("""
            UPDATE users
            SET energy_full_notified=0
            WHERE user_id=?
            """, (user_id,))

    conn.commit()

    return notify_users


# ==============================
# ✅ PASSIVE HP REGEN SYSTEM
# ==============================

HP_REGEN_PERCENT = 0.10
HP_REGEN_MINUTES = 1


def init_hp_regen_system():
    migrations = [
        ("users", "last_hp_regen_update", "TEXT DEFAULT ''"),
        ("users", "hp_full_notified", "INTEGER DEFAULT 1"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()


def apply_passive_hp_regen(user_id):
    from datetime import datetime, timedelta

    init_hp_regen_system()

    cursor.execute("""
    SELECT hp, last_hp_regen_update
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return 0

    hp, last_update = row
    max_hp = get_max_hp(user_id)

    if hp is None:
        hp = max_hp

    now = datetime.now()

    if not last_update:
        last_update_dt = now

        cursor.execute("""
        UPDATE users
        SET last_hp_regen_update=?
        WHERE user_id=?
        """, (last_update_dt.isoformat(), user_id))

        conn.commit()
        return hp

    try:
        last_update_dt = datetime.fromisoformat(last_update)
    except Exception:
        last_update_dt = now

    if hp >= max_hp:
        cursor.execute("""
        UPDATE users
        SET hp=?,
            last_hp_regen_update=?,
            hp_full_notified=1
        WHERE user_id=?
        """, (max_hp, now.isoformat(), user_id))

        conn.commit()
        return max_hp

    diff_seconds = (now - last_update_dt).total_seconds()
    regen_ticks = int(diff_seconds // (HP_REGEN_MINUTES * 60))

    if regen_ticks <= 0:
        return hp

    heal_per_tick = max(1, int(max_hp * HP_REGEN_PERCENT))
    total_heal = heal_per_tick * regen_ticks

    new_hp = min(max_hp, hp + total_heal)

    new_update_dt = last_update_dt + timedelta(
        minutes=regen_ticks * HP_REGEN_MINUTES
    )

    hp_full_notified = 0 if new_hp >= max_hp else 0

    cursor.execute("""
    UPDATE users
    SET hp=?,
        last_hp_regen_update=?,
        hp_full_notified=?
    WHERE user_id=?
    """, (
        new_hp,
        new_update_dt.isoformat(),
        hp_full_notified,
        user_id
    ))

    conn.commit()

    return new_hp


def get_users_for_hp_full_notification():
    init_hp_regen_system()

    cursor.execute("""
    SELECT user_id
    FROM users
    """)

    rows = cursor.fetchall()
    notify_users = []

    for row in rows:
        user_id = row[0]

        hp = apply_passive_hp_regen(user_id)
        max_hp = get_max_hp(user_id)

        cursor.execute("""
        SELECT hp_full_notified
        FROM users
        WHERE user_id=?
        """, (user_id,))

        notified_row = cursor.fetchone()
        notified = notified_row[0] if notified_row else 1

        if hp >= max_hp and not notified:
            notify_users.append(user_id)

            cursor.execute("""
            UPDATE users
            SET hp_full_notified=1
            WHERE user_id=?
            """, (user_id,))

        elif hp < max_hp and notified:
            cursor.execute("""
            UPDATE users
            SET hp_full_notified=0
            WHERE user_id=?
            """, (user_id,))

    conn.commit()

    return notify_users


def get_current_hp(user_id):
    return apply_passive_hp_regen(user_id)


def set_current_hp(user_id, hp):
    from datetime import datetime

    init_hp_regen_system()

    max_hp = get_max_hp(user_id)

    hp = int(hp)
    hp = max(0, min(max_hp, hp))

    hp_full_notified = 1 if hp >= max_hp else 0

    cursor.execute("""
    UPDATE users
    SET hp=?,
        last_hp_regen_update=?,
        hp_full_notified=?
    WHERE user_id=?
    """, (
        hp,
        datetime.now().isoformat(),
        hp_full_notified,
        user_id
    ))

    conn.commit()


# ==============================
# ✅ DEV / TEST LEVEL TOOLS
# ==============================

def set_player_level_for_test(user_id, target_level):
    try:
        target_level = int(target_level)
    except Exception:
        return {
            "success": False,
            "message": "❌ Рівень має бути числом."
        }

    if target_level < 1:
        target_level = 1

    if target_level > 30:
        target_level = 30

    cursor.execute("""
    SELECT user_id
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено. Спочатку натисни /start."
        }

    base_stat = 10 + (target_level - 1)

    cursor.execute("""
    UPDATE users
    SET
        level=?,
        exp=0,
        str=?,
        dex=?,
        intelligence=?,
        wis=?,
        sta=?
    WHERE user_id=?
    """, (
        target_level,
        base_stat,
        base_stat,
        base_stat,
        base_stat,
        base_stat,
        user_id
    ))

    conn.commit()

    new_max_hp = get_max_hp(user_id)

    cursor.execute("""
    UPDATE users
    SET
        max_hp=?,
        hp=?
    WHERE user_id=?
    """, (
        new_max_hp,
        new_max_hp,
        user_id
    ))

    conn.commit()

    return {
        "success": True,
        "level": target_level,
        "base_stat": base_stat,
        "max_hp": new_max_hp,
        "message": (
            f"✅ DEV: рівень персонажа встановлено.\n\n"
            f"🏆 Рівень: {target_level}\n"
            f"✨ Досвід: 0/{get_exp_to_next_level(target_level)}\n"
            f"💪 Базові характеристики: {base_stat}\n"
            f"❤️ HP: {new_max_hp}/{new_max_hp}"
        )
    }


def reset_player_level_for_test(user_id):
    return set_player_level_for_test(user_id, 1)

# ==============================
# ✅ DEV GOLD TOOL
# ==============================

def set_gold_for_test(user_id, amount):
    """
    DEV-функція.
    Встановлює золото вручну.
    Приклади:
    /gold 100
    /gold 0
    """

    try:
        amount = float(amount)
    except Exception:
        return {
            "success": False,
            "message": "❌ Значення золота має бути числом."
        }

    if amount < 0:
        amount = 0

    cursor.execute("""
    SELECT user_id
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено. Спочатку натисни /start."
        }

    cursor.execute("""
    UPDATE users
    SET gold=?
    WHERE user_id=?
    """, (amount, user_id))

    conn.commit()

    return {
        "success": True,
        "gold": amount,
        "message": f"✅ DEV: золото встановлено {amount:.2f} 🪙"
    }

# ==============================
# ✅ DAILY QUEST SYSTEM
# ==============================

DAILY_QUEST_ID_KILL_MONSTERS = "kill_25_monsters"
DAILY_QUEST_TARGET_KILLS = 25
DAILY_QUEST_REWARD_ITEM_ID = 201  # 🔴 Мале зілля здоров’я
DAILY_QUEST_REWARD_QUANTITY = 3


def get_daily_today_str():
    from datetime import date
    return date.today().isoformat()


def init_daily_quest_system():
    """
    Щоденні завдання v1.

    Поточна версія:
    - 1 завдання на день
    - вбити 25 монстрів
    - нагорода: Мале зілля здоров’я x3
    """

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_daily_quests (
        user_id INTEGER PRIMARY KEY,
        quest_date TEXT,
        quest_id TEXT,
        progress INTEGER,
        target_count INTEGER,
        completed INTEGER,
        reward_claimed INTEGER
    )
    """)

    conn.commit()


def reset_daily_quest_if_needed(user_id):
    init_daily_quest_system()

    today = get_daily_today_str()

    cursor.execute("""
    SELECT quest_date
    FROM user_daily_quests
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        cursor.execute("""
        INSERT INTO user_daily_quests (
            user_id,
            quest_date,
            quest_id,
            progress,
            target_count,
            completed,
            reward_claimed
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            today,
            DAILY_QUEST_ID_KILL_MONSTERS,
            0,
            DAILY_QUEST_TARGET_KILLS,
            0,
            0
        ))

        conn.commit()
        return

    quest_date = row[0] or ""

    if quest_date != today:
        cursor.execute("""
        UPDATE user_daily_quests
        SET
            quest_date=?,
            quest_id=?,
            progress=0,
            target_count=?,
            completed=0,
            reward_claimed=0
        WHERE user_id=?
        """, (
            today,
            DAILY_QUEST_ID_KILL_MONSTERS,
            DAILY_QUEST_TARGET_KILLS,
            user_id
        ))

        conn.commit()


def get_daily_quest_status(user_id):
    reset_daily_quest_if_needed(user_id)

    cursor.execute("""
    SELECT
        quest_date,
        quest_id,
        progress,
        target_count,
        completed,
        reward_claimed
    FROM user_daily_quests
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "exists": False,
            "message": "❌ Щоденне завдання не знайдено."
        }

    (
        quest_date,
        quest_id,
        progress,
        target_count,
        completed,
        reward_claimed
    ) = row

    return {
        "exists": True,
        "quest_date": quest_date,
        "quest_id": quest_id,
        "progress": progress or 0,
        "target_count": target_count or DAILY_QUEST_TARGET_KILLS,
        "completed": bool(completed),
        "reward_claimed": bool(reward_claimed),
        "reward_item_id": DAILY_QUEST_REWARD_ITEM_ID,
        "reward_quantity": DAILY_QUEST_REWARD_QUANTITY
    }


def process_daily_quest_progress_on_kill(user_id, mob=None):
    """
    Викликається після перемоги над будь-яким монстром.

    Враховуються:
    - звичайні монстри
    - елітні монстри
    - боси, коли вони будуть реалізовані
    """

    reset_daily_quest_if_needed(user_id)

    status = get_daily_quest_status(user_id)

    if not status["exists"]:
        return {
            "updated": False,
            "completed": False,
            "message": None
        }

    if status["reward_claimed"]:
        return {
            "updated": False,
            "completed": False,
            "message": None
        }

    if status["completed"]:
        return {
            "updated": False,
            "completed": True,
            "message": None
        }

    progress = status["progress"]
    target_count = status["target_count"]

    new_progress = min(target_count, progress + 1)
    completed = 1 if new_progress >= target_count else 0

    cursor.execute("""
    UPDATE user_daily_quests
    SET progress=?,
        completed=?
    WHERE user_id=?
    """, (
        new_progress,
        completed,
        user_id
    ))

    conn.commit()

    if completed:
        return {
            "updated": True,
            "completed": True,
            "message": (
                "📆 Щоденне завдання виконано!\n"
                "✅ Прогрес: 25/25\n"
                "🏛️ Поверніться до Ратуші за нагородою."
            )
        }

    return {
        "updated": True,
        "completed": False,
        "message": f"📆 Щоденне завдання: {new_progress}/{target_count}"
    }


def claim_daily_quest_reward(user_id):
    reset_daily_quest_if_needed(user_id)

    status = get_daily_quest_status(user_id)

    if not status["exists"]:
        return {
            "success": False,
            "message": "❌ Щоденне завдання не знайдено."
        }

    if not status["completed"]:
        return {
            "success": False,
            "message": (
                "❌ Щоденне завдання ще не виконано.\n\n"
                f"📈 Прогрес: {status['progress']}/{status['target_count']}"
            )
        }

    if status["reward_claimed"]:
        return {
            "success": False,
            "message": "✅ Нагороду за сьогодні вже отримано."
        }

    result = add_item(
        user_id=user_id,
        item_id=DAILY_QUEST_REWARD_ITEM_ID,
        quantity=DAILY_QUEST_REWARD_QUANTITY
    )

    added = result.get("added", 0)
    lost = result.get("lost", 0)
    name = result.get("name", "Предмет")

    if added <= 0:
        return {
            "success": False,
            "message": (
                "🎒 Сумка переповнена.\n\n"
                "Звільни місце в інвентарі та спробуй забрати нагороду ще раз."
            )
        }

    cursor.execute("""
    UPDATE user_daily_quests
    SET reward_claimed=1
    WHERE user_id=?
    """, (user_id,))

    conn.commit()

    message = (
        "🎁 Ви отримали нагороду за щоденне завдання!\n\n"
        f"📦 {name} x{added}"
    )

    if lost > 0:
        message += f"\n⚠️ Не влізло в сумку: x{lost}"

    return {
        "success": True,
        "message": message
    }

# ==============================
# ✅ WEAPON DAMAGE SYSTEM V1
# ==============================

def init_weapon_damage_system():
    """
    Додає службові поля для майбутнього збереження damage на зброї.

    Поточна v1 може рахувати damage динамічно з:
    - item_level
    - rarity
    - weapon_hands
    - назви зброї

    Але поля залишаємо в БД для майбутньої заточки.
    """

    migrations = [
        ("items", "weapon_min_damage", "INTEGER DEFAULT 0"),
        ("items", "weapon_max_damage", "INTEGER DEFAULT 0"),
        ("items", "weapon_min_magic_damage", "INTEGER DEFAULT 0"),
        ("items", "weapon_max_magic_damage", "INTEGER DEFAULT 0"),
        ("items", "weapon_attack_type", "TEXT DEFAULT ''"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()


def is_weapon_name_magical(name):
    """
    Тимчасова логіка до класів/типів зброї.

    Посох = magical.
    Все інше = physical.
    """

    if not name:
        return False

    name_lower = name.lower()

    if "посох" in name_lower:
        return True

    return False


def calculate_weapon_damage_by_values(item_level, rarity, weapon_hands=1):
    """
    Базова формула Weapon Damage v1.

    1H:
    min = level × 0.8 × rarity_multiplier
    max = level × 1.2 × rarity_multiplier

    2H:
    додатково ×1.35
    """

    init_dynamic_equipment_system()
    init_weapon_damage_system()

    item_level = int(item_level or 1)
    item_level = max(1, item_level)

    rarity_multiplier = DYNAMIC_STAT_MULTIPLIERS.get(rarity, 1.0)

    hand_multiplier = 1.0

    if int(weapon_hands or 1) == 2:
        hand_multiplier = 1.35

    min_damage = int(round(item_level * 0.8 * rarity_multiplier * hand_multiplier))
    max_damage = int(round(item_level * 1.2 * rarity_multiplier * hand_multiplier))

    min_damage = max(1, min_damage)
    max_damage = max(min_damage, max_damage)

    return min_damage, max_damage


def get_weapon_damage_by_inventory_id(inventory_id):
    """
    Повертає damage профіль предмета.

    Якщо предмет не є main_hand зброєю — повертає нулі.
    """

    init_dynamic_equipment_system()
    init_weapon_damage_system()

    cursor.execute("""
    SELECT
        items.name,
        items.category,
        items.slot_key,
        items.weapon_hands,
        items.rarity,
        items.item_level,
        items.weapon_min_damage,
        items.weapon_max_damage,
        items.weapon_min_magic_damage,
        items.weapon_max_magic_damage,
        items.weapon_attack_type
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.id=?
    """, (inventory_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "is_weapon": False,
            "attack_type": "physical",
            "physical_min": 0,
            "physical_max": 0,
            "magic_min": 0,
            "magic_max": 0,
            "text": None
        }

    (
        name,
        category,
        slot_key,
        weapon_hands,
        rarity,
        item_level,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type
    ) = row

    if category != "equipment" or slot_key != "main_hand":
        return {
            "is_weapon": False,
            "attack_type": "physical",
            "physical_min": 0,
            "physical_max": 0,
            "magic_min": 0,
            "magic_max": 0,
            "text": None
        }

    is_magical = is_weapon_name_magical(name)

    attack_type = "magical" if is_magical else "physical"

    # Якщо в майбутньому damage буде записаний у БД — використовуємо його.
    if is_magical:
        if weapon_min_magic_damage and weapon_max_magic_damage:
            min_dmg = weapon_min_magic_damage
            max_dmg = weapon_max_magic_damage
        else:
            min_dmg, max_dmg = calculate_weapon_damage_by_values(
                item_level=item_level,
                rarity=rarity,
                weapon_hands=weapon_hands
            )

        return {
            "is_weapon": True,
            "attack_type": attack_type,
            "physical_min": 0,
            "physical_max": 0,
            "magic_min": min_dmg,
            "magic_max": max_dmg,
            "text": f"🔮 Маг. урон: {min_dmg}-{max_dmg}"
        }

    if weapon_min_damage and weapon_max_damage:
        min_dmg = weapon_min_damage
        max_dmg = weapon_max_damage
    else:
        min_dmg, max_dmg = calculate_weapon_damage_by_values(
            item_level=item_level,
            rarity=rarity,
            weapon_hands=weapon_hands
        )

    return {
        "is_weapon": True,
        "attack_type": attack_type,
        "physical_min": min_dmg,
        "physical_max": max_dmg,
        "magic_min": 0,
        "magic_max": 0,
        "text": f"⚔️ Урон: {min_dmg}-{max_dmg}"
    }


def get_player_attack_profile(user_id):
    """
    Повертає повний профіль атаки гравця для бою.

    v1:
    physical:
        damage = random weapon damage + STR - DEF × 0.5

    magical:
        damage = random magic weapon damage + INT - DEF × 0.5
    """

    stats = get_player_stats(user_id)

    if not stats:
        return {
            "attack_type": "physical",
            "stat_attack": 0,
            "weapon_min_damage": 0,
            "weapon_max_damage": 0,
            "display_attack": 0,
            "weapon_text": "Без зброї"
        }

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    main_hand_id = get_equipped_slot(user_id, "main_hand")

    if not main_hand_id:
        return {
            "attack_type": "physical",
            "stat_attack": total_str,
            "weapon_min_damage": 0,
            "weapon_max_damage": 0,
            "display_attack": total_str,
            "weapon_text": "Без зброї"
        }

    weapon_data = get_weapon_damage_by_inventory_id(main_hand_id)

    if not weapon_data.get("is_weapon"):
        return {
            "attack_type": "physical",
            "stat_attack": total_str,
            "weapon_min_damage": 0,
            "weapon_max_damage": 0,
            "display_attack": total_str,
            "weapon_text": "Без зброї"
        }

    attack_type = weapon_data["attack_type"]

    if attack_type == "magical":
        stat_attack = total_int
        weapon_min = weapon_data["magic_min"]
        weapon_max = weapon_data["magic_max"]
    else:
        stat_attack = total_str
        weapon_min = weapon_data["physical_min"]
        weapon_max = weapon_data["physical_max"]

    display_attack = stat_attack + weapon_max

    return {
        "attack_type": attack_type,
        "stat_attack": stat_attack,
        "weapon_min_damage": weapon_min,
        "weapon_max_damage": weapon_max,
        "display_attack": display_attack,
        "weapon_text": weapon_data.get("text")
    }


def get_inventory_weapon_damage_display(inventory_id):
    """
    Для інвентаря.
    Повертає текст damage зброї або None.
    """

    weapon_data = get_weapon_damage_by_inventory_id(inventory_id)

    if not weapon_data.get("is_weapon"):
        return None

    return weapon_data.get("text")

# ==============================
# ✅ DEV RESET HERO TOOL
# ==============================

def reset_hero_for_test(user_id):
    """
    DEV-функція.
    Повністю видаляє прогрес героя і створює персонажа заново.

    Видаляє:
    - users
    - inventory
    - equipment_slots
    - active contracts
    - daily quests

    Потім викликає create_user(user_id).
    """

    try:
        cursor.execute("""
        DELETE FROM inventory
        WHERE user_id=?
        """, (user_id,))

        cursor.execute("""
        DELETE FROM equipment_slots
        WHERE user_id=?
        """, (user_id,))

        try:
            cursor.execute("""
            DELETE FROM user_active_contracts
            WHERE user_id=?
            """, (user_id,))
        except Exception:
            pass

        try:
            cursor.execute("""
            DELETE FROM user_daily_quests
            WHERE user_id=?
            """, (user_id,))
        except Exception:
            pass

        cursor.execute("""
        DELETE FROM users
        WHERE user_id=?
        """, (user_id,))

        conn.commit()

        create_user(user_id)

        return {
            "success": True,
            "message": (
                "✅ DEV: герой повністю скинутий.\n\n"
                "Створено нового персонажа з нуля:\n"
                "🏆 Рівень: 1\n"
                "✨ EXP: 0\n"
                "🪙 Золото: 0\n"
                "🎒 Інвентар очищено\n"
                "📜 Контракти очищено\n"
                "📆 Щоденні завдання очищено"
            )
        }

    except Exception as error:
        return {
            "success": False,
            "message": f"❌ DEV reset error: {error}"
        }

# ==============================
# ✅ ROLE-BASED EQUIPMENT GENERATION V1
# ==============================

MAIN_HAND_PROFILES = {
    "sword_1h": {
        "name": "Одноручний меч",
        "hands": 1,
        "attack_type": "physical",
        "main_stats": ["str"],
        "extra_stats": ["str", "sta"]
    },
    "wand_1h": {
        "name": "Жезл",
        "hands": 1,
        "attack_type": "magical",
        "main_stats": ["int"],
        "extra_stats": ["int", "wis"]
    },
    "sword_2h": {
        "name": "Дворучний меч",
        "hands": 2,
        "attack_type": "physical",
        "main_stats": ["str"],
        "extra_stats": ["str", "sta"]
    },
    "staff_2h": {
        "name": "Дворучний посох",
        "hands": 2,
        "attack_type": "magical",
        "main_stats": ["int"],
        "extra_stats": ["int", "wis"]
    },
    "bow_2h": {
        "name": "Лук",
        "hands": 2,
        "attack_type": "physical",
        "main_stats": ["dex"],
        "extra_stats": ["dex", "str"]
    },
    "crossbow_2h": {
        "name": "Арбалет",
        "hands": 2,
        "attack_type": "physical",
        "main_stats": ["dex"],
        "extra_stats": ["dex", "str"]
    }
}


OFF_HAND_PROFILES = {
    "shield": {
        "name": "Щит",
        "attack_type": "defense",
        "main_stats": ["sta"],
        "extra_stats": ["sta", "wis"]
    },
    "talisman": {
        "name": "Магічний талісман",
        "attack_type": "magical",
        "main_stats": ["wis"],
        "extra_stats": ["wis", "int"]
    },
    "dagger": {
        "name": "Кинджал для другої руки",
        "attack_type": "physical",
        "main_stats": ["dex"],
        "extra_stats": ["dex", "str"]
    }
}


ARMOR_EXTRA_STATS_BY_SLOT = {
    "helmet": ["sta", "wis", "dex"],
    "shoulders": ["sta", "str"],
    "chest": ["sta"],
    "gloves": ["dex", "str"],
    "legs": ["sta", "dex"],
    "boots": ["dex"],
    "necklace": ["wis", "int"],
    "ring": ["str", "dex", "int", "wis", "sta"]
}


def init_dynamic_equipment_system():
    migrations = [
        ("items", "item_level", "INTEGER DEFAULT 1"),
        ("items", "is_generated", "INTEGER DEFAULT 0"),
        ("items", "item_subtype", "TEXT DEFAULT ''"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()


def init_weapon_damage_system():
    migrations = [
        ("items", "weapon_min_damage", "INTEGER DEFAULT 0"),
        ("items", "weapon_max_damage", "INTEGER DEFAULT 0"),
        ("items", "weapon_min_magic_damage", "INTEGER DEFAULT 0"),
        ("items", "weapon_max_magic_damage", "INTEGER DEFAULT 0"),
        ("items", "weapon_attack_type", "TEXT DEFAULT ''"),
        ("items", "item_subtype", "TEXT DEFAULT ''"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()


def add_stat_value(stats, stat_key, value):
    if stat_key == "str":
        stats["bonus_str"] += value
    elif stat_key == "dex":
        stats["bonus_dex"] += value
    elif stat_key == "int":
        stats["bonus_int"] += value
    elif stat_key == "wis":
        stats["bonus_wis"] += value
    elif stat_key == "sta":
        stats["bonus_sta"] += value


def get_random_main_hand_profile():
    return random.choice(list(MAIN_HAND_PROFILES.keys()))


def get_random_off_hand_profile():
    return random.choice(list(OFF_HAND_PROFILES.keys()))


def get_profile_for_generated_item(slot_key, item_profile=None):
    if slot_key == "main_hand":
        if item_profile in MAIN_HAND_PROFILES:
            return item_profile

        return get_random_main_hand_profile()

    if slot_key == "off_hand":
        if item_profile in OFF_HAND_PROFILES:
            return item_profile

        return get_random_off_hand_profile()

    return ""


def get_dynamic_weapon_name(slot_key, rarity, weapon_hands=1, item_profile=None):
    icon = DYNAMIC_RARITY_ICONS.get(rarity, "⚪")

    if slot_key == "main_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = MAIN_HAND_PROFILES.get(profile_key, MAIN_HAND_PROFILES["sword_1h"])
        return f"{icon} {profile['name']}"

    if slot_key == "off_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = OFF_HAND_PROFILES.get(profile_key, OFF_HAND_PROFILES["shield"])
        return f"{icon} {profile['name']}"

    return f"{icon} Зброя"


def generate_dynamic_equipment_stats(slot_key, item_level, rarity, weapon_hands=1, item_profile=None):
    stats = {
        "bonus_str": 0,
        "bonus_dex": 0,
        "bonus_int": 0,
        "bonus_wis": 0,
        "bonus_sta": 0,
        "pdef": 0,
        "mdef": 0
    }

    # ==============================
    # MAIN HAND
    # ==============================

    if slot_key == "main_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = MAIN_HAND_PROFILES.get(profile_key, MAIN_HAND_PROFILES["sword_1h"])

        main_stat = profile["main_stats"][0]
        base_multiplier = 1.00

        if profile["hands"] == 2:
            base_multiplier = 1.20

        value = get_dynamic_stat_value(item_level, rarity, base_multiplier)
        add_stat_value(stats, main_stat, value)

        extra_pool = profile["extra_stats"]

    # ==============================
    # OFF HAND
    # ==============================

    elif slot_key == "off_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = OFF_HAND_PROFILES.get(profile_key, OFF_HAND_PROFILES["shield"])

        if profile_key == "shield":
            stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.35)
            stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.55)

        elif profile_key == "talisman":
            stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 1.35)
            stats["bonus_wis"] = get_dynamic_stat_value(item_level, rarity, 0.65)

        elif profile_key == "dagger":
            stats["bonus_dex"] = get_dynamic_stat_value(item_level, rarity, 0.95)
            stats["bonus_str"] = get_dynamic_stat_value(item_level, rarity, 0.35)

        extra_pool = profile["extra_stats"]

    # ==============================
    # ARMOR SLOTS
    # ==============================

    elif slot_key == "helmet":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 0.80)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.40)

        bonus = random.choice(["sta", "wis", "dex"])
        value = get_dynamic_stat_value(item_level, rarity, 0.25)
        add_stat_value(stats, bonus, value)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "shoulders":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.00)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.25)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "chest":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.60)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.35)
        stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.55)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "gloves":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 0.55)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.20)
        stats["bonus_dex"] = get_dynamic_stat_value(item_level, rarity, 0.60)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["dex"])

    elif slot_key == "legs":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.20)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.30)
        stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.45)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "boots":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 0.45)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.20)
        stats["bonus_dex"] = get_dynamic_stat_value(item_level, rarity, 0.80)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["dex"])

    # ==============================
    # JEWELRY
    # ==============================

    elif slot_key == "necklace":
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 1.30)
        stats["bonus_wis"] = get_dynamic_stat_value(item_level, rarity, 0.80)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["wis", "int"])

    elif slot_key == "ring":
        stat_choice = random.choice(["str", "dex", "int", "wis", "sta"])
        value = get_dynamic_stat_value(item_level, rarity, 0.90)
        add_stat_value(stats, stat_choice, value)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["str", "dex", "int", "wis", "sta"])

    else:
        extra_pool = ["str", "dex", "int", "wis", "sta"]

    # ==============================
    # EXTRA BONUSES BY RARITY
    # ==============================

    if rarity in ["uncommon", "rare", "epic"]:
        bonus_count = 1
        min_bonus = 2

        if rarity == "rare":
            bonus_count = 2
            min_bonus = 3

        if rarity == "epic":
            bonus_count = 3
            min_bonus = 4

        for _ in range(bonus_count):
            bonus_type = random.choice(extra_pool)

            bonus_value = get_dynamic_stat_value(item_level, rarity, 0.30)
            bonus_value = max(min_bonus, bonus_value)

            add_stat_value(stats, bonus_type, bonus_value)

    return stats


def calculate_weapon_damage_by_values(item_level, rarity, weapon_hands=1):
    init_dynamic_equipment_system()
    init_weapon_damage_system()

    item_level = int(item_level or 1)
    item_level = max(1, item_level)

    rarity_multiplier = DYNAMIC_STAT_MULTIPLIERS.get(rarity, 1.0)

    hand_multiplier = 1.0

    if int(weapon_hands or 1) == 2:
        hand_multiplier = 1.35

    min_damage = int(round(item_level * 0.8 * rarity_multiplier * hand_multiplier))
    max_damage = int(round(item_level * 1.2 * rarity_multiplier * hand_multiplier))

    min_damage = max(1, min_damage)
    max_damage = max(min_damage, max_damage)

    return min_damage, max_damage


def detect_weapon_profile_from_name(name):
    if not name:
        return ""

    lowered = name.lower()

    if "дворучний посох" in lowered:
        return "staff_2h"

    if "жезл" in lowered or "одноручний посох" in lowered:
        return "wand_1h"

    if "дворучний меч" in lowered:
        return "sword_2h"

    if "лук" in lowered:
        return "bow_2h"

    if "арбалет" in lowered:
        return "crossbow_2h"

    if "меч" in lowered:
        return "sword_1h"

    if "щит" in lowered:
        return "shield"

    if "талісман" in lowered:
        return "talisman"

    if "кинджал" in lowered:
        return "dagger"

    return ""


def is_weapon_profile_magical(profile_key):
    if profile_key in MAIN_HAND_PROFILES:
        return MAIN_HAND_PROFILES[profile_key]["attack_type"] == "magical"

    return False


def get_weapon_damage_by_inventory_id(inventory_id):
    init_dynamic_equipment_system()
    init_weapon_damage_system()

    cursor.execute("""
    SELECT
        items.name,
        items.category,
        items.slot_key,
        items.weapon_hands,
        items.rarity,
        items.item_level,
        items.weapon_min_damage,
        items.weapon_max_damage,
        items.weapon_min_magic_damage,
        items.weapon_max_magic_damage,
        items.weapon_attack_type,
        items.item_subtype
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.id=?
    """, (inventory_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "is_weapon": False,
            "attack_type": "physical",
            "physical_min": 0,
            "physical_max": 0,
            "magic_min": 0,
            "magic_max": 0,
            "text": None
        }

    (
        name,
        category,
        slot_key,
        weapon_hands,
        rarity,
        item_level,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type,
        item_subtype
    ) = row

    if category != "equipment" or slot_key != "main_hand":
        return {
            "is_weapon": False,
            "attack_type": "physical",
            "physical_min": 0,
            "physical_max": 0,
            "magic_min": 0,
            "magic_max": 0,
            "text": None
        }

    profile_key = item_subtype or detect_weapon_profile_from_name(name)

    if profile_key not in MAIN_HAND_PROFILES:
        profile_key = detect_weapon_profile_from_name(name)

    is_magical = is_weapon_profile_magical(profile_key)
    attack_type = "magical" if is_magical else "physical"

    if is_magical:
        if weapon_min_magic_damage and weapon_max_magic_damage:
            min_dmg = weapon_min_magic_damage
            max_dmg = weapon_max_magic_damage
        else:
            min_dmg, max_dmg = calculate_weapon_damage_by_values(
                item_level=item_level,
                rarity=rarity,
                weapon_hands=weapon_hands
            )

        return {
            "is_weapon": True,
            "attack_type": attack_type,
            "physical_min": 0,
            "physical_max": 0,
            "magic_min": min_dmg,
            "magic_max": max_dmg,
            "text": f"🔮 Маг. урон: {min_dmg}-{max_dmg}"
        }

    if weapon_min_damage and weapon_max_damage:
        min_dmg = weapon_min_damage
        max_dmg = weapon_max_damage
    else:
        min_dmg, max_dmg = calculate_weapon_damage_by_values(
            item_level=item_level,
            rarity=rarity,
            weapon_hands=weapon_hands
        )

    return {
        "is_weapon": True,
        "attack_type": attack_type,
        "physical_min": min_dmg,
        "physical_max": max_dmg,
        "magic_min": 0,
        "magic_max": 0,
        "text": f"⚔️ Урон: {min_dmg}-{max_dmg}"
    }


def create_generated_equipment_item(user_id, item_level, rarity):
    init_dynamic_equipment_system()
    init_weapon_damage_system()

    item_level = int(item_level)
    item_level = max(1, item_level)

    if rarity not in ["common", "uncommon", "rare", "epic"]:
        rarity = "common"

    capacity = get_bag_capacity(user_id)
    used_slots = get_inventory_used_slots(user_id)

    if used_slots >= capacity:
        return {
            "success": False,
            "lost": 1,
            "message": "🎒 Сумка переповнена. Екіпірування не влізло."
        }

    slot_key = get_dynamic_slot_key()
    item_profile = get_profile_for_generated_item(slot_key)
    weapon_hands = 1
    weapon_attack_type = ""

    if slot_key == "main_hand":
        profile = MAIN_HAND_PROFILES[item_profile]
        weapon_hands = profile["hands"]
        weapon_attack_type = profile["attack_type"]
        name = get_dynamic_weapon_name(slot_key, rarity, weapon_hands, item_profile)
        type_ = "weapon"

    elif slot_key == "off_hand":
        profile = OFF_HAND_PROFILES[item_profile]
        weapon_hands = 1
        weapon_attack_type = profile["attack_type"]
        name = get_dynamic_weapon_name(slot_key, rarity, weapon_hands, item_profile)
        type_ = "offhand"

    else:
        item_profile = ""
        weapon_hands = 1
        name = get_dynamic_armor_name(slot_key, rarity)
        type_ = slot_key

    rarity_name = DYNAMIC_RARITY_NAMES.get(rarity, "Звичайний")
    name = f"{name} {item_level} рівня"

    stats = generate_dynamic_equipment_stats(
        slot_key=slot_key,
        item_level=item_level,
        rarity=rarity,
        weapon_hands=weapon_hands,
        item_profile=item_profile
    )

    sell_price = get_dynamic_sell_price(item_level, rarity)

    weapon_min_damage = 0
    weapon_max_damage = 0
    weapon_min_magic_damage = 0
    weapon_max_magic_damage = 0

    if slot_key == "main_hand":
        min_dmg, max_dmg = calculate_weapon_damage_by_values(
            item_level=item_level,
            rarity=rarity,
            weapon_hands=weapon_hands
        )

        if weapon_attack_type == "magical":
            weapon_min_magic_damage = min_dmg
            weapon_max_magic_damage = max_dmg
        else:
            weapon_min_damage = min_dmg
            weapon_max_damage = max_dmg

    cursor.execute("""
    INSERT INTO items (
        name,
        type,
        rarity,
        category,
        slot_key,
        weapon_hands,
        max_stack,
        sell_price,
        bonus_str,
        bonus_dex,
        bonus_int,
        bonus_wis,
        bonus_sta,
        pdef,
        mdef,
        item_level,
        is_generated,
        item_subtype,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        type_,
        rarity,
        "equipment",
        slot_key,
        weapon_hands,
        1,
        sell_price,
        stats["bonus_str"],
        stats["bonus_dex"],
        stats["bonus_int"],
        stats["bonus_wis"],
        stats["bonus_sta"],
        stats["pdef"],
        stats["mdef"],
        item_level,
        1,
        item_profile,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type
    ))

    item_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO inventory (
        user_id,
        item_id,
        quantity,
        durability
    )
    VALUES (?, ?, ?, ?)
    """, (
        user_id,
        item_id,
        1,
        100
    ))

    inventory_id = cursor.lastrowid

    conn.commit()

    return {
        "success": True,
        "lost": 0,
        "name": name,
        "rarity": rarity,
        "rarity_name": rarity_name,
        "slot_key": slot_key,
        "item_id": item_id,
        "inventory_id": inventory_id,
        "message": f"{name}"
    }


def create_generated_equipment_item_for_slot(user_id, item_level, rarity, slot_key, item_profile=None):
    init_dynamic_equipment_system()
    init_weapon_damage_system()

    if slot_key not in SLOT_ORDER:
        return {
            "success": False,
            "message": "❌ Невідомий слот спорядження."
        }

    item_level = int(item_level)
    item_level = max(1, item_level)

    if rarity not in ["common", "uncommon", "rare", "epic"]:
        rarity = "common"

    capacity = get_bag_capacity(user_id)
    used_slots = get_inventory_used_slots(user_id)

    if used_slots >= capacity:
        return {
            "success": False,
            "lost": 1,
            "message": "🎒 Сумка переповнена. Предмет не куплено."
        }

    item_profile = get_profile_for_generated_item(slot_key, item_profile)

    weapon_hands = 1
    weapon_attack_type = ""

    if slot_key == "main_hand":
        profile = MAIN_HAND_PROFILES[item_profile]
        weapon_hands = profile["hands"]
        weapon_attack_type = profile["attack_type"]
        name = get_dynamic_weapon_name(slot_key, rarity, weapon_hands, item_profile)
        type_ = "weapon"

    elif slot_key == "off_hand":
        profile = OFF_HAND_PROFILES[item_profile]
        weapon_hands = 1
        weapon_attack_type = profile["attack_type"]
        name = get_dynamic_weapon_name(slot_key, rarity, weapon_hands, item_profile)
        type_ = "offhand"

    else:
        item_profile = ""
        weapon_hands = 1
        name = get_dynamic_armor_name(slot_key, rarity)
        type_ = slot_key

    name = f"{name} {item_level} рівня"

    stats = generate_dynamic_equipment_stats(
        slot_key=slot_key,
        item_level=item_level,
        rarity=rarity,
        weapon_hands=weapon_hands,
        item_profile=item_profile
    )

    sell_price = get_dynamic_sell_price(item_level, rarity)

    weapon_min_damage = 0
    weapon_max_damage = 0
    weapon_min_magic_damage = 0
    weapon_max_magic_damage = 0

    if slot_key == "main_hand":
        min_dmg, max_dmg = calculate_weapon_damage_by_values(
            item_level=item_level,
            rarity=rarity,
            weapon_hands=weapon_hands
        )

        if weapon_attack_type == "magical":
            weapon_min_magic_damage = min_dmg
            weapon_max_magic_damage = max_dmg
        else:
            weapon_min_damage = min_dmg
            weapon_max_damage = max_dmg

    cursor.execute("""
    INSERT INTO items (
        name,
        type,
        rarity,
        category,
        slot_key,
        weapon_hands,
        max_stack,
        sell_price,
        bonus_str,
        bonus_dex,
        bonus_int,
        bonus_wis,
        bonus_sta,
        pdef,
        mdef,
        item_level,
        is_generated,
        item_subtype,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        type_,
        rarity,
        "equipment",
        slot_key,
        weapon_hands,
        1,
        sell_price,
        stats["bonus_str"],
        stats["bonus_dex"],
        stats["bonus_int"],
        stats["bonus_wis"],
        stats["bonus_sta"],
        stats["pdef"],
        stats["mdef"],
        item_level,
        1,
        item_profile,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type
    ))

    item_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO inventory (
        user_id,
        item_id,
        quantity,
        durability
    )
    VALUES (?, ?, ?, ?)
    """, (
        user_id,
        item_id,
        1,
        100
    ))

    inventory_id = cursor.lastrowid

    conn.commit()

    return {
        "success": True,
        "name": name,
        "item_id": item_id,
        "inventory_id": inventory_id,
        "slot_key": slot_key,
        "item_level": item_level
    }


def get_common_equipment_shop_suboffers(user_id, slot_key):
    player_level = get_player_level(user_id)
    price = get_common_equipment_price_for_slot(player_level, slot_key)

    if slot_key == "main_hand":
        return [
            {
                "slot_key": slot_key,
                "profile_key": profile_key,
                "name": profile["name"],
                "hands": profile["hands"],
                "attack_type": profile["attack_type"],
                "item_level": player_level,
                "price": price
            }
            for profile_key, profile in MAIN_HAND_PROFILES.items()
        ]

    if slot_key == "off_hand":
        return [
            {
                "slot_key": slot_key,
                "profile_key": profile_key,
                "name": profile["name"],
                "hands": 1,
                "attack_type": profile["attack_type"],
                "item_level": player_level,
                "price": price
            }
            for profile_key, profile in OFF_HAND_PROFILES.items()
        ]

    return []


def buy_common_equipment_from_trader(user_id, slot_key, item_profile=None):
    if slot_key not in SLOT_ORDER:
        return {
            "success": False,
            "message": "❌ Невідомий слот спорядження."
        }

    if slot_key == "main_hand" and item_profile not in MAIN_HAND_PROFILES:
        return {
            "success": False,
            "message": "❌ Невідомий тип зброї."
        }

    if slot_key == "off_hand" and item_profile not in OFF_HAND_PROFILES:
        return {
            "success": False,
            "message": "❌ Невідомий тип предмета для другої руки."
        }

    player_level = get_player_level(user_id)
    price = get_common_equipment_price_for_slot(player_level, slot_key)

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено."
        }

    gold = row[0] or 0.0

    if gold < price:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо золота.\n\n"
                f"💳 Потрібно: {price:.2f} 🪙\n"
                f"💰 У тебе: {gold:.2f} 🪙"
            )
        }

    result = create_generated_equipment_item_for_slot(
        user_id=user_id,
        item_level=player_level,
        rarity="common",
        slot_key=slot_key,
        item_profile=item_profile
    )

    if not result.get("success"):
        return result

    cursor.execute("""
    UPDATE users
    SET gold = gold - ?
    WHERE user_id=?
    """, (price, user_id))

    conn.commit()

    return {
        "success": True,
        "message": (
            f"✅ Куплено базове спорядження.\n\n"
            f"📦 {result['name']}\n"
            f"🏷 Рівень предмета: {player_level}\n"
            f"💳 Сплачено: {price:.2f} 🪙"
        )
    }

# ==============================
# ✅ PATCH: MAIN HAND DAGGER PROFILE
# ==============================

MAIN_HAND_PROFILES = {
    "sword_1h": {
        "name": "Одноручний меч",
        "hands": 1,
        "attack_type": "physical",
        "main_stats": ["str"],
        "extra_stats": ["str", "sta"]
    },
    "dagger_1h": {
        "name": "Кинджал",
        "hands": 1,
        "attack_type": "physical",
        "main_stats": ["dex"],
        "extra_stats": ["dex", "str"]
    },
    "wand_1h": {
        "name": "Жезл",
        "hands": 1,
        "attack_type": "magical",
        "main_stats": ["int"],
        "extra_stats": ["int", "wis"]
    },
    "sword_2h": {
        "name": "Дворучний меч",
        "hands": 2,
        "attack_type": "physical",
        "main_stats": ["str"],
        "extra_stats": ["str", "sta"]
    },
    "staff_2h": {
        "name": "Дворучний посох",
        "hands": 2,
        "attack_type": "magical",
        "main_stats": ["int"],
        "extra_stats": ["int", "wis"]
    },
    "bow_2h": {
        "name": "Лук",
        "hands": 2,
        "attack_type": "physical",
        "main_stats": ["dex"],
        "extra_stats": ["dex", "str"]
    },
    "crossbow_2h": {
        "name": "Арбалет",
        "hands": 2,
        "attack_type": "physical",
        "main_stats": ["dex"],
        "extra_stats": ["dex", "str"]
    }
}


def detect_weapon_profile_from_name(name):
    if not name:
        return ""

    lowered = name.lower()

    if "дворучний посох" in lowered:
        return "staff_2h"

    if "жезл" in lowered or "одноручний посох" in lowered:
        return "wand_1h"

    if "дворучний меч" in lowered:
        return "sword_2h"

    if "кинджал" in lowered:
        return "dagger_1h"

    if "лук" in lowered:
        return "bow_2h"

    if "арбалет" in lowered:
        return "crossbow_2h"

    if "меч" in lowered:
        return "sword_1h"

    if "щит" in lowered:
        return "shield"

    if "талісман" in lowered:
        return "talisman"

    return ""

# ==============================
# ✅ BAG SIZE 40 + LOCATION TRASH LOOT
# ==============================

DEFAULT_BAG_SLOTS = 40


def expand_bag_slots_to_40():
    """
    Робить базовий розмір сумки 40 слотів.
    Для існуючих персонажів, у кого менше 40, піднімає до 40.
    """

    try:
        cursor.execute("""
        UPDATE users
        SET bag_slots=?
        WHERE bag_slots IS NULL OR bag_slots < ?
        """, (DEFAULT_BAG_SLOTS, DEFAULT_BAG_SLOTS))

        conn.commit()
    except Exception:
        pass


def seed_location_trash_items():
    """
    Сірий лут для нової структури мобів 1–10.
    Кожен моб має свій унікальний trash item.
    """

    trash_items = [
        # 1–5: Початок Шляху
        (107, "🐗 Ікло дикого кабана", "trash", "grey", "trash", None, 1, 20, 0.12, 0, 0, 0, 0, 0, 0, 0),
        (108, "🌱 Рунічний пагін", "trash", "grey", "trash", None, 1, 20, 0.14, 0, 0, 0, 0, 0, 0, 0),

        (109, "🦡 Борсучий кіготь", "trash", "grey", "trash", None, 1, 20, 0.18, 0, 0, 0, 0, 0, 0, 0),
        (110, "💎 Слиз рунічного слимака", "trash", "grey", "trash", None, 1, 20, 0.20, 0, 0, 0, 0, 0, 0, 0),

        (111, "🦇 Крило лісового кажана", "trash", "grey", "trash", None, 1, 20, 0.24, 0, 0, 0, 0, 0, 0, 0),
        (112, "🩸 Крапля темної крові", "trash", "grey", "trash", None, 1, 20, 0.28, 0, 0, 0, 0, 0, 0, 0),

        (113, "🕷️ Павуча лапка", "trash", "grey", "trash", None, 1, 20, 0.32, 0, 0, 0, 0, 0, 0, 0),
        (114, "🧪 Кислотна залоза", "trash", "grey", "trash", None, 1, 20, 0.36, 0, 0, 0, 0, 0, 0, 0),

        (115, "🐺 Вовче ікло", "trash", "grey", "trash", None, 1, 20, 0.42, 0, 0, 0, 0, 0, 0, 0),
        (116, "👻 Примарна шерсть", "trash", "grey", "trash", None, 1, 20, 0.48, 0, 0, 0, 0, 0, 0, 0),

        # 6–10: Темний Бір
        (117, "👺 Гоблінський зуб", "trash", "grey", "trash", None, 1, 20, 0.55, 0, 0, 0, 0, 0, 0, 0),
        (118, "🧪 Знахарський амулет", "trash", "grey", "trash", None, 1, 20, 0.62, 0, 0, 0, 0, 0, 0, 0),

        (119, "🗡️ Тупий гоблінський кинджал", "trash", "grey", "trash", None, 1, 20, 0.70, 0, 0, 0, 0, 0, 0, 0),
        (120, "🧙 Шаманська намистина", "trash", "grey", "trash", None, 1, 20, 0.78, 0, 0, 0, 0, 0, 0, 0),

        (121, "🪓 Уламок сокири берсерка", "trash", "grey", "trash", None, 1, 20, 0.88, 0, 0, 0, 0, 0, 0, 0),
        (122, "🔥 Обвуглений рунічний попіл", "trash", "grey", "trash", None, 1, 20, 0.95, 0, 0, 0, 0, 0, 0, 0),

        (123, "🛡️ Іржава пластина щита", "trash", "grey", "trash", None, 1, 20, 1.05, 0, 0, 0, 0, 0, 0, 0),
        (124, "🔮 Рунічний уламок культиста", "trash", "grey", "trash", None, 1, 20, 1.15, 0, 0, 0, 0, 0, 0, 0),

        (125, "🧟 Осквернений уламок обладунку", "trash", "grey", "trash", None, 1, 20, 1.30, 0, 0, 0, 0, 0, 0, 0),
        (126, "🕯️ Чорна свічка віщуна", "trash", "grey", "trash", None, 1, 20, 1.45, 0, 0, 0, 0, 0, 0, 0),
    ]

    for item in trash_items:
        cursor.execute("""
        INSERT OR REPLACE INTO items (
            id, name, type, rarity, category,
            slot_key, weapon_hands,
            max_stack, sell_price,
            bonus_str, bonus_dex, bonus_int, bonus_wis, bonus_sta,
            pdef, mdef
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)

    conn.commit()


# ==============================
# ✅ OVERRIDE create_user WITH 40 SLOTS
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
        DEFAULT_BAG_SLOTS,
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

    ensure_equipment_slots(user_id)
    migrate_legacy_equipment_to_slots(user_id)
    expand_bag_slots_to_40()

# ==============================
# ✅ GOLD FORMAT HELPERS
# ==============================

GOLD_ICON = "💰"
GOLD_NAME = "золото"


def format_gold(amount):
    try:
        amount = float(amount)
    except Exception:
        amount = 0.0

    return f"{amount:.2f} {GOLD_ICON} {GOLD_NAME}"


# ==============================
# ✅ OVERRIDE: BUY ITEM FOR GOLD
# ==============================

def buy_item_for_gold(user_id, item_id, price, quantity=1):
    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено"
        }

    gold = row[0] or 0
    total_price = float(price) * quantity

    if gold < total_price:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо золота.\n"
                f"Потрібно: {format_gold(total_price)}\n"
                f"У тебе: {format_gold(gold)}"
            )
        }

    add_result = add_item(user_id, item_id, quantity)

    added = add_result.get("added", 0)
    lost = add_result.get("lost", 0)
    name = add_result.get("name", "Предмет")

    if added <= 0:
        return {
            "success": False,
            "message": "🎒 Сумка переповнена. Предмет не куплено."
        }

    actual_price = float(price) * added

    cursor.execute("""
    UPDATE users
    SET gold = gold - ?
    WHERE user_id=?
    """, (actual_price, user_id))

    conn.commit()

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    new_gold_row = cursor.fetchone()
    new_gold = new_gold_row[0] if new_gold_row else 0

    message = (
        f"✅ Куплено: {name} x{added}\n"
        f"💳 Витрачено: {format_gold(actual_price)}\n"
        f"💰 Залишилось: {format_gold(new_gold)}"
    )

    if lost > 0:
        message += f"\n⚠️ Не влізло в сумку: x{lost}"

    return {
        "success": True,
        "message": message,
        "added": added,
        "lost": lost,
        "gold_left": new_gold
    }


# ==============================
# ✅ OVERRIDE: SELL EQUIPMENT TO TRADER
# ==============================

def sell_inventory_item_to_trader(user_id, inventory_id):
    if is_inventory_item_equipped(user_id, inventory_id):
        return {
            "success": False,
            "message": (
                "❌ Неможливо продати вдягнений предмет.\n\n"
                "Спочатку зніми його з персонажа."
            )
        }

    cursor.execute("""
    SELECT
        inventory.id,
        inventory.item_id,
        items.name,
        items.category,
        inventory.quantity,
        items.sell_price
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.id=? AND inventory.user_id=?
    """, (inventory_id, user_id))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Предмет не знайдено в інвентарі."
        }

    inv_id, item_id, name, category, quantity, sell_price = row

    quantity = quantity or 1
    sell_price = sell_price or 0

    if category != "equipment":
        return {
            "success": False,
            "message": "❌ Через це меню можна продавати тільки спорядження."
        }

    if sell_price <= 0:
        return {
            "success": False,
            "message": "❌ Цей предмет не має ціни продажу."
        }

    total_gold = round(quantity * sell_price, 2)

    cursor.execute("""
    DELETE FROM inventory
    WHERE id=? AND user_id=?
    """, (inventory_id, user_id))

    cursor.execute("""
    UPDATE users
    SET gold = gold + ?
    WHERE user_id=?
    """, (total_gold, user_id))

    conn.commit()

    return {
        "success": True,
        "message": (
            f"💰 Спорядження продано торговцю.\n\n"
            f"📦 {name} x{quantity}\n"
            f"💰 Отримано: {format_gold(total_gold)}"
        ),
        "gold_earned": total_gold
    }


# ==============================
# ✅ OVERRIDE: COMMON EQUIPMENT BUY
# ==============================

def buy_common_equipment_from_trader(user_id, slot_key, item_profile=None):
    if slot_key not in SLOT_ORDER:
        return {
            "success": False,
            "message": "❌ Невідомий слот спорядження."
        }

    if slot_key == "main_hand" and item_profile not in MAIN_HAND_PROFILES:
        return {
            "success": False,
            "message": "❌ Невідомий тип зброї."
        }

    if slot_key == "off_hand" and item_profile not in OFF_HAND_PROFILES:
        return {
            "success": False,
            "message": "❌ Невідомий тип предмета для другої руки."
        }

    player_level = get_player_level(user_id)
    price = get_common_equipment_price_for_slot(player_level, slot_key)

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено."
        }

    gold = row[0] or 0.0

    if gold < price:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо золота.\n\n"
                f"💳 Потрібно: {format_gold(price)}\n"
                f"💰 У тебе: {format_gold(gold)}"
            )
        }

    result = create_generated_equipment_item_for_slot(
        user_id=user_id,
        item_level=player_level,
        rarity="common",
        slot_key=slot_key,
        item_profile=item_profile
    )

    if not result.get("success"):
        return result

    cursor.execute("""
    UPDATE users
    SET gold = gold - ?
    WHERE user_id=?
    """, (price, user_id))

    conn.commit()

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    new_gold_row = cursor.fetchone()
    new_gold = new_gold_row[0] if new_gold_row else 0

    return {
        "success": True,
        "message": (
            f"✅ Куплено базове спорядження.\n\n"
            f"📦 {result['name']}\n"
            f"🏷 Рівень предмета: {player_level}\n"
            f"💳 Сплачено: {format_gold(price)}\n"
            f"💰 Залишилось: {format_gold(new_gold)}"
        )
    }


# ==============================
# ✅ OVERRIDE: REPAIR ONE
# ==============================

def repair_equipped_item(user_id, inventory_id):
    if not is_inventory_item_equipped(user_id, inventory_id):
        return {
            "success": False,
            "message": "❌ Цей предмет не вдягнений."
        }

    item = get_item_by_inventory_id_full(inventory_id)

    if not item:
        return {
            "success": False,
            "message": "❌ Предмет не знайдено."
        }

    (
        inv_id,
        item_id,
        name,
        type_,
        rarity,
        category,
        slot_key,
        weapon_hands,
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
        return {
            "success": False,
            "message": "❌ Цей предмет не є спорядженням."
        }

    if durability is None:
        durability = 100

    repair_cost = calculate_repair_cost(durability, rarity)

    if repair_cost <= 0:
        return {
            "success": False,
            "message": f"🛠️ {name} вже має повну міцність."
        }

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено."
        }

    gold = row[0] or 0.0

    if gold < repair_cost:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо золота для ремонту.\n\n"
                f"📦 Предмет: {name}\n"
                f"💳 Потрібно: {format_gold(repair_cost)}\n"
                f"💰 У тебе: {format_gold(gold)}"
            )
        }

    cursor.execute("""
    UPDATE inventory
    SET durability=100
    WHERE id=?
    """, (inventory_id,))

    cursor.execute("""
    UPDATE users
    SET gold = gold - ?
    WHERE user_id=?
    """, (repair_cost, user_id))

    conn.commit()

    return {
        "success": True,
        "message": (
            f"✅ Предмет відремонтовано.\n\n"
            f"📦 {name}\n"
            f"🛠️ Міцність: {durability}/100 → 100/100\n"
            f"💳 Сплачено: {format_gold(repair_cost)}"
        ),
        "repair_cost": repair_cost
    }


# ==============================
# ✅ OVERRIDE: REPAIR ALL
# ==============================

def repair_all_equipped(user_id):
    equipped_items = get_equipped_items_for_repair(user_id)
    total_cost = get_total_repair_cost(user_id)

    if total_cost <= 0:
        return {
            "success": False,
            "message": "🛠️ Усе спорядження вже має повну міцність.",
            "total_cost": 0.0
        }

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено.",
            "total_cost": total_cost
        }

    gold = row[0] or 0.0

    if gold < total_cost:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо золота для повного ремонту.\n\n"
                f"💳 Потрібно: {format_gold(total_cost)}\n"
                f"💰 У тебе: {format_gold(gold)}\n\n"
                f"ℹ️ Можеш відремонтувати окремі речі нижче."
            ),
            "total_cost": total_cost
        }

    repaired_count = 0

    for item in equipped_items:
        inventory_id = item["inventory_id"]

        if not inventory_id:
            continue

        if item["repair_cost"] <= 0:
            continue

        cursor.execute("""
        UPDATE inventory
        SET durability=100
        WHERE id=?
        """, (inventory_id,))

        repaired_count += 1

    cursor.execute("""
    UPDATE users
    SET gold = gold - ?
    WHERE user_id=?
    """, (total_cost, user_id))

    conn.commit()

    return {
        "success": True,
        "message": (
            f"✅ Спорядження відремонтовано.\n"
            f"🛠️ Відремонтовано речей: {repaired_count}\n"
            f"💳 Сплачено: {format_gold(total_cost)}"
        ),
        "total_cost": total_cost,
        "repaired_count": repaired_count
    }

# ==============================
# ✅ SHOP PREVIEW PURCHASE SYSTEM
# ==============================

def init_shop_preview_system():
    migrations = [
        ("items", "shop_preview_owner", "INTEGER DEFAULT NULL"),
        ("items", "shop_preview_price", "REAL DEFAULT 0"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()


def cleanup_shop_previews_for_user(user_id):
    init_shop_preview_system()

    try:
        cursor.execute("""
        DELETE FROM items
        WHERE shop_preview_owner=?
          AND id NOT IN (
              SELECT item_id FROM inventory
          )
        """, (user_id,))

        conn.commit()
    except Exception:
        pass


def create_common_equipment_shop_preview(user_id, slot_key, item_profile=None):
    """
    Створює preview-предмет у таблиці items, але НЕ додає його в інвентар.

    Це потрібно, щоб гравець бачив саме той предмет, який купить.
    """

    init_dynamic_equipment_system()
    init_weapon_damage_system()
    init_shop_preview_system()

    cleanup_shop_previews_for_user(user_id)

    if slot_key not in SLOT_ORDER:
        return {
            "success": False,
            "message": "❌ Невідомий слот спорядження."
        }

    if slot_key == "main_hand" and item_profile not in MAIN_HAND_PROFILES:
        return {
            "success": False,
            "message": "❌ Невідомий тип зброї."
        }

    if slot_key == "off_hand" and item_profile not in OFF_HAND_PROFILES:
        return {
            "success": False,
            "message": "❌ Невідомий тип предмета для другої руки."
        }

    player_level = get_player_level(user_id)
    item_level = player_level
    rarity = "common"
    price = get_common_equipment_price_for_slot(item_level, slot_key)

    item_profile = get_profile_for_generated_item(slot_key, item_profile)

    weapon_hands = 1
    weapon_attack_type = ""

    if slot_key == "main_hand":
        profile = MAIN_HAND_PROFILES[item_profile]
        weapon_hands = profile["hands"]
        weapon_attack_type = profile["attack_type"]
        name = get_dynamic_weapon_name(slot_key, rarity, weapon_hands, item_profile)
        type_ = "weapon"

    elif slot_key == "off_hand":
        profile = OFF_HAND_PROFILES[item_profile]
        weapon_hands = 1
        weapon_attack_type = profile["attack_type"]
        name = get_dynamic_weapon_name(slot_key, rarity, weapon_hands, item_profile)
        type_ = "offhand"

    else:
        item_profile = ""
        weapon_hands = 1
        name = get_dynamic_armor_name(slot_key, rarity)
        type_ = slot_key

    name = f"{name} {item_level} рівня"

    stats = generate_dynamic_equipment_stats(
        slot_key=slot_key,
        item_level=item_level,
        rarity=rarity,
        weapon_hands=weapon_hands,
        item_profile=item_profile
    )

    sell_price = get_dynamic_sell_price(item_level, rarity)

    weapon_min_damage = 0
    weapon_max_damage = 0
    weapon_min_magic_damage = 0
    weapon_max_magic_damage = 0

    if slot_key == "main_hand":
        min_dmg, max_dmg = calculate_weapon_damage_by_values(
            item_level=item_level,
            rarity=rarity,
            weapon_hands=weapon_hands
        )

        if weapon_attack_type == "magical":
            weapon_min_magic_damage = min_dmg
            weapon_max_magic_damage = max_dmg
        else:
            weapon_min_damage = min_dmg
            weapon_max_damage = max_dmg

    cursor.execute("""
    INSERT INTO items (
        name,
        type,
        rarity,
        category,
        slot_key,
        weapon_hands,
        max_stack,
        sell_price,
        bonus_str,
        bonus_dex,
        bonus_int,
        bonus_wis,
        bonus_sta,
        pdef,
        mdef,
        item_level,
        is_generated,
        item_subtype,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type,
        shop_preview_owner,
        shop_preview_price
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        type_,
        rarity,
        "equipment",
        slot_key,
        weapon_hands,
        1,
        sell_price,
        stats["bonus_str"],
        stats["bonus_dex"],
        stats["bonus_int"],
        stats["bonus_wis"],
        stats["bonus_sta"],
        stats["pdef"],
        stats["mdef"],
        item_level,
        1,
        item_profile,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type,
        user_id,
        price
    ))

    item_id = cursor.lastrowid
    conn.commit()

    return {
        "success": True,
        "item_id": item_id,
        "price": price,
        "name": name
    }


def get_shop_preview_item(item_id, user_id):
    init_shop_preview_system()

    cursor.execute("""
    SELECT
        id,
        name,
        type,
        rarity,
        category,
        slot_key,
        weapon_hands,
        max_stack,
        sell_price,
        bonus_str,
        bonus_dex,
        bonus_int,
        bonus_wis,
        bonus_sta,
        pdef,
        mdef,
        item_level,
        item_subtype,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type,
        shop_preview_price
    FROM items
    WHERE id=?
      AND shop_preview_owner=?
    """, (item_id, user_id))

    return cursor.fetchone()


def cancel_common_equipment_shop_preview(user_id, item_id):
    init_shop_preview_system()

    cursor.execute("""
    DELETE FROM items
    WHERE id=?
      AND shop_preview_owner=?
      AND id NOT IN (
          SELECT item_id FROM inventory
      )
    """, (item_id, user_id))

    conn.commit()

    return {
        "success": True,
        "message": "❌ Купівлю скасовано."
    }


def confirm_common_equipment_shop_preview(user_id, item_id):
    init_shop_preview_system()

    preview = get_shop_preview_item(item_id, user_id)

    if not preview:
        return {
            "success": False,
            "message": "❌ Попередній перегляд предмета не знайдено або застарів."
        }

    price = preview[23] or 0
    name = preview[1]

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено."
        }

    gold = row[0] or 0.0

    if gold < price:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо золота.\n\n"
                f"💳 Потрібно: {format_gold(price)}\n"
                f"💰 У тебе: {format_gold(gold)}"
            )
        }

    capacity = get_bag_capacity(user_id)
    used_slots = get_inventory_used_slots(user_id)

    if used_slots >= capacity:
        return {
            "success": False,
            "message": "🎒 Сумка переповнена. Предмет не куплено."
        }

    cursor.execute("""
    INSERT INTO inventory (
        user_id,
        item_id,
        quantity,
        durability
    )
    VALUES (?, ?, ?, ?)
    """, (
        user_id,
        item_id,
        1,
        100
    ))

    cursor.execute("""
    UPDATE users
    SET gold = gold - ?
    WHERE user_id=?
    """, (price, user_id))

    cursor.execute("""
    UPDATE items
    SET shop_preview_owner=NULL,
        shop_preview_price=0
    WHERE id=?
    """, (item_id,))

    conn.commit()

    cursor.execute("""
    SELECT gold
    FROM users
    WHERE user_id=?
    """, (user_id,))

    new_gold_row = cursor.fetchone()
    new_gold = new_gold_row[0] if new_gold_row else 0

    return {
        "success": True,
        "message": (
            f"✅ Куплено базове спорядження.\n\n"
            f"📦 {name}\n"
            f"💳 Сплачено: {format_gold(price)}\n"
            f"💰 Залишилось: {format_gold(new_gold)}"
        )
    }


def get_shop_preview_weapon_damage_text(item_id):
    init_weapon_damage_system()

    cursor.execute("""
    SELECT
        name,
        slot_key,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type
    FROM items
    WHERE id=?
    """, (item_id,))

    row = cursor.fetchone()

    if not row:
        return None

    (
        name,
        slot_key,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type
    ) = row

    if slot_key != "main_hand":
        return None

    if weapon_attack_type == "magical":
        return f"🔮 Маг. урон: {weapon_min_magic_damage}-{weapon_max_magic_damage}"

    return f"⚔️ Урон: {weapon_min_damage}-{weapon_max_damage}"

# ==============================
# ✅ CHARACTER NAME / CLASS / MP SYSTEM
# ==============================

CLASS_CONFIGS = {
    "warrior": {
        "name": "🛡️ Воїн",
        "resource": "rage",
        "description": (
            "Фізичний боєць ближнього бою.\n"
            "Основні характеристики: Сила, Витривалість.\n"
            "Ресурс у бою: 🔴 Лютість."
        )
    },
    "knight": {
        "name": "⚔️ Лицар",
        "resource": "rage",
        "description": (
            "Захисник із високим фізичним захистом і щитом.\n"
            "Основні характеристики: Витривалість, Фіз. захист.\n"
            "Ресурс у бою: 🔴 Лютість."
        )
    },
    "scout": {
        "name": "🏹 Скаут",
        "resource": "combat_energy",
        "description": (
            "Дистанційний фізичний боєць із пастками та точними пострілами.\n"
            "Основні характеристики: Спритність, Сила.\n"
            "Ресурс у бою: 🟡 Енергія."
        )
    },
    "rogue": {
        "name": "🗡️ Розбійник",
        "resource": "combat_energy_combo",
        "description": (
            "Швидкий боєць ближнього бою з майбутньою механікою комбо.\n"
            "Основні характеристики: Спритність, Сила.\n"
            "Ресурс у бою: 🟡 Енергія + комбо-очки."
        )
    },
    "mage": {
        "name": "🔮 Маг",
        "resource": "mana",
        "description": (
            "Магічний боєць із високим вибуховим уроном.\n"
            "Основні характеристики: Інтелект, Мудрість.\n"
            "Ресурс у бою: 🔵 Мана."
        )
    },
    "priest": {
        "name": "⚕️ Жрець",
        "resource": "mana",
        "description": (
            "Магічний клас підтримки з лікуванням і захистом.\n"
            "Основні характеристики: Мудрість, Інтелект.\n"
            "Ресурс у бою: 🔵 Мана."
        )
    }
}


CLASS_RESET_SPHERE_ITEM_ID = 301


def init_character_class_system():
    migrations = [
        ("users", "character_name", "TEXT DEFAULT ''"),
        ("users", "character_class", "TEXT DEFAULT ''"),
        ("users", "class_selected_at", "TEXT DEFAULT ''"),
        ("users", "class_change_available", "INTEGER DEFAULT 0"),
        ("users", "mp", "INTEGER DEFAULT 0"),
        ("users", "max_mp", "INTEGER DEFAULT 0"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()


def seed_class_reset_sphere_item():
    """
    🔮 Сфера нового шляху.
    Предмет для майбутньої зміни класу.
    Зараз додаємо в базу, щоб можна було видавати через DEV і тестувати інвентар.
    """

    try:
        cursor.execute("""
        INSERT OR REPLACE INTO items (
            id,
            name,
            type,
            rarity,
            category,
            slot_key,
            weapon_hands,
            max_stack,
            sell_price,
            bonus_str,
            bonus_dex,
            bonus_int,
            bonus_wis,
            bonus_sta,
            pdef,
            mdef
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            CLASS_RESET_SPHERE_ITEM_ID,
            "🔮 Сфера нового шляху",
            "class_reset",
            "epic",
            "potion",
            None,
            1,
            10,
            0.0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
        ))

        conn.commit()
    except Exception:
        pass


def get_character_name(user_id):
    init_character_class_system()

    cursor.execute("""
    SELECT character_name
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return ""

    return row[0] or ""


def get_character_class(user_id):
    init_character_class_system()

    cursor.execute("""
    SELECT character_class
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return ""

    return row[0] or ""


def get_character_class_display(user_id):
    class_key = get_character_class(user_id)

    if not class_key:
        return "Не обрано"

    return CLASS_CONFIGS.get(class_key, {}).get("name", "Невідомий клас")


def get_character_resource_type(user_id):
    class_key = get_character_class(user_id)

    if not class_key:
        return ""

    return CLASS_CONFIGS.get(class_key, {}).get("resource", "")


def normalize_character_name(name):
    name = (name or "").strip()

    while "  " in name:
        name = name.replace("  ", " ")

    return name


def validate_character_name(name):
    name = normalize_character_name(name)

    if len(name) < 2:
        return {
            "success": False,
            "message": "❌ Ім’я персонажа має містити щонайменше 2 символи."
        }

    if len(name) > 24:
        return {
            "success": False,
            "message": "❌ Ім’я персонажа не може бути довшим за 24 символи."
        }

    forbidden = ["/", "\\", "<", ">", "{", "}", "[", "]", "|"]

    for symbol in forbidden:
        if symbol in name:
            return {
                "success": False,
                "message": "❌ Ім’я містить недозволені символи."
            }

    return {
        "success": True,
        "name": name
    }


def set_character_name(user_id, name):
    init_character_class_system()

    validation = validate_character_name(name)

    if not validation["success"]:
        return validation

    clean_name = validation["name"]

    cursor.execute("""
    UPDATE users
    SET character_name=?
    WHERE user_id=?
    """, (clean_name, user_id))

    conn.commit()

    return {
        "success": True,
        "name": clean_name,
        "message": f"✅ Ім’я персонажа збережено: {clean_name}"
    }


def set_character_class(user_id, class_key):
    init_character_class_system()

    if class_key not in CLASS_CONFIGS:
        return {
            "success": False,
            "message": "❌ Невідомий клас персонажа."
        }

    from datetime import datetime

    cursor.execute("""
    UPDATE users
    SET character_class=?,
        class_selected_at=?
    WHERE user_id=?
    """, (
        class_key,
        datetime.now().isoformat(),
        user_id
    ))

    conn.commit()

    refresh_user_mp(user_id)

    return {
        "success": True,
        "class_key": class_key,
        "class_name": CLASS_CONFIGS[class_key]["name"],
        "message": f"✅ Клас обрано: {CLASS_CONFIGS[class_key]['name']}"
    }


def needs_character_name(user_id):
    return get_character_name(user_id) == ""


def needs_character_class(user_id):
    return get_character_class(user_id) == ""


def get_max_mp(user_id):
    """
    Базова формула MP.
    Поки проста, щоб не ламати баланс:

    max_mp = 50 + INT * 5 + WIS * 3

    Надалі можна буде змінити під класи.
    """

    stats = get_player_stats(user_id)

    if not stats:
        return 0

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    max_mp = 50 + (total_int * 5) + (total_wis * 3)

    return max(0, int(max_mp))


def refresh_user_mp(user_id):
    init_character_class_system()

    class_key = get_character_class(user_id)
    resource_type = CLASS_CONFIGS.get(class_key, {}).get("resource", "")

    if resource_type != "mana":
        cursor.execute("""
        UPDATE users
        SET mp=0,
            max_mp=0
        WHERE user_id=?
        """, (user_id,))

        conn.commit()

        return {
            "mp": 0,
            "max_mp": 0
        }

    max_mp = get_max_mp(user_id)

    cursor.execute("""
    SELECT mp
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()
    current_mp = row[0] if row else max_mp

    if current_mp is None or current_mp <= 0:
        current_mp = max_mp

    if current_mp > max_mp:
        current_mp = max_mp

    cursor.execute("""
    UPDATE users
    SET mp=?,
        max_mp=?
    WHERE user_id=?
    """, (
        current_mp,
        max_mp,
        user_id
    ))

    conn.commit()

    return {
        "mp": current_mp,
        "max_mp": max_mp
    }


def get_user_mp(user_id):
    refresh_user_mp(user_id)

    cursor.execute("""
    SELECT mp, max_mp
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "mp": 0,
            "max_mp": 0
        }

    mp, max_mp = row

    return {
        "mp": mp or 0,
        "max_mp": max_mp or 0
    }


def get_character_profile_summary(user_id):
    init_character_class_system()

    return {
        "name": get_character_name(user_id),
        "class_key": get_character_class(user_id),
        "class_name": get_character_class_display(user_id),
        "resource_type": get_character_resource_type(user_id),
        "mp_data": get_user_mp(user_id)
    }


def grant_class_change_available(user_id):
    init_character_class_system()

    cursor.execute("""
    UPDATE users
    SET class_change_available=1
    WHERE user_id=?
    """, (user_id,))

    conn.commit()

    return {
        "success": True,
        "message": "✅ Зміна класу доступна."
    }


def grant_class_change_available(user_id):
    init_character_class_system()

    cursor.execute("""
    UPDATE users
    SET class_change_available=1
    WHERE user_id=?
    """, (user_id,))

    conn.commit()

    return {
        "success": True,
        "message": "✅ Зміна класу доступна."
    }


def consume_class_change_available(user_id):
    init_character_class_system()

    cursor.execute("""
    SELECT class_change_available
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row or not row[0]:
        return {
            "success": False,
            "message": "❌ Зміна класу недоступна."
        }

    cursor.execute("""
    UPDATE users
    SET class_change_available=0
    WHERE user_id=?
    """, (user_id,))

    conn.commit()

    return {
        "success": True,
        "message": "✅ Дозвіл на зміну класу використано."
    }

# ==============================
# ✅ PROFILE DISPLAY HELPERS
# ==============================

def get_physical_crit_chance_display(user_id):
    """
    Шанс фізичного криту для профілю.
    Формула відповідає логіці combat_system:
    5 + ((DEX - 10) / level) * 0.5
    """

    stats = get_player_stats(user_id)

    if not stats:
        return 5.0

    total_str, total_dex, total_int, total_wis, total_sta, level = stats

    if level <= 0:
        level = 1

    chance = 5 + ((total_dex - 10) / max(1, level)) * 0.5

    return max(1.0, min(35.0, chance))


def get_magical_crit_chance_display(user_id):
    """
    Шанс магічного криту для профілю.
    Формула відповідає логіці combat_system:
    5 + ((WIS - 10) / level) * 0.5
    """

    stats = get_player_stats(user_id)

    if not stats:
        return 5.0

    total_str, total_dex, total_int, total_wis, total_sta, level = stats

    if level <= 0:
        level = 1

    chance = 5 + ((total_wis - 10) / max(1, level)) * 0.5

    return max(1.0, min(35.0, chance))


def get_base_dodge_chance_display(user_id):
    """
    Базовий ухил для профілю.

    У реальному бою ухил залежить від DEX гравця і DEX конкретного моба.
    Тут показуємо базове значення для довідки.
    """

    return 5.0


def get_enemy_crit_chance_against_player(user_id):
    """
    Шанс криту ворога по гравцю.
    Формула відповідає combat_system:
    max(0, 10 - STA // 25)
    """

    stats = get_player_stats(user_id)

    if not stats:
        return 10.0

    total_str, total_dex, total_int, total_wis, total_sta, level = stats

    chance = max(0, 10 - (total_sta // 25))

    return float(chance)

# ==============================
# ✅ CLASS RESET SPHERE USAGE
# ==============================

def has_class_change_available(user_id):
    init_character_class_system()

    cursor.execute("""
    SELECT class_change_available
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return False

    return bool(row[0])


def grant_class_change_available(user_id):
    init_character_class_system()

    cursor.execute("""
    UPDATE users
    SET class_change_available=1
    WHERE user_id=?
    """, (user_id,))

    conn.commit()

    return {
        "success": True,
        "message": "✅ Зміна класу доступна."
    }


def consume_class_change_available(user_id):
    init_character_class_system()

    cursor.execute("""
    SELECT class_change_available
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row or not row:
        return {
            "success": False,
            "message": "❌ Зміна класу недоступна."
        }

    cursor.execute("""
    UPDATE users
    SET class_change_available=0
    WHERE user_id=?
    """, (user_id,))

    conn.commit()

    return {
        "success": True,
        "message": "✅ Дозвіл на зміну класу використано."
    }


def is_class_reset_sphere_inventory_item(user_id, inventory_id):
    seed_class_reset_sphere_item()

    cursor.execute("""
    SELECT
        inventory.id,
        inventory.item_id,
        items.type,
        items.name
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.id=?
      AND inventory.user_id=?
    """, (inventory_id, user_id))

    row = cursor.fetchone()

    if not row:
        return False

    inv_id, item_id, type_, name = row

    return item_id == CLASS_RESET_SPHERE_ITEM_ID or type_ == "class_reset"


def use_class_reset_sphere_from_inventory(user_id, inventory_id):
    """
    Використання 🔮 Сфери нового шляху.

    Ефект:
    - витрачає 1 предмет;
    - відкриває право на зміну класу;
    - сам вибір класу виконується в handlers/start.py.
    """

    init_character_class_system()
    seed_class_reset_sphere_item()

    cursor.execute("""
    SELECT
        inventory.id,
        inventory.item_id,
        inventory.quantity,
        items.name,
        items.type
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.id=?
      AND inventory.user_id=?
    """, (inventory_id, user_id))

    row = cursor.fetchone()

    if not row or not row[0]:
        return {
            "success": False,
            "message": "❌ Предмет не знайдено в інвентарі."
        }

    inv_id, item_id, quantity, name, type_ = row

    if item_id != CLASS_RESET_SPHERE_ITEM_ID and type_ != "class_reset":
        return {
            "success": False,
            "message": "❌ Це не Сфера нового шляху."
        }

    quantity = quantity or 1

    if quantity <= 1:
        cursor.execute("""
        DELETE FROM inventory
        WHERE id=?
          AND user_id=?
        """, (inventory_id, user_id))
    else:
        cursor.execute("""
        UPDATE inventory
        SET quantity = quantity - 1
        WHERE id=?
          AND user_id=?
        """, (inventory_id, user_id))

    cursor.execute("""
    UPDATE users
    SET class_change_available=1
    WHERE user_id=?
    """, (user_id,))

    conn.commit()

    return {
        "success": True,
        "message": (
            "🔮 Сфера нового шляху використана.\n\n"
            "Ти можеш обрати новий клас персонажа."
        )
    }