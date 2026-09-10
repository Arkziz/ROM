#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical Attribute Allocation domain service.

This module owns read and allocation transactions for Stage 18.16.
It does not own Telegram UI, effective-stat aggregation, legacy migration,
resource recalculation, or reset-item behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

POINTS_PER_LEVEL = 5
ATTRIBUTE_TO_COLUMN = {
    "strength": "allocated_strength",
    "dexterity": "allocated_dexterity",
    "intelligence": "allocated_intelligence",
    "wisdom": "allocated_wisdom",
    "stamina": "allocated_stamina",
}
ATTRIBUTE_ALIASES = {
    "str": "strength",
    "dex": "dexterity",
    "int": "intelligence",
    "wis": "wisdom",
    "sta": "stamina",
}
ALLOCATED_COLUMNS = tuple(ATTRIBUTE_TO_COLUMN.values())


class AttributeAllocationError(RuntimeError):
    """Base domain error for attribute point operations."""


class PlayerNotFoundError(AttributeAllocationError):
    pass


class InvalidAllocationError(AttributeAllocationError):
    pass


class InsufficientAttributePointsError(AttributeAllocationError):
    pass


class StaleAttributeStateError(AttributeAllocationError):
    pass


class AttributeInvariantError(AttributeAllocationError):
    pass


@dataclass(frozen=True)
class AttributePointState:
    user_id: int
    free_attribute_points: int
    total_attribute_points_earned: int
    allocated_strength: int
    allocated_dexterity: int
    allocated_intelligence: int
    allocated_wisdom: int
    allocated_stamina: int

    @property
    def allocated_total(self) -> int:
        return (
            self.allocated_strength
            + self.allocated_dexterity
            + self.allocated_intelligence
            + self.allocated_wisdom
            + self.allocated_stamina
        )

    @property
    def invariant_valid(self) -> bool:
        return self.total_attribute_points_earned == (
            self.free_attribute_points + self.allocated_total
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["allocated_total"] = self.allocated_total
        result["invariant_valid"] = self.invariant_valid
        return result


def _db_module(db_module=None):
    if db_module is not None:
        return db_module
    import db
    return db


def _row_value(row, key: str, index: int) -> int:
    if hasattr(row, "keys") and key in row.keys():
        return int(row[key] or 0)
    return int(row[index] or 0)


def _state_from_row(user_id: int, row) -> AttributePointState:
    if row is None:
        raise PlayerNotFoundError(f"Player not found: {user_id}")
    names = (
        "free_attribute_points",
        "total_attribute_points_earned",
        "allocated_strength",
        "allocated_dexterity",
        "allocated_intelligence",
        "allocated_wisdom",
        "allocated_stamina",
    )
    values = [_row_value(row, name, index) for index, name in enumerate(names)]
    state = AttributePointState(int(user_id), *values)
    _validate_state(state)
    return state


def _validate_state(state: AttributePointState) -> None:
    values = (
        state.free_attribute_points,
        state.total_attribute_points_earned,
        state.allocated_strength,
        state.allocated_dexterity,
        state.allocated_intelligence,
        state.allocated_wisdom,
        state.allocated_stamina,
    )
    if any(value < 0 for value in values):
        raise AttributeInvariantError("Attribute point values cannot be negative")
    if not state.invariant_valid:
        raise AttributeInvariantError(
            "Attribute point invariant failed: total earned must equal free plus allocated"
        )


def _fetch_state(cursor, user_id: int) -> AttributePointState:
    row = cursor.execute(
        """SELECT free_attribute_points, total_attribute_points_earned,
                  allocated_strength, allocated_dexterity,
                  allocated_intelligence, allocated_wisdom, allocated_stamina
             FROM users WHERE user_id=?""",
        (int(user_id),),
    ).fetchone()
    return _state_from_row(int(user_id), row)


def get_attribute_point_state(user_id: int, *, db_module=None) -> dict[str, Any]:
    """Return authoritative persistent point state without mutation."""
    database = _db_module(db_module)
    return _fetch_state(database.cursor, int(user_id)).to_dict()


def normalize_allocation(allocation: Mapping[str, int]) -> dict[str, int]:
    """Validate and normalize a pending allocation to canonical attribute names."""
    if not isinstance(allocation, Mapping) or not allocation:
        raise InvalidAllocationError("Allocation must be a non-empty mapping")
    normalized = {name: 0 for name in ATTRIBUTE_TO_COLUMN}
    seen = set()
    for raw_name, raw_value in allocation.items():
        name = str(raw_name).strip().lower()
        name = ATTRIBUTE_ALIASES.get(name, name)
        if name not in ATTRIBUTE_TO_COLUMN:
            raise InvalidAllocationError(f"Unsupported attribute: {raw_name}")
        if name in seen:
            raise InvalidAllocationError(f"Duplicate attribute after normalization: {name}")
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            raise InvalidAllocationError(f"Allocation for {name} must be an integer")
        if raw_value < 0:
            raise InvalidAllocationError(f"Allocation for {name} cannot be negative")
        normalized[name] = raw_value
        seen.add(name)
    if sum(normalized.values()) <= 0:
        raise InvalidAllocationError("Allocation total must be greater than zero")
    return normalized


def allocate_attribute_points(
    user_id: int,
    allocation: Mapping[str, int],
    *,
    expected_free_attribute_points: int | None = None,
    db_module=None,
) -> dict[str, Any]:
    """Atomically allocate points and return before/after state.

    `expected_free_attribute_points` is an optimistic concurrency token for UI
    confirmation. A repeated or stale confirmation fails instead of spending a
    newer balance.
    """
    normalized = normalize_allocation(allocation)
    spent = sum(normalized.values())
    database = _db_module(db_module)
    connection = database.conn
    cursor = database.cursor

    if connection.in_transaction:
        raise AttributeAllocationError(
            "allocate_attribute_points requires ownership of its transaction"
        )

    connection.execute("BEGIN IMMEDIATE")
    try:
        before = _fetch_state(cursor, int(user_id))
        if expected_free_attribute_points is not None:
            if isinstance(expected_free_attribute_points, bool) or not isinstance(
                expected_free_attribute_points, int
            ):
                raise InvalidAllocationError(
                    "expected_free_attribute_points must be an integer or None"
                )
            if before.free_attribute_points != expected_free_attribute_points:
                raise StaleAttributeStateError(
                    "Attribute point balance changed; refresh before confirming"
                )
        if spent > before.free_attribute_points:
            raise InsufficientAttributePointsError(
                f"Not enough free attribute points: required={spent}, "
                f"available={before.free_attribute_points}"
            )

        cursor.execute(
            """UPDATE users SET
                   free_attribute_points = free_attribute_points - ?,
                   allocated_strength = allocated_strength + ?,
                   allocated_dexterity = allocated_dexterity + ?,
                   allocated_intelligence = allocated_intelligence + ?,
                   allocated_wisdom = allocated_wisdom + ?,
                   allocated_stamina = allocated_stamina + ?
                 WHERE user_id=? AND free_attribute_points >= ?""",
            (
                spent,
                normalized["strength"],
                normalized["dexterity"],
                normalized["intelligence"],
                normalized["wisdom"],
                normalized["stamina"],
                int(user_id),
                spent,
            ),
        )
        if cursor.rowcount != 1:
            raise StaleAttributeStateError(
                "Attribute point state changed during confirmation"
            )
        after = _fetch_state(cursor, int(user_id))
        if after.total_attribute_points_earned != before.total_attribute_points_earned:
            raise AttributeInvariantError("Allocation cannot change total earned points")
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    return {
        "user_id": int(user_id),
        "spent": spent,
        "allocation": normalized,
        "before": before.to_dict(),
        "after": after.to_dict(),
    }
