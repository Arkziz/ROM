#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'reports/stage_21_14_2b_event_schedules_rewards_parity_resolution.json').read_text(encoding='utf-8'))
assert data['stage']=='21.14.2b' and data['status']=='PASS'
assert data['decision']=='PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED'
assert not data['failed_checks']
assert {x['area'] for x in data['resolutions']}=={'shop_exact_once', 'schedule', 'lifecycle', 'clock', 'statistics_exact_once', 'announcements', 'identity', 'timezone', 'rewards', 'eligibility'}
assert all(x['status']=='RESOLVED' for x in data['resolutions'])
print('PASS: Stage 21.14.2b parity resolution contract')
