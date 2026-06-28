import random

from db import (
    add_exp,
    add_gold,
    add_kill,
    add_item,
    get_inventory_used_slots,
    get_bag_capacity,
    get_base_exp_for_level
)


# ==============================
# ✅ LEVEL DIFFERENCE MULTIPLIER
# ==============================

def get_level_difference_multiplier(player_level, mob_level):
    """
    Δ = mob_level - player_level

    Таблиця:
    Δ <= -3: x0.3
    Δ = -2: x0.5
    Δ = -1: x0.8
    Δ = 0: x1.0
    Δ = +1: x1.2
    Δ = +2: x1.5
    Δ >= +3: x1.8
    """

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
    """
    Нова EXP-система.

    BaseEXP береться з таблиці db.BASE_EXP_BY_LEVEL.
    Якщо моб рівня гравця — дає BaseEXP цього рівня.
    Якщо моб слабший/сильніший — працює multiplier_delta.
    """

    mob_level = int(mob.get("level", player_level))

    base_exp = get_base_exp_for_level(mob_level)
    multiplier = get_level_difference_multiplier(player_level, mob_level)

    random_factor = random.uniform(0.9, 1.1)

    exp = round(base_exp * multiplier * random_factor)

    if exp < 1:
        exp = 1

    return int(exp)


# ==============================
# ✅ GOLD CALCULATION
# ==============================

def calculate_gold_reward(player_level, mob):
    """
    Обережна базова формула золота.
    Якщо у моба явно задані gold/min_gold/max_gold — використовуємо їх.
    Інакше даємо невелике золото від рівня моба.
    """

    mob_level = int(mob.get("level", player_level))

    if "gold" in mob:
        return round(float(mob["gold"]), 2)

    if "gold_reward" in mob:
        return round(float(mob["gold_reward"]), 2)

    if "min_gold" in mob and "max_gold" in mob:
        return round(random.uniform(float(mob["min_gold"]), float(mob["max_gold"])), 2)

    # fallback
    min_gold = max(0.05, mob_level * 0.08)
    max_gold = max(0.10, mob_level * 0.18)

    return round(random.uniform(min_gold, max_gold), 2)


# ==============================
# ✅ LOOT
# ==============================

def get_random_quantity(value):
    """
    Підтримка:
    quantity: 1
    quantity: [1, 3]
    """

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
    """
    Сумісність із різними старими структурами мобів.
    Підтримує:
    - trash_item_id
    - trash_items
    - trash_drops
    - loot_item_id
    """

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

    # базовий шанс луту
    loot_chance = mob.get("loot_chance", 0.45)

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
    """
    Гнучкий лут, щоб не ламати старі data/mobs.py.
    Якщо є loot_table — використовує її.
    Якщо ні — пробує старі ключі.
    """

    if "loot_table" in mob and isinstance(mob["loot_table"], list):
        return roll_loot_from_loot_table(user_id, mob["loot_table"])

    if "loot" in mob and isinstance(mob["loot"], list):
        return roll_loot_from_loot_table(user_id, mob["loot"])

    return roll_loot_from_simple_keys(user_id, mob)


# ==============================
# ✅ PROCESS VICTORY REWARD
# ==============================

def process_victory_reward(user_id, player_level, mob):
    """
    Основна функція нагороди за перемогу.
    Її викликає handlers/combat.py.
    """

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