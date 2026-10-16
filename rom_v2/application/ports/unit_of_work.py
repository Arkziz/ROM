"""Explicit transaction boundary port for ROM V2."""
from __future__ import annotations

from typing import Protocol


class UnitOfWork(Protocol):
    """Own one transaction and one commit point for a business operation."""

    def commit(self) -> None:
        """Commit aggregate state, events, outbox, and idempotency atomically."""
        ...

    def rollback(self) -> None:
        """Discard every uncommitted change in the active operation."""
        ...
