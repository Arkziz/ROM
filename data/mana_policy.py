"""Pure canonical policy for ROM Mana calculations.

This module owns numeric Mana policy only. It must stay free of SQLite, Telegram,
combat-handler, character-system, and simulator dependencies. Runtime integration
is intentionally deferred to later Stage 20.3 sub-stages.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import isfinite
from typing import Any, Mapping

MANA_REGEN_PERCENT_PER_FULL_MINUTE = Decimal("30")
MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT = Decimal("50")
MANA_POST_COMBAT_FLOOR_TARGET_PERCENT = Decimal("50")
MANA_COST_ROUNDING_POLICY = "ROUND_HALF_UP"

MANA_COST_FLAT_FIELD = "mana_cost_flat"
MANA_COST_MAX_MP_PERCENT_FIELD = "mana_cost_max_mp_percent"
MANA_RESTORE_MAX_MP_PERCENT_FIELD = "restore_max_mp_percent"


class ManaPolicyError(ValueError):
    """Raised when Mana policy input or a Mana skill definition is invalid."""


def _decimal(value: Any, field_name: str) -> Decimal:
    """Return a finite Decimal while rejecting bool and malformed input."""
    if isinstance(value, bool) or value is None:
        raise ManaPolicyError(f"{field_name} must be a finite number, not {value!r}")
    if isinstance(value, float) and not isfinite(value):
        raise ManaPolicyError(f"{field_name} must be finite")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ManaPolicyError(f"{field_name} must be a finite number") from error
    if not result.is_finite():
        raise ManaPolicyError(f"{field_name} must be finite")
    return result


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    result = _decimal(value, field_name)
    if result < 0:
        raise ManaPolicyError(f"{field_name} must not be negative")
    return result


def _non_negative_int(value: Any, field_name: str) -> int:
    number = _non_negative_decimal(value, field_name)
    if number != number.to_integral_value():
        raise ManaPolicyError(f"{field_name} must be an integer")
    return int(number)


def round_mana_value(value: Any) -> int:
    """Round a non-negative Mana value with explicit half-up semantics."""
    number = _non_negative_decimal(value, "value")
    return int(number.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def validate_mana_skill_definition(skill: Mapping[str, Any]) -> dict[str, Decimal]:
    """Validate and normalize the future hybrid-cost contract of one Mana skill."""
    if not isinstance(skill, Mapping):
        raise ManaPolicyError("skill must be a mapping")
    if str(skill.get("cost_type") or "") != "mana":
        raise ManaPolicyError("skill cost_type must be 'mana'")
    missing = [
        field for field in (MANA_COST_FLAT_FIELD, MANA_COST_MAX_MP_PERCENT_FIELD)
        if field not in skill
    ]
    if missing:
        raise ManaPolicyError("missing Mana cost fields: " + ", ".join(missing))
    normalized = {
        MANA_COST_FLAT_FIELD: _non_negative_decimal(
            skill[MANA_COST_FLAT_FIELD], MANA_COST_FLAT_FIELD
        ),
        MANA_COST_MAX_MP_PERCENT_FIELD: _non_negative_decimal(
            skill[MANA_COST_MAX_MP_PERCENT_FIELD], MANA_COST_MAX_MP_PERCENT_FIELD
        ),
    }
    if MANA_RESTORE_MAX_MP_PERCENT_FIELD in skill:
        normalized[MANA_RESTORE_MAX_MP_PERCENT_FIELD] = _non_negative_decimal(
            skill[MANA_RESTORE_MAX_MP_PERCENT_FIELD],
            MANA_RESTORE_MAX_MP_PERCENT_FIELD,
        )
    return normalized


def calculate_mana_skill_cost(skill: Mapping[str, Any], max_mp: Any) -> int:
    """Return round-half-up(flat + Max MP * percent / 100)."""
    maximum = _non_negative_int(max_mp, "max_mp")
    policy = validate_mana_skill_definition(skill)
    raw_cost = (
        policy[MANA_COST_FLAT_FIELD]
        + Decimal(maximum)
        * policy[MANA_COST_MAX_MP_PERCENT_FIELD]
        / Decimal("100")
    )
    return round_mana_value(raw_cost)


def calculate_mana_restore_amount(max_mp: Any, percent: Any) -> int:
    """Return a clamped nominal percentage restoration amount."""
    maximum = _non_negative_int(max_mp, "max_mp")
    restore_percent = _non_negative_decimal(percent, "percent")
    amount = round_mana_value(Decimal(maximum) * restore_percent / Decimal("100"))
    return min(maximum, amount)


def calculate_post_combat_mp_floor(
    max_mp: Any,
    percent: Any = MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT,
) -> int:
    """Return the active canonical 50% post-combat Mana floor."""
    return calculate_mana_restore_amount(max_mp, percent)


def apply_post_combat_mp_floor_value(
    current_mp: Any,
    max_mp: Any,
    percent: Any = MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT,
) -> int:
    """Apply a floor without adding it and without exceeding Max MP."""
    maximum = _non_negative_int(max_mp, "max_mp")
    current = min(_non_negative_int(current_mp, "current_mp"), maximum)
    return max(current, calculate_post_combat_mp_floor(maximum, percent))


def calculate_passive_mp_regen_per_full_minute(max_mp: Any) -> int:
    """Return the unchanged 30% per-full-minute passive regeneration tick."""
    return calculate_mana_restore_amount(max_mp, MANA_REGEN_PERCENT_PER_FULL_MINUTE)
