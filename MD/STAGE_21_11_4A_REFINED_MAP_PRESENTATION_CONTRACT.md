# Stage 21.11.4a - Refined Map Presentation contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Refined contracts: **6**
- Remaining unresolved contracts: **6**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Refined unresolved contracts

### NAVIGATION_DTO_AND_CALLBACK_POLICY

Confirmed:

- map text and inline keyboard are built separately
- callback handlers are registered inside register_map_handlers
- callback actions include open, info, preview, start, cancel and players flows
- travel cancel callback carries travel_id and revision

Remaining question: Resolve a typed navigation DTO and stable callback codec so handlers never parse presentation text or accept stale actions implicitly.

### DIRECTION_BUTTONS_AND_UNLOCK_FILTERING

Confirmed:

- directions derive from get_adjacent_nodes(current)
- huntable destination availability is filtered through is_location_unlocked
- city is not subject to a location-level unlock gate
- preview is separate from start

Remaining question: Resolve exact locked-destination visibility, ordering, labels and button/action states for every current node and level boundary.

### ACTIVE_TRAVEL_PRESENTATION_POLICY

Confirmed:

- get_active_travel switches map rendering into an in-transit state
- remaining seconds are derived from arrival_at and current UTC time
- active travel offers cancellation using travel_id and revision
- normal direction actions are not used as the active-travel primary flow

Remaining question: Resolve the DTO fields, countdown rounding, refresh behavior and stale active-travel snapshot handling.

### ARRIVAL_CANCEL_AND_REFRESH_POLICY

Confirmed:

- start and cancel callbacks re-render the map
- cancel presentation currently compresses failures into a generic terminal message
- arrival notification is produced outside the map handler by travel recovery
- refresh/open returns to the canonical map render

Remaining question: Resolve typed result-to-message mapping, arrival/cancel refresh actions, obsolete callback behavior and post-commit notification boundary.

### TECHNICAL_ID_NON_DISCLOSURE

Confirmed:

- technical IDs occur in callback/source logic
- user-facing node names are resolved through node/location metadata
- Початок Шляху and Місто are visible labels
- Темний Бір is data-driven and need not appear as a hard-coded handler literal

Remaining question: Resolve a hard invariant that technical IDs may exist only in DTO/callback payloads and never in user-visible text or fallback formatting.

### PRESENTATION_DOMAIN_BOUNDARY

Confirmed:

- handlers/map.py owns Telegram rendering and callback registration
- data/travel_presentation.py owns route prose and node-name resolution
- World Graph owns adjacency and duration
- Location Catalog owns unlocks
- Travel Aggregate owns travel state and transitions

Remaining question: Resolve one application query DTO boundary so presentation does not call persistence/domain owners through multiple ad hoc paths or duplicate business rules.

No runtime wiring, Telegram mutation or new presentation behavior is authorized.

## Next patch

`patch_21_11_4b_resolve_map_presentation_parity.py`
