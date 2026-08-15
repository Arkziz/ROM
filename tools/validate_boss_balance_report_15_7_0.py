from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'reports'/'boss_stage_15_7_0_balance_simulation.json';d=json.loads(p.read_text(encoding='utf-8'))
assert d['version']=='15.7.0';assert d['total_trials']==12000;assert d['cells']==60
assert set(d['classes'])=={'warrior','knight','scout','rogue','mage','priest'}
assert d['database_writes']==0 and d['live_balance_changed'] is False and d['feature_gate_changed'] is False
assert d['verdict'] in {'PASS','PASS_WITH_REVIEW'}
assert len(d['rows'])==60 and all(x['trials']==200 for x in d['rows'])
print('[PASS] boss simulation report schema and coverage',{'verdict':d['verdict'],'cells':d['cells'],'trials':d['total_trials']})
