from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from systems.drop_system import classify_enemy
from systems.rune_system import classify_rune_drop_enemy
cases=[
 ({'is_boss':True},'boss'),
 ({'boss':True},'boss'),
 ({'enemy_type':'boss'},'boss'),
 ({'mob_type':'boss'},'boss'),
 ({'is_boss':True,'is_elite':True},'boss'),
 ({'is_elite':True},'elite'),
 ({},'normal'),
]
rows=[]
for mob,expected in cases:
 central=classify_enemy(mob);rune=classify_rune_drop_enemy(mob)
 assert central==expected,(mob,central,expected)
 assert rune==expected,(mob,rune,expected)
 rows.append({'mob':mob,'expected':expected,'central':central,'rune':rune})
result={'version':'15.6.1','verdict':'PASS','cases':rows,'boss_priority_confirmed':True}
out=ROOT/'reports'/'boss_stage_15_6_0_classification_matrix.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('[PASS] central and rune classification matrix',{'cases':len(rows),'boss_priority':True})
