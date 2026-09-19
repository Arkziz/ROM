from __future__ import annotations

"""Validated operator facade for the existing class progression simulator."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .parity_foundation import SUPPORTED_CLASSES, SimulatorScenarioPolicy
from .progression_models import PROFILES
from .world_progression import WorldProgressionSimulator

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


def _result_payload(request: ClassProgressionRequest, result: Any) -> dict[str, Any]:
    raw = result.to_dict() if hasattr(result, "to_dict") else asdict(result)
    events = list(getattr(result, "events", []) or [])
    final_level = int(raw.get("final_level", 0))
    target = int(request.target_level)
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
    return _result_payload(normalized, simulator.run())
