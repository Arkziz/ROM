"""Aggregate-oriented repository ports for ROM V2."""
from __future__ import annotations

from typing import Protocol, TypeVar

AggregateT = TypeVar("AggregateT")
AggregateIdT = TypeVar("AggregateIdT")


class AggregateRepository(Protocol[AggregateT, AggregateIdT]):
    """Define persistence operations without transaction ownership."""

    def get(self, aggregate_id: AggregateIdT) -> AggregateT | None:
        """Return one aggregate by stable identity when present."""
        ...

    def add(self, aggregate: AggregateT) -> None:
        """Register a new aggregate in the active Unit of Work."""
        ...

    def save(self, aggregate: AggregateT, expected_version: int) -> None:
        """Persist an aggregate using optimistic expected-version semantics."""
        ...

    def exists(self, aggregate_id: AggregateIdT) -> bool:
        """Return whether an aggregate identity already exists."""
        ...
