from __future__ import annotations
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
handler=ROOT/'handlers'/'combat.py';text=handler.read_text(encoding='utf-8');tree=ast.parse(text)
functions={n.name:n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
required_helpers={'_calculate_enemy_turn_15_5_0','_finalize_enemy_turn_15_5_0','_apply_boss_dot_at_player_turn_15_5_0'}
missing=sorted(required_helpers-set(functions))
metrics={
 'calculate_helper_definitions':sum(1 for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_calculate_enemy_turn_15_5_0'),
 'finalize_helper_definitions':sum(1 for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_finalize_enemy_turn_15_5_0'),
 'dot_helper_definitions':sum(1 for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_apply_boss_dot_at_player_turn_15_5_0'),
 'calculate_bridge_calls':text.count('mob_attack_result = _calculate_enemy_turn_15_5_0('),
 'finalize_bridge_calls':text.count('boss_action_text = _finalize_enemy_turn_15_5_0('),
 'dot_bridge_calls':text.count('player_effects_text += _apply_boss_dot_at_player_turn_15_5_0(mob)'),
 'effective_defense_calls':text.count('boss_pdef, boss_mdef = get_effective_boss_defenses(mob)'),
 'feature_gate_disabled':'BOSS_ENCOUNTERS_ENABLED = False' in (ROOT/'data'/'bosses.py').read_text(encoding='utf-8'),
}
findings=[]
if missing:findings.append('missing helpers: '+', '.join(missing))
for key in ('calculate_helper_definitions','finalize_helper_definitions','dot_helper_definitions','effective_defense_calls'):
 if metrics[key]!=1:findings.append(f'{key}={metrics[key]}, expected=1')
for key in ('calculate_bridge_calls','finalize_bridge_calls','dot_bridge_calls'):
 if metrics[key]!=3:findings.append(f'{key}={metrics[key]}, expected=3')
if not metrics['feature_gate_disabled']:findings.append('feature gate is not disabled')
result={'version':'15.5.1','verdict':'PASS' if not findings else 'FAIL','metrics':metrics,'findings':findings}
out=ROOT/'reports'/'boss_stage_15_5_1_handler_validation.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
assert not findings,result
print('[PASS] semantic handler integration validation',metrics)
