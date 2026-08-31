"""
Refine system module - equipment enhancement
"""

from .connection import conn, cursor


# ==============================
# REFINE SYSTEM CONSTANTS
# ==============================

REFINE_STONE_ITEM_ID = 601
SUCCESS_RUNE_ITEM_ID = 602


# ==============================
# REFINE SYSTEM CORE
# ==============================

def init_refine_system():
    """Ініціалізує БД для системи заточки."""
    try:
        cursor.execute("""
        ALTER TABLE inventory
        ADD COLUMN refine_level INTEGER DEFAULT 0
        """)
        conn.commit()
    except Exception:
        pass
    seed_refine_items()


def _get_table_columns(table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def _insert_item_dynamic(values_by_column):
    columns = _get_table_columns("items")
    insert_columns = []
    insert_values = []
    for column in columns:
        if column in values_by_column:
            insert_columns.append(column)
            insert_values.append(values_by_column[column])
    placeholders = ", ".join(["?"] * len(insert_columns))
    columns_sql = ", ".join(insert_columns)
    cursor.execute(f"""
    INSERT OR IGNORE INTO items ({columns_sql})
    VALUES ({placeholders})
    """, insert_values)


def seed_refine_items():
    common_values = {
        "slot_key": "", "weapon_hands": 1, "max_stack": 999, "bonus_str": 0,
        "bonus_dex": 0, "bonus_int": 0, "bonus_wis": 0, "bonus_sta": 0,
        "pdef": 0, "mdef": 0, "item_level": 1, "is_generated": 0,
        "item_subtype": "", "armor_type": "", "weapon_min_damage": 0,
        "weapon_max_damage": 0, "weapon_min_magic_damage": 0,
        "weapon_max_magic_damage": 0, "weapon_attack_type": "",
        "shop_preview_owner": None, "shop_preview_price": 0,
    }
    stone_values = dict(common_values)
    stone_values.update({
        "id": REFINE_STONE_ITEM_ID,
        "name": "🪨 Камінь Посилення",
        "type": "refine_stone",
        "rarity": "common",
        "category": "material",
        "sell_price": 1.0
    })
    rune_values = dict(common_values)
    rune_values.update({
        "id": SUCCESS_RUNE_ITEM_ID,
        "name": "💎 Руна Успіху",
        "type": "success_rune",
        "rarity": "rare",
        "category": "material",
        "sell_price": 5.0
    })
    _insert_item_dynamic(stone_values)
    _insert_item_dynamic(rune_values)
    conn.commit()


def get_inventory_item_refine_info(inventory_id):
    init_refine_system()
    cursor.execute("""
    SELECT inventory.id, inventory.user_id, inventory.item_id, inventory.quantity,
           inventory.durability, inventory.refine_level, items.name, items.type,
           items.rarity, items.category, items.slot_key, items.weapon_hands,
           items.item_level, items.item_subtype, items.armor_type,
           items.weapon_min_damage, items.weapon_max_damage,
           items.weapon_min_magic_damage, items.weapon_max_magic_damage,
           items.weapon_attack_type
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.id=?
    """, (inventory_id,))
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "inventory_id": row[0], "user_id": row[1], "item_id": row[2],
        "quantity": row[3], "durability": row[4], "refine_level": row[5],
        "name": row[6], "type": row[7], "rarity": row[8], "category": row[9],
        "slot_key": row[10], "weapon_hands": row[11], "item_level": row[12],
        "item_subtype": row[13], "armor_type": row[14],
        "weapon_min_damage": row[15], "weapon_max_damage": row[16],
        "weapon_min_magic_damage": row[17], "weapon_max_magic_damage": row[18],
        "weapon_attack_type": row[19],
    }


def set_inventory_refine_level(inventory_id, refine_level):
    init_refine_system()
    try:
        refine_level = int(refine_level)
    except Exception:
        refine_level = 0
    refine_level = max(0, refine_level)
    cursor.execute("UPDATE inventory SET refine_level=? WHERE id=?", (refine_level, inventory_id))
    conn.commit()
    return refine_level


def get_refine_resource_counts(user_id):
    from .inventory import count_user_item
    return {
        "stone": count_user_item(user_id, REFINE_STONE_ITEM_ID),
        "success_rune": count_user_item(user_id, SUCCESS_RUNE_ITEM_ID)
    }


# ==============================
# REFINE EFFECTS WRAPPERS
# ==============================

def get_refine_total_armor_hp_bonus_percent(user_id):
    """
    Повертає сумарний HP% бонус від заточеної броні.
    """
    from systems.refine_system import get_armor_refine_hp_bonus_percent
    from systems.equipment_system import get_all_equipped_items
    
    init_refine_system()
    
    armor_slots = {
        "helmet",
        "shoulders",
        "chest",
        "gloves",
        "legs",
        "boots",
    }
    
    equipped_items = get_all_equipped_items(user_id)
    total_bonus = 0.0
    
    for item in equipped_items:
        slot_key = item.get("slot_key")
        if slot_key not in armor_slots:
            continue
        
        inventory_id = item.get("inventory_id")
        if not inventory_id:
            continue
        
        cursor.execute("""
        SELECT
            inventory.refine_level,
            items.rarity
        FROM inventory
        JOIN items ON inventory.item_id = items.id
        WHERE inventory.id=? AND inventory.user_id=?
        """, (inventory_id, user_id))
        
        row = cursor.fetchone()
        if not row:
            continue
        
        refine_level, rarity = row
        
        try:
            refine_level = int(refine_level or 0)
        except Exception:
            refine_level = 0
        
        if refine_level <= 0:
            continue
        
        total_bonus += float(
            get_armor_refine_hp_bonus_percent(
                refine_level=refine_level,
                rarity=rarity
            )
        )
    
    return round(total_bonus, 2)


def get_refine_effects_summary_for_user(user_id):
    """
    Діагностичний helper для тестів.
    """
    from .player import get_max_hp
    
    return {
        "armor_hp_bonus_percent": get_refine_total_armor_hp_bonus_percent(user_id),
        "max_hp": get_max_hp(user_id),
    }


# ==============================
# REFINE DISPLAY NAMES
# ==============================

def get_inventory_refine_display_line(inventory_id):
    """
    Текстовий рядок для деталей предмета.
    """
    from systems.equipment_system import get_inventory_refine_level
    
    try:
        refine_level = get_inventory_refine_level(inventory_id)
    except Exception:
        refine_level = 0
    
    try:
        refine_level = int(refine_level or 0)
    except Exception:
        refine_level = 0
    
    if refine_level <= 0:
        return ""
    
    return f"✨ Заточка: +{refine_level}\n"


# ==============================
# REFINE MATERIAL STACK FIX
# ==============================

def ensure_refine_material_stack_sizes():
    """
    Гарантує, що матеріали заточки стакаються до 999.
    """
    from data.balance import REFINE_MATERIAL_MAX_STACK
    
    try:
        init_refine_system()
    except Exception:
        pass
    
    cursor.execute("""
    UPDATE items
    SET max_stack=?
    WHERE id IN (401, 402)
    """, (REFINE_MATERIAL_MAX_STACK,))
    
    conn.commit()


def get_refine_material_stack_debug():
    """
    DEV/helper: повертає поточні max_stack для матеріалів заточки.
    """
    ensure_refine_material_stack_sizes()
    
    cursor.execute("""
    SELECT id, name, max_stack
    FROM items
    WHERE id IN (401, 402)
    ORDER BY id
    """)
    
    return cursor.fetchall()
