# ROM Stage 18.29.3b: Event Kill Statistics

Adds persistent, exactly-once event-mob victory storage and read-only leaderboard queries.

- Receipt identity: `(event_key, terminal_event_id)`.
- Aggregate identity: `(event_key, user_id, mob_key)`.
- Ranking: kills DESC, first_reached_at ASC, user_id ASC.
- Top size: 100; page size: 10; own rank can be returned outside top 100.
- This stage does not connect combat victory, Telegram UI, drops or exchange.
