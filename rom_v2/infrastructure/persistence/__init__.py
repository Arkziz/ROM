"""Persistence contracts, migrations, and isolated SQLite adapters for ROM V2."""

from rom_v2.infrastructure.persistence.migrator import MigrationResult, V2Migrator
from rom_v2.infrastructure.persistence.schema_contract import SCHEMA_CONTRACT

__all__ = ["MigrationResult", "SCHEMA_CONTRACT", "V2Migrator"]
