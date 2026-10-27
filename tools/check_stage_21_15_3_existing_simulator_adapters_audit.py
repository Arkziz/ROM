#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'reports/stage_21_15_3_existing_simulator_adapters_audit.json').read_text(encoding='utf-8'))
assert data['stage']=='21.15.3' and data['status']=='PASS'
assert data['summary']['next_action']=='GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW'
assert data['simulator_executed'] is False and data['production_sqlite_opened'] is False
assert data['environment_file_opened'] is False and data['game_db_wal_shm']=='NOT_MANIPULATED'
print('PASS: Stage 21.15.3 existing simulator adapters audit')
