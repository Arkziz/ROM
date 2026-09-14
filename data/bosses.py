"""Canonical location-boss definitions for ROM Stage 15.

This module contains data only. It does not select encounters, mutate combat,
write to SQLite, award rewards, or call Telegram APIs.
"""
from __future__ import annotations

BOSS_SCHEMA_VERSION = "15.1.0"
BOSS_CORE_STAT_MULTIPLIER = 2.0
BOSS_HP_MULTIPLIER = BOSS_CORE_STAT_MULTIPLIER
BOSS_ATTACK_MULTIPLIER = BOSS_CORE_STAT_MULTIPLIER
BOSS_ENRAGE_HP_PERCENT = 0.25

# Stage 15.2.0 safety gate. Encounter architecture is installed now, but live
# boss encounters remain disabled until boss combat actions/enrage are wired.
BOSS_ENCOUNTERS_ENABLED = True
BOSS_ENCOUNTER_CHANCE_PERCENT = 1.0

BOSS_DEFINITIONS = {
    "pack_leader": {
        "boss_key": "pack_leader",
        "name": "👑🐺 Ватажок Зграї",
        "location_id": "start_path",
        "level_min": 1,
        "level_max": 5,
        "attack_type": "physical",
        "reference_level": 5,
        "reference_stats": {
            "hp_min": 550, "hp_max": 650,
            "attack_min": 60, "attack_max": 75,
            "pdef_min": 12, "pdef_max": 16,
            "mdef_min": 8, "mdef_max": 12,
            "dex_min": 15, "dex_max": 18,
        },
        "ai_before_enrage": (
            ("ferocious_bite", 0.55),
            ("fang_rend", 0.25),
            ("spectral_roar", 0.20),
        ),
        "ai_after_enrage": (
            ("ferocious_bite", 0.55),
            ("fang_rend", 0.25),
            ("spectral_roar", 0.20),
        ),
        "skills": {
            "ferocious_bite": {
                "name": "🐾 Лютий Укус", "damage_multiplier": 1.0,
                "attack_type": "physical",
            },
            "fang_rend": {
                "name": "🩸 Розрив Іклами", "damage_multiplier": 1.4,
                "attack_type": "physical", "bleed_turns": 2,
                "bleed_damage_fraction": 0.20, "bleed_min_damage": 1,
                "bleed_refresh_policy": "replace",
            },
            "spectral_roar": {
                "name": "👻 Примарний Рик", "damage_multiplier": 1.3,
                "attack_type": "magical",
            },
            "enraged_rend": {
                "name": "🩸 Скажений Розрив", "damage_multiplier": 1.7,
                "attack_type": "physical", "once_per_fight": True,
            },
        },
        "enrage": {
            "hp_threshold_fraction": 0.25,
            "permanent_attack_buff_percent": 20,
            "special_skill_key": "enraged_rend",
            "special_replaces_regular_action": True,
        },
    },
    "goblin_king": {
        "boss_key": "goblin_king",
        "name": "👑👺 Король Гоблінів",
        "location_id": "dark_forest",
        "level_min": 6,
        "level_max": 10,
        "attack_type": "physical",
        "reference_level": 10,
        "reference_stats": {
            "hp_min": 1650, "hp_max": 1930,
            "attack_min": 145, "attack_max": 175,
            "pdef_min": 30, "pdef_max": 36,
            "mdef_min": 16, "mdef_max": 22,
            "dex_min": 16, "dex_max": 20,
        },
        "ai_before_enrage": (
            ("chieftain_axe", 0.50),
            ("skull_splitter", 0.25),
            ("battle_cry", 0.15),
            ("defense_command", 0.10),
        ),
        "ai_after_enrage": (
            ("chieftain_axe", 0.40),
            ("skull_splitter", 0.30),
            ("battle_cry", 0.15),
            ("defense_command", 0.15),
        ),
        "skills": {
            "chieftain_axe": {
                "name": "⚔️ Сокира Вождя", "damage_multiplier": 1.0,
                "attack_type": "physical",
            },
            "skull_splitter": {
                "name": "🪓 Розкол Черепа", "damage_multiplier": 1.3,
                "attack_type": "physical",
            },
            "battle_cry": {
                "name": "📣 Бойовий Клич", "no_damage": True,
                "attack_buff_percent": 15, "duration_turns": 3,
                "refresh_policy": "replace",
            },
            "defense_command": {
                "name": "🛡️ Команда до Оборони", "no_damage": True,
                "pdef_buff_percent": 30, "mdef_buff_percent": 30,
                "duration_turns": 2, "refresh_policy": "replace",
            },
            "tyrant_strike": {
                "name": "☠️ Удар Тирана", "damage_multiplier": 1.6,
                "attack_type": "physical", "once_per_fight": True,
            },
        },
        "enrage": {
            "hp_threshold_fraction": 0.25,
            "permanent_attack_buff_percent": 20,
            "special_skill_key": "tyrant_strike",
            "special_replaces_regular_action": True,
        },
    },
}

BOSS_KEY_BY_LOCATION = {
    definition["location_id"]: boss_key
    for boss_key, definition in BOSS_DEFINITIONS.items()
}


def get_boss_definition(boss_key):
    return BOSS_DEFINITIONS.get(str(boss_key or ""))


def get_location_boss_definition(location_id):
    boss_key = BOSS_KEY_BY_LOCATION.get(str(location_id or ""))
    return get_boss_definition(boss_key)
