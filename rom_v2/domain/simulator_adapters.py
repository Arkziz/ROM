"""Flat, API-ready simulator adapters.

These adapters provide deterministic clock, seeded randomness and isolated
in-memory repositories. They do not duplicate gameplay formulas, access SQLite,
or connect runtime/Telegram. Production application/domain services remain the
only owners of gameplay calculations.
"""
from __future__ import annotations

import copy
import hashlib
import pickle
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Generic, Iterable, Protocol, Sequence, TypeVar

T = TypeVar("T")
K = TypeVar("K")


def _aware_utc(value: datetime, field: str) -> datetime:
    """Normalize an aware timestamp and fail closed for naive simulator time."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field}_must_be_timezone_aware")
    return value.astimezone(timezone.utc)


class ClockPort(Protocol):
    def now_utc(self) -> datetime: ...


class RandomSourcePort(Protocol):
    def random(self) -> float: ...
    def randint(self, minimum: int, maximum: int) -> int: ...
    def choice(self, values: Sequence[T]) -> T: ...
    def shuffle(self, values: list[T]) -> None: ...


@dataclass(slots=True)
class SimulationClockAdapter:
    """Injected deterministic UTC clock; never reads wall-clock time."""

    _current: datetime

    def __post_init__(self) -> None:
        self._current = _aware_utc(self._current, "current")

    @classmethod
    def at_start(cls, value: datetime | None = None) -> "SimulationClockAdapter":
        return cls(value or datetime(2026, 1, 1, tzinfo=timezone.utc))

    def now_utc(self) -> datetime:
        return self._current

    def advance(self, delta: timedelta) -> datetime:
        if delta.total_seconds() < 0:
            raise ValueError("simulation_clock_cannot_move_backwards")
        self._current = self._current + delta
        return self._current


class SeededRandomAdapter:
    """Seed-owned RNG with draw accounting and no module-global reseeding."""

    def __init__(self, seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise TypeError("seed_must_be_integer")
        self.seed = seed
        self.draw_count = 0
        self._rng = random.Random(seed)

    def _drawn(self, value: T) -> T:
        self.draw_count += 1
        return value

    def random(self) -> float:
        return self._drawn(self._rng.random())

    def randint(self, minimum: int, maximum: int) -> int:
        if minimum > maximum:
            raise ValueError("minimum_must_not_exceed_maximum")
        return self._drawn(self._rng.randint(minimum, maximum))

    def choice(self, values: Sequence[T]) -> T:
        if not values:
            raise ValueError("choice_requires_non_empty_values")
        return self._drawn(self._rng.choice(values))

    def choices(self, values: Sequence[T], *, weights: Sequence[float] | None = None, k: int = 1) -> list[T]:
        if not values:
            raise ValueError("choices_requires_non_empty_values")
        if k < 0:
            raise ValueError("choices_k_must_not_be_negative")
        if weights is not None and len(weights) != len(values):
            raise ValueError("weights_length_must_match_values")
        result = self._rng.choices(values, weights=weights, k=k)
        self.draw_count += k
        return result

    def uniform(self, minimum: float, maximum: float) -> float:
        if minimum > maximum:
            raise ValueError("minimum_must_not_exceed_maximum")
        return self._drawn(self._rng.uniform(minimum, maximum))

    def shuffle(self, values: list[T]) -> None:
        self._rng.shuffle(values)
        self.draw_count += max(0, len(values) - 1)

    def state_digest(self) -> str:
        return hashlib.sha256(pickle.dumps(self._rng.getstate(), protocol=4)).hexdigest()


class IsolatedRepository(Generic[K, T]):
    """Deep-copying in-memory repository with explicit transaction snapshots."""

    def __init__(self, items: Iterable[tuple[K, T]] = ()) -> None:
        self._items: dict[K, T] = {key: copy.deepcopy(value) for key, value in items}
        self._snapshot: dict[K, T] | None = None

    @property
    def transaction_active(self) -> bool:
        return self._snapshot is not None

    def begin(self) -> None:
        if self.transaction_active:
            raise RuntimeError("sandbox_transaction_already_active")
        self._snapshot = copy.deepcopy(self._items)

    def get(self, key: K) -> T | None:
        value = self._items.get(key)
        return copy.deepcopy(value) if value is not None else None

    def save(self, key: K, value: T) -> None:
        if not self.transaction_active:
            raise RuntimeError("sandbox_transaction_required")
        self._items[key] = copy.deepcopy(value)

    def delete(self, key: K) -> None:
        if not self.transaction_active:
            raise RuntimeError("sandbox_transaction_required")
        self._items.pop(key, None)

    def commit(self) -> None:
        if not self.transaction_active:
            raise RuntimeError("sandbox_transaction_required")
        self._snapshot = None

    def rollback(self) -> None:
        if not self.transaction_active:
            raise RuntimeError("sandbox_transaction_required")
        self._items = self._snapshot or {}
        self._snapshot = None

    def export(self) -> dict[K, T]:
        return copy.deepcopy(self._items)


@dataclass(frozen=True, slots=True)
class SimulatorAdapters:
    """One isolated adapter bundle supplied to production application services."""

    clock: SimulationClockAdapter
    random: SeededRandomAdapter
    repositories: dict[str, IsolatedRepository[object, object]]

    @classmethod
    def isolated(cls, *, seed: int, start_at: datetime | None = None) -> "SimulatorAdapters":
        return cls(
            clock=SimulationClockAdapter.at_start(start_at),
            random=SeededRandomAdapter(seed),
            repositories={},
        )

    def register_repository(self, name: str, repository: IsolatedRepository[object, object]) -> None:
        key = name.strip()
        if not key:
            raise ValueError("repository_name_must_not_be_empty")
        if key in self.repositories:
            raise ValueError(f"duplicate_simulator_repository::{key}")
        self.repositories[key] = repository
