from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class AssetValuation:
    cash_gold: float
    inventory_liquidation_value: float
    equipped_item_value: float
    consumable_value: float
    resource_value: float
    total_net_worth: float
    valued_items: int
    unvalued_items: int
    coverage: str

    def to_dict(self):
        return asdict(self)


def _number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _mapping(value):
    return value if isinstance(value, Mapping) else {}


def _items_from_payload(payload: Mapping[str, Any]):
    candidates = [
        payload.get("final_inventory"),
        payload.get("inventory"),
        _mapping(payload.get("state")).get("inventory"),
        _mapping(payload.get("final_state")).get("inventory"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
        if isinstance(candidate, Mapping):
            items = candidate.get("items")
            if isinstance(items, list):
                return items
    return []


def _equipped_ids(payload: Mapping[str, Any]):
    candidates = [
        payload.get("final_equipment"),
        payload.get("equipment"),
        _mapping(payload.get("state")).get("equipment"),
        _mapping(payload.get("final_state")).get("equipment"),
    ]
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            slots = candidate.get("slots", candidate)
            if isinstance(slots, Mapping):
                return {value for value in slots.values() if value is not None}
    return set()


def _explicit_unit_sell_value(item: Mapping[str, Any]):
    for key in ("sell_value", "sell_price", "vendor_value", "liquidation_value"):
        if item.get(key) is not None:
            return max(0.0, _number(item.get(key)))
    return None


def _category(item: Mapping[str, Any]):
    return str(item.get("category") or item.get("kind") or item.get("item_type") or "").lower()


def value_progression_assets(payload: Mapping[str, Any]) -> AssetValuation:
    """Value only assets with explicit sell values in the simulation payload.

    The function deliberately does not invent prices. If the current checkpoint schema
    omits final inventory or explicit sell values, coverage is UNAVAILABLE/PARTIAL and
    total_net_worth contains only values that can be proven from the payload.
    """
    cash = round(_number(payload.get("final_gold", payload.get("gold", 0.0))), 6)
    items = _items_from_payload(payload)
    equipped = _equipped_ids(payload)
    inventory_value = 0.0
    equipped_value = 0.0
    consumable_value = 0.0
    resource_value = 0.0
    valued = 0
    unvalued = 0

    for raw in items:
        item = _mapping(raw)
        quantity = max(0, int(_number(item.get("quantity", 1), 1)))
        unit_value = _explicit_unit_sell_value(item)
        if unit_value is None:
            unvalued += 1
            continue
        value = unit_value * quantity
        valued += 1
        item_id = item.get("simulation_item_id", item.get("inventory_id", item.get("id")))
        category = _category(item)
        if item_id in equipped or bool(item.get("equipped")):
            equipped_value += value
        elif category in {"potion", "consumable"}:
            consumable_value += value
        elif category in {"rune", "material", "resource", "refine_stone", "token"}:
            resource_value += value
        else:
            inventory_value += value

    if not items:
        coverage = "UNAVAILABLE"
    elif unvalued:
        coverage = "PARTIAL"
    else:
        coverage = "FULL"
    total = cash + inventory_value + equipped_value + consumable_value + resource_value
    return AssetValuation(
        cash_gold=round(cash, 6),
        inventory_liquidation_value=round(inventory_value, 6),
        equipped_item_value=round(equipped_value, 6),
        consumable_value=round(consumable_value, 6),
        resource_value=round(resource_value, 6),
        total_net_worth=round(total, 6),
        valued_items=valued,
        unvalued_items=unvalued,
        coverage=coverage,
    )
