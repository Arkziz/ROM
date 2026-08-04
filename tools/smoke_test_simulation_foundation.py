from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from datetime import datetime, timezone

from systems.simulation import (
    SimulationCharacter, SimulationClock, SimulationConfig, SimulationEquipment,
    SimulationInventory, SimulationInventoryItem, SimulationMetrics, SimulationRng,
    SimulationRunResult, SimulationState, write_simulation_reports,
)


def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build(seed=12345, capacity=40):
    config = SimulationConfig("warrior", target_level=20, profile_key="regular", seed=seed, inventory_capacity=capacity)
    clock = SimulationClock.at_start()
    clock.advance(hours=17)
    rng = SimulationRng(seed)
    sequence = [rng.randint(1, 100), round(rng.uniform(0.0, 1.0), 8), rng.choice(["a", "b", "c"])]
    inventory = SimulationInventory(capacity=capacity, reserve_slots=2)
    item = SimulationInventoryItem(inventory.allocate_id(), 201, "Potion", "potion", quantity=3, max_stack=20)
    inventory.items.append(item)
    state = SimulationState("foundation_seed_12345", SimulationCharacter("warrior"), inventory, SimulationEquipment())
    metrics = SimulationMetrics()
    metrics.increment("foundation_events")
    metrics.set_gauge("inventory_utilization", inventory.utilization)
    metrics.record("foundation_ready", clock.iso(), sequence=sequence)
    result = SimulationRunResult(
        state.run_id, config.schema_version, config.to_dict(), config.fingerprint(), seed,
        rng.snapshot(), "2026-01-01T00:00:00+00:00", clock.iso(), state.to_dict(), metrics.to_dict(),
    )
    return result.to_dict(), sequence


def main():
    first, seq1 = build()
    second, seq2 = build()
    assert seq1 == seq2
    assert digest(first) == digest(second)
    config40 = SimulationConfig("mage", inventory_capacity=40)
    config60 = SimulationConfig("mage", inventory_capacity=60)
    assert config40.fingerprint() != config60.fingerprint()
    assert not SimulationClock(datetime(2026, 1, 1, 16, 59, tzinfo=timezone.utc)).is_active(config40.profile)
    assert SimulationClock(datetime(2026, 1, 1, 17, 0, tzinfo=timezone.utc)).is_active(config40.profile)
    try:
        SimulationConfig("mage", pvp_enabled=True)
        raise AssertionError("PvP guard failed")
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as temp:
        jp, mp = write_simulation_reports(first, Path(temp))
        loaded = json.loads(jp.read_text(encoding="utf-8"))
        assert loaded == first
        assert "ROM Simulation Report" in mp.read_text(encoding="utf-8")
    forbidden = ("import db", "from db", "sqlite3", "telebot")
    package = Path("systems/simulation")
    for path in package.glob("*.py"):
        text = path.read_text(encoding="utf-8-sig")
        assert not any(token in text for token in forbidden), (path, forbidden)
    print("[OK] Simulation foundation smoke test")
    print("- deterministic seeded RNG: PASS")
    print("- deterministic config fingerprint: PASS")
    print("- SimulationClock active windows: PASS")
    print("- inventory capacities 40/60: PASS")
    print("- JSON/Markdown reports: PASS")
    print("- PvP deferred guard: PASS")
    print("- database/telegram imports: 0")


if __name__ == "__main__":
    main()
