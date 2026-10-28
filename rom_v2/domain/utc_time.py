from __future__ import annotations

"""Canonical UTC helpers for ROM V2 domain and application code."""

from datetime import datetime, timezone


def normalize_utc(value: datetime, field: str) -> datetime:
    """Return an aware timestamp normalized to UTC and reject naive values."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field}_must_be_timezone_aware")
    return value.astimezone(timezone.utc)


def utc_now() -> datetime:
    """Return the current aware UTC timestamp for infrastructure composition only."""
    return datetime.now(timezone.utc)
