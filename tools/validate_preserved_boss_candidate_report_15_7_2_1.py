from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reports' / 'boss_stage_15_7_2_candidate_search.json'
assert SOURCE.exists(), f'missing preserved candidate report: {SOURCE}'
d = json.loads(SOURCE.read_text(encoding='utf-8'))

assert d['version'] == '15.7.2'
assert d['mode'] == 'read_only_candidate_search'
assert d['trial_count'] == 129600, d['trial_count']
assert d['trials_per_cell'] == 15
assert set(d['boss_results']) == {'pack_leader', 'goblin_king'}
assert d['production_files_changed'] is False
assert d['database_writes'] == 0
assert d['feature_gate_changed'] is False

summary = {}
for boss_key, item in d['boss_results'].items():
    assert item['candidate_count'] == 72, (boss_key, item['candidate_count'])
    assert len(item['top_candidates']) == 10
    rec = item['recommended']
    assert rec['candidate_id']
    assert set(rec['summary']) == {'progression', 'strong', 'class_spread'}
    assert len(rec['cells']) == 60
    summary[boss_key] = {
        'candidate_id': rec['candidate_id'],
        'start_hp_scale': rec['start_hp_scale'],
        'end_hp_scale': rec['end_hp_scale'],
        'start_atk_scale': rec['start_atk_scale'],
        'end_atk_scale': rec['end_atk_scale'],
        'skill_scale': rec['skill_scale'],
        'summary': rec['summary'],
        'score': rec['score'],
    }

out = {
    'version': '15.7.2.1',
    'verdict': 'PASS',
    'source_report': 'reports/boss_stage_15_7_2_candidate_search.json',
    'validated_trial_count': 129600,
    'candidate_count': 144,
    'recommendations': summary,
    'long_search_rerun': False,
    'production_files_changed': False,
    'database_writes': 0,
}
path = ROOT / 'reports' / 'boss_stage_15_7_2_1_recovered_validation.json'
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print('[PASS] preserved 15.7.2 report validated without rerun', {'trials': 129600, 'candidates': 144})
