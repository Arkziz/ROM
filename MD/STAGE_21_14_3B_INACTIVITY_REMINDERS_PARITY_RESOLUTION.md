# Stage 21.14.3b — Inactivity reminders parity resolution

- Status: **PASS**
- Decision: **PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED**
- Production mutation: **NO**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Resolved contract

### threshold
- Status: **RESOLVED**
- A reminder becomes eligible only after seven full 24-hour periods have elapsed since canonical last_activity_at; equality at the threshold is eligible, earlier instants are not.

### clock
- Status: **RESOLVED**
- All comparisons use timezone-aware UTC instants and an injected evaluation instant. Unit tests must not depend on wall-clock time.

### cycle_identity
- Status: **RESOLVED**
- The inactivity cycle is anchored to the observed last_activity_at value. A changed last_activity_at starts a new cycle; an unchanged value keeps the same cycle.

### exact_once
- Status: **RESOLVED**
- At most one successful reminder is recorded for one user and one inactivity-cycle anchor. Repeated evaluation of the same cycle must not send again.

### persistent_audit
- Status: **RESOLVED**
- Successful delivery is persisted in inactivity_reminders with the user, cycle anchor and delivery timestamp sufficient to enforce exact-once behavior across restarts.

### delivery_failure
- Status: **RESOLVED**
- A failed delivery must not be promoted to a successful exact-once receipt. Retry behavior remains eligible until a successful receipt exists; no retry cadence is invented.

### scheduler_boundary
- Status: **RESOLVED**
- This contract defines deterministic eligibility and receipt semantics only. It does not authorize a scheduler cadence, background worker, Telegram runtime wiring, or startup catch-up policy.

### content_boundary
- Status: **RESOLVED**
- No new reminder text, reward, penalty, eligibility gate, channel, or user preference is invented. Presentation content remains owned by confirmed V1 evidence or a later runtime-integration stage.

## Authoritative V1 evidence files

- `data/guild_resource_policy.py`
- `data/story_quest_hierarchy.py`
- `db_modules/dev_compat.py`
- `main.py`
- `systems/event_shop_system.py`
- `systems/guild_resource_system.py`
- `systems/inactivity_reminder_system.py`
- `systems/notifications.py`
- `systems/player_interaction_system.py`
- `tests_v2/test_premium_combat.py`

## Implementation authorization

Stage 21.14.3c may implement an API-ready deterministic domain contract, repository protocol, and tests. It must not connect a scheduler, Telegram runtime, production database adapter, or invent reminder content.
