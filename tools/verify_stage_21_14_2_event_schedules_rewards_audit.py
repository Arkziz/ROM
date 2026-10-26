#!/usr/bin/env python3
"""Verify Stage 21.14.2 audit artifacts without opening a database."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'reports/stage_21_14_2_existing_event_schedules_rewards_audit.json').read_text(encoding="utf-8"))
assert (ROOT/'MD/STAGE_21_14_2_EXISTING_EVENT_SCHEDULES_REWARDS_AUDIT.md').is_file()
assert data["stage"]=="21.14.2"
assert data["audit_mode"]=="STATIC_READ_ONLY_V1"
assert data["preflight"]["starting_head"]=='1f1ed0db9ea0cabd608508b99ee54823984a5731'
assert data["scan"]["parse_failures"]==[]
assert data["safety"]=={"database_opened":False,"v1_runtime_imported":False,"telegram_started":False,"runtime_started":False,"production_source_modified":False,"wal_shm_manipulated":False,"main_py_started":False}
assert data["summary"]["evidence_rows"]==len(data["evidence"])
assert data["summary"]["source_files"]==len({r["path"] for r in data["evidence"]})
print("[PASS] Stage 21.14.2 audit artifacts verified.")
