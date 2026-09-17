# Stage 18.28: Event Engine Foundation Closure

## Final status

`CLOSED`

## Implemented foundation

- Explicit `EVENT_MODULES` allowlist and unique `EVENT_KEY` registry.
- Timezone-aware UTC lifecycle with `START_AT <= now < END_AT`.
- Deterministic lifecycle tests through an explicit `now`.
- Complete non-production event template for mobs, bosses, items, drops, quests, rewards, shop, statistics and handlers.
- Active-only mob, boss and drop providers.
- Registered-event item provider so inactive event items remain resolvable.
- Static event item namespace `4000..9999`.
- Permanent aligned blocks of 50 IDs, 120 blocks total, never reused.
- Startup loading and event handler registration facade.
- Normal event encounter integration with resolution order `event_normal -> boss -> elite -> normal`.
- One event encounter roll and one weighted candidate selection.
- Canonical normal mob factory for event-mob combat construction.
- Validated additive event-drop planning and canonical inventory award owner.
- Explicit defer decision for production event-boss routing.

## Zero-event production state

- Production event modules: `0`
- Production event handlers: `0`
- Production event candidates: `0`
- Production event drop rules: `0`
- Reserved event item blocks: `0`
- Event item rows: `0`
- New buttons or callbacks: `0`

## Canonical invariants

1. `_template` is never registered as production content.
2. Event handlers are registered for enabled modules and callbacks must recheck active lifecycle before mutation.
3. Event mobs and rewards provide data; canonical systems retain combat and inventory ownership.
4. Event item IDs belong to the permanent block assigned to their `EVENT_KEY`.
5. Unused IDs remain reserved to the same event owner.
6. Generated equipment continues to use the generated namespace from `10000`.
7. Event drops are additive and do not replace ordinary loot.
8. Event-boss routing is deferred until a real event boss is approved and manually verified.
9. `game.db-wal` and `game.db-shm` are never manipulated by patches.

## Deferred to Stage 18.29

- First production event package.
- First permanent event item-block assignment.
- Real event item definitions and catalog rows.
- Real event mob and event currency.
- Atomic event-shop exchange and any required persistence.
- Telegram event UI and direct gameplay acceptance.

## Verification

All maintained Stage 18.28 smoke tests pass, the production database remains unchanged and zero-event gameplay parity is preserved. Manual game verification is not required for this closure because no production event content exists.
