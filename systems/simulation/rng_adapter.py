from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, MutableSequence, Sequence, TypeVar

from .rng import SimulationRng

T = TypeVar("T")


class RandomModuleAdapter:
    """Subset of random module API backed by one SimulationRng instance."""

    def __init__(self, rng: SimulationRng) -> None:
        self.rng = rng

    def random(self) -> float:
        return self.rng.random()

    def randint(self, a: int, b: int) -> int:
        return self.rng.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        return self.rng.uniform(a, b)

    def choice(self, values: Sequence[T]) -> T:
        return self.rng.choice(values)

    def choices(self, population: Sequence[T], weights=None, *, cum_weights=None, k: int = 1):
        if cum_weights is not None:
            raise ValueError("cum_weights is not supported by SimulationRng adapter")
        return self.rng.choices(population, weights=weights, k=k)

    def shuffle(self, values: MutableSequence[Any]) -> None:
        self.rng.shuffle(values)


@contextmanager
def inject_module_rng(module: Any, rng: SimulationRng) -> Iterator[RandomModuleAdapter]:
    """Temporarily replace module.random without touching Python global RNG state."""
    if not hasattr(module, "random"):
        raise AttributeError(f"{getattr(module, '__name__', module)!r} has no random dependency")
    original = module.random
    adapter = RandomModuleAdapter(rng)
    module.random = adapter
    try:
        yield adapter
    finally:
        module.random = original
