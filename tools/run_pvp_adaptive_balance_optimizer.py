from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_adaptive_balance_optimizer import format_summary,run_optimizer
p=argparse.ArgumentParser(); p.add_argument("--minutes",type=float,default=20); p.add_argument("--seed",type=int,default=14644); p.add_argument("--fresh",action="store_true"); a=p.parse_args()
checkpoint=ROOT/"tools"/"pvp_adaptive_balance_optimizer_checkpoint.json"; report=ROOT/"tools"/"pvp_adaptive_balance_optimizer_report.json"
if a.fresh and checkpoint.exists(): checkpoint.unlink()
r=run_optimizer(a.minutes,a.seed,checkpoint,report,False); print(format_summary(r)); print(f"JSON: {report.relative_to(ROOT)}"); print(f"Checkpoint: {checkpoint.relative_to(ROOT)}")
