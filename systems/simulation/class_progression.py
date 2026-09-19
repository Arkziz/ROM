from __future__ import annotations

"""Validated operator facade for the existing class progression simulator."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .parity_foundation import SUPPORTED_CLASSES, SimulatorScenarioPolicy
from .progression_models import PROFILES
from .world_progression import WorldProgressionSimulator
from .progression_economy_reporting import build_economy_equipment_report

# ROM 18.30.3 CLASS PROGRESSION SIMULATION


@dataclass(frozen=True)
class ClassProgressionRequest:
    character_class: str
    target_level: int
    seed: int = 1
    profile: str = "hardcore"
    start_level: int = 1
    max_days: int = 365
    inventory_capacity: int = 40

    def normalized(self) -> "ClassProgressionRequest":
        character_class = str(self.character_class).strip().lower()
        profile = str(self.profile).strip().lower()
        target_level = int(self.target_level)
        start_level = int(self.start_level)
        max_days = int(self.max_days)
        capacity = int(self.inventory_capacity)
        if character_class not in SUPPORTED_CLASSES:
            raise ValueError(f"Unsupported class: {character_class}")
        if profile not in PROFILES:
            raise ValueError(f"Unsupported profile: {profile}")
        if start_level != 1:
            raise ValueError("Stage 18.30.3 currently supports canonical start level 1 only")
        if target_level <= start_level:
            raise ValueError("Target level must be greater than start level")
        if target_level > 50:
            raise ValueError("Target level cannot exceed configured progression level 50")
        if max_days < 1:
            raise ValueError("max_days must be positive")
        if capacity < 1:
            raise ValueError("inventory_capacity must be positive")
        return ClassProgressionRequest(character_class, target_level, int(self.seed), profile, start_level, max_days, capacity)


def _event_counts(events: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        key = str(getattr(event, "event_type", "unknown"))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))



def _duration_payload(elapsed_minutes: int) -> dict[str, int | str]:
    total = max(0, int(elapsed_minutes))
    days, rem = divmod(total, 1440)
    hours, minutes = divmod(rem, 60)
    return {"total_minutes": total, "calendar_days": days + (1 if rem or total == 0 else 0), "full_days": days, "hours": hours, "minutes": minutes, "formatted": f"{days} дн {hours} год {minutes} хв"}


def _mob_encounter_summary(events: list[Any]) -> dict[str, Any]:
    by_mob: dict[tuple[str, int, str], int] = {}
    by_level: dict[int, int] = {}
    by_delta = {-1: 0, 0: 0, 1: 0}
    by_attack: dict[str, int] = {}
    by_location: dict[str, int] = {}
    candidate_sizes: dict[int, int] = {}
    for event in events:
        details = dict(getattr(event, "details", {}) or {})
        if str(details.get("battle_outcome", "")) not in {"victory", "defeat", "escape"}:
            continue
        name = str(details.get("mob", "")); level = int(details.get("mob_level", details.get("level", 1))); kind = str(details.get("encounter_type", "normal"))
        by_mob[(name, level, kind)] = by_mob.get((name, level, kind), 0) + 1
        by_level[level] = by_level.get(level, 0) + 1
        delta = int(details.get("level_delta", level - int(details.get("player_level", details.get("level", level)))))
        if delta not in {-1, 0, 1}: raise RuntimeError(f"Mob level delta outside canonical range: {delta}")
        by_delta[delta] += 1
        attack = str(details.get("attack_type", "unknown")); by_attack[attack] = by_attack.get(attack, 0) + 1
        location = str(details.get("location_id", "unknown")); by_location[location] = by_location.get(location, 0) + 1
        size = int(details.get("candidate_count", 0)); candidate_sizes[size] = candidate_sizes.get(size, 0) + 1
    rows = [{"name": key[0], "level": key[1], "encounter_type": key[2], "count": count} for key, count in sorted(by_mob.items(), key=lambda row: (row[0][1], row[0][0], row[0][2]))]
    total = sum(row["count"] for row in rows)
    return {"total": total, "unique_mobs": len(rows), "by_mob": rows, "by_level": {str(k): v for k, v in sorted(by_level.items())}, "by_level_delta": {str(k): v for k, v in sorted(by_delta.items())}, "by_attack_type": dict(sorted(by_attack.items())), "by_location": dict(sorted(by_location.items())), "candidate_pool_sizes": {str(k): v for k, v in sorted(candidate_sizes.items())}}


def _contract_summary(events: list[Any]) -> tuple[dict[str, int], dict[str, int], list[dict[str, Any]]]:
    encounters = {"normal": 0, "elite": 0, "boss": 0}
    outcomes = {"victory": 0, "defeat": 0, "escape": 0}
    ledger: dict[tuple, dict[str, Any]] = {}
    for event in events:
        details = dict(getattr(event, "details", {}) or {})
        outcome = str(details.get("battle_outcome", ""))
        if outcome in outcomes:
            outcomes[outcome] += 1
            kind = str(details.get("encounter_type", "normal"))
            encounters[kind if kind in encounters else "normal"] += 1
        for item in details.get("loot_records", []) or []:
            key = (item.get("item_id"), item.get("name"), item.get("category"), item.get("rarity"))
            row = ledger.setdefault(key, {"item_id": item.get("item_id"), "name": item.get("name"), "category": item.get("category"), "rarity": item.get("rarity"), "slot_key": item.get("slot_key", ""), "item_level": int(item.get("item_level", 1)), "armor_type": item.get("armor_type", ""), "weapon_hands": int(item.get("weapon_hands", 1)), "stats": dict(item.get("stats", {})), "sell_price": float(item.get("sell_price", 0.0)), "created_ids": [], "found": 0, "awarded": 0, "lost_due_capacity": 0, "destinations": {}})
            row["created_ids"].extend(int(value) for value in item.get("created_ids", []) or [])
            for field in ("found", "awarded", "lost_due_capacity"): row[field] += int(item.get(field, 0))
            destination = str(item.get("destination", "unknown")); row["destinations"][destination] = row["destinations"].get(destination, 0) + int(item.get("found", 0))
    rows = sorted(ledger.values(), key=lambda row: (str(row["category"]), str(row["name"]), int(row["item_id"] or 0)))
    for row in rows:
        if row["found"] != row["awarded"] + row["lost_due_capacity"]: raise RuntimeError(f"Loot conservation failed: {row}")
    return encounters, outcomes, rows

def _result_payload(request: ClassProgressionRequest, result: Any, project_root: Path) -> dict[str, Any]:
    raw = result.to_dict() if hasattr(result, "to_dict") else asdict(result)
    events = list(getattr(result, "events", []) or [])
    final_level = int(raw.get("final_level", 0))
    target = int(request.target_level)
    encounters, outcomes, loot_ledger = _contract_summary(events)
    mob_encounters = _mob_encounter_summary(events)
    duration = _duration_payload(int(raw.get("elapsed_minutes", 0)))
    payload = {
        "status": str(raw.get("status", "unknown")),
        "class": request.character_class,
        "start_level": request.start_level,
        "target_level": target,
        "final_level": final_level,
        "target_reached": final_level >= target,
        "seed": request.seed,
        "profile": request.profile,
        "max_days": request.max_days,
        "days": int(raw.get("days", 0)),
        "elapsed_minutes": int(raw.get("elapsed_minutes", 0)),
        "time_to_target": duration,
        "encounters": encounters,
        "mob_encounters": mob_encounters,
        "battle_outcomes": outcomes,
        "loot_ledger": loot_ledger,
        "loot_found_total": sum(row["found"] for row in loot_ledger),
        "hunts": int(raw.get("battles", 0)),
        "battles": int(raw.get("battles", 0)),
        "wins": int(raw.get("wins", 0)),
        "defeats": int(raw.get("deaths", 0)),
        "escapes": int(raw.get("escapes", 0)),
        "exp_gained": int(raw.get("exp_gained", 0)),
        "gold_gained": float(raw.get("gold_gained", 0.0)),
        "final_gold": float(raw.get("final_gold", 0.0)),
        "energy_spent": int(raw.get("energy_spent", 0)),
        "energy_regenerated": int(raw.get("energy_regenerated", 0)),
        "items_awarded": int(raw.get("items_awarded", 0)),
        "items_lost": int(raw.get("items_lost", 0)),
        "final_free_slots": int(raw.get("final_free_slots", 0)),
        "event_counts": _event_counts(events),
        "canonical_result": raw,
    }
    economy_equipment = build_economy_equipment_report(events, loot_ledger, payload["gold_gained"], payload["final_gold"], request.character_class, project_root)
    payload["economy"] = economy_equipment["gold"]
    payload["resources"] = economy_equipment["resources"]
    payload["loot_lifecycle"] = economy_equipment["loot_lifecycle"]
    payload["final_loadout"] = economy_equipment["final_loadout"]
    if payload["target_reached"] and final_level != target:
        raise RuntimeError("Progression simulator advanced beyond the requested target level")
    return payload


def run_class_progression(project_root: Path, request: ClassProgressionRequest) -> dict[str, Any]:
    normalized = request.normalized()
    policy = SimulatorScenarioPolicy()
    policy.validate()
    if normalized.profile != "hardcore":
        raise ValueError("Stage 18.30 acceptance policy requires the 09:00-23:00 hardcore profile")
    simulator = WorldProgressionSimulator(
        project_root=Path(project_root),
        character_class=normalized.character_class,
        target_level=normalized.target_level,
        profile=normalized.profile,
        seed=normalized.seed,
        inventory_capacity=normalized.inventory_capacity,
        max_days=normalized.max_days,
    )
    return _result_payload(normalized, simulator.run(), Path(project_root))
