from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class SimulationEvent:
    sequence: int
    event_type: str
    occurred_at: str
    values: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationMetrics:
    counters: Dict[str, int] = field(default_factory=dict)
    totals: Dict[str, float] = field(default_factory=dict)
    gauges: Dict[str, float] = field(default_factory=dict)
    events: List[SimulationEvent] = field(default_factory=list)

    def increment(self, name: str, amount: int = 1) -> int:
        self.counters[name] = int(self.counters.get(name, 0)) + int(amount)
        return self.counters[name]

    def add_total(self, name: str, amount: float) -> float:
        self.totals[name] = float(self.totals.get(name, 0.0)) + float(amount)
        return self.totals[name]

    def set_gauge(self, name: str, value: float) -> float:
        self.gauges[name] = float(value)
        return self.gauges[name]

    def record(self, event_type: str, occurred_at: str, **values: Any) -> SimulationEvent:
        event = SimulationEvent(len(self.events) + 1, str(event_type), str(occurred_at), dict(values))
        self.events.append(event)
        return event

    def to_dict(self) -> Dict[str, Any]:
        return {
            "counters": dict(sorted(self.counters.items())),
            "totals": dict(sorted(self.totals.items())),
            "gauges": dict(sorted(self.gauges.items())),
            "events": [asdict(event) for event in self.events],
        }
