# Stage 21.11.4b - Resolved Map Presentation parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **6/6**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### NAVIGATION_DTO_AND_CALLBACK_POLICY

One immutable MapView DTO carries mode, current node label, directions, optional active-travel snapshot and stable actions. Callback payloads use versioned technical tokens only: map:open, map:info:<node>, map:preview:<node>, map:start:<node>, map:cancel:<travel_id>:<revision>, map:players. Unknown, malformed or obsolete callbacks fail closed and trigger canonical re-render.

### DIRECTION_BUTTONS_AND_UNLOCK_FILTERING

Directions preserve World Graph adjacency order. Unlocked adjacent destinations expose preview; locked huntable destinations remain visible as localized locked information without a start action. City has no unlock gate. Preview never mutates travel state.

### ACTIVE_TRAVEL_PRESENTATION_POLICY

When ACTIVE travel exists, MapView enters IN_TRANSIT mode, hides normal start actions, shows localized from/to names, non-negative remaining seconds rounded up to the next whole second, refresh and cancel carrying exact travel_id/revision. A stale snapshot is replaced by a fresh canonical query.

### ARRIVAL_CANCEL_AND_REFRESH_POLICY

Start and successful cancel always re-query and re-render MapView. Typed failures map to localized messages without changing DTO state. Arrival notification is post-commit and outside Map Presentation implementation. Refresh/open are side-effect-free canonical queries; obsolete callbacks answer as non-current and re-render.

### TECHNICAL_ID_NON_DISCLOSURE

Technical node IDs are permitted only in DTO identity fields, callback payloads, logs and tests. Every user-visible node reference must use canonical World Graph/Location Catalog localized names. Unknown IDs use one localized unknown-place label and are never title-cased, underscored or echoed.

### PRESENTATION_DOMAIN_BOUNDARY

A pure MapPresentationService composes World Graph, Location Catalog and Travel query DTOs. It returns text-independent view/action DTOs. Telegram adapters alone render text/keyboards and decode callbacks. Domain/application owners never import Telegram, and presentation never duplicates adjacency, unlock, ETA or transition rules.

## Next patch

`patch_21_11_4c_implement_map_presentation.py`
