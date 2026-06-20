import random

from data.mobs import LOCATION_1_MOBS


# ==============================
# ✅ HELPERS
# ==============================

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


# ==============================
# ✅ MOB GENERATION
# ==============================

def build_mob(mob_template):
    return {
        "name": mob_template["name"],
        "level": mob_template["level"],

        "hp": random.randint(
            mob_template["hp_min"],
            mob_template["hp_max"]
        ),

        "attack": random.randint(
            mob_template["attack_min"],
            mob_template["attack_max"]
        ),

        "def": random.randint(
            mob_template["def_min"],
            mob_template["def_max"]
        ),

        "dex": random.randint(
            mob_template["dex_min"],
            mob_template["dex_max"]
        ),

        "attack_type": mob_template["attack_type"],

        "base_exp": mob_template.get("base_exp", 0),
        "trash_item_id": mob_template.get("trash_item_id"),
        "trash_chance": mob_template.get("trash_chance", 80),
        "potion_item_id": mob_template.get("potion_item_id"),
        "potion_chance": mob_template.get("potion_chance", 0),
        "is_boss": mob_template.get("is_boss", False)
    }


def generate_mob(player_level):
    """
    Генерація моба з урахуванням рівня гравця.

    Правило:
    - гравець бачить тільки мобів, у яких min_player_level <= player_level;
    - пріоритет мають моби близькі до рівня гравця;
    - гравець 1 рівня більше не зустріне моба 6 рівня.
    """

    unlocked = [
        mob for mob in LOCATION_1_MOBS
        if mob["min_player_level"] <= player_level
    ]

    if not unlocked:
        unlocked = [LOCATION_1_MOBS[0]]

    # Основний пул: моби від -1 до +1 рівня від гравця
    near_level = [
        mob for mob in unlocked
        if player_level - 1 <= mob["level"] <= player_level + 1
    ]

    # Якщо таких немає — беремо всіх відкритих
    if not near_level:
        near_level = unlocked

    selected_template = random.choice(near_level)

    return build_mob(selected_template)


# ==============================
# ✅ CRIT FORMULAS
# ==============================

def get_physical_crit_chance(dex, level):
    if level <= 0:
        level = 1

    crit_chance = (dex / (level * 40)) * 100
    return clamp(crit_chance, 0, 50)


def get_magical_crit_chance(wis, level):
    if level <= 0:
        level = 1

    crit_chance = (wis / (level * 50)) * 100
    return clamp(crit_chance, 0, 50)


# ==============================
# ✅ DODGE FORMULA
# ==============================

def get_dodge_chance(player_dex, mob_dex, level):
    if level <= 0:
        level = 1

    dodge_chance = ((player_dex - mob_dex) / (level * 2)) + 5
    return clamp(dodge_chance, 0, 30)


# ==============================
# ✅ PLAYER ATTACK
# ==============================

def calculate_player_attack(
    player_atk,
    mob_def,
    dex,
    wis,
    level,
    attack_type="physical"
):
    # Поки гравець бʼє фізично.
    # Але підтримка magical вже закладена на майбутнє.

    base_damage = max(
        1,
        int(player_atk - (mob_def * 0.5) + random.randint(-2, 3))
    )

    if attack_type == "magical":
        crit_chance = get_magical_crit_chance(wis, level)
    else:
        crit_chance = get_physical_crit_chance(dex, level)

    is_crit = random.uniform(0, 100) <= crit_chance

    damage = base_damage * 2 if is_crit else base_damage

    return {
        "damage": damage,
        "is_crit": is_crit,
        "crit_chance": round(crit_chance, 2)
    }


# ==============================
# ✅ MOB ATTACK
# ==============================

def calculate_mob_attack(
    mob_attack,
    player_pdef,
    player_mdef,
    player_dex,
    mob_dex,
    sta,
    level,
    attack_type="physical"
):
    # ==============================
    # DODGE
    # ==============================

    is_dodge = False

    # Ухил працює тільки проти фізичних атак
    if attack_type == "physical":
        dodge_chance = get_dodge_chance(player_dex, mob_dex, level)
        is_dodge = random.uniform(0, 100) <= dodge_chance
    else:
        dodge_chance = 0

    if is_dodge:
        return {
            "damage": 0,
            "is_crit": False,
            "is_dodge": True,
            "dodge_chance": round(dodge_chance, 2),
            "crit_chance": 0
        }

    # ==============================
    # DEFENSE LAYER
    # ==============================

    if attack_type == "magical":
        defense = player_mdef
    else:
        defense = player_pdef

    # Damage = ATK - (DEF * 0.5), мінімум 1
    damage = max(
        1,
        int(mob_attack - (defense * 0.5) + random.randint(-2, 2))
    )

    # ==============================
    # MOB CRIT
    # ==============================

    base_mob_crit_chance = 10

    # STA зменшує шанс криту моба
    anti_crit = sta // 25
    mob_crit_chance = max(0, base_mob_crit_chance - anti_crit)

    is_crit = random.uniform(0, 100) <= mob_crit_chance

    if is_crit:
        damage *= 2

    return {
        "damage": damage,
        "is_crit": is_crit,
        "is_dodge": False,
        "dodge_chance": round(dodge_chance, 2),
        "crit_chance": round(mob_crit_chance, 2)
    }