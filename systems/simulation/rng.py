from __future__ import annotations

from hashlib import sha256
import pickle
import random
from typing import Any, MutableSequence, Sequence, TypeVar

T = TypeVar("T")


class SimulationRng:
    """Seeded RNG wrapper. No module-level random state is used."""

    def __init__(self, seed: int) -> None:
        self.seed = int(seed)
        self._random = random.Random(self.seed)
        self.draw_count = 0

    def _draw(self) -> None:
        self.draw_count += 1

    def random(self) -> float:
        self._draw()
        return self._random.random()

    def randint(self, a: int, b: int) -> int:
        self._draw()
        return self._random.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        self._draw()
        return self._random.uniform(a, b)

    def choice(self, values: Sequence[T]) -> T:
        if not values:
            raise IndexError("cannot choose from an empty sequence")
        self._draw()
        return self._random.choice(values)

    def choices(self, values: Sequence[T], weights=None, k: int = 1):
        if not values:
            raise IndexError("cannot choose from an empty sequence")
        self._draw()
        return self._random.choices(values, weights=weights, k=k)

    def shuffle(self, values: MutableSequence[Any]) -> None:
        self._draw()
        self._random.shuffle(values)

    def state_digest(self) -> str:
        return sha256(pickle.dumps(self._random.getstate(), protocol=4)).hexdigest()

    def snapshot(self) -> dict:
        return {"seed": self.seed, "draw_count": self.draw_count, "state_digest": self.state_digest()}
