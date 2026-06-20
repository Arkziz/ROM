import random

from db import (
    add_exp,
    add_gold,
    add_kill,
    add_item,
    get_inventory_used_slots,
    get_bag_capacity
)


# ==============================
# EXP
# ==============================

def calculate_exp_reward(player_level, mob_level, base_exp):
    diff = player_level - mob_level

    # Сірі моби
    if diff >= 5:
        return 0

    # Моб молодший або рівний
    if diff >= 0:
        multiplier = 1 - (diff / 5)
        return max(0, int(base_exp * multiplier))

    # Моб старший
    level_gap = mob_level - player_level
    multiplier = 1 + (0.15 * level_gap)

    return int(base_exp * multiplier)


# ==============================
# GOLD
# ==============================

def calculate_gold_reward(mob_level):
    base_gold = mob_level * 0.2

    gold = random.uniform(base_gold * 0.8, base_gold * 1.2)

    return round(gold, 2)


# ==============================
# LOOT
# ==============================

def roll_loot(user_id, mob):
    loot_messages = []

    # 1. Trash loot
    trash_item_id = mob.get("trash_item_id")
    trash_chance = mob.get("trash_chance", 80)

    if trash_item_id and random.randint(1, 100) <= trash_chance:
        result = add_item(user_id, trash_item_id, 1)

        if result["added"] > 0:
            loot_messages.append(f"🔘 {result['name']} x{result['added']}")

        if result["lost"] > 0:
            loot_messages.append(f"⚠️ Не влізло в сумку: {result['name']} x{result['lost']}")

    # 2. Potion loot
    potion_item_id = mob.get("potion_item_id")
    potion_chance = mob.get("potion_chance", 0)

    if potion_item_id and random.randint(1, 100) <= potion_chance:
        result = add_item(user_id, potion_item_id, 1)

        if result["added"] > 0:
            loot_messages.append(f"🧪 {result['name']} x{result['added']}")

        if result["lost"] > 0:
            loot_messages.append(f"⚠️ Не влізло в сумку: {result['name']} x{result['lost']}")

    # 3. Equipment loot
    equipment_roll = random.randint(1, 100)

    equipment_item_id = None

    is_boss = mob.get("is_boss", False)

    if is_boss:
        # Пізніше зробимо окремий boss loot pool
        equipment_item_id = random.choice([2, 3, 6, 7])
    else:
        if equipment_roll <= 1:
            # Green
            equipment_item_id = random.choice([2, 6])
        elif equipment_roll <= 6:
            # White
            equipment_item_id = random.choice([1, 5])

    if equipment_item_id:
        result = add_item(user_id, equipment_item_id, 1)

        if result["added"] > 0:
            loot_messages.append(f"🎒 {result['name']}")

        if result["lost"] > 0:
            loot_messages.append(f"⚠️ Не влізло в сумку: {result['name']}")

    return loot_messages


# ==============================
# FULL REWARD PIPELINE
# ==============================

def process_victory_reward(user_id, player_level, mob):
    mob_level = mob.get("level", 1)
    base_exp = mob.get("base_exp", 20)

    exp_reward = calculate_exp_reward(player_level, mob_level, base_exp)
    gold_reward = calculate_gold_reward(mob_level)

    exp_result = add_exp(user_id, exp_reward)
    add_gold(user_id, gold_reward)
    add_kill(user_id)

    loot_messages = roll_loot(user_id, mob)

    used_slots = get_inventory_used_slots(user_id)
    capacity = get_bag_capacity(user_id)

    return {
        "exp": exp_reward,
        "gold": gold_reward,
        "exp_result": exp_result,
        "loot_messages": loot_messages,
        "used_slots": used_slots,
        "capacity": capacity
    }