from __future__ import annotations
import json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from systems.boss_system import roll_boss_encounter
trials=100000
hits=sum(roll_boss_encounter(random.Random(152000+i),chance_percent=1.0,enabled=True) for i in range(trials))
rate=hits/trials*100
assert 0.85<=rate<=1.15,(hits,rate)
result={"version":"15.2.0","trials":trials,"configured_percent":1.0,"boss_hits":hits,"actual_percent":round(rate,4),"acceptance_percent":[0.85,1.15],"verdict":"PASS"}
out=ROOT/'reports'/'boss_stage_15_2_0_encounter_distribution.json'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print("[PASS] encounter distribution",result)
