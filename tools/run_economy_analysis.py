from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.simulation.economy_analyzer import analyze_economy
from systems.simulation.population_cache import load_progression_cache
from systems.simulation.population_reporting import atomic_json, economy_markdown


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-level", type=int, default=3)
    parser.add_argument("--inventory", type=int, choices=(40, 60), default=40)
    args = parser.parse_args()
    rows = load_progression_cache(ROOT, args.target_level, args.inventory)
    if not rows:
        raise SystemExit("No cached progression payloads match the requested parameters")
    economy = analyze_economy(rows).to_dict()
    report = {
        "schema": "rom.simulation.economy.v1",
        "version": "13.8.0",
        "target_level": args.target_level,
        "inventory_capacity": args.inventory,
        "economy": economy,
        "database_writes": 0,
    }
    base = ROOT / "MD" / f"SIMULATION_ECONOMY_13_8_0_l{args.target_level}_{args.inventory}slots"
    atomic_json(base.with_suffix(".json"), report)
    base.with_suffix(".md").write_text(economy_markdown(report), encoding="utf-8")
    print("[OK] Economy analysis 13.8.0")
    print(f"- cached runs: {len(rows)}")
    print(f"- gold faucets: {economy['gold_faucets']}")
    print(f"- gold sinks: {economy['gold_sinks']}")
    print(f"- net gold created: {economy['net_gold_created']}")
    print(f"- asset coverage: {economy['asset_coverage']}")
    print(f"- JSON: {base.with_suffix('.json').relative_to(ROOT)}")
    print(f"- Markdown: {base.with_suffix('.md').relative_to(ROOT)}")
    print("- database writes: 0")


if __name__ == "__main__":
    main()
