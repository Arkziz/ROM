"""Pure shadow stat calculations for ROM Stage 18.15.6.

This module has no database imports and is not connected to production wrappers.
All inputs must already be effective exact-once values assembled by the caller.
"""
from __future__ import annotations

from data.stat_system_config import (
    MAGICAL_ATTACK_SCALING,
    MAX_MP_SCALING,
    MANA_CLASSES,
    PHYSICAL_ATTACK_SCALING,
    PRIMARY_STAT_KEYS,
)

PHYSICAL_CLASSES = frozenset({"warrior", "knight", "rogue", "scout"})
MAGICAL_CLASSES = frozenset({"mage", "priest"})


BASIC_ATTACK_TYPE_BY_CLASS = {
    "warrior": "physical",
    "knight": "physical",
    "scout": "physical",
    "rogue": "physical",
    "mage": "magical",
    "priest": "magical",
}


def resolve_basic_attack_type(character_class):
    """Return the zero-resource basic-attack damage type for a player class.

    The resolver is intentionally class-owned rather than weapon-owned: weapon
    ranges remain part of damage calculation, while the class selects PATK/PDEF
    or MATK/MDEF routing. Unknown classes fail closed instead of silently using
    the historical physical fallback.
    """
    class_key = str(character_class or "").strip().lower()
    try:
        return BASIC_ATTACK_TYPE_BY_CLASS[class_key]
    except KeyError as error:
        raise ValueError(f"Unsupported character class for basic attack: {character_class!r}") from error
SUPPORTED_CLASSES = PHYSICAL_CLASSES | MAGICAL_CLASSES


def _number(value) -> float:
    try:
        result = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    return result


def _whole_non_negative(value) -> int:
    return max(0, int(_number(value)))


def calculate_max_hp(*, base_hp=0, stamina_hp=0, equipment_hp=0, refinement_hp=0) -> int:
    """Combine already-calculated HP components without redefining HP scaling."""
    return _whole_non_negative(
        _number(base_hp) + _number(stamina_hp) + _number(equipment_hp) + _number(refinement_hp)
    )


def _calculate_weighted_attack(character_class, matrix, *, strength=0, dexterity=0, intelligence=0, wisdom=0, stamina=0) -> int:
    class_key = str(character_class or "").strip().casefold()
    coefficients = matrix.get(class_key)
    if coefficients is None:
        return 0
    stats = {
        "str": _number(strength),
        "dex": _number(dexterity),
        "int": _number(intelligence),
        "wis": _number(wisdom),
        "sta": _number(stamina),
    }
    raw = sum(stats[key] * coefficients[key] for key in PRIMARY_STAT_KEYS)
    return max(1, int(raw))


def calculate_physical_attack(character_class, *, strength=0, dexterity=0, intelligence=0, wisdom=0, stamina=0) -> int:
    """Return configurable class-aware physical attack."""
    return _calculate_weighted_attack(
        character_class,
        PHYSICAL_ATTACK_SCALING,
        strength=strength,
        dexterity=dexterity,
        intelligence=intelligence,
        wisdom=wisdom,
        stamina=stamina,
    )

def calculate_magical_attack(character_class, *, strength=0, dexterity=0, intelligence=0, wisdom=0, stamina=0) -> int:
    """Return configurable class-aware magical attack."""
    return _calculate_weighted_attack(
        character_class,
        MAGICAL_ATTACK_SCALING,
        strength=strength,
        dexterity=dexterity,
        intelligence=intelligence,
        wisdom=wisdom,
        stamina=stamina,
    )

def calculate_physical_defense(*, equipment_pdef=0, stamina=0) -> int:
    """Stage 18.14.2: active item PDEF plus total STA at coefficient 0.35."""
    from data.defense_policy import calculate_total_defense

    return int(calculate_total_defense(equipment_pdef, stamina))



def calculate_magical_defense(*, equipment_mdef=0, wisdom=0) -> int:
    """Stage 18.14.2: active item MDEF plus total WIS at coefficient 0.35."""
    from data.defense_policy import calculate_total_defense

    return int(calculate_total_defense(equipment_mdef, wisdom))



def calculate_max_mp(character_class, *, level=0, intelligence=0, wisdom=0) -> int:
    """Return configurable maximum mana for mana classes."""
    class_key = str(character_class or "").strip().casefold()
    if class_key not in MANA_CLASSES:
        return 0
    raw = (
        MAX_MP_SCALING["base"]
        + _number(level) * MAX_MP_SCALING["level"]
        + _number(intelligence) * MAX_MP_SCALING["int"]
        + _number(wisdom) * MAX_MP_SCALING["wis"]
    )
    return max(0, int(raw))

__all__ = [
    "calculate_max_hp",
    "calculate_physical_attack",
    "calculate_magical_attack",
    "calculate_physical_defense",
    "calculate_magical_defense",
    "calculate_max_mp",
]
