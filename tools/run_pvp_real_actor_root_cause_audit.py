from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_root_cause_metric_semantics import format_summary,run_audit,save_report
p=argparse.ArgumentParser(); p.add_argument("--trials",type=int,default=100); p.add_argument("--seed",type=int,default=14632); a=p.parse_args()
result=run_audit(a.trials,a.seed); path=save_report(result,ROOT/"tools"/"pvp_real_actor_root_cause_audit_report.json")
print(format_summary(result)); print(f"JSON: {path.relative_to(ROOT)}")
