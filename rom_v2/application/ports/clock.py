"""Clock port for deterministic ROM V2 time access."""
from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Provide UTC wall time and monotonic elapsed-time measurements."""

    def now_utc(self) -> datetime:
        """Return a timezone-aware UTC datetime."""
        ...

    def monotonic_seconds(self) -> float:
        """Return a non-decreasing elapsed-time value."""
        ...
