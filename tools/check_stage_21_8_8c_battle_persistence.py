#!/usr/bin/env python3
"""Stage 21.8.8c smoke check for the pure encounter lifecycle API."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Direct execution sets sys.path[0] to ROM/tools, so add the repository root
# explicitly before importing rom_v2. This keeps the smoke check independent
# from the caller's PYTHONPATH while avoiding any V1/runtime import.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rom_v2.domain.battle_persistence import PersistedEncounterStatus, begin_persisted_encounter, recover_persisted_encounters_after_restart

now = datetime(2026, 1, 1, tzinfo=timezone.utc)
marker = begin_persisted_encounter("smoke-encounter", "smoke-actor", now, now + timedelta(seconds=1))
results = recover_persisted_encounters_after_restart([marker], now + timedelta(seconds=1))
assert len(results) == 1 and results[0].accepted
assert results[0].marker.status is PersistedEncounterStatus.EXPIRED
print("STAGE_21_8_8C_BATTLE_PERSISTENCE_SMOKE: PASS")
