"""Injected random-source port for deterministic ROM V2 behavior."""
from __future__ import annotations

from typing import Protocol, TypeVar

ChoiceT = TypeVar("ChoiceT")


class RandomSource(Protocol):
    """Expose explicit gameplay random operations without hidden reseeding."""

    def random(self) -> float:
        """Return a floating-point draw in the half-open range [0, 1)."""
        ...

    def randint(self, minimum: int, maximum: int) -> int:
        """Return an integer from the inclusive range."""
        ...

    def choice(self, values: tuple[ChoiceT, ...]) -> ChoiceT:
        """Return one value from a validated non-empty sequence."""
        ...

    def shuffle(self, values: list[ChoiceT]) -> None:
        """Shuffle the supplied mutable sequence through the injected source."""
        ...
