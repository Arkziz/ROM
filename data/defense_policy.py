"""Canonical defense policy approved in ROM Stage 18.14.2."""

DEFENSE_STAT_COEFFICIENT = 0.35
DAMAGE_DEFENSE_COEFFICIENT = 0.5
MINIMUM_DAMAGE = 1


def calculate_stat_defense(primary_stat):
    """Return the raw defense layer produced by STA or WIS."""
    return max(0.0, float(primary_stat or 0)) * DEFENSE_STAT_COEFFICIENT


def calculate_total_defense(item_defense, primary_stat):
    """Combine active item defense with the symmetric primary-stat layer."""
    return max(0.0, float(item_defense or 0)) + calculate_stat_defense(primary_stat)


def calculate_damage_after_defense(attack, defense):
    """Document the unchanged Stage 18 damage contract."""
    return max(float(MINIMUM_DAMAGE), float(attack) - max(0.0, float(defense)) * DAMAGE_DEFENSE_COEFFICIENT)
