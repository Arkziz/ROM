import random

from db import (
    add_exp,
    add_gold,
    add_kill,
    add_item,
    get_inventory_used_slots,
    get_bag_capacity,
    get_base_exp_for_level,
    create_generated_equipment_item
)


# ==============================
# ✅ EQUIPMENT DROP CONFIG
# ==============================

NORMAL_EQUIPMENT_DROP_CHANCE = 0.20
ELITE_EQUIPMENT_DROP_CHANCE = 0.45


def roll_normal_equipment_rarity():
    """
    Звичайний моб:
    80% common
    20% uncommon
    """

    roll = random.random()

    if roll <= 0.80:
        return "common"

    return "uncommon"


def roll_elite_equipment_rarity():
    """
    Елітний моб:
    75% uncommon
    25% rare
    """

    roll = random.random()

    if roll <= 0.75:
        return "uncommon"

    return "rare"


# ==============================
# ✅ LEVEL DIFFERENCE MULTIPLIER
# ==============================

def get_level_difference_multiplier(player_level, mob_level):
    delta = int(mob_level) - int(player_level)

    if delta <= -3:
        return 0.3

    if delta == -2:
        return 0.5

    if delta == -1:
        return 0.8

    if delta == 0:
        return 1.0

    if delta == 1:
        return 1.2

    if delta == 2:
        return 1.5

    return 1.8


# ==============================
# ✅ EXP CALCULATION
# ==============================

def calculate_exp_reward(player_level, mob):
    mob_level = int(mob.get("level", player_level))

    base_exp = get_base_exp_for_level(mob_level)
    level_multiplier = get_level_difference_multiplier(player_level, mob_level)
    random_factor = random.uniform(0.9, 1.1)

    elite_multiplier = float(mob.get("elite_exp_multiplier", 1.0))

    exp = round(
        base_exp
        * level_multiplier
        * random_factor
        * elite_multiplier
    )

    if exp < 1:
        exp = 1

    return int(exp)


# ==============================
# ✅ GOLD CALCULATION
# ==============================

def calculate_gold_reward(player_level, mob):
    mob_level = int(mob.get("level", player_level))

    if "gold" in mob:
        gold = float(mob["gold"])

    elif "gold_reward" in mob:
        gold = float(mob["gold_reward"])

    elif "min_gold" in mob and "max_gold" in mob:
        gold = random.uniform(
            float(mob["min_gold"]),
            float(mob["max_gold"])
        )

    else:
        min_gold = max(0.05, mob_level * 0.08)
        max_gold = max(0.10, mob_level * 0.18)
        gold = random.uniform(min_gold, max_gold)

    elite_multiplier = float(mob.get("elite_gold_multiplier", 1.0))

    return round(gold * elite_multiplier, 2)


# ==============================
# ✅ EQUIPMENT DROP
# ==============================

def roll_equipment_drop(user_id, mob):
    """
    Динамічний дроп екіпірування.

    Звичайний моб:
    - 20% шанс предмета
    - 80% common / 20% uncommon

    Елітний моб:
    - 45% шанс предмета
    - 75% uncommon / 25% rare
    """

    mob_level = int(mob.get("level", 1))
    is_elite = bool(mob.get("is_elite", False))

    if is_elite:
        drop_chance = ELITE_EQUIPMENT_DROP_CHANCE
    else:
        drop_chance = NORMAL_EQUIPMENT_DROP_CHANCE

    if random.random() > drop_chance:
        return None

    if is_elite:
        rarity = roll_elite_equipment_rarity()
    else:
        rarity = roll_normal_equipment_rarity()

    result = create_generated_equipment_item(
        user_id=user_id,
        item_level=mob_level,
        rarity=rarity
    )

    if not result.get("success"):
        return result.get("message", "🎒 Екіпірування не влізло в сумку.")

    rarity_text = {
        "common": "⚪",
        "uncommon": "🟢",
        "rare": "🔵",
        "epic": "🟣"
    }.get(rarity, "⚪")

    if is_elite:
        return f"{rarity_text} Елітний трофей: {result['name']}"

    return f"{rarity_text} Знайдено спорядження: {result['name']}"


# ==============================
# ✅ SIMPLE LOOT
# ==============================

def get_random_quantity(value):
    if isinstance(value, list) or isinstance(value, tuple):
        if len(value) >= 2:
            return random.randint(int(value[0]), int(value[1]))

    return int(value or 1)


def roll_loot_from_loot_table(user_id, loot_table):
    messages = []

    for loot in loot_table:
        item_id = loot.get("item_id")
        chance = loot.get("chance", 0)
        quantity = get_random_quantity(loot.get("quantity", 1))

        if not item_id:
            continue

        roll = random.random()

        if roll <= chance:
            result = add_item(user_id, item_id, quantity)

            if result.get("added", 0) > 0:
                name = result.get("name", "Предмет")
                added = result.get("added", 0)

                messages.append(f"{name} x{added}")

            if result.get("lost", 0) > 0:
                name = result.get("name", "Предмет")
                lost = result.get("lost", 0)

                messages.append(f"⚠️ Не влізло в сумку: {name} x{lost}")

    return messages


def roll_loot_from_simple_keys(user_id, mob):
    messages = []

    possible_items = []

    if "trash_item_id" in mob:
        possible_items.append(mob["trash_item_id"])

    if "loot_item_id" in mob:
        possible_items.append(mob["loot_item_id"])

    if "trash_items" in mob and isinstance(mob["trash_items"], list):
        possible_items.extend(mob["trash_items"])

    if "trash_drops" in mob and isinstance(mob["trash_drops"], list):
        possible_items.extend(mob["trash_drops"])

    if not possible_items:
        return messages

    loot_chance = mob.get("loot_chance", 0.45)

    # Елітний моб має трохи більший шанс на ресурсний/сірий лут.
    if mob.get("is_elite"):
        loot_chance = min(1.0, loot_chance + 0.20)

    if random.random() > loot_chance:
        return messages

    item_id = random.choice(possible_items)

    result = add_item(user_id, item_id, 1)

    if result.get("added", 0) > 0:
        name = result.get("name", "Предмет")
        added = result.get("added", 0)

        messages.append(f"{name} x{added}")

    if result.get("lost", 0) > 0:
        name = result.get("name", "Предмет")
        lost = result.get("lost", 0)

        messages.append(f"⚠️ Не влізло в сумку: {name} x{lost}")

    return messages


def roll_loot(user_id, mob):
    messages = []

    # 1. Сірий/ресурсний лут
    if "loot_table" in mob and isinstance(mob["loot_table"], list):
        messages.extend(roll_loot_from_loot_table(user_id, mob["loot_table"]))

    elif "loot" in mob and isinstance(mob["loot"], list):
        messages.extend(roll_loot_from_loot_table(user_id, mob["loot"]))

    else:
        messages.extend(roll_loot_from_simple_keys(user_id, mob))

    # 2. Динамічний дроп екіпірування
    equipment_message = roll_equipment_drop(user_id, mob)

    if equipment_message:
        messages.append(equipment_message)

    return messages


# ==============================
# ✅ PROCESS VICTORY REWARD
# ==============================

def process_victory_reward(user_id, player_level, mob):
    exp = calculate_exp_reward(
        player_level=player_level,
        mob=mob
    )

    gold = calculate_gold_reward(
        player_level=player_level,
        mob=mob
    )

    exp_result = add_exp(user_id, exp)
    add_gold(user_id, gold)
    add_kill(user_id)

    loot_messages = roll_loot(user_id, mob)

    used_slots = get_inventory_used_slots(user_id)
    capacity = get_bag_capacity(user_id)

    return {
        "exp": exp,
        "gold": gold,
        "exp_result": exp_result,
        "loot_messages": loot_messages,
        "used_slots": used_slots,
        "capacity": capacity
    }