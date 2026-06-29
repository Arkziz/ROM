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
    "chest": "🦹 Тіло",
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
    "uncommon": 3.0,
    "rare": 10.0,
    "epic": 25.0
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
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    # ==============================
    # REPAIR OLD USERS
    # ==============================

    cursor.execute("UPDATE users SET gold = 0 WHERE gold IS NULL")
    cursor.execute("UPDATE users SET kills = 0 WHERE kills IS NULL")
    cursor.execute("UPDATE users SET bag_slots = 20 WHERE bag_slots IS NULL")
    cursor.execute("""
    UPDATE users
    SET current_location = 'start_path'
    WHERE current_location IS NULL OR current_location = ''
    """)

    # ==============================
    # REPAIR OLD INVENTORY
    # ==============================

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
        # id, name, type, rarity, category, slot_key, weapon_hands,
        # max_stack, sell_price,
        # str, dex, int, wis, sta, pdef, mdef

        # ==============================
        # MAIN HAND
        # ==============================
        (1, "⚪ Старий меч", "weapon", "common", "equipment", "main_hand", 1, 1, 1.00, 1, 0, 0, 0, 0, 0, 0),
        (2, "🟢 Залізний меч", "weapon", "uncommon", "equipment", "main_hand", 1, 1, 3.00, 2, 0, 0, 0, 0, 0, 0),
        (3, "🔵 Меч воїна", "weapon", "rare", "equipment", "main_hand", 1, 1, 8.00, 4, 0, 0, 0, 0, 0, 0),
        (4, "🟣 Епічний клинок", "weapon", "epic", "equipment", "main_hand", 2, 1, 25.00, 7, 0, 0, 0, 0, 0, 0),

        # ==============================
        # OFF HAND
        # ==============================
        (8, "⚪ Деревʼяний щит", "offhand", "common", "equipment", "off_hand", 1, 1, 1.00, 0, 0, 0, 0, 1, 2, 0),
        (9, "🟢 Малий круглий щит", "offhand", "uncommon", "equipment", "off_hand", 1, 1, 3.00, 0, 0, 0, 0, 2, 4, 0),
        (10, "🔵 Рунічна сфера", "offhand", "rare", "equipment", "off_hand", 1, 1, 8.00, 0, 0, 1, 3, 0, 0, 5),

        # ==============================
        # HELMET
        # ==============================
        (11, "⚪ Старий шолом", "helmet", "common", "equipment", "helmet", 1, 1, 1.00, 0, 0, 0, 0, 1, 2, 0),
        (12, "🟢 Шкіряний капюшон", "helmet", "uncommon", "equipment", "helmet", 1, 1, 3.00, 0, 1, 0, 1, 1, 3, 1),

        # ==============================
        # SHOULDERS
        # ==============================
        (13, "⚪ Потерті наплічники", "shoulders", "common", "equipment", "shoulders", 1, 1, 1.00, 0, 0, 0, 0, 1, 2, 0),
        (14, "🟢 Наплічники слідопита", "shoulders", "uncommon", "equipment", "shoulders", 1, 1, 3.00, 0, 1, 0, 0, 2, 4, 0),

        # ==============================
        # CHEST
        # ==============================
        (5, "⚪ Стара броня", "armor", "common", "equipment", "chest", 1, 1, 1.00, 0, 0, 0, 1, 1, 2, 0),
        (6, "🟢 Шкіряна броня", "armor", "uncommon", "equipment", "chest", 1, 1, 3.00, 0, 1, 0, 2, 2, 4, 1),
        (7, "🔵 Лицарська броня", "armor", "rare", "equipment", "chest", 1, 1, 8.00, 0, 2, 0, 3, 4, 8, 2),

        # ==============================
        # GLOVES
        # ==============================
        (15, "⚪ Старі рукавиці", "gloves", "common", "equipment", "gloves", 1, 1, 1.00, 0, 0, 0, 0, 1, 1, 0),
        (16, "🟢 Рукавиці мисливця", "gloves", "uncommon", "equipment", "gloves", 1, 1, 3.00, 1, 1, 0, 0, 1, 2, 0),

        # ==============================
        # LEGS
        # ==============================
        (17, "⚪ Старі поножі", "legs", "common", "equipment", "legs", 1, 1, 1.00, 0, 0, 0, 0, 1, 2, 0),
        (18, "🟢 Шкіряні поножі", "legs", "uncommon", "equipment", "legs", 1, 1, 3.00, 0, 1, 0, 0, 2, 4, 0),

        # ==============================
        # BOOTS
        # ==============================
        (19, "⚪ Старі чоботи", "boots", "common", "equipment", "boots", 1, 1, 1.00, 0, 1, 0, 0, 0, 1, 0),
        (20, "🟢 Чоботи слідопита", "boots", "uncommon", "equipment", "boots", 1, 1, 3.00, 0, 2, 0, 0, 1, 2, 0),

        # ==============================
        # NECKLACE
        # ==============================
        (21, "⚪ Простий амулет", "necklace", "common", "equipment", "necklace", 1, 1, 1.00, 0, 0, 0, 1, 0, 0, 2),
        (22, "🟢 Амулет мудрості", "necklace", "uncommon", "equipment", "necklace", 1, 1, 3.00, 0, 0, 0, 3, 0, 0, 5),
        (23, "🔵 Рунічне намисто", "necklace", "rare", "equipment", "necklace", 1, 1, 8.00, 0, 0, 1, 5, 0, 0, 10),

        # ==============================
        # RING
        # ==============================
        (24, "⚪ Мідне кільце", "ring", "common", "equipment", "ring", 1, 1, 1.00, 1, 0, 0, 0, 0, 0, 0),
        (25, "🟢 Перстень спритності", "ring", "uncommon", "equipment", "ring", 1, 1, 3.00, 0, 3, 0, 0, 0, 0, 0),
        (26, "🔵 Перстень сили", "ring", "rare", "equipment", "ring", 1, 1, 8.00, 5, 0, 0, 0, 0, 0, 0),

        # ==============================
        # TRASH
        # ==============================
        (101, "🐾 Густа вовча шкура", "trash", "grey", "trash", None, 1, 20, 0.50, 0, 0, 0, 0, 0, 0, 0),
        (102, "🐗 Жорстка щетина", "trash", "grey", "trash", None, 1, 20, 0.15, 0, 0, 0, 0, 0, 0, 0),
        (103, "🦡 Борсучий жир", "trash", "grey", "trash", None, 1, 20, 0.25, 0, 0, 0, 0, 0, 0, 0),
        (104, "👹 Гоблінська сережка", "trash", "grey", "trash", None, 1, 20, 0.35, 0, 0, 0, 0, 0, 0, 0),
        (105, "🕷️ Липка павутина", "trash", "grey", "trash", None, 1, 20, 0.60, 0, 0, 0, 0, 0, 0, 0),
        (106, "💎 Тріснутий рунічний уламок", "trash", "grey", "trash", None, 1, 20, 0.75, 0, 0, 0, 0, 0, 0, 0),

        # ==============================
        # POTIONS
        # ==============================
        (201, "🔴 Мале зілля здоров’я", "potion_hp", "common", "potion", None, 1, 10, 1.00, 0, 0, 0, 0, 0, 0, 0),
        (202, "🔵 Мале зілля мани", "potion_mp", "common", "potion", None, 1, 10, 1.20, 0, 0, 0, 0, 0, 0, 0),
        (203, "🔴 Середнє зілля здоров’я", "potion_hp_medium", "common", "potion", None, 1, 10, 3.00, 0, 0, 0, 0, 0, 0, 0),
        (204, "🔵 Середнє зілля мани", "potion_mp_medium", "common", "potion", None, 1, 10, 3.60, 0, 0, 0, 0, 0, 0, 0),

        # ==============================
        # RUNES
        # ==============================
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

    # legacy compatibility
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

    # legacy compatibility
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
    # compatibility function for old handlers
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
    # compatibility return shape: 17 fields
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
    # compatibility return shape: 17 fields
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

    # ==============================
    # LEVEL REQUIREMENT CHECK
    # ==============================

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

    # Якщо пробуємо вдягнути off_hand, але main_hand дворучний
    if slot_key == "off_hand" and is_main_hand_two_handed(user_id):
        return "❌ Неможливо: дворучна зброя блокує другу руку"

    # Якщо вдягаємо дворучну зброю — очищаємо off_hand
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

# EXP за моба свого рівня.
# Це базова шкала, під яку рахується вся прогресія.
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


# Скільки "умовних мобів" потрібно на перехід між рівнями.
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
    """
    EXP за моба рівня level.
    Для 1–30 використовується ручна таблиця.
    Після 30 рівня — м'яке масштабування.
    """

    level = int(level)

    if level in BASE_EXP_BY_LEVEL:
        return BASE_EXP_BY_LEVEL[level]

    if level > 30:
        return int(BASE_EXP_BY_LEVEL[30] * (1.12 ** (level - 30)))

    return BASE_EXP_BY_LEVEL[1]


def get_contract_exp_for_level(level):
    """
    EXP за 1 щоденний контракт.
    Затверджено: 1 контракт = 20 умовних мобів поточного рівня.
    """

    return get_base_exp_for_level(level) * CONTRACT_MOBS_EQUIVALENT


def get_exp_to_next_level(level):
    """
    EXP для переходу з level на level + 1.
    Формула:
    EXP_to_next = base_exp_for_level * conditional_mobs_to_next
    """

    level = int(level)

    base_exp = get_base_exp_for_level(level)

    if level in CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL:
        mobs_required = CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL[level]
        return int(base_exp * mobs_required)

    # Після 30 рівня — тимчасова м'яка прогресія.
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


def damage_equipped_items_on_death(user_id, amount=10):
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
    """
    Природний знос спорядження після перемоги.

    Правила:
    - після перемоги є chance_percent шанс, що знос спрацює;
    - якщо спрацював, випадкова одягнена річ втрачає -1 durability;
    - природний знос НЕ може опустити durability нижче 1;
    - до 0 предмет може добити тільки смерть.
    """

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

        # Природний знос не може зняти останню одиницю міцності
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
    """
    Лінива ініціалізація системи контрактів.
    """

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
        reward_exp INTEGER
    )
    """)

    migrations = [
        ("users", "daily_contracts_completed", "INTEGER DEFAULT 0"),
        ("users", "daily_contract_date", "TEXT DEFAULT ''"),

        ("user_active_contracts", "target_mob_name", "TEXT DEFAULT ''"),
        ("user_active_contracts", "target_mob_level", "INTEGER DEFAULT 0"),
        ("user_active_contracts", "target_min_level", "INTEGER DEFAULT 0"),
        ("user_active_contracts", "target_max_level", "INTEGER DEFAULT 0"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    # Старі активні контракти без конкретного моба прибираємо,
    # бо нова система вже працює за конкретною ціллю.
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
        reward_exp
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
        reward_exp
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
        "reward_exp": reward_exp
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
    """
    Створює контракт на конкретного моба.

    Правило:
    - 1 контракт = EXP за 20 умовних мобів поточного рівня.
    - target_mob_name вибирається у handlers/contracts.py
      з доступних мобів для рівня гравця.
    """

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
        reward_exp
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        reward_exp
    ))

    conn.commit()

    return {
        "success": True,
        "message": (
            f"📜 Контракт прийнято!\n\n"
            f"🎯 Завдання:\n"
            f"Вбий {target_kills} × {target_mob_name} "
            f"(рівень {target_mob_level}).\n\n"
            f"✨ Нагорода: {reward_exp} EXP"
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
    """
    Викликається після перемоги над мобом.

    Нова логіка:
    - контракт має конкретну ціль: target_mob_name;
    - прогрес рахується тільки якщо вбитий саме цей моб;
    - елітна версія цього ж моба також зараховується;
    - рівень також перевіряємо, щоб уникнути збігів назв у майбутньому.
    """

    reset_daily_contracts_if_needed(user_id)

    active_contract = get_active_contract(user_id)

    if not active_contract:
        return {
            "updated": False,
            "completed": False,
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
        reward_exp = active_contract["reward_exp"]

        exp_result = add_exp(user_id, reward_exp)

        cursor.execute("""
        UPDATE users
        SET daily_contracts_completed = daily_contracts_completed + 1
        WHERE user_id=?
        """, (user_id,))

        cursor.execute("""
        DELETE FROM user_active_contracts
        WHERE id=?
        """, (active_contract["id"],))

        conn.commit()

        message = (
            f"📜 Контракт виконано!\n"
            f"🎯 Ціль: {target_name}\n"
            f"✅ Прогрес: {active_contract['target_kills']}/{active_contract['target_kills']}\n"
            f"✨ Нагорода контракту: +{reward_exp} EXP"
        )

        if exp_result and exp_result.get("level_ups", 0) > 0:
            message += f"\n🏆 Новий рівень: {exp_result['level']}!"

        return {
            "updated": True,
            "completed": True,
            "reward_exp": reward_exp,
            "exp_result": exp_result,
            "message": message
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

# ==============================
# ✅ DEV / TEST LEVEL TOOLS
# ==============================

def set_player_level_for_test(user_id, target_level):
    """
    DEV-функція для тестування.
    Встановлює рівень персонажа вручну.

    Правила:
    - level = target_level
    - exp = 0
    - базові характеристики = 10 + (level - 1)
    - max_hp перераховується
    - hp відновлюється до max_hp
    - інвентар, золото, екіпірування не чіпає
    """

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
    """
    DEV-функція.
    Повертає персонажа на 1 рівень.
    """

    return set_player_level_for_test(user_id, 1)

# ==============================
# ✅ ENERGY SYSTEM
# ==============================

ENERGY_MAX = 40
ENERGY_REGEN_MINUTES = 5


def init_energy_system():
    """
    Лінива ініціалізація енергії.
    Додає поля в users, якщо їх ще немає.
    """

    migrations = [
        ("users", "energy", "INTEGER DEFAULT 100"),
        ("users", "last_energy_update", "TEXT DEFAULT ''"),
        ("users", "energy_full_notified", "INTEGER DEFAULT 1"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    # Щоб після додавання поля не засипати старих гравців повідомленнями при старті бота
    cursor.execute("""
    UPDATE users
    SET energy_full_notified = 1
    WHERE energy IS NULL OR energy >= ?
    """, (ENERGY_MAX,))

    cursor.execute("""
    UPDATE users
    SET energy = ?
    WHERE energy IS NULL
    OR energy > ?
    """, (ENERGY_MAX, ENERGY_MAX))

    conn.commit()


def get_user_energy(user_id):
    """
    Повертає актуальну енергію з урахуванням пасивної регенерації.

    Правила:
    - максимум 100
    - +1 енергія кожні 5 хвилин
    """

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
    """
    Списує 1 енергію за полювання.
    Якщо енергії 0 — не дозволяє бій.
    """

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
    """
    DEV-функція.
    Встановлює енергію вручну.
    Приклади:
    /energy 100
    /energy 0
    """

    from datetime import datetime

    init_energy_system()

    try:
        amount = int(amount)
    except Exception:
        amount = ENERGY_MAX

    amount = max(0, min(ENERGY_MAX, amount))

    # Якщо ставимо 100 вручну — дозволяємо тестове повідомлення
    notified = 0 if amount >= ENERGY_MAX else 0

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
    """
    Перевіряє всіх користувачів.
    Якщо енергія стала 100/100 і повідомлення ще не надсилалось —
    повертає user_id для повідомлення.
    """

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
    """
    Лінива ініціалізація пасивного відновлення HP.
    """

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
    """
    Пасивне відновлення HP поза боєм.

    Правила:
    - +10% від max_hp кожні 2 хвилини;
    - не вище max_hp;
    - якщо HP повне, таймер оновлюється;
    - працює автоматично при читанні HP.
    """

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

    # Якщо HP стало повним пасивно — notification worker потім надішле повідомлення
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
    """
    Повертає user_id гравців, у яких HP стало 100%,
    але повідомлення ще не надсилалося.
    """

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


# ==============================
# ✅ OVERRIDE HP FUNCTIONS WITH REGEN SUPPORT
# ==============================

def get_current_hp(user_id):
    """
    Повертає актуальне HP з урахуванням пасивної регенерації.
    """

    return apply_passive_hp_regen(user_id)


def set_current_hp(user_id, hp):
    """
    Встановлює HP вручну.
    Після будь-якої зміни HP таймер регенерації стартує заново.
    """

    from datetime import datetime

    init_hp_regen_system()

    max_hp = get_max_hp(user_id)

    hp = int(hp)
    hp = max(0, min(max_hp, hp))

    # Якщо HP повне через смерть/банку/ручний сет — не треба слати notification.
    # Якщо HP нижче максимуму — дозволяємо notification, коли пасивно відновиться.
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
    "uncommon": 1.5,
    "rare": 2.3,
    "epic": 3.5
}


DYNAMIC_SELL_MULTIPLIERS = {
    "common": 0.40,
    "uncommon": 1.20,
    "rare": 3.00,
    "epic": 8.00
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
    """
    Додає службові поля для динамічних предметів.
    Старі handlers не залежать від цих полів, але вони корисні для майбутнього:
    - item_level
    - is_generated
    """

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
    multiplier = DYNAMIC_SELL_MULTIPLIERS.get(rarity, 0.40)

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
    """
    Генерує бонуси під нашу поточну систему:
    bonus_str, bonus_dex, bonus_int, bonus_wis, bonus_sta, pdef, mdef

    Поки без класів і без armor_type.
    """

    b_str = 0
    b_dex = 0
    b_int = 0
    b_wis = 0
    b_sta = 0
    pdef = 0
    mdef = 0

    # ==============================
    # MAIN HAND
    # ==============================

    if slot_key == "main_hand":
        # Частина зброї фізична, частина магічна.
        # Поки без класів — повний рандом.
        if random.random() < 0.55:
            b_str = get_dynamic_stat_value(item_level, rarity, 1.0)

            if weapon_hands == 2:
                b_str = int(round(b_str * 1.35))
        else:
            b_int = get_dynamic_stat_value(item_level, rarity, 1.0)

            if weapon_hands == 2:
                b_int = int(round(b_int * 1.35))

    # ==============================
    # OFF HAND
    # ==============================

    elif slot_key == "off_hand":
        choice = random.choice(["shield", "talisman", "dagger"])

        if choice == "shield":
            pdef = get_dynamic_stat_value(item_level, rarity, 1.2)
            b_sta = get_dynamic_stat_value(item_level, rarity, 0.4)

        elif choice == "talisman":
            mdef = get_dynamic_stat_value(item_level, rarity, 1.2)
            b_wis = get_dynamic_stat_value(item_level, rarity, 0.5)

        else:
            b_dex = get_dynamic_stat_value(item_level, rarity, 0.8)

    # ==============================
    # ARMOR SLOTS
    # ==============================

    elif slot_key in ["helmet", "shoulders", "chest", "gloves", "legs", "boots"]:
        if slot_key == "chest":
            pdef = get_dynamic_stat_value(item_level, rarity, 1.6)
            b_sta = get_dynamic_stat_value(item_level, rarity, 0.6)

        elif slot_key in ["helmet", "shoulders", "legs"]:
            pdef = get_dynamic_stat_value(item_level, rarity, 1.0)
            mdef = get_dynamic_stat_value(item_level, rarity, 0.4)

        elif slot_key == "gloves":
            pdef = get_dynamic_stat_value(item_level, rarity, 0.7)
            b_dex = get_dynamic_stat_value(item_level, rarity, 0.5)

        elif slot_key == "boots":
            pdef = get_dynamic_stat_value(item_level, rarity, 0.6)
            b_dex = get_dynamic_stat_value(item_level, rarity, 0.8)

    # ==============================
    # JEWELRY
    # ==============================

    elif slot_key == "necklace":
        mdef = get_dynamic_stat_value(item_level, rarity, 1.3)
        b_wis = get_dynamic_stat_value(item_level, rarity, 0.8)

    elif slot_key == "ring":
        stat_choice = random.choice(["str", "dex", "int", "wis", "sta"])

        value = get_dynamic_stat_value(item_level, rarity, 0.9)

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

    # ==============================
    # EXTRA BONUSES BY RARITY
    # ==============================

    if rarity in ["uncommon", "rare", "epic"]:
        bonus_count = 1

        if rarity == "rare":
            bonus_count = 2

        if rarity == "epic":
            bonus_count = 3

        for _ in range(bonus_count):
            bonus_type = random.choice(["str", "dex", "int", "wis", "sta"])

            bonus_value = get_dynamic_stat_value(item_level, rarity, 0.35)

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
    """
    Створює нову випадкову річ у таблиці items
    і кладе її в inventory гравця.

    Повертає структуру:
    {
        success,
        name,
        inventory_id,
        item_id,
        lost,
        message
    }
    """

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
    """
    Повертає рівень предмета.
    Для старих предметів без item_level повертає 1.
    """

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