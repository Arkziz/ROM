"""Pure candidate formulas for ROM Stat System 2.0.

This module has no database or systems dependencies. Candidate coefficients are
not connected to production gameplay until later shadow acceptance and switch stages.
"""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Mapping

SUPPORTED_CLASSES = ("warrior", "knight", "rogue", "scout", "mage", "priest")
SUPPORTED_STATS = ("str", "dex", "int", "wis")
ROUNDING_POLICY = "round-half-away-from-zero"
UNKNOWN_CLASS_POLICY = "identity"

# Candidate A follows the technical-plan ordering.
_CANDIDATE_A = {
    "warrior": {"patk": {"str": 1.5}, "matk": {"int": 1.0}},
    "knight": {"patk": {"str": 2.0}, "matk": {"int": 1.0}},
    "rogue": {"patk": {"str": 0.5, "dex": 1.5}, "matk": {"int": 1.0}},
    "scout": {"patk": {"str": 0.5, "dex": 1.5}, "matk": {"int": 1.0}},
    "mage": {"patk": {"str": 1.0}, "matk": {"int": 2.0}},
    "priest": {"patk": {"str": 1.0}, "matk": {"int": 1.2, "wis": 0.8}},
}

# Candidate B follows the conceptual-plan warrior/knight ordering.
_CANDIDATE_B = {
    "warrior": {"patk": {"str": 2.0}, "matk": {"int": 1.0}},
    "knight": {"patk": {"str": 1.5}, "matk": {"int": 1.0}},
    "rogue": {"patk": {"str": 0.5, "dex": 1.5}, "matk": {"int": 1.0}},
    "scout": {"patk": {"str": 0.75, "dex": 1.25}, "matk": {"int": 1.0}},
    "mage": {"patk": {"str": 1.0}, "matk": {"int": 2.0}},
    "priest": {"patk": {"str": 1.0}, "matk": {"int": 1.2, "wis": 0.8}},
}

# Candidate C is normalized for the Stage 18.15.2 shadow comparison.
_CANDIDATE_C = {
    "warrior": {"patk": {"str": 2.0}, "matk": {"int": 1.0}},
    "knight": {"patk": {"str": 1.5}, "matk": {"int": 1.0}},
    "rogue": {"patk": {"str": 0.4, "dex": 1.6}, "matk": {"int": 1.0}},
    "scout": {"patk": {"str": 0.7, "dex": 1.3}, "matk": {"int": 1.0}},
    "mage": {"patk": {"str": 1.0}, "matk": {"int": 2.0}},
    "priest": {"patk": {"str": 1.0}, "matk": {"int": 1.1, "wis": 0.9}},
}

CLASS_SCALING_CANDIDATES = MappingProxyType({
    "current_identity": MappingProxyType({
        class_key: MappingProxyType({
            "patk": MappingProxyType({"str": 1.0}),
            "matk": MappingProxyType({"int": 1.0}),
        })
        for class_key in SUPPORTED_CLASSES
    }),
    "candidate_a": MappingProxyType({key: MappingProxyType({kind: MappingProxyType(values) for kind, values in value.items()}) for key, value in _CANDIDATE_A.items()}),
    "candidate_b": MappingProxyType({key: MappingProxyType({kind: MappingProxyType(values) for kind, values in value.items()}) for key, value in _CANDIDATE_B.items()}),
    "candidate_c": MappingProxyType({key: MappingProxyType({kind: MappingProxyType(values) for kind, values in value.items()}) for key, value in _CANDIDATE_C.items()}),
})


def normalize_class_key(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be an int or float, excluding bool")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if result < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return result


def round_stat(value: object) -> int:
    number = _number(value, "value")
    return int(math.floor(number + 0.5))


def validate_class_scaling(candidate: Mapping[str, Mapping[str, Mapping[str, object]]]) -> None:
    if set(candidate) != set(SUPPORTED_CLASSES):
        raise ValueError("candidate must define exactly the six supported classes")
    for class_key in SUPPORTED_CLASSES:
        entry = candidate[class_key]
        if set(entry) != {"patk", "matk"}:
            raise ValueError(f"{class_key} must define patk and matk")
        for attack_kind in ("patk", "matk"):
            coefficients = entry[attack_kind]
            if not coefficients:
                raise ValueError(f"{class_key}.{attack_kind} must not be empty")
            for stat_name, coefficient in coefficients.items():
                if stat_name not in SUPPORTED_STATS:
                    raise ValueError(f"unsupported stat: {stat_name}")
                _number(coefficient, f"{class_key}.{attack_kind}.{stat_name}")


def get_candidate(name: str) -> Mapping[str, Mapping[str, Mapping[str, float]]]:
    key = str(name).strip().lower()
    if key not in CLASS_SCALING_CANDIDATES:
        raise KeyError(f"unknown scaling candidate: {name}")
    candidate = CLASS_SCALING_CANDIDATES[key]
    validate_class_scaling(candidate)
    return candidate


def _calculate_attack(
    class_key: object,
    stats: Mapping[str, object],
    attack_kind: str,
    candidate: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> int:
    validate_class_scaling(candidate)
    normalized = normalize_class_key(class_key)
    if normalized not in candidate:
        identity_stat = "str" if attack_kind == "patk" else "int"
        return round_stat(_number(stats.get(identity_stat, 0), identity_stat))
    total = 0.0
    for stat_name, coefficient in candidate[normalized][attack_kind].items():
        total += _number(stats.get(stat_name, 0), stat_name) * _number(coefficient, f"coefficient.{stat_name}")
    return max(0, round_stat(total))


def calc_patk(class_key: object, stats: Mapping[str, object], candidate_name: str = "candidate_c") -> int:
    return _calculate_attack(class_key, stats, "patk", get_candidate(candidate_name))


def calc_matk(class_key: object, stats: Mapping[str, object], candidate_name: str = "candidate_c") -> int:
    return _calculate_attack(class_key, stats, "matk", get_candidate(candidate_name))


def calc_max_hp_parity(level: object, total_sta: object, refine_percent: object = 0.0) -> int:
    from data.player_hp import calculate_base_max_hp
    base_hp = calculate_base_max_hp(round_stat(level), round_stat(total_sta))
    multiplier = 1.0 + _number(refine_percent, "refine_percent") / 100.0
    return max(1, round_stat(base_hp * multiplier))


def calc_pdef_parity(item_pdef: object, total_sta: object) -> int:
    from data.defense_policy import calculate_total_defense
    return int(calculate_total_defense(_number(item_pdef, "item_pdef"), _number(total_sta, "total_sta")))


def calc_mdef_parity(item_mdef: object, total_wis: object) -> int:
    from data.defense_policy import calculate_total_defense
    return int(calculate_total_defense(_number(item_mdef, "item_mdef"), _number(total_wis, "total_wis")))
