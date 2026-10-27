# Stage 21.14.3c — Inactivity reminders implementation

## Result

- Status: **API_READY_IMPLEMENTED**
- Threshold: **7 full days from `last_activity_at`**
- Exact-once boundary: **one successful reminder per activity cycle**
- Runtime/Telegram/persistence adapters: **NOT CONNECTED**
- Scheduler/background loop: **NOT IMPLEMENTED**
- Reminder message content: **NOT INVENTED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Implemented API-ready contract

- Timezone-aware timestamps are normalized to UTC.
- The reminder becomes due at `last_activity_at + 7 days`, including the exact boundary.
- A deterministic cycle key is derived from `user_id` and normalized `last_activity_at`.
- A delivered cycle key suppresses all repeated evaluations of the same cycle.
- A changed `last_activity_at` creates a distinct cycle.
- A persistent-audit receipt can be built only after an external adapter confirms successful delivery.
- Evaluation uses an injected timestamp. No real clock, scheduler, Telegram call, retry loop, SQL repository or message text is embedded in the domain.

## Verification

The executable check runs deterministic tests for the seven-day boundary,
replay suppression, new-cycle behavior, timezone normalization, fail-closed
naive timestamps, immutable threshold policy and post-success audit receipts.
