"""Dynamic equipment generation restored from final legacy db.py definitions."""

import math

import random

import sqlite3

from db_modules.connection import conn, cursor

from data.equipment_profiles import *

DYNAMIC_RARITY_ICONS = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣"
}

DYNAMIC_STAT_MULTIPLIERS = {
    "common": 1.0,
    "uncommon": 1.35,
    "rare": 1.85,
    "epic": 2.60
}

DYNAMIC_SELL_MULTIPLIERS = {
    "common": 0.30,
    "uncommon": 0.90,
    "rare": 2.25,
    "epic": 6.00
}

DYNAMIC_SLOT_NAMES = {
    "main_hand": "Зброя",
    "off_hand": "Друга рука",
    "helmet": "Шолом",
    "shoulders": "Наплічники",
    "chest": "Обладунок",
    "gloves": "Рукавиці",
    "legs": "Поножі",
    "boots": "Чоботи",
    "necklace": "Амулет",
    "ring": "Кільце"
}

def get_dynamic_stat_value(item_level, rarity, base=1.0):
    multiplier = DYNAMIC_STAT_MULTIPLIERS.get(rarity, 1.0)
    value = int(round(item_level * base * multiplier))

    return max(1, value)

def get_dynamic_sell_price(item_level, rarity):
    multiplier = DYNAMIC_SELL_MULTIPLIERS.get(rarity, 0.30)

    return round(max(0.10, item_level * multiplier), 2)

def get_dynamic_armor_name(slot_key, rarity):
    icon = DYNAMIC_RARITY_ICONS.get(rarity, "⚪")
    base_name = DYNAMIC_SLOT_NAMES.get(slot_key, "Річ")

    return f"{icon} {base_name}"

def init_dynamic_equipment_system():
    migrations = [
        ("items", "item_level", "INTEGER DEFAULT 1"),
        ("items", "is_generated", "INTEGER DEFAULT 0"),
        ("items", "item_subtype", "TEXT DEFAULT ''"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()

def add_stat_value(stats, stat_key, value):
    if stat_key == "str":
        stats["bonus_str"] += value
    elif stat_key == "dex":
        stats["bonus_dex"] += value
    elif stat_key == "int":
        stats["bonus_int"] += value
    elif stat_key == "wis":
        stats["bonus_wis"] += value
    elif stat_key == "sta":
        stats["bonus_sta"] += value

def get_random_main_hand_profile():
    return random.choice(list(MAIN_HAND_PROFILES.keys()))

def get_random_off_hand_profile():
    return random.choice(list(OFF_HAND_PROFILES.keys()))

def get_profile_for_generated_item(slot_key, item_profile=None):
    if slot_key == "main_hand":
        if item_profile in MAIN_HAND_PROFILES:
            return item_profile

        return get_random_main_hand_profile()

    if slot_key == "off_hand":
        if item_profile in OFF_HAND_PROFILES:
            return item_profile

        return get_random_off_hand_profile()

    return ""

def get_dynamic_weapon_name(slot_key, rarity, weapon_hands=1, item_profile=None):
    icon = DYNAMIC_RARITY_ICONS.get(rarity, "⚪")

    if slot_key == "main_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = MAIN_HAND_PROFILES.get(profile_key, MAIN_HAND_PROFILES["sword_1h"])
        return f"{icon} {profile['name']}"

    if slot_key == "off_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = OFF_HAND_PROFILES.get(profile_key, OFF_HAND_PROFILES["shield"])
        return f"{icon} {profile['name']}"

    return f"{icon} Зброя"

def generate_dynamic_equipment_stats(slot_key, item_level, rarity, weapon_hands=1, item_profile=None):
    stats = {
        "bonus_str": 0,
        "bonus_dex": 0,
        "bonus_int": 0,
        "bonus_wis": 0,
        "bonus_sta": 0,
        "pdef": 0,
        "mdef": 0
    }

    # ==============================
    # MAIN HAND
    # ==============================

    if slot_key == "main_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = MAIN_HAND_PROFILES.get(profile_key, MAIN_HAND_PROFILES["sword_1h"])

        main_stat = profile["main_stats"][0]
        base_multiplier = 1.00

        if profile["hands"] == 2:
            base_multiplier = 1.20

        value = get_dynamic_stat_value(item_level, rarity, base_multiplier)
        add_stat_value(stats, main_stat, value)

        extra_pool = profile["extra_stats"]

    # ==============================
    # OFF HAND
    # ==============================

    elif slot_key == "off_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = OFF_HAND_PROFILES.get(profile_key, OFF_HAND_PROFILES["shield"])

        if profile_key == "shield":
            stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.35)
            stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.55)

        elif profile_key == "talisman":
            stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 1.35)
            stats["bonus_wis"] = get_dynamic_stat_value(item_level, rarity, 0.65)

        elif profile_key == "dagger":
            stats["bonus_dex"] = get_dynamic_stat_value(item_level, rarity, 0.95)
            stats["bonus_str"] = get_dynamic_stat_value(item_level, rarity, 0.35)

        extra_pool = profile["extra_stats"]

    # ==============================
    # ARMOR SLOTS
    # ==============================

    elif slot_key == "helmet":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 0.80)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.40)

        bonus = random.choice(["sta", "wis", "dex"])
        value = get_dynamic_stat_value(item_level, rarity, 0.25)
        add_stat_value(stats, bonus, value)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "shoulders":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.00)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.25)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "chest":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.60)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.35)
        stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.55)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "gloves":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 0.55)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.20)
        stats["bonus_dex"] = get_dynamic_stat_value(item_level, rarity, 0.60)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["dex"])

    elif slot_key == "legs":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.20)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.30)
        stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.45)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "boots":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 0.45)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.20)
        stats["bonus_dex"] = get_dynamic_stat_value(item_level, rarity, 0.80)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["dex"])

    # ==============================
    # JEWELRY
    # ==============================

    elif slot_key == "necklace":
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 1.30)
        stats["bonus_wis"] = get_dynamic_stat_value(item_level, rarity, 0.80)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["wis", "int"])

    elif slot_key == "ring":
        stat_choice = random.choice(["str", "dex", "int", "wis", "sta"])
        value = get_dynamic_stat_value(item_level, rarity, 0.90)
        add_stat_value(stats, stat_choice, value)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["str", "dex", "int", "wis", "sta"])

    else:
        extra_pool = ["str", "dex", "int", "wis", "sta"]

    # ==============================
    # EXTRA BONUSES BY RARITY
    # ==============================

    if rarity in ["uncommon", "rare", "epic"]:
        bonus_count = 1
        min_bonus = 2

        if rarity == "rare":
            bonus_count = 2
            min_bonus = 3

        if rarity == "epic":
            bonus_count = 3
            min_bonus = 4

        for _ in range(bonus_count):
            bonus_type = random.choice(extra_pool)

            bonus_value = get_dynamic_stat_value(item_level, rarity, 0.30)
            bonus_value = max(min_bonus, bonus_value)

            add_stat_value(stats, bonus_type, bonus_value)

    return stats

def normalize_equipment_restriction_value(value):
    if value is None:
        return ""

    return str(value).strip()

ARMOR_DEFENSE_DISTRIBUTION_PROFILES = {
    "cloth": {
        # Тканина: мало фізичного, багато магічного.
        "pdef_share": 0.30,
        "mdef_share": 0.70,
        "total_multiplier": 1.00
    },
    "leather": {
        # Шкіра: близько до балансу, трохи більше фізичного.
        "pdef_share": 0.55,
        "mdef_share": 0.45,
        "total_multiplier": 1.05
    },
    "chain": {
        # Кольчуга: високий фізичний, нижчий магічний.
        "pdef_share": 0.75,
        "mdef_share": 0.25,
        "total_multiplier": 1.10
    },
    "plate": {
        # Лати: максимум фізичного, мінімум магічного.
        "pdef_share": 0.88,
        "mdef_share": 0.12,
        "total_multiplier": 1.15
    }
}

ARMOR_PRIMARY_STAT_PROFILES = {
    # Тканина для мага / жерця:
    # інтелект, мудрість, трохи витривалості.
    "cloth": {
        "primary_weights": [
            ("int", 40),
            ("wis", 40),
            ("sta", 20)
        ],
        "secondary_weights": [
            ("wis", 45),
            ("int", 45),
            ("sta", 10)
        ],
        "main_multiplier": 1.00,
        "secondary_multiplier": 0.50
    },

    # Шкіра для скаута / розбійника:
    # спритність, сила, трохи витривалості.
    "leather": {
        "primary_weights": [
            ("dex", 50),
            ("str", 30),
            ("sta", 20)
        ],
        "secondary_weights": [
            ("sta", 45),
            ("str", 35),
            ("dex", 20)
        ],
        "main_multiplier": 1.00,
        "secondary_multiplier": 0.50
    },

    # Кольчуга для воїна:
    # сила і витривалість.
    "chain": {
        "primary_weights": [
            ("str", 55),
            ("sta", 40),
            ("dex", 5)
        ],
        "secondary_weights": [
            ("sta", 55),
            ("str", 40),
            ("dex", 5)
        ],
        "main_multiplier": 1.00,
        "secondary_multiplier": 0.50
    },

    # Лати для лицаря:
    # витривалість головна, сила друга.
    "plate": {
        "primary_weights": [
            ("sta", 65),
            ("str", 35)
        ],
        "secondary_weights": [
            ("str", 70),
            ("sta", 30)
        ],
        "main_multiplier": 1.25,
        "secondary_multiplier": 0.50
    }
}

def pick_weighted_stat(weighted_stats, exclude_stat=None):
    """
    Вибирає характеристику за вагами.
    """

    filtered = []

    for stat_key, weight in weighted_stats:
        if exclude_stat is not None and stat_key == exclude_stat:
            continue

        filtered.append((stat_key, weight))

    if not filtered:
        filtered = weighted_stats

    if not filtered:
        return ""

    total_weight = sum(weight for _, weight in filtered)

    if total_weight <= 0:
        return filtered[0][0]

    roll = random.randint(1, total_weight)
    current = 0

    for stat_key, weight in filtered:
        current += weight

        if roll <= current:
            return stat_key

    return filtered[-1][0]

def add_primary_stat_to_stats(stats, stat_key, value):
    """
    Додає основну характеристику у stats.
    """

    value = int(value or 0)

    if value <= 0:
        return

    if stat_key == "str":
        stats["bonus_str"] += value

    elif stat_key == "dex":
        stats["bonus_dex"] += value

    elif stat_key == "int":
        stats["bonus_int"] += value

    elif stat_key == "wis":
        stats["bonus_wis"] += value

    elif stat_key == "sta":
        stats["bonus_sta"] += value

def get_existing_primary_stat_budget(stats):
    """
    Рахує поточний бюджет основних характеристик.
    Наприклад chest 8 common дає bonus_sta = 4, отже budget = 4.
    """

    return (
        int(stats.get("bonus_str", 0) or 0)
        + int(stats.get("bonus_dex", 0) or 0)
        + int(stats.get("bonus_int", 0) or 0)
        + int(stats.get("bonus_wis", 0) or 0)
        + int(stats.get("bonus_sta", 0) or 0)
    )

def clear_primary_stat_bonuses(stats):
    """
    Очищає старі slot-based характеристики.
    """

    stats["bonus_str"] = 0
    stats["bonus_dex"] = 0
    stats["bonus_int"] = 0
    stats["bonus_wis"] = 0
    stats["bonus_sta"] = 0

def apply_armor_type_primary_stat_profile_to_stats(stats, armor_type):
    """
    Перерозподіляє основні характеристики броні залежно від armor_type.

    cloth   -> INT / WIS / STA
    leather -> DEX / STR / STA
    chain   -> STR / STA / рідко DEX
    plate   -> STA / STR
    """

    armor_type = normalize_equipment_restriction_value(armor_type)

    if not armor_type:
        return stats

    profile = ARMOR_PRIMARY_STAT_PROFILES.get(armor_type)

    if not profile:
        return stats

    existing_budget = get_existing_primary_stat_budget(stats)

    if existing_budget <= 0:
        return stats

    clear_primary_stat_bonuses(stats)

    main_multiplier = float(profile.get("main_multiplier", 1.0))
    secondary_multiplier = float(profile.get("secondary_multiplier", 0.5))

    primary_value = int(round(existing_budget * main_multiplier))
    secondary_value = int(round(existing_budget * secondary_multiplier))

    primary_value = max(1, primary_value)

    if existing_budget >= 2:
        secondary_value = max(1, secondary_value)
    else:
        secondary_value = 0

    primary_stat = pick_weighted_stat(
        profile.get("primary_weights", []),
        exclude_stat=None
    )

    secondary_stat = None

    if secondary_value > 0:
        secondary_stat = pick_weighted_stat(
            profile.get("secondary_weights", []),
            exclude_stat=primary_stat
        )

    add_primary_stat_to_stats(
        stats=stats,
        stat_key=primary_stat,
        value=primary_value
    )

    if secondary_stat:
        add_primary_stat_to_stats(
            stats=stats,
            stat_key=secondary_stat,
            value=secondary_value
        )

    return stats

def apply_armor_type_defense_profile_to_stats(stats, armor_type):
    """
    Центральна функція профілю броні.

    Робить 2 речі:
    1. Перерозподіляє PDEF/MDEF залежно від armor_type.
    2. Перерозподіляє основні характеристики залежно від armor_type.
    """

    armor_type = normalize_equipment_restriction_value(armor_type)

    if not armor_type:
        return stats

    # ==============================
    # 1. PDEF / MDEF redistribution
    # ==============================

    defense_profile = ARMOR_DEFENSE_DISTRIBUTION_PROFILES.get(armor_type)

    if defense_profile:
        base_pdef = int(stats.get("pdef", 0) or 0)
        base_mdef = int(stats.get("mdef", 0) or 0)
        base_total = base_pdef + base_mdef

        if base_total > 0:
            total_multiplier = float(defense_profile.get("total_multiplier", 1.0))
            pdef_share = float(defense_profile.get("pdef_share", 0.5))
            mdef_share = float(defense_profile.get("mdef_share", 0.5))

            total_defense = int(round(base_total * total_multiplier))

            if total_defense < 2:
                total_defense = 2

            new_pdef = int(round(total_defense * pdef_share))
            new_mdef = int(round(total_defense * mdef_share))

            new_pdef = max(1, new_pdef)
            new_mdef = max(1, new_mdef)

            # Гарантія: тканина завжди має MDEF > PDEF.
            if armor_type == "cloth" and new_mdef <= new_pdef:
                total = max(2, new_pdef + new_mdef)
                new_mdef = max(1, int(round(total * 0.70)))
                new_pdef = max(1, total - new_mdef)

                if new_mdef <= new_pdef:
                    new_mdef = new_pdef + 1

            # Гарантія: лати завжди мають PDEF > MDEF.
            if armor_type == "plate" and new_pdef <= new_mdef:
                total = max(2, new_pdef + new_mdef)
                new_pdef = max(1, int(round(total * 0.88)))
                new_mdef = max(1, total - new_pdef)

                if new_pdef <= new_mdef:
                    new_pdef = new_mdef + 1

            stats["pdef"] = new_pdef
            stats["mdef"] = new_mdef

    # ==============================
    # 2. Primary stats redistribution
    # ==============================

    stats = apply_armor_type_primary_stat_profile_to_stats(
        stats=stats,
        armor_type=armor_type
    )

    return stats

__all__ = ['init_dynamic_equipment_system', 'get_dynamic_weapon_name', 'get_dynamic_armor_name', 'generate_dynamic_equipment_stats', 'apply_armor_type_defense_profile_to_stats', 'get_dynamic_sell_price']
