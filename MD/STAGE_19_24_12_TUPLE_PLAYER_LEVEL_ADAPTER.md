# Stage 19.24.12 — Tuple player-level adapter

## Рішення

**PASS_PENDING_MANUAL_GAME_CHECK**

Canonical story level adapter now supports the existing `db.get_player_stats()` contract `(STR, DEX, INT, WIS, STA, level)` and retains dict, Mapping, sqlite3.Row and object support. Production content and DB were not changed.
