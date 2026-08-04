from __future__ import annotations

import hashlib
import json
import os
import statistics
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from .world_progression import WorldProgressionSimulator
from .asset_valuation import value_progression_assets

CLASSES = ("warrior", "knight", "scout", "rogue", "mage", "priest")
PROFILES = ("casual", "regular", "hardcore")
CACHE_SCHEMA = "pve_balance_v1"


def _stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _mean(values):
    return round(statistics.fmean(values), 6) if values else 0.0


def _percentile(values, percentile):
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * float(percentile)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return round(ordered[low] * (1 - fraction) + ordered[high] * fraction, 6)


@dataclass(frozen=True, order=True)
class ScenarioSpec:
    character_class: str
    profile: str
    seed: int
    target_level: int
    inventory_capacity: int
    max_days: int = 365


@dataclass(frozen=True)
class AnalysisConfig:
    target_level: int = 5
    profiles: tuple = ("regular",)
    classes: tuple = CLASSES
    seeds: tuple = tuple(range(137000, 137010))
    inventory_capacity: int = 40
    compare_inventory: bool = False
    max_days: int = 365

    def validate(self):
        if not 2 <= int(self.target_level) <= 10:
            raise ValueError("target_level must be 2..10 for current production content")
        if not self.classes or any(value not in CLASSES for value in self.classes):
            raise ValueError("invalid classes")
        if not self.profiles or any(value not in PROFILES for value in self.profiles):
            raise ValueError("invalid profiles")
        if not self.seeds:
            raise ValueError("at least one seed is required")
        if self.inventory_capacity not in (40, 60):
            raise ValueError("inventory_capacity must be 40 or 60")
        return self

    def fingerprint(self):
        return hashlib.sha256(_stable(asdict(self)).encode()).hexdigest()


class ResultCache:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.directory = self.root / "simulation_reports" / "cache" / CACHE_SCHEMA
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key_for(spec: ScenarioSpec):
        value = (
            f"{spec.character_class}|{spec.profile}|{spec.seed}|"
            f"{spec.target_level}|{spec.inventory_capacity}|{spec.max_days}"
        )
        return hashlib.sha256(value.encode()).hexdigest()

    def path_for(self, spec: ScenarioSpec):
        return self.directory / f"{self.key_for(spec)}.json"

    def exists(self, spec: ScenarioSpec):
        return self.path_for(spec).exists()

    def load(self, spec: ScenarioSpec):
        return json.loads(self.path_for(spec).read_text(encoding="utf-8"))

    def save(self, spec: ScenarioSpec, payload):
        path = self.path_for(spec)
        temporary = path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(_stable(payload), encoding="utf-8")
        temporary.replace(path)
        return path


def _execute_scenario_worker(root_text: str, spec_payload: dict):
    root = Path(root_text)
    spec = ScenarioSpec(**spec_payload)
    cache = ResultCache(root)
    result = WorldProgressionSimulator(
        root,
        spec.character_class,
        spec.target_level,
        spec.profile,
        spec.seed,
        inventory_capacity=spec.inventory_capacity,
        max_days=spec.max_days,
    ).run()
    payload = asdict(result)
    cache.save(spec, payload)
    return spec_payload


def build_execution_plan(config: AnalysisConfig, include_walls=True, include_inventory=None):
    config = config.validate()
    include_inventory = config.compare_inventory if include_inventory is None else bool(include_inventory)
    plan = set()

    def add_level(target_level, capacity):
        for character_class in config.classes:
            for profile in config.profiles:
                for seed in config.seeds:
                    plan.add(
                        ScenarioSpec(
                            character_class,
                            profile,
                            int(seed),
                            int(target_level),
                            int(capacity),
                            int(config.max_days),
                        )
                    )

    add_level(config.target_level, config.inventory_capacity)
    if include_walls:
        for target_level in range(2, config.target_level + 1):
            add_level(target_level, config.inventory_capacity)
    if include_inventory:
        add_level(config.target_level, 40)
        add_level(config.target_level, 60)
    return tuple(sorted(plan))


def inspect_execution_plan(root: Path, plan: Sequence[ScenarioSpec], force=False):
    cache = ResultCache(root)
    cached = 0 if force else sum(cache.exists(spec) for spec in plan)
    return {
        "unique_scenarios": len(plan),
        "cache_hits": cached,
        "new_simulations": len(plan) - cached,
    }


def execute_plan(root: Path, plan: Sequence[ScenarioSpec], workers=1, force=False, progress=None):
    root = Path(root)
    cache = ResultCache(root)
    workers = max(1, min(int(workers), 8))
    cached_specs = [] if force else [spec for spec in plan if cache.exists(spec)]
    pending = list(plan) if force else [spec for spec in plan if not cache.exists(spec)]
    total = len(plan)
    completed = len(cached_specs)
    started_at = time.monotonic()

    def notify(spec, source):
        nonlocal completed
        completed += 1
        elapsed = max(time.monotonic() - started_at, 0.001)
        fresh_done = max(completed - len(cached_specs), 0)
        fresh_total = len(pending)
        eta = 0.0
        if fresh_done and fresh_total > fresh_done:
            eta = elapsed / fresh_done * (fresh_total - fresh_done)
        if progress:
            progress(completed, total, spec, source, elapsed, eta)

    if progress and cached_specs:
        progress(completed, total, cached_specs[-1], "cache", 0.0, 0.0)

    try:
        if workers == 1:
            for spec in pending:
                _execute_scenario_worker(str(root), asdict(spec))
                notify(spec, "run")
        else:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(_execute_scenario_worker, str(root), asdict(spec)): spec
                    for spec in pending
                }
                for future in as_completed(futures):
                    spec = futures[future]
                    future.result()
                    notify(spec, "run")
    except KeyboardInterrupt:
        raise RuntimeError(
            "Analysis interrupted. Completed scenarios are checkpointed in the cache; "
            "rerun the same command to resume."
        )

    payloads = {spec: cache.load(spec) for spec in plan}
    return payloads, {
        "unique_scenarios": total,
        "cache_hits": len(cached_specs),
        "fresh_runs": len(pending),
        "workers": workers,
        "elapsed_seconds": round(time.monotonic() - started_at, 3),
    }


def _event_counts(payload):
    counts = {}
    for event in payload.get("events", []):
        counts[event["event_type"]] = counts.get(event["event_type"], 0) + 1
    return counts


def aggregate_group(rows):
    runs = len(rows)
    battles = sum(item["battles"] for item in rows)
    wins = sum(item["wins"] for item in rows)
    deaths = sum(item["deaths"] for item in rows)
    minutes = sum(item["elapsed_minutes"] for item in rows)
    hours = minutes / 60.0
    events = {}
    valuations = [value_progression_assets(item) for item in rows]
    for item in rows:
        for key, value in _event_counts(item).items():
            events[key] = events.get(key, 0) + value
    coverage_counts = {}
    for valuation in valuations:
        coverage_counts[valuation.coverage] = coverage_counts.get(valuation.coverage, 0) + 1
    return {
        "runs": runs,
        "completed_runs": sum(item["status"] == "completed" for item in rows),
        "mean_days": _mean([item["days"] for item in rows]),
        "mean_battles": _mean([item["battles"] for item in rows]),
        "mean_deaths": _mean([item["deaths"] for item in rows]),
        "win_rate": round(wins / battles, 6) if battles else 0.0,
        "death_rate": round(deaths / battles, 6) if battles else 0.0,
        "mean_elapsed_hours": _mean([item["elapsed_minutes"] / 60 for item in rows]),
        "battles_per_elapsed_hour": round(battles / hours, 6) if hours else 0.0,
        "exp_per_elapsed_hour": round(sum(item["exp_gained"] for item in rows) / hours, 6) if hours else 0.0,
        "gold_per_elapsed_hour": round(sum(item["gold_gained"] for item in rows) / hours, 6) if hours else 0.0,
        "mean_final_gold": _mean([item["final_gold"] for item in rows]),
        "mean_total_net_worth": _mean([item.total_net_worth for item in valuations]),
        "mean_inventory_liquidation_value": _mean([item.inventory_liquidation_value for item in valuations]),
        "mean_equipped_item_value": _mean([item.equipped_item_value for item in valuations]),
        "mean_consumable_value": _mean([item.consumable_value for item in valuations]),
        "mean_resource_value": _mean([item.resource_value for item in valuations]),
        "asset_valuation_coverage": dict(sorted(coverage_counts.items())),
        "mean_city_visits": _mean([item["city_visits"] for item in rows]),
        "mean_full_bag_events": _mean([item["full_bag_events"] for item in rows]),
        "mean_items_awarded": _mean([item["items_awarded"] for item in rows]),
        "mean_items_lost": _mean([item["items_lost"] for item in rows]),
        "p50_battles": _percentile([item["battles"] for item in rows], 0.5),
        "p90_battles": _percentile([item["battles"] for item in rows], 0.9),
        "p90_deaths": _percentile([item["deaths"] for item in rows], 0.9),
        "event_counts": dict(sorted(events.items())),
        "totals": {
            "battles": battles,
            "wins": wins,
            "deaths": deaths,
            "city_visits": sum(item["city_visits"] for item in rows),
            "full_bag_events": sum(item["full_bag_events"] for item in rows),
            "items_awarded": sum(item["items_awarded"] for item in rows),
            "items_lost": sum(item["items_lost"] for item in rows),
        },
    }



def _rows_for(payloads, config, target_level, capacity):
    rows = []
    for character_class in config.classes:
        for profile in config.profiles:
            for seed in config.seeds:
                spec = ScenarioSpec(
                    character_class,
                    profile,
                    int(seed),
                    int(target_level),
                    int(capacity),
                    int(config.max_days),
                )
                rows.append(payloads[spec])
    return rows


def build_balance_report(config, payloads, execution, include_inventory=None):
    include_inventory = config.compare_inventory if include_inventory is None else bool(include_inventory)
    groups = {}
    for character_class in config.classes:
        groups[character_class] = {}
        for profile in config.profiles:
            specs = [
                ScenarioSpec(character_class, profile, int(seed), config.target_level, config.inventory_capacity, config.max_days)
                for seed in config.seeds
            ]
            groups[character_class][profile] = aggregate_group([payloads[spec] for spec in specs])
    inventory_comparison = None
    if include_inventory:
        inventory_comparison = {
            str(capacity): aggregate_group(_rows_for(payloads, config, config.target_level, capacity))
            for capacity in (40, 60)
        }
    return {
        "schema": "rom.simulation.pve_balance.v1",
        "version": "13.7.2",
        "config": asdict(config),
        "config_fingerprint": config.fingerprint(),
        "run_count": len(config.classes) * len(config.profiles) * len(config.seeds),
        "cache_hits": execution["cache_hits"],
        "execution": execution,
        "groups": groups,
        "inventory_comparison": inventory_comparison,
        "database_writes": 0,
    }


class PveBalanceAnalyzer:
    def __init__(self, root: Path, config: AnalysisConfig, force=False, workers=1):
        self.root = Path(root)
        self.config = config.validate()
        self.force = force
        self.workers = workers

    def execute(self, progress=None):
        plan = build_execution_plan(
            self.config,
            include_walls=False,
            include_inventory=self.config.compare_inventory,
        )
        payloads, execution = execute_plan(
            self.root,
            plan,
            workers=self.workers,
            force=self.force,
            progress=progress,
        )
        return build_balance_report(self.config, payloads, execution)
