"""
Shop system and class-based equipment restrictions
"""

from .connection import conn, cursor, SLOT_ORDER
from data.equipment_profiles import (
    EQUIPMENT_SLOTS,
    MAIN_HAND_PROFILES,
    OFF_HAND_PROFILES,
    MAIN_HAND_ALLOWED_BY_CLASS,
    OFF_HAND_ALLOWED_BY_CLASS
)


# ==============================
# COMMON EQUIPMENT SHOP
# ==============================

COMMON_SHOP_PRICE_MULTIPLIERS = {
    "main_hand": 4.0,
    "off_hand": 3.0,
    "helmet": 2.0,
    "shoulders": 1.5,
    "chest": 2.5,
    "gloves": 1.3,
    "legs": 1.8,
    "boots": 1.3,
    "necklace": 2.0,
    "ring": 2.0
}


def get_common_equipment_price_for_slot(item_level, slot_key):
    """Розраховує ціну для звичайного предмета за слотом."""
    multiplier = COMMON_SHOP_PRICE_MULTIPLIERS.get(slot_key, 1.5)
    return round(max(1.0, item_level * multiplier), 2)


def get_allowed_main_hand_subtypes_for_class(class_key):
    """Повертає дозволені підтипи зброї основної руки для класу."""
    return MAIN_HAND_ALLOWED_BY_CLASS.get(class_key, [])


def get_allowed_off_hand_subtypes_for_class(class_key):
    """Повертає дозволені підтипи зброї другої руки для класу."""
    return OFF_HAND_ALLOWED_BY_CLASS.get(class_key, [])


def get_allowed_shop_main_hand_profiles(user_id):
    """Повертає дозволені профілі зброї основної руки для користувача."""
    from .character import get_character_class
    
    class_key = get_character_class(user_id)
    allowed = get_allowed_main_hand_subtypes_for_class(class_key)

    return [
        profile_key
        for profile_key in allowed
        if profile_key in MAIN_HAND_PROFILES
    ]


def get_allowed_shop_off_hand_profiles(user_id):
    """Повертає дозволені профілі зброї другої руки для користувача."""
    from .character import get_character_class
    
    class_key = get_character_class(user_id)
    allowed = get_allowed_off_hand_subtypes_for_class(class_key)

    return [
        profile_key
        for profile_key in allowed
        if profile_key in OFF_HAND_PROFILES
    ]


def get_common_equipment_shop_offer(user_id):
    """Формує список пропозицій магазину екіпірування для користувача."""
    from .player import get_player_level
    
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


def get_common_equipment_shop_suboffers(user_id, slot_key):
    """Повертає підпропозиції для конкретного слота екіпірування."""
    from .player import get_player_level
    
    player_level = get_player_level(user_id)
    price = get_common_equipment_price_for_slot(player_level, slot_key)

    if slot_key == "main_hand":
        allowed_profiles = get_allowed_shop_main_hand_profiles(user_id)

        return [
            {
                "slot_key": slot_key,
                "profile_key": profile_key,
                "name": MAIN_HAND_PROFILES[profile_key]["name"],
                "hands": MAIN_HAND_PROFILES[profile_key]["hands"],
                "attack_type": MAIN_HAND_PROFILES[profile_key]["attack_type"],
                "item_level": player_level,
                "price": price
            }
            for profile_key in allowed_profiles
        ]

    if slot_key == "off_hand":
        allowed_profiles = get_allowed_shop_off_hand_profiles(user_id)

        return [
            {
                "slot_key": slot_key,
                "profile_key": profile_key,
                "name": OFF_HAND_PROFILES[profile_key]["name"],
                "hands": 1,
                "attack_type": OFF_HAND_PROFILES[profile_key]["attack_type"],
                "item_level": player_level,
                "price": price
            }
            for profile_key in allowed_profiles
        ]

    return []


def cleanup_shop_previews_for_user(user_id):
    """Видаляє старі preview предмети для користувача."""
    init_shop_preview_system()
    
    cursor.execute("""
    DELETE FROM items
    WHERE shop_preview_owner=?
      AND id NOT IN (
          SELECT item_id FROM inventory
      )
    """, (user_id,))
    
    conn.commit()


def is_shop_profile_allowed_for_user(user_id, slot_key, item_profile):
    """
    Перевіряє чи дозволений профіль предмета для користувача.
    """
    if slot_key == "main_hand":
        return item_profile in get_allowed_shop_main_hand_profiles(user_id)

    if slot_key == "off_hand":
        return item_profile in get_allowed_shop_off_hand_profiles(user_id)

    return True


def get_profile_for_generated_item(slot_key, item_profile):
    """Отримує профіль для генерації предмета."""
    if slot_key in ["main_hand", "off_hand"]:
        return item_profile
    return ""


def get_shop_armor_type_for_user(user_id):
    """Return the canonical armor type allowed for the user's class."""
    from data.equipment_profiles import ARMOR_ALLOWED_BY_CLASS
    from .character import get_character_class

    class_key = get_character_class(user_id)
    return str(ARMOR_ALLOWED_BY_CLASS.get(class_key) or "cloth")


def create_common_equipment_shop_preview(user_id, slot_key, item_profile=None):
    """
    Створює preview-предмет у таблиці items для попереднього перегляду покупки.
    """
    from systems import dynamic_equipment_system
    from systems.equipment_system import is_armor_slot
    from .equipment import init_weapon_damage_system, calculate_weapon_damage_by_values
    from .player import get_player_level
    from .inventory import get_bag_capacity, get_inventory_used_slots
    from .utils import format_gold
    
    # Init systems
    try:
        dynamic_equipment_system.init_dynamic_equipment_system()
    except:
        pass
    
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

    if slot_key in ["main_hand", "off_hand"]:
        if not is_shop_profile_allowed_for_user(user_id, slot_key, item_profile):
            return {
                "success": False,
                "message": "❌ Цей предмет не підходить твоєму класу."
            }

    player_level = get_player_level(user_id)
    item_level = player_level
    rarity = "common"
    price = get_common_equipment_price_for_slot(item_level, slot_key)

    item_profile = get_profile_for_generated_item(slot_key, item_profile)

    weapon_hands = 1
    weapon_attack_type = ""
    armor_type = ""

    if slot_key == "main_hand":
        profile = MAIN_HAND_PROFILES[item_profile]
        weapon_hands = profile["hands"]
        weapon_attack_type = profile["attack_type"]
        name = dynamic_equipment_system.get_dynamic_weapon_name(slot_key, rarity, weapon_hands, item_profile)
        type_ = "weapon"

    elif slot_key == "off_hand":
        profile = OFF_HAND_PROFILES[item_profile]
        weapon_hands = 1
        weapon_attack_type = profile["attack_type"]
        name = dynamic_equipment_system.get_dynamic_weapon_name(slot_key, rarity, weapon_hands, item_profile)
        type_ = "offhand"

    else:
        item_profile = ""
        weapon_hands = 1
        armor_type = get_shop_armor_type_for_user(user_id)
        name = dynamic_equipment_system.get_dynamic_armor_name(slot_key, rarity)
        type_ = slot_key

    name = f"{name} {item_level} рівня"

    stats = dynamic_equipment_system.generate_dynamic_equipment_stats(
        slot_key=slot_key,
        item_level=item_level,
        rarity=rarity,
        weapon_hands=weapon_hands,
        item_profile=item_profile
    )

    if is_armor_slot(slot_key):
        stats = dynamic_equipment_system.apply_armor_type_defense_profile_to_stats(
            stats=stats,
            armor_type=armor_type
        )

    sell_price = dynamic_equipment_system.get_dynamic_sell_price(item_level, rarity)

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
        armor_type,
        shop_preview_owner,
        shop_preview_price
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        armor_type,
        user_id,
        price
    ))

    item_id = cursor.lastrowid
    conn.commit()

    return {
        "success": True,
        "item_id": item_id,
        "price": price,
        "name": name,
        "armor_type": armor_type,
        "item_subtype": item_profile
    }


def get_shop_preview_item(item_id, user_id):
    """Отримує preview предмет для конкретного користувача."""
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
        armor_type,
        shop_preview_price
    FROM items
    WHERE id=?
      AND shop_preview_owner=?
    """, (item_id, user_id))

    return cursor.fetchone()


def cancel_common_equipment_shop_preview(user_id, item_id):
    """Скасовує preview покупки."""
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
    """Підтверджує та завершує покупку preview предмета."""
    from .player import get_wallet
    from .inventory import get_bag_capacity, get_inventory_used_slots
    from .utils import format_gold
    
    init_shop_preview_system()

    preview = get_shop_preview_item(item_id, user_id)

    if not preview:
        return {
            "success": False,
            "message": "❌ Попередній перегляд предмета не знайдено або застарів."
        }

    price = preview[24] or 0
    name = preview[1]

    gold = get_wallet(user_id)

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

    new_gold = get_wallet(user_id)

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
    """Повертає текст опису шкоди зброї для preview предмета."""
    from .equipment import init_weapon_damage_system
    
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
        return ""
    
    slot_key = row[1]
    weapon_min_damage = row[2] or 0
    weapon_max_damage = row[3] or 0
    weapon_min_magic_damage = row[4] or 0
    weapon_max_magic_damage = row[5] or 0
    weapon_attack_type = row[6] or ""
    
    if slot_key not in ["main_hand", "off_hand"]:
        return ""
    
    if weapon_attack_type == "magical":
        if weapon_min_magic_damage > 0 or weapon_max_magic_damage > 0:
            return f"✨ Магічна шкода: {weapon_min_magic_damage}-{weapon_max_magic_damage}"
    else:
        if weapon_min_damage > 0 or weapon_max_damage > 0:
            return f"⚔️ Фізична шкода: {weapon_min_damage}-{weapon_max_damage}"
    
    return ""


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
