import random


# ==============================
# ✅ HELPERS
# ==============================

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


# ==============================
# ✅ MOB GENERATION
# ==============================

def generate_mob():
    mobs = [
        {
            "name": "🐺 Вовк",
            "hp": random.randint(35, 50),
            "attack": random.randint(6, 10),
            "def": random.randint(2, 5),
            "dex": random.randint(10, 14),
            "attack_type": "physical"
        },
        {
            "name": "🐗 Кабан",
            "hp": random.randint(40, 60),
            "attack": random.randint(5, 9),
            "def": random.randint(3, 6),
            "dex": random.randint(6, 10),
            "attack_type": "physical"
        },
        {
            "name": "👹 Гоблін",
            "hp": random.randint(30, 45),
            "attack": random.randint(7, 11),
            "def": random.randint(2, 4),
            "dex": random.randint(9, 13),
            "attack_type": "physical"
        },
        {
            "name": "🔮 Гоблін-маг",
            "hp": random.randint(25, 40),
            "attack": random.randint(8, 13),
            "def": random.randint(1, 3),
            "dex": random.randint(6, 10),
            "attack_type": "magical"
        }
    ]

    return random.choice(mobs)


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
    # Але функція вже підтримує магічний крит на майбутнє.

    base_damage = max(1, int(player_atk - (mob_def * 0.5) + random.randint(-2, 3)))

    if attack_type == "magical":
        crit_chance = get_magical_crit_chance(wis, level)
    else:
        crit_chance = get_physical_crit_chance(dex, level)

    is_crit = random.uniform(0, 100) <= crit_chance

    final_damage = base_damage * 2 if is_crit else base_damage

    return {
        "damage": final_damage,
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

    # Ухиляння працює тільки проти фізичних атак
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

    # Damage = ATK - (DEF * 0.5)
    damage = max(1, int(mob_attack - (defense * 0.5) + random.randint(-2, 2)))

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