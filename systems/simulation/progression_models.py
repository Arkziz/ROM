from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

@dataclass(frozen=True)
class ProgressionProfile:
    key: str
    start_hour: int
    end_hour: int

PROFILES = {
    "casual": ProgressionProfile("casual", 18, 21),
    "regular": ProgressionProfile("regular", 17, 23),
    "hardcore": ProgressionProfile("hardcore", 9, 23),
}

@dataclass
class ProgressionEvent:
    minute: int
    day: int
    event_type: str
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProgressionResult:
    run_id: str
    character_class: str
    target_level: int
    final_level: int
    profile: str
    seed: int
    days: int
    elapsed_minutes: int
    battles: int
    wins: int
    deaths: int
    energy_spent: int
    energy_regenerated: int
    exp_gained: int
    gold_gained: float
    final_gold: float
    city_visits: int
    full_bag_events: int
    items_awarded: int
    items_lost: int
    final_free_slots: int
    events: List[ProgressionEvent]
    status: str

    def to_dict(self):
        return asdict(self)
