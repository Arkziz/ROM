from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_policy_balance_candidate_sandbox import format_summary,run_sandbox,save_report
p=argparse.ArgumentParser(); p.add_argument("--trials",type=int,default=50); p.add_argument("--seed",type=int,default=14640); a=p.parse_args(); r=run_sandbox(a.trials,a.seed); q=save_report(r,ROOT/"tools"/"pvp_policy_balance_candidate_sandbox_report.json"); print(format_summary(r)); print(f"JSON: {q.relative_to(ROOT)}")
