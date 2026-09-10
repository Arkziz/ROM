#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM migration 042: Attribute Points schema foundation only."""
from __future__ import annotations
NUMERIC_COLUMNS=("free_attribute_points","total_attribute_points_earned","allocated_strength","allocated_dexterity","allocated_intelligence","allocated_wisdom","allocated_stamina")
TEXT_COLUMNS=("attribute_points_migrated_at",)
def _columns(conn):
    return {str(r[1]) for r in conn.execute("PRAGMA table_info(users)")}
def up(conn):
    cols=_columns(conn)
    for name in NUMERIC_COLUMNS:
        if name not in cols:
            conn.execute(f'ALTER TABLE users ADD COLUMN "{name}" INTEGER NOT NULL DEFAULT 0 CHECK("{name}" >= 0)')
            cols.add(name)
    for name in TEXT_COLUMNS:
        if name not in cols:
            conn.execute(f'ALTER TABLE users ADD COLUMN "{name}" TEXT NULL')
            cols.add(name)
    missing=sorted(set(NUMERIC_COLUMNS+TEXT_COLUMNS)-_columns(conn))
    if missing: raise RuntimeError(f"Migration 042 missing columns: {missing}")
    for name in NUMERIC_COLUMNS:
        nulls=conn.execute(f'SELECT COUNT(*) FROM users WHERE "{name}" IS NULL').fetchone()[0]
        negatives=conn.execute(f'SELECT COUNT(*) FROM users WHERE "{name}" < 0').fetchone()[0]
        if nulls or negatives: raise RuntimeError(f"Invariant failed for {name}: null={nulls}, negative={negatives}")
