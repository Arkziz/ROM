"""Pure shadow stat calculations for ROM Stage 18.15.6.

This module has no database imports and is not connected to production wrappers.
All inputs must already be effective exact-once values assembled by the caller.
"""
from __future__ import annotations

PHYSICAL_CLASSES = frozenset({"warrior", "knight", "rogue", "scout"})
MAGICAL_CLASSES = frozenset({"mage", "priest"})
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


def calculate_physical_attack(character_class, *, strength=0, dexterity=0) -> int:
    """Candidate F2. No direct level, STA or WIS contribution."""
    class_key = str(character_class or "").strip().casefold()
    strength = _number(strength)
    dexterity = _number(dexterity)
    if class_key in {"warrior", "knight"}:
        raw = strength
    elif class_key in {"rogue", "scout"}:
        raw = strength * 0.55 + dexterity * 0.55
    elif class_key in MAGICAL_CLASSES:
        raw = strength * 0.20
    else:
        return 0
    return max(1, int(raw))


def calculate_magical_attack(character_class, *, intelligence=0) -> int:
    """Offensive MATK is INT-driven; WIS is intentionally not an input."""
    class_key = str(character_class or "").strip().casefold()
    intelligence = _number(intelligence)
    if class_key in MAGICAL_CLASSES:
        raw = intelligence
    elif class_key in PHYSICAL_CLASSES:
        raw = intelligence * 0.20
    else:
        return 0
    return max(1, int(raw))


def calculate_physical_defense(*, equipment_pdef=0, stamina=0) -> int:
    """Stage 18.14.2: active item PDEF plus total STA at coefficient 0.35."""
    from data.defense_policy import calculate_total_defense

    return int(calculate_total_defense(equipment_pdef, stamina))



def calculate_magical_defense(*, equipment_mdef=0, wisdom=0) -> int:
    """Stage 18.14.2: active item MDEF plus total WIS at coefficient 0.35."""
    from data.defense_policy import calculate_total_defense

    return int(calculate_total_defense(equipment_mdef, wisdom))



def calculate_max_mp(character_class, *, level=0, intelligence=0, wisdom=0) -> int:
    """WIS-focused resource formula: 100 + level*20 + INT*2 + WIS*3."""
    class_key = str(character_class or "").strip().casefold()
    if class_key not in MAGICAL_CLASSES:
        return 0
    raw = 100 + _number(level) * 20 + _number(intelligence) * 2 + _number(wisdom) * 3
    return _whole_non_negative(raw)


__all__ = [
    "calculate_max_hp",
    "calculate_physical_attack",
    "calculate_magical_attack",
    "calculate_physical_defense",
    "calculate_magical_defense",
    "calculate_max_mp",
]
