"""Canonical Priest healing lifecycle shared by production and simulators."""
PRIEST_HEALING_SKILL_KEY = "priest_healing_blessing"
PRIEST_HEALING_EFFECT_KEY = "priest_healing_blessing_hot"
PRIEST_HEALING_DURATION_TURNS = 2
PRIEST_HEALING_COOLDOWN_TURNS = 4
PRIEST_HEALING_REAPPLICATION_POLICY = "replace"


def build_priest_healing_effect(heal_per_turn):
    """Return a fresh two-tick HoT payload; assignment by key refreshes it."""
    return {
        "name": "🌿 Благословення зцілення",
        "type": "hot",
        "turns": PRIEST_HEALING_DURATION_TURNS,
        "heal": max(0, int(heal_per_turn)),
        "modifiers": {},
    }
