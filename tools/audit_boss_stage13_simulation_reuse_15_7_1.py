from __future__ import annotations
import ast,inspect,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from systems.simulation.production_parity import run_required_parity,source_dependency_report
from systems.simulation.skill_catalog import load_production_skill_catalog
from systems.simulation.progression_provider import ProgressionProvider
from systems.simulation.pve_battle import ExactPveBattleEngine
catalog=load_production_skill_catalog(ROOT)
parity=run_required_parity()
deps=source_dependency_report()
findings=[]
if parity['verdict']!='PASS':findings.append('stage13_required_production_parity_failed')
if set(catalog)!={'warrior','knight','scout','rogue','mage','priest'}:findings.append('skill_catalog_class_mismatch')
if any(len(v)!=3 for v in catalog.values()):findings.append('skill_catalog_skill_count_mismatch')
required_modules=['systems.simulation.production_parity','systems.simulation.skill_catalog','systems.simulation.progression_provider','systems.simulation.pve_battle','systems.simulation.combat_actor_stats']
result={'version':'15.7.1','verdict':'PASS' if not findings else 'FAIL','stage13_parity_verdict':parity['verdict'],'stage13_parity_cases':parity['cases'],'stage13_parity_failed':parity['failed'],'production_skill_count':sum(len(v) for v in catalog.values()),'classes':sorted(catalog),'reused_modules':required_modules,'source_dependencies':deps,'findings':findings,'database_writes':0}
out=ROOT/'reports'/'boss_stage_15_7_1_production_parity_audit.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
assert not findings,result
print('[PASS] Stage 13 PvE simulation reuse and production parity',{'parity_cases':parity['cases'],'skills':result['production_skill_count']})
