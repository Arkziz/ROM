from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.simulation.economic_ledger import EconomicScenarioSpec
from systems.simulation.economic_progression import run_economic_progression

def main():
    p=argparse.ArgumentParser();p.add_argument("character_class");p.add_argument("target_level",type=int);p.add_argument("profile",choices=("casual","regular","hardcore"));p.add_argument("--seed",type=int,default=138100);p.add_argument("--inventory",type=int,choices=(40,60),default=40);p.add_argument("--max-days",type=int,default=365);p.add_argument("--force",action="store_true");a=p.parse_args()
    s=EconomicScenarioSpec(a.character_class,a.profile,a.seed,a.target_level,a.inventory,a.max_days);r=run_economic_progression(ROOT,s,a.force);d=ROOT/"simulation_reports"/"economic_v2";d.mkdir(parents=True,exist_ok=True);path=d/f"economic_{a.character_class}_l{a.target_level}_{a.profile}_{a.inventory}s_{a.seed}.json";path.write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8");q=r["economic_reconciliation"];v=r["asset_valuation"]
    print("[OK] Economic progression v2");print(f"- status: {r.get('status')}");print(f"- level: {r.get('final_level')}/{r.get('target_level')}");print(f"- ledger reconciliation: {'PASS' if q['passed'] else 'FAIL'}; delta={q['delta']}");print(f"- asset coverage: {v['coverage']}; net worth={v['total_net_worth']}");print(f"- JSON: {path.relative_to(ROOT)}")
if __name__=="__main__":main()
