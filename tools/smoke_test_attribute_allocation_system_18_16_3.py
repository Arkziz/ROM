#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sqlite3
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from systems.attribute_allocation_system import (
    AttributeInvariantError,
    InsufficientAttributePointsError,
    InvalidAllocationError,
    StaleAttributeStateError,
    allocate_attribute_points,
    get_attribute_point_state,
)
class TestDatabase:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

def require_raises(error_type, operation):
    try:
        operation()
    except error_type:
        return
    raise AssertionError(f"Expected {error_type.__name__}")

def main():
    with tempfile.TemporaryDirectory(prefix="rom_attribute_api_") as temp:
        database = TestDatabase(str(Path(temp) / "test.db"))
        database.cursor.execute("""CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            free_attribute_points INTEGER NOT NULL DEFAULT 0,
            total_attribute_points_earned INTEGER NOT NULL DEFAULT 0,
            allocated_strength INTEGER NOT NULL DEFAULT 0,
            allocated_dexterity INTEGER NOT NULL DEFAULT 0,
            allocated_intelligence INTEGER NOT NULL DEFAULT 0,
            allocated_wisdom INTEGER NOT NULL DEFAULT 0,
            allocated_stamina INTEGER NOT NULL DEFAULT 0
        )""")
        database.cursor.execute("INSERT INTO users VALUES (1, 10, 10, 0, 0, 0, 0, 0)")
        database.cursor.execute("INSERT INTO users VALUES (2, 2, 10, 2, 2, 2, 1, 1)")
        database.cursor.execute("INSERT INTO users VALUES (3, 5, 99, 0, 0, 0, 0, 0)")
        database.conn.commit()

        initial = get_attribute_point_state(1, db_module=database)
        assert initial["free_attribute_points"] == 10 and initial["invariant_valid"]
        result = allocate_attribute_points(
            1, {"str": 2, "dexterity": 1, "wis": 2},
            expected_free_attribute_points=10, db_module=database,
        )
        assert result["spent"] == 5
        assert result["after"]["free_attribute_points"] == 5
        assert result["after"]["allocated_strength"] == 2
        assert result["after"]["allocated_dexterity"] == 1
        assert result["after"]["allocated_wisdom"] == 2
        assert result["after"]["total_attribute_points_earned"] == 10
        assert result["after"]["invariant_valid"]

        snapshot = get_attribute_point_state(1, db_module=database)
        require_raises(
            StaleAttributeStateError,
            lambda: allocate_attribute_points(
                1, {"sta": 1}, expected_free_attribute_points=10,
                db_module=database,
            ),
        )
        assert get_attribute_point_state(1, db_module=database) == snapshot

        require_raises(
            InsufficientAttributePointsError,
            lambda: allocate_attribute_points(2, {"strength": 3}, db_module=database),
        )
        require_raises(
            InvalidAllocationError,
            lambda: allocate_attribute_points(1, {"luck": 1}, db_module=database),
        )
        require_raises(
            InvalidAllocationError,
            lambda: allocate_attribute_points(1, {"str": -1}, db_module=database),
        )
        require_raises(
            AttributeInvariantError,
            lambda: get_attribute_point_state(3, db_module=database),
        )
        assert not database.conn.in_transaction
        database.conn.close()
    print("[PASS] Stage 18.16.3 atomic allocation API contract")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
