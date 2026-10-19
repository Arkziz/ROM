"""Ordered database migrations for the isolated ROM V2 database."""
from rom_v2.infrastructure.persistence.migrations.v001_v2_baseline import MIGRATION as V001
from rom_v2.infrastructure.persistence.migrations.v002_primary_stats_parity import MIGRATION as V002
from rom_v2.infrastructure.persistence.migrations.v003_item_identity_parity import MIGRATION as MIGRATION_003
MIGRATIONS = (V001, V002, MIGRATION_003,)
__all__=["MIGRATIONS"]
