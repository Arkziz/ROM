# Stage 21.14.2c — Event schedules/rewards implementation

## Result

- Status: **API_READY_IMPLEMENTED**
- Runtime/Telegram wiring: **NOT CONNECTED**
- Production persistence wiring: **NOT CONNECTED**
- Scheduler/background worker: **NOT IMPLEMENTED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Implemented contract

- Canonical non-empty `event_key` identity with fail-closed duplicate detection.
- Timezone-aware schedule values normalized to UTC.
- Half-open active interval: `start_at <= now < end_at`.
- Deterministic evaluation on access with a caller-provided clock instant.
- Lifecycle states: upcoming, active, completed, disabled.
- Eligibility limited to the confirmed enabled gate and active schedule window.
- Immutable direct-reward catalogs.
- Empty direct-reward catalog for `test_event_2026` parity.

## Explicit boundaries

Event drops and event-shop offers remain separate systems. This stage does not
invent a direct event reward, scheduler, push announcement channel, level/class/
location eligibility, retry policy, Telegram handler, database repository, or
production migration.

## Automated verification

`tools/check_stage_21_14_2c_event_schedules_rewards.py` runs deterministic unit
tests for boundaries, UTC normalization, disabled events, duplicate/unknown
identity handling, and the empty direct-reward parity contract.
