import random

from db import (
    add_exp,
    add_gold,
    add_kill,
    add_item,
    get_inventory_used_slots,
    get_bag_capacity,
    get_base_exp_for_level,
    create_generated_equipment_item,
)


REWARD_SYSTEM_UI_VERSION = "5.9.3-final-trophy-messages"


# ==============================
# EQUIPMENT DROP CONFIG
# ==============================

NORMAL_EQUIPMENT_DROP_CHANCE = 0.20
ELITE_EQUIPMENT_DROP_CHANCE = 0.45

NORMAL_CLASS_AWARE_EQUIPMENT_CHANCE = 0.50
ELITE_CLASS_AWARE_EQUIPMENT_CHANCE = 0.70


def roll_normal_equipment_rarity():
    roll = random.random()

    if roll <= 0.80:
        return "common"

    return "uncommon"


def roll_elite_equipment_rarity():
    roll = random.random()

    if roll <= 0.75:
        return "uncommon"

    return "rare"


# ==============================
# LEVEL DIFFERENCE MULTIPLIER
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
# EXP CALCULATION
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
# GOLD CALCULATION
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
# EQUIPMENT TROPHY DISPLAY HELPERS
# ==============================

def build_trophy_display_name(result):
    """
    Формує красиву назву трофея для повідомлення про лут.

    Для броні додає armor_type:
    Поножі 1 рівня -> Поножі [Тканина] 1 рівня

    Для зброї / off-hand тип у дужках не додається.
    """

    from db import (
        get_item_classification_by_inventory_id,
        get_armor_type_label,
        is_armor_slot,
    )

    name = result.get("name", "Трофей")
    inventory_id = result.get("inventory_id")

    if not inventory_id:
        return name

    classification = get_item_classification_by_inventory_id(inventory_id)

    if not classification:
        return name

    slot_key = classification.get("slot_key", "")
    armor_type = classification.get("armor_type", "")

    if not is_armor_slot(slot_key):
        return name

    if not armor_type:
        return name

    armor_label = get_armor_type_label(armor_type)

    if not armor_label:
        return name

    if f"[{armor_label}]" in name:
        return name

    marker = " рівня"

    if marker in name:
        index = name.rfind(marker)
        before_level = name[:index]
        after_level = name[index:]

        parts = before_level.rsplit(" ", 1)

        if len(parts) == 2 and parts[1].isdigit():
            return f"{parts[0]} [{armor_label}] {parts[1]}{after_level}"

    return f"{name} [{armor_label}]"


def is_trophy_suitable_for_class(user_id, result):
    """
    Перевіряє фактичну сумісність випалого предмета з поточним класом.
    """

    from db import can_equip_inventory_item_by_class

    inventory_id = result.get("inventory_id")

    if not inventory_id:
        return False

    check = can_equip_inventory_item_by_class(
        user_id=user_id,
        inventory_id=inventory_id,
    )

    return bool(check.get("success"))


def build_trophy_drop_message(user_id, result, rarity, is_elite):
    rarity_text = {
        "common": "⚪",
        "uncommon": "🟢",
        "rare": "🔵",
        "epic": "🟣",
    }.get(rarity, "⚪")

    item_name = build_trophy_display_name(result)

    is_suitable = (
        bool(result.get("class_aware"))
        or is_trophy_suitable_for_class(user_id, result)
    )

    if is_elite:
        if is_suitable:
            return (
                f"{rarity_text} 🎯 Елітний трофей під твій клас:\n"
                f"  📦 {item_name}"
            )

        return (
            f"{rarity_text} Елітний трофей:\n"
            f"  📦 {item_name}"
        )

    if is_suitable:
        return (
            f"{rarity_text} 🎯 Знайдено трофей під твій клас:\n"
            f"  📦 {item_name}"
        )

    return (
        f"{rarity_text} Знайдено трофей:\n"
        f"  📦 {item_name}"
    )


# ==============================
# EQUIPMENT DROP
# ==============================

def roll_equipment_drop(user_id, mob):
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
        class_aware_chance = ELITE_CLASS_AWARE_EQUIPMENT_CHANCE
    else:
        rarity = roll_normal_equipment_rarity()
        class_aware_chance = NORMAL_CLASS_AWARE_EQUIPMENT_CHANCE

    result = create_generated_equipment_item(
        user_id=user_id,
        item_level=mob_level,
        rarity=rarity,
        class_aware_chance=class_aware_chance,
    )

    if not result.get("success"):
        return result.get("message", "🎒 Екіпірування не влізло в сумку.")

    return build_trophy_drop_message(
        user_id=user_id,
        result=result,
        rarity=rarity,
        is_elite=is_elite,
    )


# ==============================
# SIMPLE LOOT
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

    if "loot_table" in mob and isinstance(mob["loot_table"], list):
        messages.extend(roll_loot_from_loot_table(user_id, mob["loot_table"]))

    elif "loot" in mob and isinstance(mob["loot"], list):
        messages.extend(roll_loot_from_loot_table(user_id, mob["loot"]))

    else:
        messages.extend(roll_loot_from_simple_keys(user_id, mob))

    trophy_message = roll_equipment_drop(user_id, mob)

    if trophy_message:
        messages.append(trophy_message)

    return messages


# ==============================
# PROCESS VICTORY REWARD
# ==============================

def process_victory_reward(user_id, player_level, mob):
    exp = calculate_exp_reward(
        player_level=player_level,
        mob=mob,
    )

    gold = calculate_gold_reward(
        player_level=player_level,
        mob=mob,
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
        "capacity": capacity,
    }
