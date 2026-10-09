"""Canonical Priest healing lifecycle shared by production and simulators."""

PRIEST_HEALING_SKILL_KEY = "priest_healing_blessing"
PRIEST_HEALING_EFFECT_KEY = "priest_healing_blessing_hot"
PRIEST_HEALING_IMMEDIATE_HEALS = 1
PRIEST_HEALING_DURATION_TURNS = 2
PRIEST_HEALING_TOTAL_HEALS = (
    PRIEST_HEALING_IMMEDIATE_HEALS + PRIEST_HEALING_DURATION_TURNS
)
PRIEST_HEALING_COOLDOWN_TURNS = 4
PRIEST_HEALING_REAPPLICATION_POLICY = "replace"


def calculate_priest_heal_amount(max_hp):
    """Return the amount used by the activation heal and both delayed ticks."""
    return max(5, int(round(max(1, int(max_hp)) * 0.10)))


def build_priest_healing_effect(heal_per_turn):
    """Return the two delayed ticks remaining after the activation heal."""
    return {
        "name": "🌿 Благословення зцілення",
        "type": "hot",
        "turns": PRIEST_HEALING_DURATION_TURNS,
        "heal": max(0, int(heal_per_turn)),
        "modifiers": {},
    }
