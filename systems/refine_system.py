"""
Rune Magic RPG - Refine System Core v1
6.0.1: core refine logic without Telegram UI.
"""

import random

REFINE_STONE_ITEM_ID = 401
SUCCESS_RUNE_ITEM_ID = 402
WEAPON_MAX_REFINE_LEVEL = 10
ARMOR_MAX_REFINE_LEVEL = 6

WEAPON_REFINE_SUCCESS_CHANCES = {0: 100, 1: 100, 2: 100, 3: 80, 4: 70, 5: 60, 6: 50, 7: 40, 8: 30, 9: 20}
ARMOR_REFINE_SUCCESS_CHANCES = {0: 100, 1: 100, 2: 70, 3: 50, 4: 30, 5: 20}
WEAPON_REFINE_DAMAGE_MULTIPLIERS = {0: 1.00, 1: 1.05, 2: 1.10, 3: 1.15, 4: 1.22, 5: 1.30, 6: 1.40, 7: 1.52, 8: 1.66, 9: 1.82, 10: 2.00}
ARMOR_REFINE_BASE_HP_BONUS_PERCENT = {0: 0.0, 1: 0.5, 2: 1.0, 3: 1.5, 4: 2.0, 5: 3.0, 6: 4.0}
ARMOR_REFINE_RARITY_HP_MULTIPLIERS = {"common": 1.0, "uncommon": 1.1, "rare": 1.2, "epic": 1.3}
ARMOR_SLOT_KEYS = {"helmet", "shoulders", "chest", "gloves", "legs", "boots"}


def normalize_refine_level(level):
    try:
        level = int(level)
    except Exception:
        level = 0
    return max(0, level)


def get_item_refine_kind(item_info):
    if not item_info:
        return ""
    category = item_info.get("category", "")
    slot_key = item_info.get("slot_key", "")
    type_ = item_info.get("type", "")
    if category != "equipment":
        return ""
    if slot_key == "main_hand" or type_ == "weapon":
        return "weapon"
    if slot_key in ARMOR_SLOT_KEYS:
        return "armor"
    return ""


def get_refine_max_level(refine_kind):
    if refine_kind == "weapon":
        return WEAPON_MAX_REFINE_LEVEL
    if refine_kind == "armor":
        return ARMOR_MAX_REFINE_LEVEL
    return 0


def get_refine_success_chance(refine_kind, current_level):
    current_level = normalize_refine_level(current_level)
    if refine_kind == "weapon":
        return WEAPON_REFINE_SUCCESS_CHANCES.get(current_level, 0)
    if refine_kind == "armor":
        return ARMOR_REFINE_SUCCESS_CHANCES.get(current_level, 0)
    return 0


def get_refine_failure_level(refine_kind, current_level):
    current_level = normalize_refine_level(current_level)
    if refine_kind == "weapon":
        return current_level if current_level <= 3 else max(0, current_level - 1)
    if refine_kind == "armor":
        return current_level if current_level <= 2 else max(0, current_level - 1)
    return current_level


def get_weapon_refine_damage_multiplier(refine_level):
    refine_level = min(normalize_refine_level(refine_level), WEAPON_MAX_REFINE_LEVEL)
    return WEAPON_REFINE_DAMAGE_MULTIPLIERS.get(refine_level, 1.00)


def apply_weapon_refine_to_damage(min_damage, max_damage, refine_level):
    multiplier = get_weapon_refine_damage_multiplier(refine_level)
    return int(round(int(min_damage or 0) * multiplier)), int(round(int(max_damage or 0) * multiplier))


def get_armor_refine_hp_bonus_percent(refine_level, rarity):
    refine_level = min(normalize_refine_level(refine_level), ARMOR_MAX_REFINE_LEVEL)
    rarity = (rarity or "common").strip().lower()
    base_bonus = ARMOR_REFINE_BASE_HP_BONUS_PERCENT.get(refine_level, 0.0)
    rarity_multiplier = ARMOR_REFINE_RARITY_HP_MULTIPLIERS.get(rarity, 1.0)
    return round(base_bonus * rarity_multiplier, 2)


def get_refine_display_suffix(refine_level):
    refine_level = normalize_refine_level(refine_level)
    return "" if refine_level <= 0 else f" [+{refine_level}]"


def can_refine_item(item_info):
    refine_kind = get_item_refine_kind(item_info)
    if not refine_kind:
        return {"success": False, "message": "❌ Цей предмет не можна заточити.", "refine_kind": ""}
    current_level = normalize_refine_level(item_info.get("refine_level", 0))
    max_level = get_refine_max_level(refine_kind)
    if current_level >= max_level:
        return {"success": False, "message": f"✅ Предмет уже має максимальну заточку +{max_level}.", "refine_kind": refine_kind}
    return {"success": True, "message": "✅ Предмет можна заточити.", "refine_kind": refine_kind, "current_level": current_level, "max_level": max_level}


def roll_refine_success(refine_kind, current_level, use_success_rune=False):
    if use_success_rune:
        return {"success": True, "chance": 100, "roll": None}
    chance = get_refine_success_chance(refine_kind, current_level)
    roll = random.randint(1, 100)
    return {"success": roll <= chance, "chance": chance, "roll": roll}


def perform_refine_attempt(user_id, inventory_id, use_success_rune=False):
    from db import init_refine_system, get_inventory_item_refine_info, count_user_item, consume_user_item_by_item_id, set_inventory_refine_level
    init_refine_system()
    item_info = get_inventory_item_refine_info(inventory_id)
    if not item_info:
        return {"success": False, "message": "❌ Предмет не знайдено."}
    if int(item_info.get("user_id", 0)) != int(user_id):
        return {"success": False, "message": "❌ Це не твій предмет."}
    refine_check = can_refine_item(item_info)
    if not refine_check.get("success"):
        return refine_check
    if count_user_item(user_id, REFINE_STONE_ITEM_ID) <= 0:
        return {"success": False, "message": "❌ Потрібен 🪨 Камінь Посилення."}
    if use_success_rune and count_user_item(user_id, SUCCESS_RUNE_ITEM_ID) <= 0:
        return {"success": False, "message": "❌ Потрібна 💎 Руна Успіху."}
    consume_user_item_by_item_id(user_id, REFINE_STONE_ITEM_ID, 1)
    if use_success_rune:
        consume_user_item_by_item_id(user_id, SUCCESS_RUNE_ITEM_ID, 1)
    refine_kind = refine_check["refine_kind"]
    current_level = refine_check["current_level"]
    roll_result = roll_refine_success(refine_kind, current_level, use_success_rune)
    if roll_result["success"]:
        new_level = current_level + 1
        set_inventory_refine_level(inventory_id, new_level)
        return {"success": True, "refine_success": True, "refine_kind": refine_kind, "old_level": current_level, "new_level": new_level, "chance": roll_result["chance"], "roll": roll_result["roll"], "used_success_rune": bool(use_success_rune), "message": f"✅ Заточка успішна: +{current_level} → +{new_level}"}
    new_level = get_refine_failure_level(refine_kind, current_level)
    set_inventory_refine_level(inventory_id, new_level)
    if new_level < current_level:
        message = f"❌ Заточка не вдалася: +{current_level} → +{new_level}"
    else:
        message = f"❌ Заточка не вдалася: +{current_level} без змін"
    return {"success": True, "refine_success": False, "refine_kind": refine_kind, "old_level": current_level, "new_level": new_level, "chance": roll_result["chance"], "roll": roll_result["roll"], "used_success_rune": bool(use_success_rune), "message": message}
