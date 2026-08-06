from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from systems.simulation.patch_regression import RegressionConfig, analyze_payloads, compare_reports, create_baseline, load_baseline, run_matrix, write_json_atomic


def csv_tuple(value): return tuple(part.strip() for part in str(value).split(",") if part.strip())
def int_tuple(value): return tuple(int(part.strip()) for part in str(value).split(",") if part.strip())

def main():
    parser = argparse.ArgumentParser(description="ROM RNG percentiles and patch regression analyzer")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--create-baseline", action="store_true")
    mode.add_argument("--compare-baseline", action="store_true")
    mode.add_argument("--replace-baseline", action="store_true")
    parser.add_argument("--baseline-name", default="stage_13_current")
    parser.add_argument("--target-level", type=int, default=2)
    parser.add_argument("--profiles", default="regular")
    parser.add_argument("--classes", default="warrior,knight,scout,rogue,mage,priest")
    parser.add_argument("--seed-start", type=int, default=139000)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--inventory", default="40,60")
    parser.add_argument("--max-days", type=int, default=365)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = RegressionConfig(target_level=args.target_level, profiles=csv_tuple(args.profiles), classes=csv_tuple(args.classes), seed_start=args.seed_start, seed_count=args.seeds, capacities=int_tuple(args.inventory), max_days=args.max_days)
    def progress(done,total,cls,profile,seed,capacity):
        if done == 1 or done == total or done % max(1,total//10) == 0: print(f"[progress] {done}/{total} {cls}/{profile}/seed={seed}/slots={capacity}")
    payloads = run_matrix(ROOT, config, force=args.force, progress=progress)
    current = analyze_payloads(ROOT, payloads, config)
    current_path = ROOT / "MD" / f"SIMULATION_RNG_CURRENT_13_9_0_{args.baseline_name}.json"
    write_json_atomic(current_path, current)
    replace = bool(args.replace_baseline)
    if args.create_baseline or replace:
        path = create_baseline(ROOT, args.baseline_name, current, replace=replace)
        print("[OK] RNG baseline created" if not replace else "[OK] RNG baseline replaced")
        print(f"- verdict: {current['verdict']}")
        print(f"- scenarios: {current['scenario_count']}")
        print(f"- baseline: {path.relative_to(ROOT)}")
    else:
        baseline = load_baseline(ROOT, args.baseline_name); diff = compare_reports(baseline, current)
        diff_path = ROOT / "MD" / f"SIMULATION_PATCH_REGRESSION_DIFF_13_9_0_{args.baseline_name}.json"; write_json_atomic(diff_path, diff)
        print("[OK] Patch regression comparison")
        print(f"- verdict: {diff['verdict']}")
        print(f"- comparisons: {len(diff['comparisons'])}")
        print(f"- findings: {len(diff['findings'])}; failures: {len(diff['failures'])}")
        print(f"- diff: {diff_path.relative_to(ROOT)}")
    print(f"- current: {current_path.relative_to(ROOT)}")
    print("- database writes: 0")

if __name__ == "__main__": main()
