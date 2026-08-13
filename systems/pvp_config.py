from __future__ import annotations

PVP_DAMAGE_MULTIPLIER = 1.1375
PVP_HEALING_MULTIPLIER = 0.8398
PVP_SHIELD_MULTIPLIER = 0.4566
PVP_DEBUFF_MULTIPLIER = 0.9044

# Stage 14.6.5 transparent PvP class profiles. These values never mutate the
# visible character sheet, HP, MP, equipment or PvE calculations.
PVP_CLASS_ATTACK_MULTIPLIER = {
    "warrior": 1.0000, "knight": 1.0000, "scout": 1.9824,
    "rogue": 1.1558, "mage": 1.1376, "priest": 1.0000,
}
PVP_CLASS_DEFENSE_MULTIPLIER = {
    "warrior": {"physical": 0.9291, "magical": 1.0000},
    "knight": {"physical": 0.5518, "magical": 1.0000},
    "scout": {"physical": 1.0000, "magical": 1.0000},
    "rogue": {"physical": 1.0000, "magical": 1.0000},
    "mage": {"physical": 1.0000, "magical": 1.0000},
    "priest": {"physical": 1.0000, "magical": 0.8172},
}
PVP_CLASS_SKILL_DAMAGE_MULTIPLIER = {
    "warrior": 0.9462, "knight": 0.7104, "scout": 0.9654,
    "rogue": 0.9921, "mage": 0.9277, "priest": 1.0500,
}
PVP_CLASS_PENETRATION = {
    "scout": {"physical": 0.2641, "magical": 0.0000},
    "rogue": {"physical": 0.4223, "magical": 0.0000},
    "mage": {"physical": 0.0000, "magical": 0.2707},
}
PVP_HEAVY_ARMOR_CLASSES = frozenset({"warrior", "knight"})
PVP_ROGUE_HEAVY_ARMOR_BONUS_PENETRATION = 0.3166
PVP_DAMAGE_RECEIVED_BY_TYPE = {
    "warrior": {"physical": 1.0000, "magical": 0.8517},
    "priest": {"physical": 0.6884, "magical": 1.0000},
}
PVP_CLASS_HOT_POWER_MULTIPLIER = {"priest": 0.7474}

PVP_ACTION_TIMEOUT_SECONDS = 20
PVP_MAX_ROUNDS = 0  # Disabled: duel ends by combat result or AFK rules only
PVP_CONSECUTIVE_AFK_LIMIT = 5
PVP_COMBAT_ENERGY_MAX = 100
# PvE resource parity for Warrior/Knight duel-local Rage.
PVP_RAGE_GAIN_ON_ATTACK = 15
PVP_RAGE_GAIN_ON_DAMAGE_TAKEN = 10
PVP_DOT_CAN_CRIT = False
PVP_POTIONS_ALLOWED = False
PVP_PRODUCTION_STATE_MUTATION = False
PVP_ENTRYPOINT = "map_same_location_online_players"
