from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_knight_judgement_terminal_audit import format_summary,run_audit,save_report
p=argparse.ArgumentParser(); p.add_argument("--trials",type=int,default=100); p.add_argument("--seed",type=int,default=14633); a=p.parse_args()
r=run_audit(a.trials,a.seed); path=save_report(r,ROOT/"tools"/"pvp_knight_judgement_terminal_audit_report.json"); print(format_summary(r)); print(f"JSON: {path.relative_to(ROOT)}")
