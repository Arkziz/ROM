#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical pure policy for class-aware generated equipment primary stats.

This module contains configuration and validation only. It performs no SQL,
creates no items, and does not own equipment generation. Stage 18.17.2 will
connect this policy to the production generator.
"""
from __future__ import annotations

from types import MappingProxyType

from data.stat_system_config import SUPPORTED_CLASSES

PRIMARY_STATS = ("str", "dex", "int", "wis", "sta")
PHYSICAL_CLASSES = frozenset({"warrior", "knight", "scout", "rogue"})
MAGICAL_CLASSES = frozenset({"mage", "priest"})
SUPPORTED_EQUIPMENT_KINDS = frozenset({"weapon", "armor", "off_hand", "jewelry"})

# Approved Stage 18.17 class identity. Weights are selection weights, not direct
# PATK/MATK coefficients and not additive stat budgets.
CLASS_STAT_WEIGHTS = MappingProxyType({
    "warrior": (("str", 60), ("sta", 30), ("dex", 10)),
    "knight":  (("sta", 50), ("str", 45), ("dex", 5)),
    "scout":   (("str", 45), ("dex", 45), ("sta", 10)),
    "rogue":   (("dex", 60), ("str", 30), ("sta", 10)),
    "mage":    (("int", 65), ("wis", 25), ("sta", 10)),
    "priest":  (("int", 50), ("wis", 40), ("sta", 10)),
})

# Main-hand keeps weapon identity while allowing every approved class scaling
# stat to appear. DEX remains rare on Warrior/Knight swords.
MAIN_HAND_STAT_WEIGHTS = MappingProxyType({
    "warrior": (("str", 65), ("sta", 25), ("dex", 10)),
    "knight":  (("str", 65), ("sta", 30), ("dex", 5)),
    "scout":   (("str", 45), ("dex", 45), ("sta", 10)),
    "rogue":   (("dex", 60), ("str", 30), ("sta", 10)),
    "mage":    (("int", 70), ("wis", 20), ("sta", 10)),
    "priest":  (("int", 55), ("wis", 35), ("sta", 10)),
})

# Explicit approved off-hand identities. Knight shield is STA + STR only.
OFF_HAND_STAT_WEIGHTS = MappingProxyType({
    ("warrior", "warrior_shield"): (("str", 65), ("sta", 35)),
    ("knight", "shield"): (("sta", 65), ("str", 35)),
    ("rogue", "dagger"): (("dex", 65), ("str", 35)),
    ("mage", "talisman"): (("int", 60), ("wis", 40)),
    ("priest", "talisman"): (("wis", 55), ("int", 45)),
})

# Jewelry is always target-class-aware. It never uses a universal all-stat pool.
JEWELRY_STAT_WEIGHTS = MappingProxyType({
    "warrior": (("str", 55), ("sta", 30), ("dex", 15)),
    "knight":  (("sta", 45), ("str", 45), ("dex", 10)),
    "scout":   (("str", 45), ("dex", 45), ("sta", 10)),
    "rogue":   (("dex", 60), ("str", 30), ("sta", 10)),
    "mage":    (("int", 60), ("wis", 30), ("sta", 10)),
    "priest":  (("int", 45), ("wis", 45), ("sta", 10)),
})

# Armor primary-stat selection is class-specific. PDEF/MDEF distribution remains
# owned by the existing cloth/leather/chain/plate defense profiles.
ARMOR_STAT_WEIGHTS = CLASS_STAT_WEIGHTS

CLASS_ARMOR_TYPES = MappingProxyType({
    "mage": "cloth",
    "priest": "cloth",
    "scout": "leather",
    "rogue": "leather",
    "warrior": "chain",
    "knight": "plate",
})

CLASS_MAIN_HAND_SUBTYPES = MappingProxyType({
    "mage": ("wand_1h", "staff_2h"),
    "priest": ("wand_1h", "staff_2h"),
    "scout": ("bow_2h", "crossbow_2h"),
    "rogue": ("dagger_1h",),
    "warrior": ("sword_1h", "sword_2h"),
    "knight": ("sword_1h",),
})

CLASS_OFF_HAND_SUBTYPES = MappingProxyType({
    "mage": ("talisman",),
    "priest": ("talisman",),
    "scout": (),
    "rogue": ("dagger",),
    "warrior": ("warrior_shield",),
    "knight": ("shield",),
})


def normalize_equipment_class(class_key: object) -> str:
    key = str(class_key or "").strip().lower()
    if key not in SUPPORTED_CLASSES:
        raise ValueError(f"Unsupported equipment target class: {class_key!r}")
    return key


def _validate_weight_profile(profile: object, label: str) -> tuple[tuple[str, int], ...]:
    if not isinstance(profile, tuple) or not profile:
        raise ValueError(f"{label}: profile must be a non-empty tuple")
    seen = set()
    total = 0
    normalized = []
    for entry in profile:
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise ValueError(f"{label}: invalid weighted entry {entry!r}")
        stat_key, weight = entry
        if stat_key not in PRIMARY_STATS or stat_key in seen:
            raise ValueError(f"{label}: invalid or duplicate stat {stat_key!r}")
        if isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0:
            raise ValueError(f"{label}: invalid weight for {stat_key}: {weight!r}")
        seen.add(stat_key)
        total += weight
        normalized.append((stat_key, weight))
    if total != 100:
        raise ValueError(f"{label}: weights total {total}, expected 100")
    return tuple(normalized)


def get_equipment_stat_weights(
    class_key: object,
    equipment_kind: str,
    *,
    item_subtype: str = "",
) -> tuple[tuple[str, int], ...]:
    """Return immutable weighted primary-stat choices for one target class."""
    cls = normalize_equipment_class(class_key)
    kind = str(equipment_kind or "").strip().lower()
    subtype = str(item_subtype or "").strip().lower()
    if kind not in SUPPORTED_EQUIPMENT_KINDS:
        raise ValueError(f"Unsupported equipment kind: {equipment_kind!r}")
    if kind == "weapon":
        if subtype and subtype not in CLASS_MAIN_HAND_SUBTYPES[cls]:
            raise ValueError(f"Main-hand subtype {subtype!r} is not allowed for {cls}")
        profile = MAIN_HAND_STAT_WEIGHTS[cls]
    elif kind == "armor":
        profile = ARMOR_STAT_WEIGHTS[cls]
    elif kind == "jewelry":
        profile = JEWELRY_STAT_WEIGHTS[cls]
    else:
        if subtype not in CLASS_OFF_HAND_SUBTYPES[cls]:
            raise ValueError(f"Off-hand subtype {subtype!r} is not allowed for {cls}")
        profile = OFF_HAND_STAT_WEIGHTS[(cls, subtype)]
    return _validate_weight_profile(profile, f"{cls}:{kind}:{subtype or '*'}")


def get_allowed_equipment_stats(class_key: object, equipment_kind: str, *, item_subtype: str = "") -> tuple[str, ...]:
    return tuple(stat for stat, _weight in get_equipment_stat_weights(class_key, equipment_kind, item_subtype=item_subtype))


def validate_equipment_stat_policy() -> tuple[str, ...]:
    problems = []
    expected_classes = set(SUPPORTED_CLASSES)
    for label, mapping in (
        ("CLASS_STAT_WEIGHTS", CLASS_STAT_WEIGHTS),
        ("MAIN_HAND_STAT_WEIGHTS", MAIN_HAND_STAT_WEIGHTS),
        ("JEWELRY_STAT_WEIGHTS", JEWELRY_STAT_WEIGHTS),
        ("CLASS_ARMOR_TYPES", CLASS_ARMOR_TYPES),
        ("CLASS_MAIN_HAND_SUBTYPES", CLASS_MAIN_HAND_SUBTYPES),
        ("CLASS_OFF_HAND_SUBTYPES", CLASS_OFF_HAND_SUBTYPES),
    ):
        if set(mapping) != expected_classes:
            problems.append(f"{label}: class set mismatch")
    for cls in SUPPORTED_CLASSES:
        for kind in ("weapon", "armor", "jewelry"):
            try:
                profile = get_equipment_stat_weights(cls, kind)
                _validate_weight_profile(profile, f"{cls}:{kind}")
            except Exception as error:
                problems.append(str(error))
        for subtype in CLASS_OFF_HAND_SUBTYPES[cls]:
            try:
                get_equipment_stat_weights(cls, "off_hand", item_subtype=subtype)
            except Exception as error:
                problems.append(str(error))
    if get_allowed_equipment_stats("knight", "off_hand", item_subtype="shield") != ("sta", "str"):
        problems.append("Knight shield must allow exactly STA and STR")
    return tuple(problems)


_POLICY_PROBLEMS = validate_equipment_stat_policy()
if _POLICY_PROBLEMS:
    raise ValueError("Invalid equipment stat policy: " + "; ".join(_POLICY_PROBLEMS))


__all__ = [
    "PRIMARY_STATS", "PHYSICAL_CLASSES", "MAGICAL_CLASSES",
    "CLASS_STAT_WEIGHTS", "MAIN_HAND_STAT_WEIGHTS", "OFF_HAND_STAT_WEIGHTS",
    "JEWELRY_STAT_WEIGHTS", "ARMOR_STAT_WEIGHTS", "CLASS_ARMOR_TYPES",
    "CLASS_MAIN_HAND_SUBTYPES", "CLASS_OFF_HAND_SUBTYPES",
    "normalize_equipment_class", "get_equipment_stat_weights",
    "get_allowed_equipment_stats", "validate_equipment_stat_policy",
]
