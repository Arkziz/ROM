# ROM Stage 18.30.2: Restore Simulator Parity Foundation

## Scope

- Focused `parity_foundation.py` module for orchestration contracts.
- In-place import wiring in `systems/simulation/__init__.py`.
- Isolated simulator state with no production database writes.
- Deterministic seeded RNG.
- Activity, fatigue, HP threshold, potion, repair and refine scenario policy.
- Fatigue 39 -> hunt -> 40 -> blocked -> five minutes -> 39 -> allowed.
- Metrics and source/sink gold ledger foundation.
- Lazy canonical-owner resolver without copied gameplay formulas.
- Premium items, event encounters and automatic potion purchases disabled.

## Non-scope

- Full class progression runner.
- Full PvE producer/consumer integration.
- Equipment, rune and refine automation.
- Monthly guild-resource simulation.
- 10,000-victory drop validation.

## Database guarantee

`game.db` is not modified. `game.db-wal` and `game.db-shm` are not deleted, cleared, checkpointed or used for rollback.

## Manual verification

**NOT REQUIRED.** Operator-shaped runtime smoke covers the infrastructure contract.
