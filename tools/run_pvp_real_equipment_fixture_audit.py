from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_real_actor_state_replay import format_summary,run_replay,save_report
p=argparse.ArgumentParser(); p.add_argument("--trials",type=int,default=100); p.add_argument("--seed",type=int,default=14631); a=p.parse_args()
result=run_replay(a.trials,a.seed); path=save_report(result,ROOT/"tools"/"pvp_real_actor_state_dominance_replay_report.json")
print(format_summary(result)); print(f"JSON: {path.relative_to(ROOT)}")
