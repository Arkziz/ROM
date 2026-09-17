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
