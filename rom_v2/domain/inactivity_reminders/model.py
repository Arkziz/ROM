"""Immutable inactivity-reminder values resolved from V1 parity evidence."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

DEFAULT_INACTIVITY_THRESHOLD = timedelta(days=7)


def aware_utc(value: datetime, field: str) -> datetime:
    """Normalize aware timestamps to UTC and reject ambiguous naive values."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field}_must_be_timezone_aware")
    return value.astimezone(timezone.utc)


def build_cycle_key(user_id: int, last_activity_at: datetime) -> str:
    """Create a stable cycle identity tied to the observed activity timestamp."""
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise ValueError("user_id_must_be_positive_integer")
    activity = aware_utc(last_activity_at, "last_activity_at")
    payload = f"{user_id}:{activity.isoformat(timespec='microseconds')}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class InactivityReminderDecision:
    """Pure evaluation result. It does not send, persist, retry, or schedule."""

    user_id: int
    last_activity_at: datetime
    evaluated_at: datetime
    due_at: datetime
    cycle_key: str
    due: bool
    already_delivered: bool


@dataclass(frozen=True, slots=True)
class InactivityReminderReceipt:
    """Persistent-audit payload for one successfully delivered cycle."""

    user_id: int
    cycle_key: str
    last_activity_at: datetime
    delivered_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.user_id, int) or isinstance(self.user_id, bool) or self.user_id <= 0:
            raise ValueError("user_id_must_be_positive_integer")
        if not self.cycle_key.strip():
            raise ValueError("cycle_key_must_not_be_empty")
        object.__setattr__(self, "cycle_key", self.cycle_key.strip())
        object.__setattr__(self, "last_activity_at", aware_utc(self.last_activity_at, "last_activity_at"))
        object.__setattr__(self, "delivered_at", aware_utc(self.delivered_at, "delivered_at"))
