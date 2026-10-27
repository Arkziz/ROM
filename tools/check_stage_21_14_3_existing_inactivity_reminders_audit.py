#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'reports/stage_21_14_3_existing_inactivity_reminders_audit.json').read_text(encoding='utf-8'))
assert data['stage']=='21.14.3' and data['status']=='PASS'
assert data['production_mutation'] is False and data['production_sqlite_opened'] is False
assert data['game_db_wal_shm']=='NOT_MANIPULATED'
assert data['summary']['next_action'] in {'GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW','RECONCILE_PARTIAL_V1_EVIDENCE_BEFORE_MUTATION','STOP_NO_V1_PARITY_CONTRACT'}
print('PASS: Stage 21.14.3 inactivity reminder audit contract')
