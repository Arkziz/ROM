"""Ordered database migrations for the isolated ROM V2 database."""

from rom_v2.infrastructure.persistence.migrations.v001_v2_baseline import MIGRATION

MIGRATIONS = (MIGRATION,)

__all__ = ["MIGRATIONS"]
