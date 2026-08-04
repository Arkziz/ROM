from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.simulation.balance_analyzer import (
    AnalysisConfig,
    CLASSES,
    PROFILES,
    build_balance_report,
    build_execution_plan,
    execute_plan,
    inspect_execution_plan,
)
from systems.simulation.progression_wall_analyzer import build_progression_wall_report


def parse_csv(value, allowed):
    if value == "all":
        return tuple(allowed)
    result = tuple(item.strip() for item in value.split(",") if item.strip())
    if any(item not in allowed for item in result):
        raise argparse.ArgumentTypeError(f"invalid value: {value}")
    return result


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_balance_md(path, data):
    config = data["config"]
    execution = data.get("execution", {})
    lines = [
        "# PvE Balance Analysis 13.7.1",
        "",
        f"- Target level: **{config['target_level']}**",
        f"- Profiles: **{', '.join(config['profiles'])}**",
        f"- Seeds: **{len(config['seeds'])}**",
        f"- Main result runs: **{data['run_count']}**",
        f"- Unique scenarios executed/planned: **{execution.get('unique_scenarios', 0)}**",
        f"- Cache hits: **{execution.get('cache_hits', 0)}**",
        f"- Fresh runs: **{execution.get('fresh_runs', 0)}**",
        f"- Workers: **{execution.get('workers', 1)}**",
        f"- Inventory: **{config['inventory_capacity']}**",
        "",
        "## Class results",
        "",
        "| Class | Profile | Runs | Win rate | Death rate | Mean battles | Mean days | EXP/hour | Gold/hour | Lost items |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for character_class, profiles in data["groups"].items():
        for profile, item in profiles.items():
            lines.append(
                f"| {character_class} | {profile} | {item['runs']} | "
                f"{item['win_rate']:.2%} | {item['death_rate']:.2%} | "
                f"{item['mean_battles']:.2f} | {item['mean_days']:.2f} | "
                f"{item['exp_per_elapsed_hour']:.2f} | {item['gold_per_elapsed_hour']:.2f} | "
                f"{item['mean_items_lost']:.2f} |"
            )
    if data.get("inventory_comparison"):
        lines.extend(
            [
                "",
                "## Inventory 40 vs 60",
                "",
                "| Slots | Full bag events | Lost items | City visits | Mean final gold |",
                "|---:|---:|---:|---:|---:|",
            ]
        )
        for slots, item in data["inventory_comparison"].items():
            lines.append(
                f"| {slots} | {item['mean_full_bag_events']:.2f} | "
                f"{item['mean_items_lost']:.2f} | {item['mean_city_visits']:.2f} | "
                f"{item['mean_final_gold']:.2f} |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_walls_md(path, data):
    lines = [
        "# Progression Wall Analysis 13.7.1",
        "",
        f"- Target level: **{data['target_level']}**",
        f"- Findings: **{len(data['findings'])}**",
        "",
        "## Findings",
    ]
    if not data["findings"]:
        lines.append("- No configured wall threshold was exceeded.")
    for finding in data["findings"]:
        lines.append(
            f"- [{finding['severity']}] {finding['class']} / {finding['profile']} / "
            f"{finding['from_level']}→{finding['to_level']}: "
            f"{'; '.join(finding['reasons'])}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_checkpoint(path, config, plan_summary, execution=None, status="planned"):
    payload = {
        "schema": "rom.simulation.pve_analysis_checkpoint.v1",
        "version": "13.7.1",
        "status": status,
        "config": {
            "target_level": config.target_level,
            "profiles": list(config.profiles),
            "classes": list(config.classes),
            "seeds": list(config.seeds),
            "inventory_capacity": config.inventory_capacity,
            "compare_inventory": config.compare_inventory,
        },
        "plan": plan_summary,
        "execution": execution or {},
    }
    write_json(path, payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-level", type=int, default=5)
    parser.add_argument("--profiles", default="regular")
    parser.add_argument("--classes", default="all")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=137000)
    parser.add_argument("--inventory", type=int, default=40, choices=(40, 60))
    parser.add_argument("--compare-inventory", action="store_true")
    parser.add_argument("--skip-walls", action="store_true")
    parser.add_argument("--skip-inventory-comparison", action="store_true")
    parser.add_argument("--workers", type=int, default=max(1, min((os.cpu_count() or 2) - 1, 4)))
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output", default="MD")
    args = parser.parse_args()

    if args.seeds < 1:
        parser.error("--seeds must be at least 1")
    if not 1 <= args.workers <= 8:
        parser.error("--workers must be between 1 and 8")

    profiles = parse_csv(args.profiles, PROFILES)
    classes = parse_csv(args.classes, CLASSES)
    seeds = tuple(range(args.seed_start, args.seed_start + args.seeds))
    compare_inventory = args.compare_inventory and not args.skip_inventory_comparison
    config = AnalysisConfig(
        args.target_level,
        profiles,
        classes,
        seeds,
        args.inventory,
        compare_inventory,
    )
    plan = build_execution_plan(
        config,
        include_walls=not args.skip_walls,
        include_inventory=compare_inventory,
    )
    summary = inspect_execution_plan(ROOT, plan, force=args.force)
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    tag = f"l{args.target_level}_{'-'.join(profiles)}_{args.seeds}s"
    checkpoint = output / f"SIMULATION_PVE_ANALYSIS_CHECKPOINT_13_7_1_{tag}.json"
    write_checkpoint(checkpoint, config, summary)

    print("[PLAN] PvE balance analysis")
    print(f"- unique scenarios: {summary['unique_scenarios']}")
    print(f"- cache hits: {summary['cache_hits']}")
    print(f"- new simulations required: {summary['new_simulations']}")
    print(f"- workers: {args.workers}")
    print(f"- walls: {'NO' if args.skip_walls else 'YES'}")
    print(f"- inventory comparison: {'YES' if compare_inventory else 'NO'}")
    print(f"- checkpoint: {checkpoint.relative_to(ROOT)}")
    if args.plan_only:
        print("[OK] Plan-only mode completed; simulations were not started.")
        return

    def progress(done, total, spec, source, elapsed, eta):
        if done == total or done == 1 or done % max(1, total // 20) == 0:
            print(
                f"[progress] {done}/{total} {spec.character_class}/{spec.profile}/"
                f"L{spec.target_level}/slots={spec.inventory_capacity}/seed={spec.seed} "
                f"({source}) elapsed={elapsed:.1f}s eta={eta:.1f}s"
            )

    try:
        payloads, execution = execute_plan(
            ROOT,
            plan,
            workers=args.workers,
            force=args.force,
            progress=progress,
        )
    except RuntimeError as error:
        write_checkpoint(checkpoint, config, inspect_execution_plan(ROOT, plan), status="interrupted")
        print(f"[STOPPED] {error}")
        raise SystemExit(130)

    balance = build_balance_report(config, payloads, execution, include_inventory=compare_inventory)
    walls = None if args.skip_walls else build_progression_wall_report(config, payloads)

    balance_json = output / f"SIMULATION_PVE_BALANCE_13_7_1_{tag}.json"
    balance_md = output / f"SIMULATION_PVE_BALANCE_13_7_1_{tag}.md"
    write_json(balance_json, balance)
    write_balance_md(balance_md, balance)

    walls_json = walls_md = None
    if walls is not None:
        walls_json = output / f"SIMULATION_PROGRESSION_WALLS_13_7_1_{tag}.json"
        walls_md = output / f"SIMULATION_PROGRESSION_WALLS_13_7_1_{tag}.md"
        write_json(walls_json, walls)
        write_walls_md(walls_md, walls)

    write_checkpoint(checkpoint, config, summary, execution, status="completed")
    print("[OK] PvE balance and progression analysis 13.7.1")
    print(f"- unique scenarios: {execution['unique_scenarios']}")
    print(f"- cache hits: {execution['cache_hits']}")
    print(f"- fresh runs: {execution['fresh_runs']}")
    print(f"- workers: {execution['workers']}")
    print(f"- elapsed seconds: {execution['elapsed_seconds']}")
    print(f"- wall findings: {0 if walls is None else len(walls['findings'])}")
    print(f"- balance JSON: {balance_json.relative_to(ROOT)}")
    print(f"- balance Markdown: {balance_md.relative_to(ROOT)}")
    if walls_json:
        print(f"- walls JSON: {walls_json.relative_to(ROOT)}")
        print(f"- walls Markdown: {walls_md.relative_to(ROOT)}")
    print(f"- checkpoint: {checkpoint.relative_to(ROOT)}")
    print("- database writes: 0")


if __name__ == "__main__":
    main()
