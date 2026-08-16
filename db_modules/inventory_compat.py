"""Inventory compatibility API restored from the final legacy db.py definitions.
This module exists only to preserve the historical `from db import ...` contract.
"""

from .connection import conn, cursor, DEFAULT_BAG_SLOTS, SLOT_ORDER

from data.classes import CLASS_CONFIGS, CLASS_RESET_SPHERE_ITEM_ID

from .equipment import (
    EQUIPMENT_SLOTS, ARMOR_SLOTS, ARMOR_TYPE_LABELS, ITEM_SUBTYPE_LABELS,
)

from data.equipment_profiles import (
    ARMOR_ALLOWED_BY_CLASS, MAIN_HAND_ALLOWED_BY_CLASS, OFF_HAND_ALLOWED_BY_CLASS,
)

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

def is_inventory_item_equipped(user_id, inventory_id):
    equipped_slots = get_all_equipped_slots(user_id)
    return inventory_id in equipped_slots.values()

def find_equipped_slot_by_inventory_id(user_id, inventory_id):
    equipped_slots = get_all_equipped_slots(user_id)

    for slot_key, equipped_inventory_id in equipped_slots.items():
        if equipped_inventory_id == inventory_id:
            return slot_key

    return None

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

def init_character_class_system():
    migrations = [
        ("users", "character_name", "TEXT DEFAULT ''"),
        ("users", "character_class", "TEXT DEFAULT ''"),
        ("users", "class_selected_at", "TEXT DEFAULT ''"),
        ("users", "class_change_available", "INTEGER DEFAULT 0"),
        ("users", "mp", "INTEGER DEFAULT 0"),
        ("users", "max_mp", "INTEGER DEFAULT 0"),
        ("users", "last_regen_at", "TEXT DEFAULT ''"),
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
        INSERT INTO items (
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

def init_class_equipment_restrictions_system():
    """
    Додає службове поле armor_type для класових обмежень броні.

    weapon_family окремо НЕ додаємо.
    У поточній системі роль weapon_family виконує items.item_subtype.
    """

    migrations = [
        ("items", "armor_type", "TEXT DEFAULT ''"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()

def normalize_equipment_restriction_value(value):
    if value is None:
        return ""

    return str(value).strip()

def get_item_classification_by_inventory_id(inventory_id):
    """
    Повертає класифікацію предмета для перевірки класових обмежень.

    Використовує:
    - items.armor_type для броні;
    - items.item_subtype для зброї / off-hand.
    """

    init_class_equipment_restrictions_system()
    init_dynamic_equipment_system()
    init_weapon_damage_system()

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
        inventory.durability,
        items.armor_type,
        items.item_subtype,
        items.weapon_attack_type
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.id=?
    """, (inventory_id,))

    row = cursor.fetchone()

    if not row:
        return None

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
        durability,
        armor_type,
        item_subtype,
        weapon_attack_type
    ) = row

    return {
        "inventory_id": inv_id,
        "item_id": item_id,
        "name": name,
        "type": type_,
        "rarity": rarity,
        "category": category,
        "slot_key": slot_key,
        "weapon_hands": int(weapon_hands or 1),
        "quantity": quantity,
        "durability": durability,
        "armor_type": normalize_equipment_restriction_value(armor_type),
        "item_subtype": normalize_equipment_restriction_value(item_subtype),
        "weapon_attack_type": normalize_equipment_restriction_value(weapon_attack_type)
    }

def _equipment_system_ro_v1():
    from systems import equipment_system
    return equipment_system

def ensure_equipment_slots(*args, **kwargs):
    return _equipment_system_ro_v1().ensure_equipment_slots(*args, **kwargs)

def init_weapon_damage_system(*args, **kwargs):
    return _equipment_system_ro_v1().init_weapon_damage_system(*args, **kwargs)

__all__ = ['is_inventory_item_equipped', 'find_equipped_slot_by_inventory_id', 'get_item_required_level_by_inventory_id', 'get_item_classification_by_inventory_id', 'is_class_reset_sphere_inventory_item', 'use_class_reset_sphere_from_inventory', 'ARMOR_ALLOWED_BY_CLASS', 'MAIN_HAND_ALLOWED_BY_CLASS', 'OFF_HAND_ALLOWED_BY_CLASS']
