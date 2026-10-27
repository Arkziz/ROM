from __future__ import annotations

import ast
import random
import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rom_v2.domain.simulator_adapters import (
    IsolatedRepository,
    SeededRandomAdapter,
    SimulationClockAdapter,
    SimulatorAdapters,
)


@dataclass
class Value:
    amount: int


class SimulatorAdaptersTests(unittest.TestCase):
    def test_clock_is_deterministic_aware_utc_and_forward_only(self) -> None:
        start = datetime(2026, 1, 1, 2, tzinfo=timezone(timedelta(hours=2)))
        clock = SimulationClockAdapter.at_start(start)
        self.assertEqual(clock.now_utc(), datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(clock.advance(timedelta(minutes=5)), datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc))
        with self.assertRaisesRegex(ValueError, "cannot_move_backwards"):
            clock.advance(timedelta(seconds=-1))
        with self.assertRaisesRegex(ValueError, "timezone_aware"):
            SimulationClockAdapter.at_start(datetime(2026, 1, 1))

    def test_seeded_rng_replays_and_does_not_change_global_random_state(self) -> None:
        global_before = random.getstate()
        first = SeededRandomAdapter(14643)
        second = SeededRandomAdapter(14643)
        self.assertEqual([first.random() for _ in range(5)], [second.random() for _ in range(5)])
        self.assertEqual(first.draw_count, 5)
        self.assertEqual(first.state_digest(), second.state_digest())
        self.assertEqual(global_before, random.getstate())

    def test_rng_supports_canonical_subset_and_fails_closed(self) -> None:
        rng = SeededRandomAdapter(7)
        self.assertIn(rng.choice((1, 2, 3)), (1, 2, 3))
        self.assertEqual(len(rng.choices((1, 2), weights=(1.0, 2.0), k=3)), 3)
        sample = [1, 2, 3]
        rng.shuffle(sample)
        self.assertEqual(sorted(sample), [1, 2, 3])
        with self.assertRaisesRegex(ValueError, "non_empty"):
            rng.choice(())
        with self.assertRaisesRegex(ValueError, "weights_length"):
            rng.choices((1, 2), weights=(1.0,), k=1)

    def test_repository_requires_transaction_and_rolls_back_deep_copies(self) -> None:
        repo = IsolatedRepository(((1, Value(5)),))
        loaded = repo.get(1)
        loaded.amount = 99
        self.assertEqual(repo.get(1).amount, 5)
        with self.assertRaisesRegex(RuntimeError, "transaction_required"):
            repo.save(1, Value(6))
        repo.begin()
        repo.save(1, Value(10))
        repo.save(2, Value(20))
        repo.rollback()
        self.assertEqual(repo.get(1).amount, 5)
        self.assertIsNone(repo.get(2))

    def test_repository_commit_persists_only_inside_sandbox(self) -> None:
        source = Value(1)
        repo = IsolatedRepository(((1, source),))
        repo.begin()
        repo.save(1, Value(2))
        repo.commit()
        self.assertEqual(repo.get(1).amount, 2)
        self.assertEqual(source.amount, 1)

    def test_adapter_bundle_isolated_and_duplicate_repository_fails(self) -> None:
        bundle = SimulatorAdapters.isolated(seed=12)
        repository = IsolatedRepository()
        bundle.register_repository("characters", repository)
        self.assertIs(bundle.repositories["characters"], repository)
        with self.assertRaisesRegex(ValueError, "duplicate_simulator_repository"):
            bundle.register_repository("characters", IsolatedRepository())

    def test_flat_module_contains_no_sqlite_or_production_paths(self) -> None:
        path = Path(__file__).resolve().parents[1] / "rom_v2/domain/simulator_adapters.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("sqlite3", imports)
        self.assertNotIn("os", imports)
        self.assertNotIn("pathlib", imports)
        self.assertNotIn("systems.simulation", source)
        self.assertNotIn("game.db", source)

    def test_adapter_does_not_define_gameplay_formula_names(self) -> None:
        path = Path(__file__).resolve().parents[1] / "rom_v2/domain/simulator_adapters.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {
            node.name.lower()
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        forbidden = {"calculate_damage", "calculate_hp", "calculate_attack", "calculate_defense", "calculate_rewards", "generate_loot"}
        self.assertFalse(names & forbidden)


if __name__ == "__main__":
    unittest.main()
