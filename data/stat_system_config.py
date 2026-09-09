from __future__ import annotations

import math

PRIMARY_STAT_KEYS = ("str", "dex", "int", "wis", "sta")
SUPPORTED_CLASSES = ("warrior", "knight", "rogue", "scout", "mage", "priest")
MANA_CLASSES = frozenset({"mage", "priest"})

PHYSICAL_ATTACK_SCALING = {
    "warrior": {"str": 1.00, "dex": 0.20, "int": 0.00, "wis": 0.00, "sta": 0.00},
    "knight":  {"str": 1.10, "dex": 0.10, "int": 0.00, "wis": 0.00, "sta": 0.00},
    "rogue":   {"str": 0.40, "dex": 0.80, "int": 0.00, "wis": 0.00, "sta": 0.00},
    "scout":   {"str": 0.65, "dex": 0.55, "int": 0.00, "wis": 0.00, "sta": 0.00},
    "mage":    {"str": 0.20, "dex": 0.00, "int": 0.00, "wis": 0.00, "sta": 0.00},
    "priest":  {"str": 0.20, "dex": 0.00, "int": 0.00, "wis": 0.00, "sta": 0.00},
}

MAGICAL_ATTACK_SCALING = {
    "warrior": {"str": 0.00, "dex": 0.00, "int": 0.20, "wis": 0.00, "sta": 0.00},
    "knight":  {"str": 0.00, "dex": 0.00, "int": 0.20, "wis": 0.00, "sta": 0.00},
    "rogue":   {"str": 0.00, "dex": 0.00, "int": 0.20, "wis": 0.00, "sta": 0.00},
    "scout":   {"str": 0.00, "dex": 0.00, "int": 0.20, "wis": 0.00, "sta": 0.00},
    "mage":    {"str": 0.00, "dex": 0.00, "int": 1.05, "wis": 0.15, "sta": 0.00},
    "priest":  {"str": 0.00, "dex": 0.00, "int": 0.90, "wis": 0.30, "sta": 0.00},
}

MAX_MP_SCALING = {
    "base": 100.0,
    "level": 20.0,
    "int": 1.0,
    "wis": 4.0,
}


def validate_stat_system_config() -> tuple[str, ...]:
    problems = []
    expected_classes = set(SUPPORTED_CLASSES)
    expected_stats = set(PRIMARY_STAT_KEYS)
    for label, matrix in (
        ("PHYSICAL_ATTACK_SCALING", PHYSICAL_ATTACK_SCALING),
        ("MAGICAL_ATTACK_SCALING", MAGICAL_ATTACK_SCALING),
    ):
        if set(matrix) != expected_classes:
            problems.append(f"{label}: class set mismatch")
        for class_key, coefficients in matrix.items():
            if set(coefficients) != expected_stats:
                problems.append(f"{label}/{class_key}: stat key mismatch")
            for stat_key, value in coefficients.items():
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    problems.append(f"{label}/{class_key}/{stat_key}: coefficient must be numeric")
                elif not math.isfinite(float(value)) or float(value) < 0:
                    problems.append(f"{label}/{class_key}/{stat_key}: coefficient must be finite and non-negative")
    if set(MAX_MP_SCALING) != {"base", "level", "int", "wis"}:
        problems.append("MAX_MP_SCALING: key mismatch")
    for key, value in MAX_MP_SCALING.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            problems.append(f"MAX_MP_SCALING/{key}: coefficient must be numeric")
        elif not math.isfinite(float(value)) or float(value) < 0:
            problems.append(f"MAX_MP_SCALING/{key}: coefficient must be finite and non-negative")
    return tuple(problems)


_CONFIG_PROBLEMS = validate_stat_system_config()
if _CONFIG_PROBLEMS:
    raise RuntimeError("Invalid stat system config: " + "; ".join(_CONFIG_PROBLEMS))
