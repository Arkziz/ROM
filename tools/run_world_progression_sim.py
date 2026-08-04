from __future__ import annotations
from pathlib import Path
import sys

# Direct execution with `python tools/run_world_progression_sim.py` places the
# tools directory, not the ROM root, at sys.path[0]. Add the project root before
# importing the systems package. This is local to this CLI process.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from pathlib import Path
from systems.simulation.progression_reporting import write_progression_report
from systems.simulation.world_progression import WorldProgressionSimulator

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("character_class")
    parser.add_argument("target_level",type=int)
    parser.add_argument("profile",choices=("casual","regular","hardcore"))
    parser.add_argument("--seed",type=int,default=136000)
    parser.add_argument("--inventory",type=int,choices=(40,60),default=40)
    parser.add_argument("--output",default="simulation_reports")
    args=parser.parse_args()
    result=WorldProgressionSimulator(Path.cwd(),args.character_class,args.target_level,args.profile,args.seed,args.inventory).run()
    json_path,md_path=write_progression_report(result,Path(args.output))
    print("[OK] World progression simulation")
    print(f"- status: {result.status}")
    print(f"- level: {result.final_level}/{result.target_level}")
    print(f"- days: {result.days}")
    print(f"- battles: {result.battles}; wins: {result.wins}; deaths: {result.deaths}")
    print(f"- JSON: {json_path}")
    print(f"- Markdown: {md_path}")
    if result.status != "completed": raise SystemExit(2)
if __name__=="__main__":main()
