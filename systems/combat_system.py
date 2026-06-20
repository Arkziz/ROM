import random


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


# ==============================
# MOB GENERATION
# ==============================

def generate_mob():
    mobs = [
        {
            "name": "🐺 Агресивний вовк",
            "level": 4,
            "hp": random.randint(35, 50),
            "attack": random.randint(6, 10),
            "def": random.randint(2, 5),
            "dex": random.randint(10, 14),
            "attack_type": "physical",
            "base_exp": 22,
            "trash_item_id": 101,
            "trash_chance": 85,
            "potion_item_id": 201,
            "potion_chance": 15,
            "is_boss": False
        },
        {
            "name": "🐗 Дикий кабан",
            "level": 2,
            "hp": random.randint(40, 60),
            "attack": random.randint(5, 9),
            "def": random.randint(3, 6),
            "dex": random.randint(6, 10),
            "attack_type": "physical",
            "base_exp": 14,
            "trash_item_id": 102,
            "trash_chance": 90,
            "potion_item_id": 201,
            "potion_chance": 15,
            "is_boss": False
        },
        {
            "name": "👹 Гоблін",
            "level": 5,
            "hp": random.randint(30, 45),
            "attack": random.randint(7, 11),
            "def": random.randint(2, 4),
            "dex": random.randint(9, 13),
            "attack_type": "physical",
            "base_exp": 30,
            "trash_item_id": 103,
            "trash_chance": 80,
            "potion_item_id": 201,
            "potion_chance": 10,
            "is_boss": False
        },
        {
            "name": "🔮 Гоблін-маг",
            "level": 6,
            "hp": random.randint(25, 40),
            "attack": random.randint(8, 13),
            "def": random.randint(1, 3),
            "dex": random.randint(6, 10),
            "attack_type": "magical",
            "base_exp": 42,
            "trash_item_id": 104,
            "trash_chance": 75,
            "potion_item_id": 202,
            "potion_chance": 25,
            "is_boss": False
        }
    ]

    return random.choice(mobs)


# ==============================
# CRIT
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
# DODGE
# ==============================

def get_dodge_chance(player_dex, mob_dex, level):
    if level <= 0:
        level = 1

    dodge_chance = ((player_dex - mob_dex) / (level * 2)) + 5

    return clamp(dodge_chance, 0, 30)


# ==============================
# PLAYER ATTACK
# ==============================

def calculate_player_attack(player_atk, mob_def, dex, wis, level, attack_type="physical"):
    base_damage = max(1, int(player_atk - (mob_def * 0.5) + random.randint(-2, 3)))

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
# MOB ATTACK
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
    is_dodge = False

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

    if attack_type == "magical":
        defense = player_mdef
    else:
        defense = player_pdef

    damage = max(1, int(mob_attack - (defense * 0.5) + random.randint(-2, 2)))

    base_mob_crit_chance = 10
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