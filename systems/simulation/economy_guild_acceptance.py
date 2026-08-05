from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping

from .economic_ledger import EconomicScenarioSpec
from .economic_progression import run_economic_progression
from .guild_population import MAX_GUILD_MEMBERS, simulate_guild_population

SCHEMA_VERSION = "rom.simulation.economy_guild_acceptance.v1"
DEFAULT_CLASSES = ("warrior", "mage")
DEFAULT_CAPACITIES = (40, 60)
DEFAULT_POPULATIONS = (10, 25, 50)


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _pair_key(payload: Mapping[str, Any]) -> tuple[str, int]:
    scenario = payload.get("scenario", {}) if isinstance(payload.get("scenario"), Mapping) else {}
    return str(scenario.get("character_class", "")), int(scenario.get("seed", 0) or 0)


def _capacity(payload: Mapping[str, Any]) -> int:
    scenario = payload.get("scenario", {}) if isinstance(payload.get("scenario"), Mapping) else {}
    return int(scenario.get("inventory_capacity", payload.get("final_asset_snapshot", {}).get("inventory_capacity", 0)) or 0)


def _run_payloads(root: Path, target_level: int, profile: str, seed: int, classes: Iterable[str], force: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for class_index, character_class in enumerate(classes):
        scenario_seed = int(seed) + class_index
        for capacity in DEFAULT_CAPACITIES:
            spec = EconomicScenarioSpec(character_class, profile, scenario_seed, target_level, capacity)
            rows.append(run_economic_progression(root, spec, force=force))
    return rows


def _aggregate_capacity(rows: list[Mapping[str, Any]], capacity: int) -> dict[str, Any]:
    selected = [row for row in rows if _capacity(row) == capacity]
    if not selected:
        raise ValueError(f"no economic v2 payloads for inventory capacity {capacity}")
    if any(row.get("asset_valuation", {}).get("coverage") != "FULL" for row in selected):
        raise ValueError(f"asset valuation coverage is not FULL for capacity {capacity}")
    if any(not row.get("economic_reconciliation", {}).get("passed") for row in selected):
        raise ValueError(f"economic reconciliation failed for capacity {capacity}")
    return {
        "inventory_capacity": capacity,
        "runs": len(selected),
        "mean_final_cash": round(mean(_num(row.get("final_gold")) for row in selected), 6),
        "mean_total_net_worth": round(mean(_num(row.get("asset_valuation", {}).get("total_net_worth")) for row in selected), 6),
        "mean_inventory_value": round(mean(_num(row.get("asset_valuation", {}).get("inventory_liquidation_value")) for row in selected), 6),
        "mean_equipped_value": round(mean(_num(row.get("asset_valuation", {}).get("equipped_item_value")) for row in selected), 6),
        "mean_consumable_value": round(mean(_num(row.get("asset_valuation", {}).get("consumable_value")) for row in selected), 6),
        "mean_resource_value": round(mean(_num(row.get("asset_valuation", {}).get("resource_value")) for row in selected), 6),
        "mean_city_visits": round(mean(_num(row.get("city_visits")) for row in selected), 6),
        "mean_full_bag_events": round(mean(_num(row.get("full_bag_events")) for row in selected), 6),
        "mean_items_lost": round(mean(_num(row.get("items_lost")) for row in selected), 6),
        "mean_free_slots": round(mean(_num(row.get("final_asset_snapshot", {}).get("free_slots")) for row in selected), 6),
        "gold_faucets": round(sum(_num(row.get("economic_reconciliation", {}).get("faucets")) for row in selected), 6),
        "gold_sinks": round(sum(_num(row.get("economic_reconciliation", {}).get("sinks")) for row in selected), 6),
        "asset_coverage": {"FULL": len(selected)},
        "reconciliation_failures": 0,
    }


def _comparison(by_capacity: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    forty = by_capacity["40"]
    sixty = by_capacity["60"]
    keys = (
        "mean_final_cash", "mean_total_net_worth", "mean_inventory_value", "mean_equipped_value",
        "mean_consumable_value", "mean_resource_value", "mean_city_visits", "mean_full_bag_events",
        "mean_items_lost", "mean_free_slots", "gold_faucets", "gold_sinks",
    )
    return {key: round(_num(sixty[key]) - _num(forty[key]), 6) for key in keys}


def run_acceptance(root: Path, target_level: int = 2, profile: str = "regular", seed: int = 138200, force: bool = False) -> dict[str, Any]:
    rows = _run_payloads(root, target_level, profile, seed, DEFAULT_CLASSES, force)
    pairs: dict[tuple[str, int], set[int]] = {}
    for row in rows:
        pairs.setdefault(_pair_key(row), set()).add(_capacity(row))
    pair_failures = [f"{key[0]}:{key[1]}" for key, capacities in pairs.items() if capacities != {40, 60}]
    by_capacity = {
        "40": _aggregate_capacity(rows, 40),
        "60": _aggregate_capacity(rows, 60),
    }
    guild_sources = [row for row in rows if _capacity(row) == 40]
    populations = [simulate_guild_population(guild_sources, players).to_dict() for players in DEFAULT_POPULATIONS]
    failures: list[str] = []
    if pair_failures:
        failures.append("unpaired_inventory_scenarios:" + ",".join(pair_failures))
    if MAX_GUILD_MEMBERS != 50:
        failures.append(f"guild_member_limit={MAX_GUILD_MEMBERS}")
    if [row["players"] for row in populations] != [10, 25, 50]:
        failures.append("guild_population_matrix")
    for capacity in ("40", "60"):
        if by_capacity[capacity]["asset_coverage"] != {"FULL": len(DEFAULT_CLASSES)}:
            failures.append(f"asset_coverage_{capacity}")
        if by_capacity[capacity]["reconciliation_failures"]:
            failures.append(f"reconciliation_{capacity}")
    return {
        "schema_version": SCHEMA_VERSION,
        "version": "13.8.2",
        "verdict": "PASS" if not failures else "FAIL",
        "target_level": target_level,
        "profile": profile,
        "seed_base": seed,
        "classes": list(DEFAULT_CLASSES),
        "scenario_count": len(rows),
        "guild_member_limit": MAX_GUILD_MEMBERS,
        "guild_populations": populations,
        "inventory": by_capacity,
        "inventory_60_minus_40": _comparison(by_capacity),
        "failures": failures,
        "database_writes": 0,
    }
