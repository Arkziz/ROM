# ==============================
# 🌿 LOCATION 1 — ПОЧАТОК ШЛЯХУ — LEVEL 1–5
# ==============================

START_PATH_MOBS = [
    # LEVEL 1
    {
        "name": "🐗 Дикий кабан",
        "level": 1,
        "min_player_level": 1,
        "location_id": "start_path",

        "hp_min": 45,
        "hp_max": 55,

        "attack_min": 7,
        "attack_max": 9,

        "pdef_min": 3,
        "pdef_max": 5,
        "mdef_min": 1,
        "mdef_max": 2,

        "dex_min": 5,
        "dex_max": 7,
               "str_min": 7,
               "str_max": 11,
               "int_min": 2,
               "int_max": 6,
               "wis_min": 3,
               "wis_max": 7,
               "sta_min": 6,
               "sta_max": 10,

        "attack_type": "physical",

        "min_gold": 0.05,
        "max_gold": 0.12,

        "loot_chance": 0.45,
        "trash_items": [107]
    },
    {
        "name": "🌱 Рунічний паросток",
        "level": 1,
        "min_player_level": 1,
        "location_id": "start_path",

        "hp_min": 38,
        "hp_max": 48,

        "attack_min": 8,
        "attack_max": 10,

        "pdef_min": 1,
        "pdef_max": 2,
        "mdef_min": 4,
        "mdef_max": 6,

        "dex_min": 4,
        "dex_max": 6,
               "str_min": 1,
               "str_max": 5,
               "int_min": 6,
               "int_max": 10,
               "wis_min": 5,
               "wis_max": 9,
               "sta_min": 4,
               "sta_max": 8,

        "attack_type": "magical",

        "min_gold": 0.06,
        "max_gold": 0.13,

        "loot_chance": 0.45,
        "trash_items": [108]
    },

    # LEVEL 2
    {
        "name": "🦡 Лісовий борсук",
        "level": 2,
        "min_player_level": 1,
        "location_id": "start_path",

        "hp_min": 68,
        "hp_max": 82,

        "attack_min": 10,
        "attack_max": 13,

        "pdef_min": 5,
        "pdef_max": 7,
        "mdef_min": 2,
        "mdef_max": 3,

        "dex_min": 6,
        "dex_max": 8,
               "str_min": 8,
               "str_max": 12,
               "int_min": 3,
               "int_max": 7,
               "wis_min": 4,
               "wis_max": 8,
               "sta_min": 7,
               "sta_max": 11,

        "attack_type": "physical",

        "min_gold": 0.09,
        "max_gold": 0.18,

        "loot_chance": 0.45,
        "trash_items": [109]
    },
    {
        "name": "💎 Рунічний слимак",
        "level": 2,
        "min_player_level": 1,
        "location_id": "start_path",

        "hp_min": 62,
        "hp_max": 76,

        "attack_min": 11,
        "attack_max": 14,

        "pdef_min": 2,
        "pdef_max": 3,
        "mdef_min": 6,
        "mdef_max": 8,

        "dex_min": 4,
        "dex_max": 6,
               "str_min": 1,
               "str_max": 5,
               "int_min": 6,
               "int_max": 10,
               "wis_min": 5,
               "wis_max": 9,
               "sta_min": 4,
               "sta_max": 8,

        "attack_type": "magical",

        "min_gold": 0.10,
        "max_gold": 0.20,

        "loot_chance": 0.45,
        "trash_items": [110]
    },

    # LEVEL 3
    {
        "name": "🦇 Лісовий кажан",
        "level": 3,
        "min_player_level": 2,
        "location_id": "start_path",

        "hp_min": 75,
        "hp_max": 92,

        "attack_min": 14,
        "attack_max": 17,

        "pdef_min": 4,
        "pdef_max": 6,
        "mdef_min": 2,
        "mdef_max": 4,

        "dex_min": 12,
        "dex_max": 15,
               "str_min": 14,
               "str_max": 19,
               "int_min": 9,
               "int_max": 14,
               "wis_min": 10,
               "wis_max": 15,
               "sta_min": 13,
               "sta_max": 18,

        "attack_type": "physical",

        "min_gold": 0.14,
        "max_gold": 0.26,

        "loot_chance": 0.48,
        "trash_items": [111]
    },
    {
        "name": "🩸 Печерний кровосос",
        "level": 3,
        "min_player_level": 2,
        "location_id": "start_path",

        "hp_min": 72,
        "hp_max": 88,

        "attack_min": 15,
        "attack_max": 19,

        "pdef_min": 2,
        "pdef_max": 4,
        "mdef_min": 7,
        "mdef_max": 10,

        "dex_min": 10,
        "dex_max": 13,
               "str_min": 7,
               "str_max": 12,
               "int_min": 12,
               "int_max": 17,
               "wis_min": 11,
               "wis_max": 16,
               "sta_min": 10,
               "sta_max": 15,

        "attack_type": "magical",

        "min_gold": 0.16,
        "max_gold": 0.30,

        "loot_chance": 0.48,
        "trash_items": [112]
    },

    # LEVEL 4
    {
        "name": "🕷️ Малий павук",
        "level": 4,
        "min_player_level": 3,
        "location_id": "start_path",

        "hp_min": 95,
        "hp_max": 115,

        "attack_min": 17,
        "attack_max": 21,

        "pdef_min": 6,
        "pdef_max": 8,
        "mdef_min": 3,
        "mdef_max": 5,

        "dex_min": 13,
        "dex_max": 16,
               "str_min": 15,
               "str_max": 20,
               "int_min": 10,
               "int_max": 15,
               "wis_min": 11,
               "wis_max": 16,
               "sta_min": 14,
               "sta_max": 19,

        "attack_type": "physical",

        "min_gold": 0.20,
        "max_gold": 0.36,

        "loot_chance": 0.50,
        "trash_items": [113]
    },
    {
        "name": "🧪 Павук-кислотник",
        "level": 4,
        "min_player_level": 3,
        "location_id": "start_path",

        "hp_min": 88,
        "hp_max": 108,

        "attack_min": 19,
        "attack_max": 23,

        "pdef_min": 3,
        "pdef_max": 5,
        "mdef_min": 9,
        "mdef_max": 12,

        "dex_min": 10,
        "dex_max": 13,
               "str_min": 7,
               "str_max": 12,
               "int_min": 12,
               "int_max": 17,
               "wis_min": 11,
               "wis_max": 16,
               "sta_min": 10,
               "sta_max": 15,

        "attack_type": "magical",

        "min_gold": 0.22,
        "max_gold": 0.40,

        "loot_chance": 0.50,
        "trash_items": [114]
    },

    # LEVEL 5
    {
        "name": "🐺 Молодий вовк",
        "level": 5,
        "min_player_level": 4,
        "location_id": "start_path",

        "hp_min": 130,
        "hp_max": 155,

        "attack_min": 22,
        "attack_max": 27,

        "pdef_min": 8,
        "pdef_max": 11,
        "mdef_min": 4,
        "mdef_max": 6,

        "dex_min": 12,
        "dex_max": 15,
               "str_min": 14,
               "str_max": 19,
               "int_min": 9,
               "int_max": 14,
               "wis_min": 10,
               "wis_max": 15,
               "sta_min": 13,
               "sta_max": 18,

        "attack_type": "physical",

        "min_gold": 0.30,
        "max_gold": 0.50,

        "loot_chance": 0.52,
        "trash_items": [115]
    },
    {
        "name": "👻 Вовк-примара",
        "level": 5,
        "min_player_level": 4,
        "location_id": "start_path",

        "hp_min": 120,
        "hp_max": 145,

        "attack_min": 24,
        "attack_max": 29,

        "pdef_min": 4,
        "pdef_max": 6,
        "mdef_min": 11,
        "mdef_max": 14,

        "dex_min": 11,
        "dex_max": 14,
               "str_min": 8,
               "str_max": 13,
               "int_min": 13,
               "int_max": 18,
               "wis_min": 12,
               "wis_max": 17,
               "sta_min": 11,
               "sta_max": 16,

        "attack_type": "magical",

        "min_gold": 0.34,
        "max_gold": 0.58,

        "loot_chance": 0.52,
        "trash_items": [116]
    },
]


# ==============================
# 🌲 LOCATION 2 — ТЕМНИЙ БІР — LEVEL 6–10
# ==============================

DARK_FOREST_MOBS = [
    # LEVEL 6
    {
        "name": "👺 Малий гоблін",
        "level": 6,
        "min_player_level": 6,
        "location_id": "dark_forest",

        "hp_min": 165,
        "hp_max": 195,

        "attack_min": 28,
        "attack_max": 34,

        "pdef_min": 10,
        "pdef_max": 13,
        "mdef_min": 5,
        "mdef_max": 7,

        "dex_min": 11,
        "dex_max": 14,
               "str_min": 13,
               "str_max": 18,
               "int_min": 8,
               "int_max": 13,
               "wis_min": 9,
               "wis_max": 14,
               "sta_min": 12,
               "sta_max": 17,

        "attack_type": "physical",

        "min_gold": 0.42,
        "max_gold": 0.75,

        "loot_chance": 0.54,
        "trash_items": [117]
    },
    {
        "name": "🧪 Гоблін-знахар",
        "level": 6,
        "min_player_level": 6,
        "location_id": "dark_forest",

        "hp_min": 155,
        "hp_max": 185,

        "attack_min": 30,
        "attack_max": 36,

        "pdef_min": 5,
        "pdef_max": 7,
        "mdef_min": 13,
        "mdef_max": 16,

        "dex_min": 9,
        "dex_max": 12,
               "str_min": 6,
               "str_max": 11,
               "int_min": 11,
               "int_max": 16,
               "wis_min": 10,
               "wis_max": 15,
               "sta_min": 9,
               "sta_max": 14,

        "attack_type": "magical",

        "min_gold": 0.46,
        "max_gold": 0.82,

        "loot_chance": 0.54,
        "trash_items": [118]
    },

    # LEVEL 7
    {
        "name": "🗡️ Гоблін-розвідник",
        "level": 7,
        "min_player_level": 6,
        "location_id": "dark_forest",

        "hp_min": 205,
        "hp_max": 240,

        "attack_min": 32,
        "attack_max": 38,

        "pdef_min": 12,
        "pdef_max": 15,
        "mdef_min": 6,
        "mdef_max": 8,

        "dex_min": 15,
        "dex_max": 18,
               "str_min": 17,
               "str_max": 22,
               "int_min": 12,
               "int_max": 17,
               "wis_min": 13,
               "wis_max": 18,
               "sta_min": 16,
               "sta_max": 21,

        "attack_type": "physical",

        "min_gold": 0.55,
        "max_gold": 0.95,

        "loot_chance": 0.55,
        "trash_items": [119]
    },
    {
        "name": "🧙 Гоблін-шаман",
        "level": 7,
        "min_player_level": 6,
        "location_id": "dark_forest",

        "hp_min": 190,
        "hp_max": 225,

        "attack_min": 35,
        "attack_max": 41,

        "pdef_min": 6,
        "pdef_max": 8,
        "mdef_min": 15,
        "mdef_max": 19,

        "dex_min": 10,
        "dex_max": 13,
               "str_min": 7,
               "str_max": 12,
               "int_min": 12,
               "int_max": 17,
               "wis_min": 11,
               "wis_max": 16,
               "sta_min": 10,
               "sta_max": 15,

        "attack_type": "magical",

        "min_gold": 0.60,
        "max_gold": 1.05,

        "loot_chance": 0.55,
        "trash_items": [120]
    },

    # LEVEL 8
    {
        "name": "🪓 Гоблін-берсерк",
        "level": 8,
        "min_player_level": 7,
        "location_id": "dark_forest",

        "hp_min": 275,
        "hp_max": 320,

        "attack_min": 42,
        "attack_max": 50,

        "pdef_min": 10,
        "pdef_max": 13,
        "mdef_min": 5,
        "mdef_max": 7,

        "dex_min": 12,
        "dex_max": 15,
               "str_min": 14,
               "str_max": 19,
               "int_min": 9,
               "int_max": 14,
               "wis_min": 10,
               "wis_max": 15,
               "sta_min": 13,
               "sta_max": 18,

        "attack_type": "physical",

        "min_gold": 0.78,
        "max_gold": 1.30,

        "loot_chance": 0.56,
        "trash_items": [121]
    },
    {
        "name": "🔥 Гоблін-піроман",
        "level": 8,
        "min_player_level": 7,
        "location_id": "dark_forest",

        "hp_min": 235,
        "hp_max": 275,

        "attack_min": 43,
        "attack_max": 52,

        "pdef_min": 6,
        "pdef_max": 8,
        "mdef_min": 17,
        "mdef_max": 21,

        "dex_min": 9,
        "dex_max": 12,
               "str_min": 6,
               "str_max": 11,
               "int_min": 11,
               "int_max": 16,
               "wis_min": 10,
               "wis_max": 15,
               "sta_min": 9,
               "sta_max": 14,

        "attack_type": "magical",

        "min_gold": 0.82,
        "max_gold": 1.40,

        "loot_chance": 0.56,
        "trash_items": [122]
    },

    # LEVEL 9
    {
        "name": "🛡️ Гоблін-страж",
        "level": 9,
        "min_player_level": 8,
        "location_id": "dark_forest",

        "hp_min": 340,
        "hp_max": 395,

        "attack_min": 40,
        "attack_max": 47,

        "pdef_min": 18,
        "pdef_max": 23,
        "mdef_min": 8,
        "mdef_max": 11,

        "dex_min": 10,
        "dex_max": 13,
               "str_min": 12,
               "str_max": 17,
               "int_min": 7,
               "int_max": 12,
               "wis_min": 8,
               "wis_max": 13,
               "sta_min": 11,
               "sta_max": 16,

        "attack_type": "physical",

        "min_gold": 1.00,
        "max_gold": 1.65,

        "loot_chance": 0.58,
        "trash_items": [123]
    },
    {
        "name": "🔮 Рунічний культист",
        "level": 9,
        "min_player_level": 8,
        "location_id": "dark_forest",

        "hp_min": 300,
        "hp_max": 350,

        "attack_min": 47,
        "attack_max": 55,

        "pdef_min": 7,
        "pdef_max": 10,
        "mdef_min": 20,
        "mdef_max": 25,

        "dex_min": 10,
        "dex_max": 13,
               "str_min": 7,
               "str_max": 12,
               "int_min": 12,
               "int_max": 17,
               "wis_min": 11,
               "wis_max": 16,
               "sta_min": 10,
               "sta_max": 15,

        "attack_type": "magical",

        "min_gold": 1.05,
        "max_gold": 1.80,

        "loot_chance": 0.58,
        "trash_items": [124]
    },

    # LEVEL 10
    {
        "name": "🧟 Осквернений воїн",
        "level": 10,
        "min_player_level": 9,
        "location_id": "dark_forest",

        "hp_min": 395,
        "hp_max": 460,

        "attack_min": 52,
        "attack_max": 62,

        "pdef_min": 20,
        "pdef_max": 26,
        "mdef_min": 9,
        "mdef_max": 12,

        "dex_min": 9,
        "dex_max": 12,
               "str_min": 11,
               "str_max": 16,
               "int_min": 6,
               "int_max": 11,
               "wis_min": 7,
               "wis_max": 12,
               "sta_min": 10,
               "sta_max": 15,

        "attack_type": "physical",

        "min_gold": 1.30,
        "max_gold": 2.10,

        "loot_chance": 0.60,
        "trash_items": [125]
    },
    {
        "name": "🕯️ Осквернений віщун",
        "level": 10,
        "min_player_level": 9,
        "location_id": "dark_forest",

        "hp_min": 340,
        "hp_max": 400,

        "attack_min": 56,
        "attack_max": 66,

        "pdef_min": 8,
        "pdef_max": 11,
        "mdef_min": 23,
        "mdef_max": 29,

        "dex_min": 9,
        "dex_max": 12,
               "str_min": 6,
               "str_max": 11,
               "int_min": 11,
               "int_max": 16,
               "wis_min": 10,
               "wis_max": 15,
               "sta_min": 9,
               "sta_max": 14,

        "attack_type": "magical",

        "min_gold": 1.40,
        "max_gold": 2.25,

        "loot_chance": 0.60,
        "trash_items": [126]
    },
]


LOCATION_MOBS_BY_LOCATION = {
    "start_path": START_PATH_MOBS,
    "dark_forest": DARK_FOREST_MOBS,
}


ALL_MOBS = START_PATH_MOBS + DARK_FOREST_MOBS


# Backward compatibility
LOCATION_1_MOBS = ALL_MOBS


def get_mobs_for_location(location_id):
    return LOCATION_MOBS_BY_LOCATION.get(location_id, START_PATH_MOBS)


def get_all_mobs():
    return ALL_MOBS