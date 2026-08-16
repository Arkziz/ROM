"""
Shop system and class-based equipment restrictions
"""

from .connection import conn, cursor


# ==============================
# SHOP PREVIEW PURCHASE SYSTEM
# ==============================

def init_shop_preview_system():
    """Ініціалізує таблиці для системи магазину."""
    try:
        cursor.execute("""
        ALTER TABLE items
        ADD COLUMN shop_preview_owner INTEGER DEFAULT NULL
        """)
        conn.commit()
    except Exception:
        pass
    
    try:
        cursor.execute("""
        ALTER TABLE items
        ADD COLUMN shop_preview_price INTEGER DEFAULT 0
        """)
        conn.commit()
    except Exception:
        pass


def get_shop_preview_items():
    """Отримує список предметів у магазині."""
    init_shop_preview_system()
    
    cursor.execute("""
    SELECT id, name, type, rarity, category, slot_key,
           shop_preview_price, item_level, armor_type,
           weapon_min_damage, weapon_max_damage,
           weapon_min_magic_damage, weapon_max_magic_damage,
           weapon_attack_type, bonus_str, bonus_dex, bonus_int, bonus_wis,
           bonus_sta, pdef, mdef
    FROM items
    WHERE shop_preview_owner IS NOT NULL
      AND shop_preview_price > 0
    ORDER BY item_level ASC, shop_preview_price ASC
    """)
    
    items = []
    for row in cursor.fetchall():
        items.append({
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "rarity": row[3],
            "category": row[4],
            "slot_key": row[5],
            "price": row[6],
            "item_level": row[7],
            "armor_type": row[8],
            "weapon_min_damage": row[9],
            "weapon_max_damage": row[10],
            "weapon_min_magic_damage": row[11],
            "weapon_max_magic_damage": row[12],
            "weapon_attack_type": row[13],
            "bonus_str": row[14],
            "bonus_dex": row[15],
            "bonus_int": row[16],
            "bonus_wis": row[17],
            "bonus_sta": row[18],
            "pdef": row[19],
            "mdef": row[20],
        })
    
    return items


def get_shop_preview_item_by_id(item_id):
    """Отримує предмет з магазину за ID."""
    init_shop_preview_system()
    
    cursor.execute("""
    SELECT id, name, type, rarity, category, slot_key,
           shop_preview_price, item_level, armor_type,
           weapon_min_damage, weapon_max_damage,
           weapon_min_magic_damage, weapon_max_magic_damage,
           weapon_attack_type, bonus_str, bonus_dex, bonus_int, bonus_wis,
           bonus_sta, pdef, mdef
    FROM items
    WHERE id=? AND shop_preview_owner IS NOT NULL AND shop_preview_price > 0
    """, (item_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        "id": row[0],
        "name": row[1],
        "type": row[2],
        "rarity": row[3],
        "category": row[4],
        "slot_key": row[5],
        "price": row[6],
        "item_level": row[7],
        "armor_type": row[8],
        "weapon_min_damage": row[9],
        "weapon_max_damage": row[10],
        "weapon_min_magic_damage": row[11],
        "weapon_max_magic_damage": row[12],
        "weapon_attack_type": row[13],
        "bonus_str": row[14],
        "bonus_dex": row[15],
        "bonus_int": row[16],
        "bonus_wis": row[17],
        "bonus_sta": row[18],
        "pdef": row[19],
        "mdef": row[20],
    }


def purchase_shop_preview_item(user_id, item_id):
    """Купує предмет з магазину. Returns (success, message)"""
    from .player import get_wallet, add_gold
    from .inventory import add_item
    
    item = get_shop_preview_item_by_id(item_id)
    if not item:
        return (False, "❌ Предмет не знайдено в магазині!")
    
    price = item["price"]
    wallet = get_wallet(user_id)
    
    if wallet < price:
        return (False, f"❌ Недостатньо золота! Потрібно: {price}, є: {wallet}")
    
    # Deduct gold
    add_gold(user_id, -price)
    
    # Add item
    add_item(user_id, item_id, quantity=1, durability=100)
    
    return (True, f"✅ Куплено {item['name']} за {price} золота!")


def clear_shop_preview_items():
    """Очищує всі предмети з магазину (для оновлення асортименту)."""
    init_shop_preview_system()
    
    cursor.execute("""
    UPDATE items
    SET shop_preview_owner = NULL,
        shop_preview_price = 0
    WHERE shop_preview_owner IS NOT NULL
    """)
    
    conn.commit()


# ==============================
# CLASS RESET SPHERE USAGE
# ==============================

def init_class_reset_sphere():
    """Ініціалізує предмет 'Сфера Скидання Класу'."""
    from .connection import DEFAULT_BAG_SLOTS
    
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO items (
            id, name, type, rarity, category, slot_key, max_stack,
            bonus_str, bonus_dex, bonus_int, bonus_wis, bonus_sta,
            pdef, mdef, sell_price, item_level, is_generated,
            item_subtype, armor_type,
            weapon_min_damage, weapon_max_damage,
            weapon_min_magic_damage, weapon_max_magic_damage,
            weapon_attack_type, weapon_hands,
            shop_preview_owner, shop_preview_price
        ) VALUES (
            900, '🔮 Сфера Скидання Класу', 'class_reset_sphere', 'epic', 'consumable',
            '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, '', '', 0, 0, 0, 0, '', 1, NULL, 0
        )
        """)
        conn.commit()
    except Exception:
        pass


def use_class_reset_sphere(user_id):
    """Використовує Сферу Скидання Класу. Returns (success, message)"""
    from .inventory import count_user_item, consume_user_item_by_item_id
    from .character import set_character_class, grant_class_change_available
    
    CLASS_RESET_SPHERE_ITEM_ID = 900
    
    init_class_reset_sphere()
    
    sphere_count = count_user_item(user_id, CLASS_RESET_SPHERE_ITEM_ID)
    if sphere_count < 1:
        return (False, "❌ У вас немає Сфери Скидання Класу!")
    
    # Consume sphere
    consume_user_item_by_item_id(user_id, CLASS_RESET_SPHERE_ITEM_ID, 1)
    
    # Reset class to novice
    set_character_class(user_id, "novice")
    
    # Grant class change token
    grant_class_change_available(user_id)
    
    return (True, "✅ Клас скинуто до Новачка! Ви можете обрати новий клас.")


# ==============================
# CLASS EQUIPMENT RESTRICTIONS
# ==============================

def can_class_equip_item(character_class, item):
    """
    Перевіряє чи може клас екіпірувати предмет.
    item: dict з полями type, armor_type, weapon_attack_type
    """
    from systems.character_system import get_class_equipment_rules
    
    rules = get_class_equipment_rules(character_class)
    
    item_type = item.get("type", "")
    armor_type = item.get("armor_type", "")
    weapon_attack_type = item.get("weapon_attack_type", "")
    
    # Armor restrictions
    if item_type == "armor":
        allowed_armor = rules.get("allowed_armor_types", [])
        if armor_type and allowed_armor and armor_type not in allowed_armor:
            return False
    
    # Weapon restrictions
    if item_type == "weapon":
        allowed_weapons = rules.get("allowed_weapon_types", [])
        if weapon_attack_type and allowed_weapons and weapon_attack_type not in allowed_weapons:
            return False
    
    return True


def get_equippable_class_items(character_class, items):
    """Фільтрує список предметів які може екіпірувати клас."""
    equippable = []
    for item in items:
        if can_class_equip_item(character_class, item):
            equippable.append(item)
    return equippable


# ==============================
# CLASS SHOP EQUIPMENT GENERATION
# ==============================

def generate_class_shop_equipment(character_class, player_level):
    """Генерує список предметів для магазину класу."""
    from systems.character_system import get_class_equipment_rules
    from systems.dynamic_equipment_system import generate_equipment_item
    
    rules = get_class_equipment_rules(character_class)
    allowed_armor = rules.get("allowed_armor_types", [])
    allowed_weapons = rules.get("allowed_weapon_types", [])
    
    generated_items = []
    
    # Generate armor pieces
    armor_slots = ["helmet", "shoulders", "chest", "gloves", "legs", "boots"]
    for slot in armor_slots:
        for armor_type in allowed_armor:
            item = generate_equipment_item(
                slot_key=slot,
                item_level=player_level,
                rarity="common",
                armor_type=armor_type
            )
            if item:
                generated_items.append(item)
    
    # Generate weapons
    weapon_slots = ["main_hand"]
    for slot in weapon_slots:
        for weapon_type in allowed_weapons:
            item = generate_equipment_item(
                slot_key=slot,
                item_level=player_level,
                rarity="common",
                weapon_attack_type=weapon_type
            )
            if item:
                generated_items.append(item)
    
    return generated_items


def populate_class_shop_for_user(user_id):
    """Заповнює магазин предметами для класу гравця."""
    from .player import get_player_level
    from .character import get_character_class
    
    clear_shop_preview_items()
    
    character_class = get_character_class(user_id)
    player_level = get_player_level(user_id)
    
    items = generate_class_shop_equipment(character_class, player_level)
    
    # Insert items into shop
    for item in items:
        # Calculate price based on item level
        base_price = 100 * item.get("item_level", 1)
        
        cursor.execute("""
        INSERT INTO items (
            name, type, rarity, category, slot_key, max_stack,
            bonus_str, bonus_dex, bonus_int, bonus_wis, bonus_sta,
            pdef, mdef, item_level, armor_type,
            weapon_min_damage, weapon_max_damage,
            weapon_min_magic_damage, weapon_max_magic_damage,
            weapon_attack_type, weapon_hands,
            shop_preview_owner, shop_preview_price,
            is_generated, item_subtype, sell_price
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("name", "Item"),
            item.get("type", "equipment"),
            item.get("rarity", "common"),
            item.get("category", "equipment"),
            item.get("slot_key", ""),
            item.get("max_stack", 1),
            item.get("bonus_str", 0),
            item.get("bonus_dex", 0),
            item.get("bonus_int", 0),
            item.get("bonus_wis", 0),
            item.get("bonus_sta", 0),
            item.get("pdef", 0),
            item.get("mdef", 0),
            item.get("item_level", 1),
            item.get("armor_type", ""),
            item.get("weapon_min_damage", 0),
            item.get("weapon_max_damage", 0),
            item.get("weapon_min_magic_damage", 0),
            item.get("weapon_max_magic_damage", 0),
            item.get("weapon_attack_type", ""),
            item.get("weapon_hands", 1),
            user_id,
            base_price,
            1,  # is_generated
            "",  # item_subtype
            base_price * 0.25  # sell_price
        ))
    
    conn.commit()
    
    return len(items)
