# Stage 21.14.3a — Inactivity reminders contract refinement

- Status: **PASS**
- Decision: **GO_TO_PARITY_RESOLUTION**
- Production mutation: **NO**
- Production SQLite opened: **NO**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Refined contract

### threshold
- Status: **CONFIRMED**
- Contract: A reminder becomes due only after seven full 24-hour days since canonical last_activity_at; equality at the threshold is due.

### clock
- Status: **CONFIRMED**
- Contract: Eligibility is evaluated against an explicit timezone-aware UTC instant. Unit tests must use an injected deterministic clock, never wall-clock sleeps.

### cycle_identity
- Status: **CONFIRMED**
- Contract: The inactivity cycle is anchored to the last_activity_at value used for eligibility. At most one successful reminder receipt may exist per user and cycle anchor.

### new_cycle
- Status: **CONFIRMED**
- Contract: A later canonical last_activity_at creates a distinct cycle after another seven-full-days interval; an earlier receipt must not suppress the new cycle.

### persistence
- Status: **CONFIRMED**
- Contract: Successful reminder delivery is represented by persistent inactivity_reminders evidence. In-memory flags are not authoritative across restarts.

### delivery_boundary
- Status: **CONFIRMED**
- Contract: Eligibility selection, Telegram delivery, and durable success receipt are distinct boundaries. A failed delivery must not be recorded as successfully sent.

### scheduler_scope
- Status: **REFINED_BOUNDARY**
- Contract: This contract does not invent scheduler cadence, startup timing, batch size, retry backoff, concurrency locking, message text, or recipient opt-out semantics unless authoritative V1 evidence explicitly owns them.

### v2_scope
- Status: **REFINED_BOUNDARY**
- Contract: A later implementation may create API-ready domain/service ports only after parity resolution; Telegram runtime and production persistence wiring remain out of scope until explicitly authorized.

## Unresolved

- None. The contract may proceed to Stage 21.14.3b parity resolution.

## Prohibitions

- Do not invent reminder text, scheduler cadence, retry policy, opt-out policy, or batch limits.
- Do not equate candidate selection with successful Telegram delivery.
- Do not record a successful reminder before delivery succeeds.
- Do not use process-local memory as the exact-once authority.
- Do not connect V2 runtime, Telegram, or production persistence during refinement.
- Do not open or manipulate game.db, game.db-wal, or game.db-shm.

## Evidence owners

- `data/guild_resource_policy.py`
- `data/story_quest_hierarchy.py`
- `db_modules/dev_compat.py`
- `handlers/about_game.py`
- `handlers/admin_crystal_credit.py`
- `handlers/attribute_allocation.py`
- `handlers/auction_house.py`
- `handlers/blacksmith.py`
- `handlers/blacksmith_repair_confirm.py`
- `handlers/city.py`
- `handlers/combat.py`
- `handlers/contracts.py`
- `handlers/crystal_shop.py`
- `handlers/daily.py`
- `handlers/dev.py`
- `handlers/event_ui.py`
- `handlers/external_links.py`
- `handlers/fatigue_artifact.py`
- `handlers/guild.py`
- `handlers/inventory.py`
- `handlers/map.py`
- `handlers/name_rune.py`
- `handlers/player_interaction.py`
- `handlers/player_rankings.py`
- `handlers/profile.py`
- `handlers/pvp_interaction.py`
- `handlers/pvp_round_ui.py`
- `handlers/refine.py`
- `handlers/runes.py`
- `handlers/start.py`
- `handlers/story_boss_invocation_wiring.py`
- `handlers/story_quest_npc_runtime.py`
- `handlers/story_quests.py`
- `handlers/timed_exp_bonus.py`
- `handlers/world_chronicles.py`
- `main.py`
- `systems/auction_house_system.py`
- `systems/event_shop_system.py`
- `systems/guild_resource_system.py`
- `systems/inactivity_reminder_system.py`
- `systems/notifications.py`
- `systems/player_interaction_system.py`
- `systems/pve_auto_escape_system.py`
- `systems/telegram_rate_limit.py`
- `systems/travel_system.py`
- `tests_v2/test_premium_combat.py`
- `systems/inactivity_reminder_system.py`
- `systems/notifications.py`
