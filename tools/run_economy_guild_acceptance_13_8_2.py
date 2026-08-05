from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.simulation.economy_guild_acceptance import run_acceptance


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _markdown(report: dict) -> str:
    forty = report["inventory"]["40"]
    sixty = report["inventory"]["60"]
    delta = report["inventory_60_minus_40"]
    lines = [
        "# Economy and Guild Acceptance 13.8.2",
        "",
        f"- Verdict: **{report['verdict']}**",
        f"- Guild member limit: **{report['guild_member_limit']}**",
        f"- Scenario count: **{report['scenario_count']}**",
        "",
        "## Inventory 40 vs 60",
        "",
        f"- Mean total net worth, 40 slots: {forty['mean_total_net_worth']}",
        f"- Mean total net worth, 60 slots: {sixty['mean_total_net_worth']}",
        f"- Delta 60-40: {delta['mean_total_net_worth']}",
        f"- Mean city visits, 40 slots: {forty['mean_city_visits']}",
        f"- Mean city visits, 60 slots: {sixty['mean_city_visits']}",
        f"- Mean items lost, 40 slots: {forty['mean_items_lost']}",
        f"- Mean items lost, 60 slots: {sixty['mean_items_lost']}",
        "",
        "## Guild populations",
        "",
    ]
    for row in report["guild_populations"]:
        lines.append(f"- {row['players']} players: mode={row['mode']}, guild EXP={row['guild_exp']}, kills={row['kills']}, contracts={row['contracts']}")
    if report["failures"]:
        lines.extend(["", "## Failures", ""] + [f"- {item}" for item in report["failures"]])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-level", type=int, default=2)
    parser.add_argument("--profile", choices=("casual", "regular", "hardcore"), default="regular")
    parser.add_argument("--seed", type=int, default=138200)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    report = run_acceptance(ROOT, args.target_level, args.profile, args.seed, args.force)
    audit_json = ROOT / "MD" / "SIMULATION_ECONOMY_GUILD_ACCEPTANCE_13_8_2.json"
    audit_md = ROOT / "MD" / "SIMULATION_ECONOMY_GUILD_ACCEPTANCE_13_8_2.md"
    comparison_json = ROOT / "MD" / "SIMULATION_INVENTORY_40_60_COMPARISON_13_8_2.json"
    comparison_md = ROOT / "MD" / "SIMULATION_INVENTORY_40_60_COMPARISON_13_8_2.md"
    _write(audit_json, json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    _write(audit_md, _markdown(report))
    comparison = {
        "version": report["version"],
        "target_level": report["target_level"],
        "profile": report["profile"],
        "inventory": report["inventory"],
        "inventory_60_minus_40": report["inventory_60_minus_40"],
        "asset_coverage": {"40": report["inventory"]["40"]["asset_coverage"], "60": report["inventory"]["60"]["asset_coverage"]},
        "database_writes": 0,
    }
    _write(comparison_json, json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    _write(comparison_md, _markdown(report))
    print("[OK] Economy/guild acceptance and inventory 40/60 report")
    print(f"- verdict: {report['verdict']}")
    print(f"- scenarios: {report['scenario_count']}")
    print(f"- guild populations: {','.join(str(x['players']) for x in report['guild_populations'])}")
    print(f"- guild member limit: {report['guild_member_limit']}")
    print(f"- asset coverage 40: {report['inventory']['40']['asset_coverage']}")
    print(f"- asset coverage 60: {report['inventory']['60']['asset_coverage']}")
    print(f"- JSON: {audit_json.relative_to(ROOT)}")
    print(f"- comparison JSON: {comparison_json.relative_to(ROOT)}")
    print("- database writes: 0")
    if report["verdict"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
