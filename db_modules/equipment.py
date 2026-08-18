"""
Equipment management module - wrapper for systems.equipment_system
"""

from .connection import SLOT_ORDER

from .connection import conn

from data.equipment_profiles import ARMOR_ALLOWED_BY_CLASS, MAIN_HAND_ALLOWED_BY_CLASS, OFF_HAND_ALLOWED_BY_CLASS


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




def get_equipped_slot(user_id, slot_key):
    """Return inventory_id equipped in one validated slot, or None."""
    slot_key = str(slot_key or "")
    if slot_key not in SLOT_ORDER:
        return None
    return get_all_equipped_slots(user_id).get(slot_key)


def get_equipped_items_for_repair(user_id):
    return _equipment_system().get_equipped_items_for_repair(user_id)


def get_total_repair_cost(user_id):
    return _equipment_system().get_total_repair_cost(user_id)


# ==============================
# INVENTORY
# ==============================

def get_inventory_detailed(user_id):
    return _equipment_system().get_inventory_detailed(user_id)


def get_inventory_entry(user_id_or_inventory_id, inventory_id=None):
    """Return inventory entry with both historical call signatures.

    Supported:
    - get_inventory_entry(inventory_id)
    - get_inventory_entry(user_id, inventory_id)
    """
    if inventory_id is None:
        return _equipment_system().get_inventory_entry(user_id_or_inventory_id)

    user_id = int(user_id_or_inventory_id)
    inventory_id = int(inventory_id)
    row = conn.execute(
        "SELECT inv.id, inv.item_id, it.name, it.type, it.category, "
        "COALESCE(inv.quantity, 1), COALESCE(inv.refine_level, 0) "
        "FROM inventory inv JOIN items it ON it.id=inv.item_id "
        "WHERE inv.user_id=? AND inv.id=?",
        (user_id, inventory_id),
    ).fetchone()
    if not row:
        return None

    values = list(row)
    values[2] = format_refined_item_name(values[2], values[-1])
    values.pop()
    return tuple(values)


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
    """Preserve the public base_name contract and bridge to the system positionally."""
    return _equipment_system().get_inventory_refined_display_name(
        inventory_id,
        base_name
    )


def format_refined_item_name(base_name, refine_level):
    """Preserve the public base_name contract while calling the system positionally."""
    return _equipment_system().format_refined_item_name(base_name, refine_level)


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


def buy_item_for_gold(user_id, item_id, price, quantity=1):
    """Atomic generic purchase using the caller-provided total price."""
    return _equipment_system().buy_item_for_gold(
        user_id,
        item_id,
        price,
        quantity
    )

def _compat_result(success, message=""):
    return {"success": bool(success), "message": str(message or "")}


def check_armor_compatibility_for_class(class_key, item_info):
    slot_key = str((item_info or {}).get("slot_key") or "")
    if slot_key not in {"helmet", "shoulders", "chest", "gloves", "legs", "boots"}:
        return _compat_result(True)
    armor_type = str((item_info or {}).get("armor_type") or "")
    allowed = str(ARMOR_ALLOWED_BY_CLASS.get(class_key) or "")
    if not armor_type or armor_type == allowed:
        return _compat_result(True)
    return _compat_result(False, "❌ Цей тип броні не підходить твоєму класу.")


def check_main_hand_compatibility_for_class(class_key, item_info):
    if str((item_info or {}).get("slot_key") or "") != "main_hand":
        return _compat_result(True)
    subtype = str((item_info or {}).get("item_subtype") or "")
    if subtype in set(MAIN_HAND_ALLOWED_BY_CLASS.get(class_key) or []):
        return _compat_result(True)
    return _compat_result(False, "❌ Ця зброя не підходить твоєму класу.")


def check_off_hand_compatibility_for_class(class_key, item_info):
    if str((item_info or {}).get("slot_key") or "") != "off_hand":
        return _compat_result(True)
    subtype = str((item_info or {}).get("item_subtype") or "")
    if subtype in set(OFF_HAND_ALLOWED_BY_CLASS.get(class_key) or []):
        return _compat_result(True)
    return _compat_result(False, "❌ Цей предмет для другої руки не підходить твоєму класу.")


def check_two_handed_conflict_for_equip(user_id, item_info):
    slot_key = str((item_info or {}).get("slot_key") or "")
    if slot_key != "off_hand":
        return _compat_result(True)
    rows = get_all_equipped_slots(user_id) or {}
    main_hand = rows.get("main_hand") if isinstance(rows, dict) else None
    if not main_hand:
        return _compat_result(True)
    try:
        main_info = get_item_classification_by_inventory_id(int(main_hand)) or {}
    except Exception:
        main_info = {}
    if int(main_info.get("weapon_hands") or 1) == 2:
        return _compat_result(False, "❌ Неможливо: дворучна зброя блокує другу руку")
    return _compat_result(True)

