from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from .asset_valuation import value_progression_assets


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _events(payload: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    value = payload.get("events", [])
    return value if isinstance(value, list) else []


def _details(event: Mapping[str, Any]) -> Mapping[str, Any]:
    value = event.get("details", {})
    return value if isinstance(value, Mapping) else {}


@dataclass(frozen=True)
class EconomyResult:
    runs: int
    gold_faucets: float
    gold_sinks: float
    gold_transfers: float
    net_gold_created: float
    mean_final_cash: float
    mean_total_net_worth: float
    asset_coverage: dict[str, int]
    repair_sink: float
    refine_sink: float
    shop_sink: float
    npc_sale_faucet: float
    combat_reward_faucet: float
    other_faucets: float
    other_sinks: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_economy(payloads: Iterable[Mapping[str, Any]]) -> EconomyResult:
    rows = list(payloads)
    faucets = sinks = transfers = 0.0
    repair = refine = shop = sales = combat = other_faucets = other_sinks = 0.0
    valuations = []
    coverage: dict[str, int] = {}

    for payload in rows:
        valuations.append(value_progression_assets(payload))
        coverage[valuations[-1].coverage] = coverage.get(valuations[-1].coverage, 0) + 1
        # gold_gained is the canonical accumulated world/combat reward metric in ProgressionResult.
        combat_value = _num(payload.get("gold_gained"))
        combat += combat_value
        faucets += combat_value
        for event in _events(payload):
            event_type = str(event.get("event_type", ""))
            details = _details(event)
            if event_type == "city_visit":
                sale = _num(details.get("sale_gold"))
                repair_cost = _num(details.get("repair_cost"))
                sales += sale
                repair += repair_cost
                faucets += sale
                sinks += repair_cost
            elif event_type in {"refine", "refine_attempt"}:
                value = _num(details.get("gold_cost"))
                refine += value
                sinks += value
            elif event_type in {"shop_purchase", "vendor_purchase"}:
                value = _num(details.get("gold_cost", details.get("cost")))
                shop += value
                sinks += value
            elif event_type in {"trade", "auction_transfer", "player_transfer"}:
                transfers += abs(_num(details.get("gold")))
            elif event_type == "economy_faucet":
                value = _num(details.get("gold"))
                other_faucets += value
                faucets += value
            elif event_type == "economy_sink":
                value = _num(details.get("gold"))
                other_sinks += value
                sinks += value

    count = len(rows)
    mean_cash = sum(item.cash_gold for item in valuations) / count if count else 0.0
    mean_worth = sum(item.total_net_worth for item in valuations) / count if count else 0.0
    return EconomyResult(
        runs=count,
        gold_faucets=round(faucets, 6),
        gold_sinks=round(sinks, 6),
        gold_transfers=round(transfers, 6),
        net_gold_created=round(faucets - sinks, 6),
        mean_final_cash=round(mean_cash, 6),
        mean_total_net_worth=round(mean_worth, 6),
        asset_coverage=dict(sorted(coverage.items())),
        repair_sink=round(repair, 6),
        refine_sink=round(refine, 6),
        shop_sink=round(shop, 6),
        npc_sale_faucet=round(sales, 6),
        combat_reward_faucet=round(combat, 6),
        other_faucets=round(other_faucets, 6),
        other_sinks=round(other_sinks, 6),
    )
