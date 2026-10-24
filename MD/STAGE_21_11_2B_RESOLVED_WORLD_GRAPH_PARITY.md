# Stage 21.11.2b - Resolved World Graph parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **4/4**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Canonical graph

- Nodes: `city`, `start_path`, `dark_forest`
- Edges: `city <-> start_path <-> dark_forest`
- Direct `city <-> dark_forest` edge: **absent**
- Duration: **20 seconds**
- Transport requirements: **none**

## Resolutions

### TRAVEL_REQUIREMENTS_AND_UNLOCK_BOUNDARY

Graph adjacency is checked first. A huntable destination must then pass the Location Catalog unlock threshold. City is a non-huntable world node and has no location-level gate. No item, ticket, fare, mount or other transport requirement exists. Travel commands must reject non-adjacent routes before creating aggregate state.

### UNKNOWN_NODE_FAIL_CLOSED_POLICY

Pure query APIs preserve V1-compatible non-throwing semantics: node lookup returns None, adjacency enumeration returns an empty tuple, and adjacency predicate returns False. Definition validation raises for malformed canonical content. Command paths convert unknown source or destination into explicit unknown_node rejection before any state mutation.

### LOCATION_CATALOG_AND_TRAVEL_AGGREGATE_BOUNDARY

World Graph owns immutable node metadata, exact adjacency and the 20-second duration. Location Catalog owns huntable content, localized location identity and unlock levels. Travel aggregate owns active-trip identity, source, destination, timestamps, revision, terminal state and persistence. The static graph never opens SQLite or stores per-user state.

### CONSUMER_ALLOWLIST_AND_SHADOW_GRAPH_POLICY

Allowed World Graph consumers are Location Catalog referential validation, future Travel application/domain orchestration, map/presentation adapters, location-context resolution, tests and smoke validators. Presentation text may be keyed by canonical directed edges but cannot define connectivity. Handlers, adapters and tests cannot own editable node or adjacency catalogs.

## Implementation boundary

Only a pure immutable World Graph API, validation, focused tests and a smoke verifier are authorized. Active travel persistence, SQLite, Telegram/runtime wiring, new nodes, new routes and transport requirements remain forbidden.

## Next patch

`patch_21_11_2c_implement_world_graph.py`
