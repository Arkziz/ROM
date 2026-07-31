"""Canonical Rune System data for ROM 10.x."""
from __future__ import annotations

RUNE_STATS = ("STR", "STA", "DEX", "INT", "WIS")
RUNE_LEVELS = (1, 2, 3, 4, 5)
RUNE_LEVEL_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
RUNE_STAT_NAMES = {
    "STR": "Сили",
    "STA": "Витривалості",
    "DEX": "Спритності",
    "INT": "Інтелекту",
    "WIS": "Мудрості",
}
RUNE_SLOT_LIMITS = {
    "main_hand": 2,
    "off_hand": 1,
    "helmet": 1,
    "shoulders": 1,
    "chest": 3,
    "gloves": 1,
    "legs": 2,
    "boots": 1,
    "necklace": 1,
    "ring": 1,
}
RUNE_ITEM_ID_START = 501
RUNE_ITEM_ID_END = 525
FIRIUS_TOKEN_ITEM_ID = 526
RUNE_EXTRACTOR_ITEM_ID = 527
PERFECT_RUNE_EXTRACTOR_ITEM_ID = 528
FIRIUS_TOKENS_PER_DAILY_REWARD = 10
RUNE_FUSION_SOURCE_QUANTITY = 3
RUNE_FUSION_TOKEN_QUANTITY = 1
RUNE_MAX_STACK = 999
FIRIUS_TOKEN_MAX_STACK = 999
EXTRACTOR_MAX_STACK = 999

RUNE_ITEM_DEFINITIONS = {}
RUNE_ITEM_ID_BY_KEY = {}
for stat_index, stat in enumerate(RUNE_STATS):
    for level in RUNE_LEVELS:
        item_id = RUNE_ITEM_ID_START + stat_index * len(RUNE_LEVELS) + level - 1
        definition = {
            "id": item_id,
            "stat": stat,
            "level": level,
            "bonus": level,
            "name": f"💠 Руна {RUNE_STAT_NAMES[stat]} {RUNE_LEVEL_ROMAN[level]}",
            "type": f"rune_{stat.lower()}_{level}",
            "rarity": "common",
            "category": "rune",
            "max_stack": RUNE_MAX_STACK,
            "sell_price": 0.0,
        }
        RUNE_ITEM_DEFINITIONS[item_id] = definition
        RUNE_ITEM_ID_BY_KEY[(stat, level)] = item_id

RUNE_UTILITY_ITEM_DEFINITIONS = {
    FIRIUS_TOKEN_ITEM_ID: {
        "id": FIRIUS_TOKEN_ITEM_ID,
        "name": "🪙 Жетон Фіріуса",
        "type": "firius_token",
        "rarity": "common",
        "category": "material",
        "max_stack": FIRIUS_TOKEN_MAX_STACK,
        "sell_price": 0.0,
    },
    RUNE_EXTRACTOR_ITEM_ID: {
        "id": RUNE_EXTRACTOR_ITEM_ID,
        "name": "🧰 Екстрактор рун",
        "type": "rune_extractor",
        "rarity": "common",
        "category": "material",
        "max_stack": EXTRACTOR_MAX_STACK,
        "sell_price": 0.0,
    },
    PERFECT_RUNE_EXTRACTOR_ITEM_ID: {
        "id": PERFECT_RUNE_EXTRACTOR_ITEM_ID,
        "name": "✨ Досконалий Екстрактор рун",
        "type": "rune_extractor_perfect",
        "rarity": "epic",
        "category": "material",
        "max_stack": EXTRACTOR_MAX_STACK,
        "sell_price": 0.0,
    },
}
ALL_RUNE_SYSTEM_ITEM_DEFINITIONS = {
    **RUNE_ITEM_DEFINITIONS,
    **RUNE_UTILITY_ITEM_DEFINITIONS,
}


def get_rune_definition(item_id):
    try:
        return RUNE_ITEM_DEFINITIONS.get(int(item_id))
    except Exception:
        return None


def get_rune_item_id(stat, level):
    try:
        return RUNE_ITEM_ID_BY_KEY.get((str(stat).strip().upper(), int(level)))
    except Exception:
        return None


def is_rune_item_id(item_id):
    return get_rune_definition(item_id) is not None


def get_rune_slot_limit(slot_key):
    return int(RUNE_SLOT_LIMITS.get(str(slot_key or ""), 0))

# ==============================
# ROM 10.13.0 RUNE MASTER SHOP
# ==============================
SIMPLE_RUNE_EXTRACTOR_GOLD_PRICE = 10.0
SIMPLE_RUNE_EXTRACTOR_SHOP_ENABLED = True
PERFECT_RUNE_EXTRACTOR_CRYSTAL_SHOP_ENABLED = False

