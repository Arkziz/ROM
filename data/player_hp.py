"""Canonical player HP policy for ROM Stage 18.12."""

STARTING_HP_BASE = 60
HP_PER_LEVEL = 20
HP_PER_STAMINA = 5
DEFAULT_STARTING_LEVEL = 1
DEFAULT_STARTING_STAMINA = 10


def calculate_base_max_hp(level, total_stamina):
    """Return base max HP before percentage modifiers such as armor refine."""
    safe_level = max(1, int(level or DEFAULT_STARTING_LEVEL))
    safe_stamina = max(0, int(total_stamina or 0))
    return max(1, STARTING_HP_BASE + safe_level * HP_PER_LEVEL + safe_stamina * HP_PER_STAMINA)


def get_starting_max_hp():
    return calculate_base_max_hp(DEFAULT_STARTING_LEVEL, DEFAULT_STARTING_STAMINA)
