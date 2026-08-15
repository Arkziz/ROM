from __future__ import annotations
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
handler=(ROOT/'handlers'/'combat.py').read_text(encoding='utf-8');reward=(ROOT/'systems'/'reward_system.py').read_text(encoding='utf-8');boss=(ROOT/'systems'/'boss_system.py').read_text(encoding='utf-8')
ast.parse(handler);ast.parse(reward);ast.parse(boss)
metrics={
 'process_victory_calls':handler.count('process_victory('),
 'process_victory_reward_definitions':reward.count('def process_victory_reward('),
 'central_drop_calls_in_reward':reward.count('process_enemy_drops(user_id, mob)'),
 'boss_direct_reward_tokens':sum(boss.count(x) for x in ('add_item(','add_gold(','add_exp(','process_enemy_drops(','award_rune_drop(')),
 'boss_handler_bridge_calls':handler.count('mob_attack_result = _calculate_enemy_turn_15_5_0('),
}
findings=[]
if metrics['process_victory_calls']<3:findings.append('combat completion paths insufficient')
if metrics['process_victory_reward_definitions']!=1:findings.append('authoritative reward function count mismatch')
if metrics['central_drop_calls_in_reward']<1:findings.append('central drop call missing')
if metrics['boss_direct_reward_tokens']!=0:findings.append('boss system contains direct reward mutation')
if metrics['boss_handler_bridge_calls']!=3:findings.append('boss handler bridge path count mismatch')
result={'version':'15.6.1','verdict':'PASS' if not findings else 'FAIL','metrics':metrics,'findings':findings,'completion_contract':'single standard PvE victory pipeline'}
out=ROOT/'reports'/'boss_stage_15_6_0_completion_contract.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
assert not findings,result
print('[PASS] boss completion uses standard PvE victory pipeline',metrics)
