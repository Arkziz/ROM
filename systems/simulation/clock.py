from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from .config import SimulationProfile

UTC = timezone.utc


@dataclass
class SimulationClock:
    current: datetime

    def __post_init__(self) -> None:
        if self.current.tzinfo is None:
            self.current = self.current.replace(tzinfo=UTC)
        else:
            self.current = self.current.astimezone(UTC)

    @classmethod
    def at_start(cls, year: int = 2026, month: int = 1, day: int = 1) -> "SimulationClock":
        return cls(datetime(year, month, day, 0, 0, tzinfo=UTC))

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()

    def iso(self) -> str:
        return self.current.isoformat(timespec="seconds")

    def advance(self, *, seconds: int = 0, minutes: int = 0, hours: int = 0, days: int = 0) -> datetime:
        delta = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        if delta.total_seconds() < 0:
            raise ValueError("SimulationClock cannot move backwards")
        self.current += delta
        return self.current

    @property
    def minute_of_day(self) -> int:
        return self.current.hour * 60 + self.current.minute

    def is_active(self, profile: SimulationProfile) -> bool:
        return profile.start_minute <= self.minute_of_day < profile.end_minute

    def next_active_start(self, profile: SimulationProfile) -> datetime:
        base = self.current.replace(hour=0, minute=0, second=0, microsecond=0)
        candidate = base + timedelta(minutes=profile.start_minute)
        if self.current < candidate:
            return candidate
        if self.is_active(profile):
            return self.current
        return candidate + timedelta(days=1)

    def active_window_end(self, profile: SimulationProfile) -> Optional[datetime]:
        if not self.is_active(profile):
            return None
        base = self.current.replace(hour=0, minute=0, second=0, microsecond=0)
        return base + timedelta(minutes=profile.end_minute)

    def jump_to_next_active_start(self, profile: SimulationProfile) -> datetime:
        target = self.next_active_start(profile)
        self.current = target
        return target

    def elapsed_regeneration_ticks(self, since: datetime, interval_minutes: int) -> int:
        if interval_minutes <= 0:
            raise ValueError("interval_minutes must be positive")
        if since.tzinfo is None:
            since = since.replace(tzinfo=UTC)
        since = since.astimezone(UTC)
        if since > self.current:
            return 0
        return int((self.current - since).total_seconds() // (interval_minutes * 60))
