import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=subprocess.run([sys.executable,"tools/run_full_production_progression_acceptance.py"],cwd=ROOT)
 assert p.returncode==0
 data=json.loads((ROOT/"MD/SIMULATION_FULL_PRODUCTION_PROGRESSION_ACCEPTANCE_13_6_5.json").read_text(encoding="utf-8"))
 assert data["verdict"] in {"PASS","REVIEW"} and data["scenario_count"]==18
 assert not data["failures"] and all(all(x["checks"].values()) for x in data["scenarios"])
 assert data["database_writes"]==0 and data["production_max_mob_level"]>=10
 print('[OK] Full production progression acceptance contracts')
 print('- six classes x three profiles: PASS')
 print('- same-seed deterministic results: PASS')
 print('- battle/energy/event/capacity invariants: PASS')
 print('- production content ceiling reported honestly: PASS')
 print('- balance-readiness blockers surfaced, not hidden: PASS')
 print('- database writes: 0')
if __name__=='__main__':main()
