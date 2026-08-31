"""Canonical central-drop configuration model for ROM Stage 11.

11.1.0 is shadow-only. No rule in this file is connected to production combat.
Existing reward_system and rune_system behavior remains authoritative until the
corresponding migration stage explicitly switches each group.
"""

CENTRAL_DROP_SCHEMA_VERSION = "11.1.0"
CENTRAL_DROP_PRODUCTION_ENABLED = True
CENTRAL_DROP_MIGRATED_RULES = ("rune", "refine_stone", "equipment", "trophy", "potion")
# ROM 11.2.0 CENTRAL RUNE MIGRATION

ENEMY_TYPES = ("normal", "elite", "boss")
DROP_MODES = ("independent", "exclusive")
BAG_POLICIES = (
    "stack_or_lose",
    "require_space",
    "currency_direct",
    "mail_if_full",
)
RESOLVER_TYPES = (
    "static_item",
    "rune",
    "equipment",
    "mob_trophy",
    "weighted_item_pool",
)

# Canonical classifier aliases. Priority is defined in systems/drop_system.py.
ENEMY_SIGNAL_ALIASES = {
    "boss": ("is_boss", "boss"),
    "elite": ("is_elite", "elite"),
}
ENEMY_TYPE_FIELDS = ("mob_type", "enemy_type")

# Shadow configuration preserving the currently active balance. Rules are
# intentionally not awarded by production code in 11.1.0.
DROP_RULES = (
    {
        "rule_id": "equipment",
        "group": "equipment",
        "mode": "independent",
        "enabled": True,
        "production_enabled": True,
        "resolver": "equipment",
        "enemy": {
            "normal": {"chance": 0.20},
            "elite": {"chance": 0.45},
            "boss": {"chance": 0.70},
        },
        "rarity_weights": {
            "normal": (("common", 0.80), ("uncommon", 0.20)),
            "elite": (("uncommon", 0.75), ("rare", 0.25)),
            "boss": (("rare", 0.85), ("epic", 0.15)),
        },
        "class_aware_chance": {
            "normal": 0.50,
            "elite": 0.70,
            "boss": 0.90,
        },
        "quantity": {"min": 1, "max": 1},
        "max_per_kill": 1,
        "bag_policy": "require_space",
        "message_policy": "legacy_equipment",
        "migration_stage": "11.4.0",
    },
    {
        "rule_id": "trophy",
        "group": "trophy",
        "mode": "independent",
        "enabled": True,
        "production_enabled": True,
        "resolver": "mob_trophy",
        "enemy": {
            "normal": {"chance": None, "source": "mob.loot_chance"},
            "elite": {"chance": None, "source": "min(1,mob.loot_chance+0.20)"},
            "boss": {"chance": None, "source": "mob.loot_chance+legacy_is_elite_bonus"},
        },
        "quantity": {"min": 1, "max": None, "source": "legacy trophy quantity"},
        "max_per_kill": 1,
        "bag_policy": "stack_or_lose",
        "message_policy": "legacy_trophy",
        "migration_stage": "11.5.0",
    },
    {
        "rule_id": "refine_stone",
        "group": "material",
        "mode": "independent",
        "enabled": True,
        "production_enabled": True,
        "resolver": "static_item",
        "item_id": 601,
        "enemy": {
            "normal": {"chance": 0.08},
            "elite": {"chance": 0.20},
            "boss": {"chance": 0.50},
        },
        "quantity": {"min": 1, "max": 1},
        "max_per_kill": 1,
        "bag_policy": "stack_or_lose",
        "message_policy": "legacy_refine_stone",
        "migration_stage": "11.3.0",
    },
    {
        "rule_id": "rune",
        "group": "rune",
        "mode": "independent",
        "enabled": True,
        "production_enabled": True,
        "resolver": "rune",
        "enemy": {
            "normal": {"chance": 0.05},
            "elite": {"chance": 0.12},
            "boss": {"chance": 0.35},
        },
        "level_weights": {
            "normal": ((1, 1.00),),
            "elite": ((1, 0.80), (2, 0.20)),
            "boss": ((1, 0.60), (2, 0.35), (3, 0.05)),
        },
        "stat_weights": (
            ("STR", 0.20), ("STA", 0.20), ("DEX", 0.20),
            ("INT", 0.20), ("WIS", 0.20),
        ),
        "quantity": {"min": 1, "max": 1},
        "max_per_kill": 1,
        "direct_max_level": 3,
        "bag_policy": "stack_or_lose",
        "message_policy": "legacy_rune",
        "migration_stage": "11.2.0",
    },
    {
        "rule_id": "potion",
        "group": "potion",
        "mode": "exclusive",
        "enabled": True,
        "production_enabled": True,
        "resolver": "weighted_item_pool",
        "enemy": {
            "normal": {"chance": 0.06},
            "elite": {"chance": 0.19},
            "boss": {"chance": 0.45},
        },
        "item_weights": {
            "normal": ((401, 4 / 6), (402, 2 / 6)),
            "elite": ((401, 10 / 19), (402, 6 / 19), (403, 2 / 19), (404, 1 / 19)),
            "boss": ((401, 20 / 45), (402, 12 / 45), (403, 8 / 45), (404, 5 / 45)),
        },
        "quantity": {"min": 1, "max": 1},
        "max_per_kill": 1,
        "bag_policy": "stack_or_lose",
        "message_policy": "standard_item",
        "migration_stage": "11.6.0",
    },
    {
        "rule_id": "simple_extractor",
        "group": "special_material",
        "mode": "independent",
        "enabled": False,
        "production_enabled": False,
        "resolver": "static_item",
        "item_id": 727,
        "enemy": {
            "normal": {"chance": 0.0},
            "elite": {"chance": 0.0},
            "boss": {"chance": 0.01, "candidate_only": True},
        },
        "quantity": {"min": 1, "max": 1},
        "max_per_kill": 1,
        "bag_policy": "stack_or_lose",
        "message_policy": "standard_item",
        "source_policy": "rune_master_gold_shop_primary",
        "migration_stage": "11.7.0",
    },
    {
        "rule_id": "perfect_extractor",
        "group": "premium_material",
        "mode": "independent",
        "enabled": False,
        "production_enabled": False,
        "resolver": "static_item",
        "item_id": 728,
        "enemy": {
            "normal": {"chance": 0.0},
            "elite": {"chance": 0.0},
            "boss": {"chance": 0.0},
        },
        "quantity": {"min": 1, "max": 1},
        "max_per_kill": 1,
        "bag_policy": "stack_or_lose",
        "message_policy": "standard_item",
        "source_policy": "future_crystal_shop",
        "migration_stage": "11.7.0",
    },
    {
        "rule_id": "success_rune",
        "group": "premium_material",
        "mode": "independent",
        "enabled": False,
        "production_enabled": False,
        "resolver": "static_item",
        "item_id": 602,
        "enemy": {
            "normal": {"chance": 0.0},
            "elite": {"chance": 0.0},
            "boss": {"chance": 0.0},
        },
        "quantity": {"min": 1, "max": 1},
        "max_per_kill": 1,
        "bag_policy": "stack_or_lose",
        "message_policy": "standard_item",
        "source_policy": "future_crystal_shop",
        "migration_stage": "11.7.0",
    },
)

DROP_RULES_BY_ID = {rule["rule_id"]: rule for rule in DROP_RULES}

# ROM 11.3.0 CENTRAL REFINE STONE MIGRATION

# ROM 11.4.0 CENTRAL EQUIPMENT MIGRATION

# ROM 11.5.0 CENTRAL TROPHY MIGRATION

# ROM 11.6.0 CENTRAL POTION DROP

# ==============================
# ROM 11.7.0 SPECIAL MATERIAL DROP POLICY
# ==============================
# These items are deliberately unavailable through enemy drops. Their rules
# remain in DROP_RULES so future sources can be configured without scattering
# item IDs through gameplay code.
SPECIAL_MATERIAL_MOB_DROP_POLICY_VERSION = "11.7.0"
SPECIAL_MATERIAL_MOB_DROP_DENYLIST = frozenset((501, 602, 727, 728, 502))
SPECIAL_MATERIAL_SOURCE_POLICY = {
    602: {
        "rule_id": "success_rune",
        "name": "Руна Успіху",
        "mob_drop": False,
        "primary_source": "future_crystal_shop",
        "bound_policy": "future_decision_required",
    },
    727: {
        "rule_id": "simple_extractor",
        "name": "Простий Екстрактор",
        "mob_drop": False,
        "primary_source": "rune_master_gold_shop",
        "boss_candidate_chance": 0.01,
        "candidate_enabled": False,
        "bound_policy": "tradeable_current_item_policy",
    },
    728: {
        "rule_id": "perfect_extractor",
        "name": "Досконалий Екстрактор",
        "mob_drop": False,
        "primary_source": "future_crystal_shop",
        "bound_policy": "future_premium_bound_candidate",
    },
}

# ==============================
# ROM 11.9.0 FINAL VICTORY INTEGRATION
# ==============================
CENTRAL_DROP_VICTORY_INTEGRATION_ENABLED = True
CENTRAL_DROP_VICTORY_INTEGRATION_VERSION = "11.9.0"
CENTRAL_DROP_VICTORY_RULE_ORDER = (
    "trophy",
    "equipment",
    "refine_stone",
    "rune",
    "potion",
)

