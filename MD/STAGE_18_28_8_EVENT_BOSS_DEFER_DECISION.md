# Stage 18.28.8: Event Boss Integration Defer Decision

## Status

`DEFER_EVENT_BOSS_INTEGRATION`

## Decision

Event-boss production integration is deferred until the first approved production event that explicitly requires an event boss.

No event-boss selector, routing branch, combat branch, database migration or production content is added at this stage.

## Rationale

The current production tree contains no production event package, event boss or event item. The future-facing provider contracts already exist, while adding routing now would create unexercised behavior without a real gameplay scenario.

## Canonical Ownership

The existing boss system remains authoritative for:

- boss schema and location ownership;
- level eligibility;
- canonical primary-stat and derived-stat construction;
- boss combat state;
- skills and action selection;
- enrage behavior;
- ordinary boss encounter probability;
- ordinary boss, elite and normal fallback behavior.

The event system currently owns only the future-facing `get_boss_candidates()` and `collect_event_boss_candidates()` contracts.

## Mandatory Future Acceptance Criteria

A future event-boss integration must:

1. Validate tuple candidates with unique `event_key` and `boss_key`.
2. Filter candidates by active lifecycle, `location_id` and player level.
3. Preserve one mutually exclusive result for each hunt.
4. Build boss statistics through the canonical boss primary-stat pipeline.
5. Attach `is_event`, `event_key` and `event_boss_key` metadata.
6. Reuse canonical boss state, skills, enrage and combat actions.
7. Route event-boss rewards through the validated additive event-drop pipeline.
8. Preserve ordinary boss, elite and normal fallback behavior.
9. Include deterministic selection and zero-event parity tests.
10. Require direct manual gameplay verification with a real production event boss.

## Current Production Effect

- Production event modules: `0`
- Production event bosses: `0`
- Production behavior change: `FALSE`
- Database migration: `NONE`
- Manual game check: `NOT REQUIRED`
- WAL/SHM: `NOT MANIPULATED`
