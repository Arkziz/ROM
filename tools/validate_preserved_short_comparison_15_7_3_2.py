from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'reports'/'boss_stage_15_7_3_short_reference_comparison.json'
assert source.exists(), f'missing preserved report: {source}'
d=json.loads(source.read_text(encoding='utf-8'))
assert d['version']=='15.7.3'
assert d['mode']=='short_bounded_read_only_comparison'
assert d['trials_per_cell']==12
assert d['executed_battles']==2016, d['executed_battles']
assert d['logical_comparisons']==1440, d['logical_comparisons']
assert len(d['elite_reference_manifest'])==8
assert len(d['boss_reference_manifest'])==6
assert set(d['elite_summary'])=={'normal','elite_x1_5'}
assert set(d['boss_summary'])=={'pack_leader','goblin_king'}
assert d['verdict'] in {'PASS','PASS_WITH_REVIEW'}
assert not d['technical_findings']
assert d['production_files_changed'] is False and d['database_writes']==0 and d['feature_gate_changed'] is False

elite=d['elite_summary']['elite_x1_5']; pack=d['boss_summary']['pack_leader']; king=d['boss_summary']['goblin_king']
conclusion={
 'elite_x1_5_too_easy': elite['win_rate']>0.85,
 'pack_leader_x2_too_easy': pack['progression']['win_rate']>0.70,
 'goblin_king_x2_too_easy': king['progression']['win_rate']>0.70,
 'do_not_apply_proposed_multipliers_yet': True,
 'next_action': 'targeted stat-reference audit using real generated normal mob instances; no battle simulation rerun',
}
out={
 'version':'15.7.3.2','verdict':'PASS','source_report':'reports/boss_stage_15_7_3_short_reference_comparison.json',
 'validated_executed_battles':2016,'validated_logical_comparisons':1440,'runtime_seconds':d['runtime_seconds'],'elite_summary':d['elite_summary'],
 'boss_summary':d['boss_summary'],'findings':d['findings'],'conclusion':conclusion,'simulation_rerun':False,
 'production_files_changed':False,'database_writes':0,
}
path=ROOT/'reports'/'boss_stage_15_7_3_2_recovered_validation.json';path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('[PASS] preserved 15.7.3 report validated without simulation rerun',{'battles':2016,'runtime_seconds':d['runtime_seconds']})
