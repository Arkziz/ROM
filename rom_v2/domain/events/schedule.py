"""Deterministic event schedule primitives resolved from V1 parity evidence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class EventLifecycle(str, Enum):
    """Derived lifecycle state. No scheduler or persisted transition is implied."""

    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    DISABLED = "disabled"


def _aware_utc(value: datetime, field: str) -> datetime:
    """Normalize an aware datetime to UTC and reject ambiguous naive values."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field}_must_be_timezone_aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class EventSchedule:
    """Half-open event window: start_at <= now < end_at."""

    start_at: datetime
    end_at: datetime

    def __post_init__(self) -> None:
        start = _aware_utc(self.start_at, "start_at")
        end = _aware_utc(self.end_at, "end_at")
        if start >= end:
            raise ValueError("start_at_must_precede_end_at")
        object.__setattr__(self, "start_at", start)
        object.__setattr__(self, "end_at", end)

    def lifecycle_at(self, instant: datetime, *, enabled: bool) -> EventLifecycle:
        """Evaluate on access; this method never creates a timer or background job."""
        current = _aware_utc(instant, "instant")
        if not enabled:
            return EventLifecycle.DISABLED
        if current < self.start_at:
            return EventLifecycle.UPCOMING
        if current < self.end_at:
            return EventLifecycle.ACTIVE
        return EventLifecycle.COMPLETED

    def is_active_at(self, instant: datetime, *, enabled: bool) -> bool:
        return self.lifecycle_at(instant, enabled=enabled) is EventLifecycle.ACTIVE


@dataclass(frozen=True, slots=True)
class EventDefinition:
    """Canonical event identity plus schedule and enabled gate."""

    event_key: str
    schedule: EventSchedule
    enabled: bool = True

    def __post_init__(self) -> None:
        key = self.event_key.strip()
        if not key:
            raise ValueError("event_key_must_not_be_empty")
        object.__setattr__(self, "event_key", key)
