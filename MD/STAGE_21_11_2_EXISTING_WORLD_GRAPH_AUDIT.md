# Stage 21.11.2 - Existing V1 World Graph audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- Implementation authorized: **False**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Canonical V1 evidence

- Authoritative owner: `data/location_graph.py`
- World nodes: `city`, `start_path`, `dark_forest`
- Huntable locations: `start_path`, `dark_forest`
- Graph: `city <-> start_path <-> dark_forest`
- Direct `city <-> dark_forest` route: **absent**
- Static travel duration: **20 seconds**
- Transport requirements in graph owner: **bounded absence**

## Contract matrix

- `WORLD_GRAPH_OWNER_AND_SCHEMA`: **V1_CONFIRMED** - data/location_graph.py owns static nodes, graph, travel duration and validation.
- `CANONICAL_NODE_IDENTITY_AND_KIND`: **V1_CONFIRMED** - city, start_path and dark_forest are the only current world nodes; huntability is explicit.
- `ADJACENCY_SYMMETRY_AND_CONNECTIVITY`: **V1_CONFIRMED** - The connected graph is city <-> start_path <-> dark_forest and has two undirected edges.
- `DIRECT_ROUTE_ABSENCE_POLICY`: **V1_CONFIRMED** - No city <-> dark_forest edge exists; absence must not be converted into an inferred route.
- `TRAVEL_REQUIREMENTS_AND_UNLOCK_BOUNDARY`: **REVIEW_REQUIRED** - No transport-requirement structure was found in the owner; exact relationship to unlock policy requires semantic refinement.
- `UNKNOWN_NODE_FAIL_CLOSED_POLICY`: **REVIEW_REQUIRED** - Existing functions are discovered, but exact unknown-node semantics require semantic refinement.
- `LOCATION_CATALOG_AND_TRAVEL_AGGREGATE_BOUNDARY`: **REVIEW_REQUIRED** - Ownership between static graph, location content and future travel state requires explicit V2 contract boundaries.
- `CONSUMER_ALLOWLIST_AND_SHADOW_GRAPH_POLICY`: **REVIEW_REQUIRED** - Known route presentation is covered, but all graph consumers and shadow definitions require exhaustive resolution.

## Unresolved contracts

- `TRAVEL_REQUIREMENTS_AND_UNLOCK_BOUNDARY`
- `UNKNOWN_NODE_FAIL_CLOSED_POLICY`
- `LOCATION_CATALOG_AND_TRAVEL_AGGREGATE_BOUNDARY`
- `CONSUMER_ALLOWLIST_AND_SHADOW_GRAPH_POLICY`

No new node, route, transport requirement or travel rule is authorized by this audit.

## Next patch

`patch_21_11_2a_refine_world_graph_contract.py`
