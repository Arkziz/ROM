from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.simulation.guild_population import simulate_guild_population
from systems.simulation.population_cache import load_progression_cache
from systems.simulation.population_reporting import atomic_json, guild_markdown


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-level", type=int, default=3)
    parser.add_argument("--inventory", type=int, choices=(40, 60), default=40)
    parser.add_argument("--players", default="10,50,100,500,1000")
    args = parser.parse_args()
    populations = [int(item.strip()) for item in args.players.split(",") if item.strip()]
    rows = load_progression_cache(ROOT, args.target_level, args.inventory)
    if not rows:
        raise SystemExit("No cached progression payloads match the requested parameters")
    values = [simulate_guild_population(rows, players).to_dict() for players in populations]
    report = {
        "schema": "rom.simulation.guild_population.v1",
        "version": "13.8.0",
        "target_level": args.target_level,
        "inventory_capacity": args.inventory,
        "source_runs": len(rows),
        "populations": values,
        "database_writes": 0,
    }
    base = ROOT / "MD" / f"SIMULATION_GUILD_POPULATION_13_8_0_l{args.target_level}_{args.inventory}slots"
    atomic_json(base.with_suffix(".json"), report)
    base.with_suffix(".md").write_text(guild_markdown(report), encoding="utf-8")
    print("[OK] Guild population simulation 13.8.0")
    print(f"- cached source runs: {len(rows)}")
    print(f"- populations: {','.join(map(str, populations))}")
    print(f"- JSON: {base.with_suffix('.json').relative_to(ROOT)}")
    print(f"- Markdown: {base.with_suffix('.md').relative_to(ROOT)}")
    print("- database writes: 0")


if __name__ == "__main__":
    main()
