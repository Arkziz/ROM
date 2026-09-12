# Stage 18.22: Inline Map and Persistent Travel — Full Documentation

## Closure

- **Final status:** PASS
- **Closure stage:** 18.22.4
- **Production feature commits:** `d494d9511f53fa13e871932e08213fa4a0d9681d`, `b8a1975f41c631e1f36c027b2b36e97631e429a6`, `571036d9b15813e65e5f45487ac324a4d057b548`
- **Manual acceptance:** PASS
- **Database quick check:** `ok`
- **Foreign-key violations:** `0`
- **WAL/SHM manipulation:** none

## Purpose

Stage 18.22 replaces immediate ReplyKeyboard location switching with an authoritative inline world map and persistent, cancellable, server-timed travel. City is a real world node, external locations remain huntable zones, and only adjacent nodes are visible and reachable.

## Canonical world graph

```text
🏙️ city
   ↕ 60 seconds
🌿 start_path
   ↕ 60 seconds
🌲 dark_forest
   ↕ future location
```

Rules:

- `city` is non-huntable.
- `start_path` and `dark_forest` are external huntable locations.
- Every current edge is bidirectional and takes exactly 60 seconds.
- Non-neighbor nodes are hidden and rejected by the domain.
- A locked adjacent external location is visible but cannot start travel.
- `dark_forest` uses the existing level-6 unlock policy.
- A future location must be added to `WORLD_NODES` and to both sides of a symmetric edge.

## User interface

### Map mode

Opening `🗺️ Мапа` replaces the persistent keyboard with one button:

```text
🔽 Згорнути мапу
```

Navigation is inline. The available buttons are generated from the current authoritative node.

### City

```text
🚶 Вирушити у Початок Шляху
👥 Гравці локації
```

### Start Path

```text
🏙️ Повернутися у Місто
🚶 Вирушити у Темний Бір
👥 Гравці локації
```

### Dark Forest

```text
🌿 Повернутися у Початок Шляху
👥 Гравці локації
```

A future forward button is absent until the future node exists.

### Active travel

```text
🔄 Оновити
❌ Скасувати подорож
```

Refresh re-reads the authoritative row and recalculates remaining time from the unchanged `arrival_at`. Refresh does not create a row, change revision, or extend travel.

## Persistent data model

Table: `location_travels`

Columns:

```text
id
user_id
from_node
to_node
status
revision
started_at
arrival_at
cancelled_at
completed_at
created_at
updated_at
```

Statuses:

```text
active
arrived
cancelled
failed
```

Database invariants:

- One partial unique index permits at most one active travel per user.
- `from_node` cannot equal `to_node`.
- A travel row references `users.user_id`.
- Historical terminal rows remain available for audit.
- Migration owner: `049_persistent_location_travel.py`.

## Transaction semantics

### Start

`start_travel` validates the user, current node, destination, adjacency, level unlock, busy state, and absence of another active travel. It persists `started_at` and `arrival_at` but does not change `users.current_location`.

### Cancel

Cancellation succeeds only while status is active and server time is before `arrival_at`. Revision can be checked by the callback. The first terminal claim wins.

### Arrival

Arrival uses one transaction to claim the active row as `arrived` and update `users.current_location` from `from_node` to `to_node`. If the source node changed unexpectedly, the travel is marked `failed` instead of moving the player.

### Restart recovery

Startup recovery completes only overdue active travel rows. The original `arrival_at` is preserved. A background worker processes later due rows. Telegram notification occurs after the authoritative database commit and cannot roll back the location.

## Location context and keyboards

`systems/location_context_system.py` resolves UI context from authoritative state:

```text
active travel → map_kb
city          → city_kb
external node → main_kb
invalid node  → map_kb, fail-closed
```

This resolver is used after trade cancellation, trade completion, and terminal trade-input recovery. Each participant receives a keyboard based on that participant's own location.

## Guards

During active travel, the feature blocks incompatible operations before mutation:

- PvE hunting and energy consumption
- PvP duel request and acceptance
- Direct trade request and acceptance
- City actions and NPC routes
- A second travel

Travel start is also blocked while the player has an active PvE or player-interaction state.

City hunting is explicitly rejected before energy consumption or mob generation. The legacy external-location fallback must not convert `city` into `start_path`. Look Around in City renders City content and `city_kb`.

## Player discovery

`👥 Гравці локації` is an inline map action in City and external locations. It reuses the canonical same-location online presence query. The return callback edits the same message back to the current authoritative map.

## Starting and migration policy

- New characters start in `city`.
- DEV reset starts in `city`.
- Existing valid users were preserved in their existing locations during Stage 18.22.1.
- Class change and ordinary restart do not reset location.

## Testing

Automated coverage includes:

- graph symmetry and known-node validation
- temporary-DB start, cancel, arrival and recovery paths
- 59-second rejection and 60-second arrival
- one-active-travel uniqueness
- level lock and non-neighbor rejection
- inline callback and collapse-keyboard contracts
- refresh and stale callback ownership
- City players
- PvE, trade, PvP and City guards
- context-aware trade recovery
- City hunt fail-closed behavior
- runtime imports
- SQLite quick check and foreign keys

Manual acceptance verified the complete UI flow, travel, cancellation, arrival, refresh, City player list, context-aware trade recovery and the recovered hunt guard.

## Known nuances

- Telegram may retain old reply buttons visually; server-side guards remain authoritative.
- Arrival notification failure does not undo committed arrival.
- Cancellation at the same moment as arrival is resolved by the first successful terminal database claim.
- Unknown location state intentionally exposes no hunting keyboard.

## Closure result

Stage 18.22 is accepted as complete when this audit reports PASS and the closure commit is created.
