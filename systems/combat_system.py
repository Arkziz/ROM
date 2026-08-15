import random

from data.mobs import get_mobs_for_location
from data.bosses import BOSS_ENCOUNTERS_ENABLED, BOSS_ENCOUNTER_CHANCE_PERCENT
from systems.boss_system import generate_hunt_encounter


# ==============================
# ✅ ELITE CONFIG
# ==============================

ELITE_CHANCE_PERCENT = 5.0

ELITE_CORE_STAT_MULTIPLIER = 1.8
ELITE_HP_MULTIPLIER = ELITE_CORE_STAT_MULTIPLIER
ELITE_ATTACK_MULTIPLIER = ELITE_CORE_STAT_MULTIPLIER
ELITE_EXP_MULTIPLIER = 3.0
ELITE_GOLD_MULTIPLIER = 3.0


# ==============================
# ✅ CRIT / DODGE HELPERS
# ==============================

def get_physical_crit_chance(dex, level):
    if level <= 0:
        level = 1

    chance = 5 + ((dex - 10) / max(1, level)) * 0.5

    return max(1, min(35, chance))


def get_magical_crit_chance(wis, level):
    if level <= 0:
        level = 1

    chance = 5 + ((wis - 10) / max(1, level)) * 0.5

    return max(1, min(35, chance))


def get_dodge_chance(player_dex, mob_dex, level):
    if level <= 0:
        level = 1

    chance = 5 + ((player_dex - mob_dex) / max(1, level)) * 0.8

    return max(1, min(30, chance))


# ==============================
# ✅ MOB GENERATION
# ==============================

def roll_is_elite():
    roll = random.randint(1, 100)
    return roll <= ELITE_CHANCE_PERCENT


def build_mob(mob_template):
    hp = random.randint(
        int(mob_template["hp_min"]),
        int(mob_template["hp_max"])
    )

    attack = random.randint(
        int(mob_template["attack_min"]),
        int(mob_template["attack_max"])
    )

    pdef = random.randint(
        int(mob_template.get("pdef_min", mob_template.get("def_min", 1))),
        int(mob_template.get("pdef_max", mob_template.get("def_max", 1)))
    )

    mdef = random.randint(
        int(mob_template.get("mdef_min", mob_template.get("def_min", 1))),
        int(mob_template.get("mdef_max", mob_template.get("def_max", 1)))
    )

    dex = random.randint(
        int(mob_template["dex_min"]),
        int(mob_template["dex_max"])
    )

    mob = {
        "name": mob_template["name"],
        "base_name": mob_template["name"],

        "level": int(mob_template["level"]),
        "location_id": mob_template.get("location_id", "start_path"),

        "hp": hp,
        "max_hp": hp,

        "attack": attack,

        "pdef": pdef,
        "mdef": mdef,

        # compatibility
        "def": pdef if mob_template.get("attack_type", "physical") == "physical" else mdef,

        "dex": dex,

        "attack_type": mob_template.get("attack_type", "physical"),

        "min_gold": mob_template.get("min_gold", 0),
        "max_gold": mob_template.get("max_gold", 0),

        "loot_chance": mob_template.get("loot_chance", 0),
        "trash_items": mob_template.get("trash_items", []),

        "is_elite": False,
        "elite_exp_multiplier": 1.0,
        "elite_gold_multiplier": 1.0
    }

    return mob


def apply_elite_modifier(mob):
    old_name = mob["name"]

    mob["name"] = f"⭐ Елітний {old_name}"
    mob["base_name"] = old_name

    mob["hp"] = int(mob["hp"] * ELITE_HP_MULTIPLIER)
    mob["max_hp"] = mob["hp"]

    mob["attack"] = int(mob["attack"] * ELITE_ATTACK_MULTIPLIER)

    mob["pdef"] = max(1, int(round(mob["pdef"] * ELITE_CORE_STAT_MULTIPLIER)))
    mob["mdef"] = max(1, int(round(mob["mdef"] * ELITE_CORE_STAT_MULTIPLIER)))
    mob["dex"] = max(1, int(round(mob["dex"] * ELITE_CORE_STAT_MULTIPLIER)))
    mob["def"] = mob["pdef"] if mob.get("attack_type", "physical") == "physical" else mob["mdef"]

    mob["is_elite"] = True
    mob["elite_exp_multiplier"] = ELITE_EXP_MULTIPLIER
    mob["elite_gold_multiplier"] = ELITE_GOLD_MULTIPLIER

    return mob


def get_available_mobs(player_level, location_id="start_path"):
    mobs = get_mobs_for_location(location_id)
    available = []

    for mob in mobs:
        mob_level = int(mob.get("level", 1))
        min_player_level = int(mob.get("min_player_level", 1))

        if min_player_level <= player_level and player_level - 1 <= mob_level <= player_level + 1:
            available.append(mob)

    if available:
        return available

    fallback = []

    for mob in mobs:
        min_player_level = int(mob.get("min_player_level", 1))

        if min_player_level <= player_level:
            fallback.append(mob)

    return fallback


def generate_mob(player_level, location_id="start_path"):
    def _build_normal_mob():
        available_mobs = get_available_mobs(
            player_level=player_level,
            location_id=location_id
        )

        if not available_mobs:
            selected_template = get_mobs_for_location(location_id)[0]
        else:
            selected_template = random.choice(available_mobs)

        return build_mob(selected_template)

    encounter = generate_hunt_encounter(
        player_level=player_level,
        location_id=location_id,
        normal_mob_factory=_build_normal_mob,
        elite_modifier=apply_elite_modifier,
        elite_roll=roll_is_elite,
        rng=random,
        boss_enabled=BOSS_ENCOUNTERS_ENABLED,
        boss_chance_percent=BOSS_ENCOUNTER_CHANCE_PERCENT,
    )
    return encounter["mob"]


# ==============================
# ✅ DAMAGE CALCULATION
# ==============================

def calculate_player_attack(
    player_stat_attack,
    mob_def,
    dex,
    wis,
    level,
    attack_type="physical",
    weapon_min_damage=0,
    weapon_max_damage=0
):
    weapon_min_damage = int(weapon_min_damage or 0)
    weapon_max_damage = int(weapon_max_damage or 0)

    if weapon_max_damage < weapon_min_damage:
        weapon_max_damage = weapon_min_damage

    weapon_damage = 0

    if weapon_max_damage > 0:
        weapon_damage = random.randint(weapon_min_damage, weapon_max_damage)

    base_damage = weapon_damage + player_stat_attack - (mob_def * 0.5)

    if base_damage < 1:
        base_damage = 1

    if attack_type == "magical":
        crit_chance = get_magical_crit_chance(wis, level)
    else:
        crit_chance = get_physical_crit_chance(dex, level)

    is_crit = random.uniform(0, 100) <= crit_chance

    if is_crit:
        base_damage *= 1.5

    damage = max(1, int(round(base_damage)))

    return {
        "damage": damage,
        "is_crit": is_crit,
        "crit_chance": crit_chance,
        "weapon_damage": weapon_damage,
        "attack_type": attack_type
    }


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
    dodge_chance = get_dodge_chance(
        player_dex=player_dex,
        mob_dex=mob_dex,
        level=level
    )

    is_dodge = random.uniform(0, 100) <= dodge_chance

    if is_dodge:
        return {
            "damage": 0,
            "is_crit": False,
            "is_dodge": True,
            "dodge_chance": dodge_chance
        }

    if attack_type == "magical":
        defense = player_mdef
    else:
        defense = player_pdef

    damage = mob_attack - (defense * 0.5)

    if damage < 1:
        damage = 1

    enemy_crit_chance = max(0, 10 - (sta // 25))
    is_crit = random.uniform(0, 100) <= enemy_crit_chance

    if is_crit:
        damage *= 1.5

    damage = max(1, int(round(damage)))

    return {
        "damage": damage,
        "is_crit": is_crit,
        "is_dodge": False,
        "dodge_chance": dodge_chance
    }
