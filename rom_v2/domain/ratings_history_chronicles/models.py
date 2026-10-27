"""Immutable API-ready models for ratings, history and chronicles."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


def aware_utc(value: datetime, field: str) -> datetime:
    """Normalize an aware timestamp to UTC and reject ambiguous naive values."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field}_must_be_timezone_aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class RatingCandidate:
    subject_id: int
    display_name: str
    score: int

    def __post_init__(self) -> None:
        if isinstance(self.subject_id, bool) or self.subject_id <= 0:
            raise ValueError("subject_id_must_be_positive")
        if not self.display_name.strip():
            raise ValueError("display_name_must_not_be_empty")
        if isinstance(self.score, bool):
            raise ValueError("score_must_be_integer")


@dataclass(frozen=True, slots=True)
class RatingEntry:
    position: int
    subject_id: int
    display_name: str
    score: int


@dataclass(frozen=True, slots=True)
class HistoryRecord:
    record_id: str
    owner_id: int
    occurred_at: datetime
    kind: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.record_id.strip() or not self.kind.strip():
            raise ValueError("history_identity_and_kind_required")
        if isinstance(self.owner_id, bool) or self.owner_id <= 0:
            raise ValueError("owner_id_must_be_positive")
        object.__setattr__(self, "occurred_at", aware_utc(self.occurred_at, "occurred_at"))


@dataclass(frozen=True, slots=True)
class ChronicleEvent:
    event_id: str
    owner_id: int
    occurred_at: datetime
    kind: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.kind.strip():
            raise ValueError("chronicle_identity_and_kind_required")
        if isinstance(self.owner_id, bool) or self.owner_id <= 0:
            raise ValueError("owner_id_must_be_positive")
        object.__setattr__(self, "occurred_at", aware_utc(self.occurred_at, "occurred_at"))


@dataclass(frozen=True, slots=True)
class Page:
    items: tuple[Any, ...]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_previous: bool
    has_next: bool
