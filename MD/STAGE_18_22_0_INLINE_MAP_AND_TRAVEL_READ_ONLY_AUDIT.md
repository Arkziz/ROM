# Stage 18.22.0: Inline Map and Travel Read-only Audit

**Status:** PASS
**Production mutation:** none
**Database mutation:** none

## Approved target

- World chain: `city ↔ start_path ↔ dark_forest ↔ future location`.
- Only adjacent nodes are displayed.
- Every edge takes 60 seconds in both directions.
- Map mode keeps one ReplyKeyboard button: `🔽 Згорнути мапу`.
- Location navigation, City and Players in location move to inline buttons.
- City has only the adjacent Start Path travel action.
- Start Path has return to City, travel to Dark Forest and Players in location.
- Dark Forest has return to Start Path, Players in location and a future next-location button only after that location exists.

## Current state

- Canonical external locations: `start_path, dark_forest`.
- Persistent travel tables: `none`.
- Immediate location mutation in map handler: `True`.
- Current DB default is start_path: `True`.

## Findings

- **HIGH REPLY_MAP_NAVIGATION_IS_LEGACY**: Location, city and location-player actions are currently ReplyKeyboard buttons and must move to one authoritative inline map.
- **HIGH LOCATION_SWITCH_IS_IMMEDIATE**: Current map handlers call set_current_location immediately; no 60-second travel state exists in the route.
- **HIGH PERSISTENT_TRAVEL_DOMAIN_MISSING**: No travel/journey table exists in production SQLite schema.
- **HIGH CITY_NODE_NOT_IN_LOCATION_CONFIG**: City is not a canonical location node in data/locations.py and must be introduced without making it huntable.
- **HIGH START_LOCATION_DEFAULT_CONFLICT**: Current users.current_location default is start_path; approved Stage 18.22 start node is city for new/reset characters.
- **MEDIUM LOCATION_GRAPH_MISSING**: LOCATION_ORDER exists, but there is no explicit canonical adjacency graph for city ↔ start_path ↔ dark_forest.
- **MEDIUM CITY_CONTEXT_DEPENDS_ON_EXTERNAL_LOCATION**: Current city text uses users.current_location as an external location label; Stage 18.22 must define city-node semantics and return navigation explicitly.
- **MEDIUM PLAYER_LIST_BACK_ROUTE_REUSES_MAP**: Existing player-list UI already has pi:back:map and should be adapted to the new inline map rather than duplicated.
- **MEDIUM TRAVEL_BUSY_GUARDS_REQUIRE_CONSOLIDATION**: PvE and player-interaction/PvP state owners are separate; travel start and incompatible actions require one fail-closed availability policy.
- **INFO LEVEL_UNLOCK_ALREADY_CANONICAL**: data/locations.py already owns unlock_level and is_location_unlocked; Stage 18.22 should reuse it for locked adjacent nodes.

## Recommended implementation split

1. **18.22.1 Persistent travel foundation:** graph, city node, schema, atomic start/cancel/arrival, startup recovery and worker.
2. **18.22.2 Inline map UI:** inline node actions, travel preview/status, map collapse keyboard, player-list return route and city/location keyboards.
3. **18.22.3 Cross-system guards:** PvE, PvP, direct trade/duel, city actions and stale callback protection.
4. **18.22.4 Manual acceptance and closure. — only if previous patches require separate recovery/UX passes.

## Database safety

- quick_check: `ok`.
- FK violations: `0`.
- DB unchanged: `True`.
- WAL/SHM were not manipulated.
