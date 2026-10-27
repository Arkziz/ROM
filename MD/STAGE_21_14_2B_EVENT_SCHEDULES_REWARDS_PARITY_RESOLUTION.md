# Stage 21.14.2b — Event schedules/rewards parity resolution

- Status: **PASS**
- Decision: **PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED**
- Production mutation: **NO**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Resolved contract

### identity
- **RESOLVED**
- EVENT_KEY is canonical; registry/config identity must match and duplicate keys fail closed.
- Owners: `events/__init__.py`, `event config.py`

### schedule
- **RESOLVED**
- START_AT and END_AT are timezone-aware instants normalized to UTC; START_AT < END_AT; active interval is start-inclusive and end-exclusive.
- Owners: `events/__init__.py`, `events/test_event_2026/config.py`

### clock
- **RESOLVED**
- Activity is evaluated on access against supplied/current UTC. No event scheduler owner exists, so cron, APScheduler, worker cadence, auto-start/stop and restart catch-up must not be invented.
- Owners: `events/__init__.py`, `handlers/event_ui.py`

### timezone
- **RESOLVED**
- Domain comparison uses aware UTC. Europe/Kyiv conversion belongs to test_event_2026 configuration and is not a global policy for future events.
- Owners: `events/test_event_2026/config.py`

### eligibility
- **RESOLVED**
- Generic eligibility is ENABLED plus active window and matching event identity. No level, class, location, premium, guild or account-age gate is evidenced.
- Owners: `events/__init__.py`, `systems/event_shop_system.py`

### rewards
- **RESOLVED**
- test_event_2026 EVENT_REWARDS is empty, so no direct scheduled/completion reward may be ported. Drops and shop offers are separate authoritative mechanisms.
- Owners: `events/test_event_2026/rewards.py`, `events/test_event_2026/shop.py`

### shop_exact_once
- **RESOLVED**
- Exchange requires caller idempotency_key backed by persistent uniqueness; replay must not debit or grant twice.
- Owners: `systems/event_shop_system.py`, `migrations/051_event_shop_exchange.py`

### statistics_exact_once
- **RESOLVED**
- Victory receipt is deduplicated by event_key plus terminal_event_id; one terminal encounter cannot increment aggregates twice.
- Owners: `systems/event_statistics_system.py`, `migrations/050_event_kill_statistics.py`

### announcements
- **RESOLVED**
- V1 establishes pull/read event UI only. No push scheduler, recipient/retry policy or delivery exact-once contract is evidenced.
- Owners: `handlers/event_ui.py`

### lifecycle
- **RESOLVED**
- Derived states are upcoming before START_AT, active inside the enabled half-open window, and completed/read-only at or after END_AT.
- Owners: `handlers/event_ui.py`

## Prohibitions

- No invented scheduler or background worker.
- No invented direct event reward.
- No invented eligibility gate.
- No runtime, Telegram or production persistence wiring in Stage 21.14.2c.
- No game.db-wal/game.db-shm manipulation.

## Authorization

Stage 21.14.2c may implement only this API-ready contract. New event content, runtime wiring, Telegram dispatch, a scheduler and production persistence integration remain out of scope.
