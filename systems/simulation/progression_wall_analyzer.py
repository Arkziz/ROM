from __future__ import annotations

from .balance_analyzer import (
    AnalysisConfig,
    ScenarioSpec,
    aggregate_group,
    build_execution_plan,
    execute_plan,
)

DELTA_FIELDS = (
    "mean_battles",
    "mean_elapsed_hours",
    "mean_deaths",
    "mean_city_visits",
    "mean_items_awarded",
    "mean_items_lost",
    "mean_final_gold",
    "mean_total_net_worth",
)


def _delta(current, previous):
    return {
        field: round(float(current.get(field, 0.0)) - float(previous.get(field, 0.0)), 6)
        for field in DELTA_FIELDS
    }


def _percentage_change(current, previous):
    if previous <= 0:
        return None
    return (current - previous) / previous * 100.0


def build_progression_wall_report(config, payloads):
    levels = []
    for target_level in range(2, config.target_level + 1):
        groups = {}
        for character_class in config.classes:
            groups[character_class] = {}
            for profile in config.profiles:
                specs = [
                    ScenarioSpec(
                        character_class,
                        profile,
                        int(seed),
                        target_level,
                        config.inventory_capacity,
                        config.max_days,
                    )
                    for seed in config.seeds
                ]
                groups[character_class][profile] = aggregate_group([payloads[spec] for spec in specs])
        levels.append({"target_level": target_level, "groups": groups})

    transitions = []
    findings = []
    for character_class in config.classes:
        for profile in config.profiles:
            cumulative_previous = {field: 0.0 for field in DELTA_FIELDS}
            previous_transition = None
            for level_item in levels:
                current = level_item["groups"][character_class][profile]
                transition = _delta(current, cumulative_previous)
                entry = {
                    "class": character_class,
                    "profile": profile,
                    "from_level": level_item["target_level"] - 1,
                    "to_level": level_item["target_level"],
                    "incremental": transition,
                    "cumulative": {field: current.get(field, 0.0) for field in DELTA_FIELDS},
                }
                transitions.append(entry)

                if previous_transition is not None:
                    reasons = []
                    death_pp = transition["mean_deaths"] - previous_transition["mean_deaths"]
                    battle_change = _percentage_change(
                        transition["mean_battles"], previous_transition["mean_battles"]
                    )
                    city_change = transition["mean_city_visits"] - previous_transition["mean_city_visits"]
                    elapsed_change = _percentage_change(
                        transition["mean_elapsed_hours"], previous_transition["mean_elapsed_hours"]
                    )
                    if death_pp >= 0.05:
                        reasons.append(f"incremental deaths +{death_pp:.2f}")
                    if battle_change is not None and battle_change >= 25:
                        reasons.append(f"incremental battles +{battle_change:.1f}%")
                    if elapsed_change is not None and elapsed_change >= 25:
                        reasons.append(f"incremental elapsed time +{elapsed_change:.1f}%")
                    if city_change >= 2:
                        reasons.append(f"incremental city visits +{city_change:.2f}")
                    if reasons:
                        findings.append(
                            {
                                "severity": "REVIEW",
                                "code": "progression_wall",
                                "class": character_class,
                                "profile": profile,
                                "from_level": entry["from_level"],
                                "to_level": entry["to_level"],
                                "reasons": reasons,
                                "current_transition": transition,
                                "previous_transition": previous_transition,
                            }
                        )
                previous_transition = transition
                cumulative_previous = current

    return {
        "schema": "rom.simulation.progression_walls.v2",
        "version": "13.7.2",
        "methodology": "incremental transition deltas, not cumulative totals",
        "target_level": config.target_level,
        "levels": levels,
        "transitions": transitions,
        "findings": findings,
        "database_writes": 0,
    }


class ProgressionWallAnalyzer:
    def __init__(self, root, config: AnalysisConfig, force=False, workers=1):
        self.root = root
        self.config = config.validate()
        self.force = force
        self.workers = workers

    def execute(self, progress=None):
        plan = build_execution_plan(self.config, include_walls=True, include_inventory=False)
        payloads, _execution = execute_plan(
            self.root,
            plan,
            workers=self.workers,
            force=self.force,
            progress=progress,
        )
        return build_progression_wall_report(self.config, payloads)
