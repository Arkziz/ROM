# ADR 21.2.6 — ROM V2 Clock and RNG abstractions

- **Status:** `ACCEPTED`
- **Clock port:** `rom_v2.application.ports.clock`
- **RNG port:** `rom_v2.application.ports.random_source`

## Clock

`Clock` exposes timezone-aware `now_utc()` and monotonic elapsed-time measurement. Domain/application code cannot call `datetime.now`, `datetime.utcnow`, `time.time` or local timezone APIs directly.

## Random source

`RandomSource` exposes explicit `random`, `randint`, `choice` and `shuffle` operations. Domain/application code cannot call the module-level `random` or `secrets` APIs for gameplay decisions. Seeds belong to composition or tests, never domain code.

## Determinism

The same initial state, command sequence, seed and controlled clock must produce the same Result and domain events. Idempotent repeats perform no additional RNG draw. Failed operations persist no RNG-dependent event.

## Production and tests

Production composition wires exactly one SystemClock and one SystemRandomSource. Tests use FakeClock and SeededRandomSource and record both seed and clock state in fixtures.

## Automated evidence

- Physical V2 exists: **False**.
- Direct time calls: **0**.
- Direct RNG calls: **0**.
- Violations: **0**.

## Next roadmap stage

Stage 21.2.7 — Configuration and secrets boundary.
