from __future__ import annotations

import math
import statistics
from typing import Iterable, Mapping, Sequence

PERCENTILES = (5, 10, 25, 50, 75, 90, 95)
LOWER_IS_BETTER = frozenset({"battles", "elapsed_minutes", "deaths", "death_rate", "city_visits", "full_bag_events", "items_lost", "gold_sinks"})
HIGHER_IS_BETTER = frozenset({"win_rate", "final_cash", "total_net_worth", "gold_faucets", "guild_exp", "guild_contracts"})


def _number(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def percentile(values: Sequence[float], percent: float) -> float:
    ordered = sorted(_number(x) for x in values)
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * float(percent) / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def distribution(values: Iterable[float]) -> dict:
    data = [_number(value) for value in values]
    if not data:
        return {"count": 0, "minimum": 0.0, "maximum": 0.0, "mean": 0.0, "median": 0.0, "standard_deviation": 0.0, "coefficient_of_variation": 0.0, "interquartile_range": 0.0, "p05_p95_spread": 0.0, "stability": "UNAVAILABLE", "percentiles": {f"p{p:02d}": 0.0 for p in PERCENTILES}}
    mean = statistics.fmean(data)
    std = statistics.pstdev(data) if len(data) > 1 else 0.0
    cv = abs(std / mean) if mean else (0.0 if std == 0.0 else float("inf"))
    pct = {f"p{p:02d}": round(percentile(data, p), 6) for p in PERCENTILES}
    if cv < 0.05:
        stability = "STABLE"
    elif cv < 0.15:
        stability = "WATCH"
    elif cv < 0.30:
        stability = "REVIEW"
    else:
        stability = "UNSTABLE"
    return {
        "count": len(data),
        "minimum": round(min(data), 6),
        "maximum": round(max(data), 6),
        "mean": round(mean, 6),
        "median": round(statistics.median(data), 6),
        "standard_deviation": round(std, 6),
        "coefficient_of_variation": round(cv, 6) if math.isfinite(cv) else "INF",
        "interquartile_range": round(pct["p75"] - pct["p25"], 6),
        "p05_p95_spread": round(pct["p95"] - pct["p05"], 6),
        "stability": stability,
        "percentiles": pct,
    }


def rng_bands(metric: str, stats: Mapping) -> dict:
    pct = dict(stats.get("percentiles") or {})
    lower_is_better = metric in LOWER_IS_BETTER
    if lower_is_better:
        unlucky, typical, lucky = pct.get("p90", 0.0), pct.get("p50", 0.0), pct.get("p10", 0.0)
    else:
        unlucky, typical, lucky = pct.get("p10", 0.0), pct.get("p50", 0.0), pct.get("p90", 0.0)
    return {"direction": "lower_is_better" if lower_is_better else "higher_is_better", "unlucky": unlucky, "typical": typical, "lucky": lucky}
