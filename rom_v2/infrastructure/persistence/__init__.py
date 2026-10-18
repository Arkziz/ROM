"""Persistence contracts, migrations, and SQLite adapters for ROM V2."""

from rom_v2.infrastructure.persistence.connection_factory import (
    ConnectionProfile,
    V2ConnectionFactory,
)
from rom_v2.infrastructure.persistence.migrator import MigrationResult, V2Migrator
from rom_v2.infrastructure.persistence.schema_contract import SCHEMA_CONTRACT
from rom_v2.infrastructure.persistence.unit_of_work import SQLiteUnitOfWork

__all__ = [
    "ConnectionProfile",
    "MigrationResult",
    "SCHEMA_CONTRACT",
    "SQLiteUnitOfWork",
    "V2ConnectionFactory",
    "V2Migrator",
]
