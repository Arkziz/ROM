from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'reports'/'boss_stage_15_7_1_root_cause_and_parity.json').read_text(encoding='utf-8'))
assert d['version']=='15.7.1';assert d['cells']==180;assert d['total_trials']==9000
assert set(d['profile_summary'])=={'naked','progression','strong'}
assert d['stage_15_7_0_root_cause']['zero_win_cells']==60
assert d['database_writes']==0 and not d['production_files_changed'] and not d['feature_gate_changed']
assert d['verdict'] in {'PASS','PASS_WITH_REVIEW'}
print('[PASS] 15.7.1 report coverage and safety',{'cells':d['cells'],'trials':d['total_trials'],'verdict':d['verdict']})
