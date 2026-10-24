# Stage 21.11.2a - Refined World Graph contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Refined contracts: **4**
- Remaining unresolved contracts: **4**
- Implementation authorized: **False**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Confirmed ownership

- Static world graph, node metadata and 20-second duration: `data/location_graph.py`
- Location content and unlock thresholds: `data/locations.py`
- Route prose: `data/travel_presentation.py`
- Persistent active-travel aggregate: `systems/travel_system.py`
- Telegram map consumer: `handlers/map.py`
- Location context consumer: `systems/location_context_system.py`

## Refined unresolved contracts

### TRAVEL_REQUIREMENTS_AND_UNLOCK_BOUNDARY

Classification: **REVIEW_REQUIRED**

Confirmed:

- Static graph edges have no item, ticket, fare or mount requirement structure.
- Map availability combines adjacency with location unlock checks.
- Travel aggregate independently rejects non-adjacent routes.

Remaining question: Resolve the exact V2 ordering and responsibility split between adjacency, destination unlock and travel command validation.

### UNKNOWN_NODE_FAIL_CLOSED_POLICY

Classification: **REVIEW_REQUIRED**

Confirmed:

- get_world_node returns None for an unknown ID.
- get_adjacent_nodes returns an empty tuple for an unknown ID.
- are_adjacent returns False when either endpoint cannot form a canonical edge.

Remaining question: Resolve one explicit V2 public API contract so lookup, query and command paths do not diverge between None, empty tuple, False and typed errors.

### LOCATION_CATALOG_AND_TRAVEL_AGGREGATE_BOUNDARY

Classification: **REVIEW_REQUIRED**

Confirmed:

- data/location_graph.py owns static nodes, adjacency and 20-second duration.
- data/locations.py owns huntable location content and unlock thresholds.
- systems/travel_system.py owns active travel lifecycle and persistence.

Remaining question: Resolve the V2 application/domain port boundary without moving persistence or active-travel state into the static graph owner.

### CONSUMER_ALLOWLIST_AND_SHADOW_GRAPH_POLICY

Classification: **REVIEW_REQUIRED**

Confirmed:

- handlers/map.py consumes adjacency, nodes and duration for map presentation.
- systems/travel_system.py consumes adjacency and duration for travel commands.
- systems/location_context_system.py consumes canonical node identity/context.
- data/travel_presentation.py owns route prose but not graph connectivity.

Remaining question: Resolve the exhaustive V2 consumer allowlist and forbid editable duplicate graph definitions in presentation, handlers, tests and adapters.

No new node, route, transport requirement, unlock rule, persistence behavior or runtime integration is authorized.

## Next patch

`patch_21_11_2b_resolve_world_graph_parity.py`
