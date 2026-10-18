"""Ordered database migrations for the isolated ROM V2 database."""
from rom_v2.infrastructure.persistence.migrations.v001_v2_baseline import MIGRATION as V001
from rom_v2.infrastructure.persistence.migrations.v002_primary_stats_parity import MIGRATION as V002
MIGRATIONS=(V001,V002)
__all__=["MIGRATIONS"]
