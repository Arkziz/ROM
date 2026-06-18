import random


def generate_mob():
    return {
        "name": random.choice(["🐺 Вовк", "🐗 Кабан", "👹 Гоблін"]),
        "hp": random.randint(30, 50),
        "attack": random.randint(5, 10),
        "def": random.randint(2, 5)
    }


def calculate_player_attack(player_atk, mob_def, dex):
    crit_chance = dex * 0.5
    is_crit = random.randint(1, 100) <= crit_chance

    damage = max(1, player_atk - mob_def + random.randint(-2, 3))

    if is_crit:
        damage *= 2

    return damage, is_crit


def calculate_mob_attack(mob_attack, player_def, dex, sta):
    dodge_chance = dex * 0.4
    is_dodge = random.randint(1, 100) <= dodge_chance

    anti_crit = sta // 25
    mob_crit_chance = max(0, 10 - anti_crit)
    is_crit = random.randint(1, 100) <= mob_crit_chance

    if is_dodge:
        return 0, False, True

    damage = max(1, mob_attack - player_def + random.randint(-2, 2))

    if is_crit:
        damage *= 2

    return damage, is_crit, False