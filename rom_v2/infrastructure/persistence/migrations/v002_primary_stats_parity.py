"""Migration 002: add V1 attribute-point invariant support."""
from __future__ import annotations
import hashlib
from rom_v2.infrastructure.persistence.migrations.v001_v2_baseline import Migration
MIGRATION_SQL=r"""ALTER TABLE character_primary_stats ADD COLUMN total_points_earned INTEGER NOT NULL DEFAULT 0 CHECK(total_points_earned>=0);
CREATE TRIGGER character_primary_stats_invariant_insert BEFORE INSERT ON character_primary_stats WHEN NEW.total_points_earned != NEW.unspent_points+NEW.strength+NEW.dexterity+NEW.intelligence+NEW.wisdom+NEW.stamina BEGIN SELECT RAISE(ABORT,'attribute_point_invariant'); END;
CREATE TRIGGER character_primary_stats_invariant_update BEFORE UPDATE ON character_primary_stats WHEN NEW.total_points_earned != NEW.unspent_points+NEW.strength+NEW.dexterity+NEW.intelligence+NEW.wisdom+NEW.stamina BEGIN SELECT RAISE(ABORT,'attribute_point_invariant'); END;"""
MIGRATION=Migration(version=2,key="primary_stats_parity",sql=MIGRATION_SQL)
