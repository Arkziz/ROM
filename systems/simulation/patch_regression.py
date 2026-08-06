from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from .economic_ledger import EconomicScenarioSpec
from .economic_progression import run_economic_progression
from .rng_percentiles import distribution, rng_bands

SCHEMA_VERSION = "rom.simulation.patch_regression.v1"
VERSION = "13.9.0"
DEFAULT_CLASSES = ("warrior", "knight", "scout", "rogue", "mage", "priest")
DEFAULT_PROFILES = ("regular",)
DEFAULT_CAPACITIES = (40, 60)
CONTROLLED_METRICS = (
    "battles", "elapsed_minutes", "deaths", "win_rate", "final_cash",
    "gold_faucets", "gold_sinks", "total_net_worth", "city_visits",
    "full_bag_events", "items_lost", "guild_exp", "guild_contracts",
)
THRESHOLDS = {
    "battles": (10.0, 20.0), "elapsed_minutes": (10.0, 20.0),
    "deaths": (20.0, 50.0), "win_rate": (3.0, 7.0),
    "final_cash": (10.0, 20.0), "gold_faucets": (10.0, 20.0),
    "gold_sinks": (10.0, 20.0), "total_net_worth": (10.0, 20.0),
    "city_visits": (20.0, 50.0), "full_bag_events": (20.0, 50.0),
    "items_lost": (0.0, 0.0), "guild_exp": (10.0, 20.0),
    "guild_contracts": (10.0, 20.0),
}

@dataclass(frozen=True)
class RegressionConfig:
    target_level: int = 2
    profiles: tuple[str, ...] = DEFAULT_PROFILES
    classes: tuple[str, ...] = DEFAULT_CLASSES
    seed_start: int = 139000
    seed_count: int = 10
    capacities: tuple[int, ...] = DEFAULT_CAPACITIES
    max_days: int = 365

    def seeds(self) -> tuple[int, ...]:
        return tuple(range(self.seed_start, self.seed_start + self.seed_count))

    def validate(self) -> None:
        if not 2 <= int(self.target_level) <= 10:
            raise ValueError("target_level must be between 2 and current production ceiling 10")
        if self.seed_count < 1:
            raise ValueError("seed_count must be positive")
        if any(int(capacity) not in (40, 60) for capacity in self.capacities):
            raise ValueError("inventory capacity must be 40 or 60")


def _num(value) -> float:
    try: return float(value)
    except (TypeError, ValueError): return 0.0


def _nested(payload: Mapping, *path, default=0.0):
    value = payload
    for key in path:
        if not isinstance(value, Mapping): return default
        value = value.get(key)
    return default if value is None else value


def metric_row(payload: Mapping) -> dict:
    wins, battles = _num(payload.get("wins")), _num(payload.get("battles"))
    ledger = payload.get("economic_ledger") if isinstance(payload.get("economic_ledger"), Mapping) else {}
    totals = ledger.get("totals") if isinstance(ledger.get("totals"), Mapping) else ledger
    valuation = payload.get("asset_valuation") if isinstance(payload.get("asset_valuation"), Mapping) else {}
    guild = payload.get("guild") if isinstance(payload.get("guild"), Mapping) else {}
    return {
        "battles": _num(payload.get("battles")),
        "elapsed_minutes": _num(payload.get("elapsed_minutes")),
        "deaths": _num(payload.get("deaths")),
        "win_rate": 100.0 * wins / battles if battles else 0.0,
        "final_cash": _num(payload.get("final_gold", valuation.get("cash_gold"))),
        "gold_faucets": _num(totals.get("faucets", totals.get("gold_faucets", 0.0))),
        "gold_sinks": _num(totals.get("sinks", totals.get("gold_sinks", 0.0))),
        "total_net_worth": _num(valuation.get("total_net_worth")),
        "city_visits": _num(payload.get("city_visits")),
        "full_bag_events": _num(payload.get("full_bag_events")),
        "items_lost": _num(payload.get("items_lost")),
        "guild_exp": _num(guild.get("exp", payload.get("guild_exp", 0.0))),
        "guild_contracts": _num(guild.get("contracts", payload.get("guild_contracts", 0.0))),
    }


def scenario_identity(payload: Mapping) -> tuple:
    scenario = payload.get("scenario") if isinstance(payload.get("scenario"), Mapping) else {}
    return (
        scenario.get("character_class", payload.get("character_class")),
        scenario.get("profile", payload.get("profile")),
        int(scenario.get("seed", payload.get("seed", 0))),
        int(scenario.get("target_level", payload.get("target_level", payload.get("final_level", 0)))),
        int(scenario.get("inventory_capacity", _nested(payload, "final_asset_snapshot", "inventory_capacity", default=0))),
    )


def source_fingerprint(root: Path) -> dict:
    paths = [
        "data/player_progression.py", "systems/combat_system.py", "systems/reward_system.py",
        "systems/refine_system.py", "systems/simulation/world_progression.py",
        "systems/simulation/pve_battle.py", "systems/simulation/economic_ledger.py",
        "systems/simulation/economic_progression.py", "systems/simulation/combat_actor_stats.py",
    ]
    entries = []
    combined = hashlib.sha256()
    for relative in paths:
        path = root / relative
        if not path.exists(): continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({"path": relative, "sha256": digest, "size": path.stat().st_size})
        combined.update(relative.encode("utf-8")); combined.update(digest.encode("ascii"))
    return {"sha256": combined.hexdigest(), "files": entries}


def run_matrix(root: Path, config: RegressionConfig, force: bool = False, progress=None) -> list[dict]:
    config.validate(); rows = []; total = len(config.classes) * len(config.profiles) * config.seed_count * len(config.capacities); done = 0
    for class_key in config.classes:
        for profile in config.profiles:
            for seed in config.seeds():
                for capacity in config.capacities:
                    spec = EconomicScenarioSpec(character_class=class_key, profile=profile, seed=seed, target_level=config.target_level, inventory_capacity=capacity, max_days=config.max_days)
                    payload = run_economic_progression(root, spec, force=force)
                    rows.append(payload); done += 1
                    if progress: progress(done, total, class_key, profile, seed, capacity)
    return rows


def analyze_payloads(root: Path, payloads: Iterable[Mapping], config: RegressionConfig) -> dict:
    rows = list(payloads); groups = {}; failures = []
    for payload in rows:
        identity = scenario_identity(payload); groups.setdefault((identity[0], identity[1], identity[4]), []).append(metric_row(payload))
        reconciliation = payload.get("economic_reconciliation") if isinstance(payload.get("economic_reconciliation"), Mapping) else {}
        valuation = payload.get("asset_valuation") if isinstance(payload.get("asset_valuation"), Mapping) else {}
        if payload.get("status") != "completed": failures.append({"code": "scenario_not_completed", "identity": identity})
        if not reconciliation.get("passed", False): failures.append({"code": "economic_reconciliation", "identity": identity})
        if valuation.get("coverage") != "FULL": failures.append({"code": "asset_coverage", "identity": identity, "coverage": valuation.get("coverage")})
    aggregates = []
    for key, metric_rows in sorted(groups.items()):
        metrics = {}; bands = {}
        for metric in CONTROLLED_METRICS:
            stats = distribution(row[metric] for row in metric_rows); metrics[metric] = stats; bands[metric] = rng_bands(metric, stats)
        aggregates.append({"character_class": key[0], "profile": key[1], "inventory_capacity": key[2], "runs": len(metric_rows), "metrics": metrics, "rng_bands": bands})
    return {
        "schema_version": SCHEMA_VERSION, "version": VERSION, "created_at": datetime.now(timezone.utc).isoformat(),
        "config": asdict(config), "source_fingerprint": source_fingerprint(root), "scenario_count": len(rows),
        "aggregates": aggregates, "failures": failures, "verdict": "PASS" if not failures else "FAIL", "database_writes": 0,
    }


def _aggregate_map(report: Mapping) -> dict:
    return {(row["character_class"], row["profile"], int(row["inventory_capacity"])): row for row in report.get("aggregates", [])}


def _canonical_json_value(value):
    """Normalize tuples/lists and nested mappings to their JSON representation."""
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def compare_reports(baseline: Mapping, current: Mapping) -> dict:
    failures = []; findings = []; comparisons = []; base_map, cur_map = _aggregate_map(baseline), _aggregate_map(current)
    if baseline.get("schema_version") != current.get("schema_version"): failures.append({"code": "schema_mismatch"})
    if _canonical_json_value(baseline.get("config")) != _canonical_json_value(current.get("config")): failures.append({"code": "config_mismatch"})
    for key in sorted(set(base_map) | set(cur_map)):
        if key not in base_map or key not in cur_map:
            failures.append({"code": "aggregate_group_mismatch", "group": key}); continue
        for metric in CONTROLLED_METRICS:
            before = _num(base_map[key]["metrics"][metric]["mean"]); after = _num(cur_map[key]["metrics"][metric]["mean"])
            absolute = after - before
            percent = 0.0 if before == 0.0 and after == 0.0 else (100.0 if before == 0.0 else absolute / abs(before) * 100.0)
            review, fail = THRESHOLDS[metric]
            magnitude = abs(percent)
            verdict = "FAIL" if magnitude > fail else ("REVIEW" if magnitude > review else "PASS")
            entry = {"group": key, "metric": metric, "baseline": round(before, 6), "current": round(after, 6), "absolute_diff": round(absolute, 6), "percent_diff": round(percent, 6), "review_threshold": review, "fail_threshold": fail, "verdict": verdict}
            comparisons.append(entry)
            if verdict == "FAIL": failures.append(entry)
            elif verdict == "REVIEW": findings.append(entry)
    verdict = "FAIL" if failures else ("REVIEW" if findings else "PASS")
    return {"schema_version": SCHEMA_VERSION, "version": VERSION, "verdict": verdict, "comparisons": comparisons, "failures": failures, "findings": findings, "database_writes": 0}


def baseline_path(root: Path, name: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name).strip("_") or "default"
    return root / "simulation_reports" / "baselines" / "stage_13_9_0" / f"{safe}.json"


def write_json_atomic(path: Path, payload: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); temporary = path.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"); os.replace(temporary, path)


def create_baseline(root: Path, name: str, report: Mapping, replace: bool = False) -> Path:
    path = baseline_path(root, name)
    if path.exists() and not replace: raise FileExistsError(f"Baseline already exists: {path}. Use --replace-baseline explicitly.")
    write_json_atomic(path, report); return path


def load_baseline(root: Path, name: str) -> dict:
    path = baseline_path(root, name)
    if not path.exists(): raise FileNotFoundError(f"Baseline not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
