# Stage 21.14.2a — Refined event schedules and rewards contract

- Status: **PASS**
- Contract: **REFINED_REVIEW_REQUIRED**
- Next action: **REVIEW_AND_RESOLVE_UNRESOLVED_BEFORE_MUTATION**
- Production mutation: **NO**
- Production SQLite access: **NO**
- Manual in-game check: **NOT REQUIRED**

## Targeted authoritative/corroborating sources

- `events/__init__.py`: enablement, exact_once, identity, namespace, presentation, schedule, timezone
- `events/_template/__init__.py`: rewards
- `events/_template/bosses.py`: parsed
- `events/_template/config.py`: enablement, identity, presentation, schedule, timezone
- `events/_template/drops.py`: parsed
- `events/_template/handlers.py`: parsed
- `events/_template/items.py`: namespace
- `events/_template/mobs.py`: parsed
- `events/_template/quests.py`: parsed
- `events/_template/rewards.py`: rewards
- `events/_template/shop.py`: parsed
- `events/_template/statistics.py`: parsed
- `events/item_namespace.py`: identity, namespace
- `events/test_event_2026/__init__.py`: enablement, identity, rewards, schedule, timezone
- `events/test_event_2026/bosses.py`: parsed
- `events/test_event_2026/config.py`: enablement, identity, presentation, schedule, timezone
- `events/test_event_2026/drops.py`: identity
- `events/test_event_2026/handlers.py`: parsed
- `events/test_event_2026/items.py`: identity, namespace, rewards
- `events/test_event_2026/mobs.py`: identity
- `events/test_event_2026/quests.py`: parsed
- `events/test_event_2026/rewards.py`: rewards
- `events/test_event_2026/shop.py`: identity, rewards
- `events/test_event_2026/statistics.py`: identity, presentation
- `handlers/event_ui.py`: enablement, identity, presentation, rewards, schedule, timezone
- `migrations/050_event_kill_statistics.py`: exact_once, identity
- `migrations/051_event_shop_exchange.py`: exact_once, identity, rewards
- `systems/event_item_catalog_system.py`: namespace
- `systems/event_shop_system.py`: enablement, exact_once, identity, presentation, rewards, timezone
- `systems/event_statistics_system.py`: exact_once, identity, timezone

## Refined boundaries

- **identity:** events package/registry candidates only; exact owner requires evidence review
- **schedule:** event config plus registry selection candidates; boundary inclusivity must follow source
- **reward_definition:** event rewards module candidate; do not infer grant timing from definitions
- **exact_once:** event statistics/shop persistence candidates only; scopes must not be merged
- **presentation:** event UI is presentation evidence, not scheduler authority

## Scheduler

- Dedicated scheduler found: **False**
- Do not invent APScheduler, cron, worker or background task. If absent, preserve evaluation-on-access behavior.

## Unresolved

- `eligibility_policy_not_explicit_in_targeted_sources`
- `announcement_policy_not_explicit_in_targeted_sources`

## Prohibitions

- Do not invent an event schedule, reward amount, event type, eligibility condition, announcement text or timezone.
- Do not merge shop-exchange idempotency with combat-statistics exact-once semantics.
- Do not use PvP, auction, quest or simulator keyword matches as event policy.
- Do not authorize V2 mutation while unresolved semantic items remain.
