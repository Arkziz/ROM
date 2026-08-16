"""
Equipment management module - wrapper for systems.equipment_system
"""


def _equipment_system():
    from systems import equipment_system
    return equipment_system


# ==============================
# IMPORTS FROM DATA
# ==============================

from data.equipment_profiles import (
    EQUIPMENT_SLOTS,
    ARMOR_TYPE_LABELS,
    ITEM_SUBTYPE_LABELS
)


# ==============================
# EQUIPMENT CONSTANTS
# ==============================

ARMOR_SLOTS = [
    "helmet",
    "shoulders",
    "chest",
    "gloves",
    "legs",
    "boots"
]


# ==============================
# EQUIPMENT UTILITY FUNCTIONS
# ==============================

def normalize_equipment_restriction_value(value):
    """Нормалізує значення обмеження екіпірування."""
    if value is None:
        return ""
    return str(value).strip()


def is_armor_slot(slot_key):
    """Перевіряє чи є слот слотом броні."""
    return slot_key in ARMOR_SLOTS


def get_armor_type_label(armor_type):
    """Повертає відображувальне ім'я типу броні."""
    armor_type = normalize_equipment_restriction_value(armor_type)
    return ARMOR_TYPE_LABELS.get(armor_type, armor_type or "Універсальний")


def get_item_subtype_label(item_subtype):
    """Повертає відображувальне ім'я підтипу предмета."""
    item_subtype = normalize_equipment_restriction_value(item_subtype)
    return ITEM_SUBTYPE_LABELS.get(item_subtype, item_subtype or "Універсальний")


# ==============================
# EQUIPMENT SLOTS
# ==============================

def ensure_equipment_slots(user_id):
    return _equipment_system().ensure_equipment_slots(user_id)


def get_all_equipped_items(user_id):
    return _equipment_system().get_all_equipped_items(user_id)


def get_all_equipped_slots(user_id):
    """
    Повертає словник {slot_key: inventory_id} для всіх слотів екіпірування.
    """
    from .connection import cursor, SLOT_ORDER
    
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


def get_equipped_items_for_repair(user_id):
    return _equipment_system().get_equipped_items_for_repair(user_id)


def get_total_repair_cost(user_id):
    return _equipment_system().get_total_repair_cost(user_id)


# ==============================
# INVENTORY
# ==============================

def get_inventory_detailed(user_id):
    return _equipment_system().get_inventory_detailed(user_id)


def get_inventory_entry(inventory_id):
    return _equipment_system().get_inventory_entry(inventory_id)


def get_item_by_inventory_id(inventory_id):
    return _equipment_system().get_item_by_inventory_id(inventory_id)


def get_item_by_inventory_id_full(inventory_id):
    return _equipment_system().get_item_by_inventory_id_full(inventory_id)


def get_item_bonuses(inventory_id):
    return _equipment_system().get_item_bonuses(inventory_id)


def get_equipped_item_defenses(user_id):
    return _equipment_system().get_equipped_item_defenses(user_id)


def get_sellable_equipment_items(user_id):
    return _equipment_system().get_sellable_equipment_items(user_id)


# ==============================
# WEAPON DAMAGE
# ==============================

def init_weapon_damage_system():
    return _equipment_system().init_weapon_damage_system()


def calculate_weapon_damage_by_values(item_level, rarity, weapon_hands):
    return _equipment_system().calculate_weapon_damage_by_values(
        item_level=item_level,
        rarity=rarity,
        weapon_hands=weapon_hands
    )


def get_weapon_damage_by_inventory_id(inventory_id):
    return _equipment_system().get_weapon_damage_by_inventory_id(inventory_id)


def get_inventory_weapon_damage_display(inventory_id):
    return _equipment_system().get_inventory_weapon_damage_display(inventory_id)


# ==============================
# REFINE DISPLAY
# ==============================

def get_inventory_refine_level(inventory_id):
    return _equipment_system().get_inventory_refine_level(inventory_id)


def get_inventory_refined_display_name(inventory_id, base_name=None):
    return _equipment_system().get_inventory_refined_display_name(
        inventory_id=inventory_id,
        base_name=base_name
    )


def format_refined_item_name(base_name, refine_level):
    return _equipment_system().format_refined_item_name(
        base_name=base_name,
        refine_level=refine_level
    )


# ==============================
# CLASS RESTRICTIONS
# ==============================

def can_equip_item_by_class(user_id, item_id):
    return _equipment_system().can_equip_item_by_class(
        user_id=user_id,
        item_id=item_id
    )


def can_equip_inventory_item_by_class(user_id, inventory_id):
    return _equipment_system().can_equip_inventory_item_by_class(
        user_id=user_id,
        inventory_id=inventory_id
    )


def is_inventory_item_class_compatible(user_id, inventory_id):
    return _equipment_system().is_inventory_item_class_compatible(
        user_id=user_id,
        inventory_id=inventory_id
    )


# ==============================
# EQUIP/UNEQUIP
# ==============================

def equip_inventory_item(user_id, inventory_id):
    return _equipment_system().equip_inventory_item(
        user_id=user_id,
        inventory_id=inventory_id
    )


def unequip_inventory_item(user_id, inventory_id):
    return _equipment_system().unequip_inventory_item(
        user_id=user_id,
        inventory_id=inventory_id
    )


def unequip_incompatible_items_after_class_change(user_id):
    return _equipment_system().unequip_incompatible_items_after_class_change(user_id)


# ==============================
# REPAIR AND DURABILITY
# ==============================

def repair_equipped_item(user_id, inventory_id):
    return _equipment_system().repair_equipped_item(
        user_id=user_id,
        inventory_id=inventory_id
    )


def repair_all_equipped(user_id):
    return _equipment_system().repair_all_equipped(user_id)


def calculate_repair_cost(durability, sell_price, rarity):
    return _equipment_system().calculate_repair_cost(
        durability=durability,
        sell_price=sell_price,
        rarity=rarity
    )


def damage_equipped_items_on_death(user_id):
    return _equipment_system().damage_equipped_items_on_death(user_id)


def apply_random_durability_wear_on_victory(user_id, chance_percent=25):
    """
    Застосовує випадкове зношування спорядження після перемоги.
    """
    return _equipment_system().apply_random_durability_wear_on_victory(
        user_id=user_id,
        chance_percent=chance_percent
    )


# ==============================
# SELL AND BUY
# ==============================

def sell_inventory_item_to_trader(user_id, inventory_id):
    return _equipment_system().sell_inventory_item_to_trader(
        user_id=user_id,
        inventory_id=inventory_id
    )


def buy_common_equipment_from_trader(user_id, item_id):
    return _equipment_system().buy_common_equipment_from_trader(
        user_id=user_id,
        item_id=item_id
    )


def buy_item_for_gold(user_id, item_id, quantity=1):
    return _equipment_system().buy_item_for_gold(
        user_id=user_id,
        item_id=item_id,
        quantity=quantity
    )
