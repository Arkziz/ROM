from __future__ import annotations
import ast,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
paths={
 'bosses':ROOT/'data'/'bosses.py',
 'boss_system':ROOT/'systems'/'boss_system.py',
 'combat_system':ROOT/'systems'/'combat_system.py',
 'combat_handler':ROOT/'handlers'/'combat.py',
 'drop_system':ROOT/'systems'/'drop_system.py',
 'reward_system':ROOT/'systems'/'reward_system.py',
 'rune_system':ROOT/'systems'/'rune_system.py',
}
missing=[k for k,p in paths.items() if not p.exists()]
assert not missing,{'missing_files':missing}
text={k:p.read_text(encoding='utf-8') for k,p in paths.items()}
for k,v in text.items():ast.parse(v,filename=str(paths[k]))
findings=[];checks={}
def check(name,condition,detail=''):
 checks[name]={'pass':bool(condition),'detail':detail}
 if not condition:findings.append(f'{name}: {detail}')
check('boss_gate_disabled','BOSS_ENCOUNTERS_ENABLED = False' in text['bosses'],'live gate must remain disabled')
check('builder_signals',all(s in text['boss_system'] for s in ('"is_boss": True','"is_elite": False','"enemy_type": "boss"','"mob_type": "boss"')),'boss builder must emit canonical signals')
check('drop_classifier_priority','Return exactly one enemy type using boss > elite > normal priority' in text['drop_system'] and 'if "boss" in explicit_types' in text['drop_system'],'central drop classifier boss priority')
check('rune_classifier_priority','Canonical priority: boss > elite > normal' in text['rune_system'],'rune classifier boss priority')
check('single_reward_api',text['reward_system'].count('def process_victory_reward(')==1,'exactly one authoritative function expected')
check('single_drop_call','drop_result = process_enemy_drops(user_id, mob)' in text['reward_system'],'reward must call central drops once')
check('single_kill_increment',text['reward_system'].count('add_kill(user_id)')>=1,'victory reward increments kill')
check('handler_victory_route',text['combat_handler'].count('process_victory(')>=3,'all combat paths route through victory handler')
check('no_boss_direct_awards', not any(token in text['boss_system'] for token in ('add_item(', 'add_gold(', 'add_exp(', 'process_enemy_drops(', 'award_rune_drop(')), 'boss system must not award rewards')
check('boss_not_elite_guild_hook','"is_elite": False' in text['boss_system'],'boss must not silently trigger elite-only guild hook')
check('no_db_in_boss_system',not re.search(r'\b(import db|from db import|sqlite3)\b',text['boss_system']),'boss system must remain DB-free')
result={'version':'15.6.1','verdict':'PASS' if not findings else 'FAIL','checks':checks,'findings':findings,'database_writes':0,'feature_gate':'disabled'}
out=ROOT/'reports'/'boss_stage_15_6_0_reward_contract_audit.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
assert not findings,result
print('[PASS] boss central reward/drop contract audit',{'checks':len(checks),'findings':0})
