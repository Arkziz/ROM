# ROM Seasonal Events

`events/` is the canonical package for seasonal event content.

## Stage 18.28.2 contract

- `EVENT_MODULES` is an explicit allowlist. Automatic package discovery is forbidden.
- `events._template` is never loaded or registered as a production event.
- `EVENT_KEY` is unique, stable, non-empty, and does not start with `_`.
- `ENABLED` is a boolean code-level gate.
- `START_AT` and `END_AT` are timezone-aware datetimes normalized to UTC.
- The active interval is `START_AT <= now < END_AT`.
- `get_active_events(now=...)` supports deterministic tests.
- Handler, encounter, drop, item, shop, persistence and UI integration are deferred.

## Stage 18.28.3 content-provider contract

Each event package may expose these public providers from its package `__init__.py`:

- `get_mob_candidates(context) -> tuple`
- `get_boss_candidates(context) -> tuple`
- `get_drop_rules(context) -> tuple`
- `get_items() -> tuple`
- `handlers.register(bot)`

Missing optional providers mean an empty contribution. A present provider must be callable and return a tuple. Registered item definitions are collected from all registered events so items can remain resolvable after `END_AT`. Mob, boss, and drop providers are collected only from active events. Handler registration uses enabled events and active state must be checked again inside every callback.

The template contains no production content, no item IDs, no callbacks, no database writes, and no automatic registration.

## Stage 18.28.4a static event item namespace

- Static event item IDs are permanently reserved in `4000..9999`.
- The namespace contains 120 aligned blocks of 25 IDs.
- One approved `EVENT_KEY` owns one permanent block. Unused IDs remain reserved to that owner.
- Blocks and item IDs are never reused by another event.
- Randomly generated equipment continues to use the generated equipment namespace.
- `EVENT_ITEM_BLOCKS` remains empty until the first production event is approved.
- No item rows are created until a real event defines content.

## Stage 18.28.8 event boss defer decision

Production event-boss routing is intentionally deferred until the first approved production event that explicitly requires an event boss.

Current guarantees:

- `get_boss_candidates()` and `collect_event_boss_candidates()` remain future-facing provider contracts.
- No production event-boss selector or encounter branch exists.
- Canonical boss schema, primary-stat construction, combat state, skills and enrage remain authoritative.
- The ordinary boss, elite and normal fallback behavior remains unchanged.
- Future event-boss integration must attach `is_event`, `event_key` and `event_boss_key` metadata.
- Future event-boss drops must reuse the validated additive event-drop pipeline.
- A real event boss requires deterministic automated tests and direct manual gameplay verification.

## Stage 18.28 foundation closure

The event engine foundation is closed and ready for Stage 18.29 pilot content. Registry, UTC lifecycle, content providers, static item namespace, startup handler registration, normal event encounters and additive event drops are production extension points with zero-event parity. Event-boss routing remains explicitly deferred until a real approved event requires it.

## Stage 18.29.1a block-extension policy

One EVENT_KEY initially receives one permanent 25-ID block. If necessary, the same EVENT_KEY may receive another explicit free block in a reviewed patch. Blocks are never automatically expanded or reused.
