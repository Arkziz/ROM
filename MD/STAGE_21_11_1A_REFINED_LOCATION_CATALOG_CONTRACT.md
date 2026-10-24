# Stage 21.11.1a - Refined Location Catalog contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **9**
- Review-required rows: **6**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `catalog`: `data/locations.py`
- `graph`: `data/location_graph.py`
- `travel`: `data/travel_presentation.py`
- `mobs`: `data/mobs.py`
- `story_names`: `systems/story_quest_location_presentation.py`

## Contract matrix

- `CANONICAL_LOCATION_CATALOG_OWNER`: **V1_CONFIRMED** - V1 centralizes location records and fallback reads.
- `UNLOCKED_LOCATION_ENUMERATION`: **V1_CONFIRMED** - V1 enumerates unlocked locations in canonical order.
- `LOCATION_UNLOCK_OWNER`: **V1_CONFIRMED** - V1 owns level-based location availability checks.
- `LOCATION_GRAPH_OWNER`: **V1_CONFIRMED** - V1 owns graph adjacency.
- `LOCATION_GRAPH_VALIDATION`: **V1_CONFIRMED** - V1 validates symmetric graph and node coverage.
- `TRAVEL_NAME_OWNER`: **V1_CONFIRMED** - V1 resolves travel-facing localized names.
- `ARRIVAL_PRESENTATION_OWNER`: **V1_CONFIRMED** - V1 formats human-readable arrival destinations.
- `LOCATION_MOB_OWNER`: **V1_CONFIRMED** - V1 maps mobs to location IDs.
- `STORY_LOCATION_NAME_OWNER`: **V1_CONFIRMED** - Story navigation has a canonical human-name resolver.
- `LOCATION_CATALOG_SCHEMA`: **REVIEW_REQUIRED** - Stable IDs, fields, order and unknown-ID fallback require exact normalization.
- `LOCALIZED_NAME_AND_TECHNICAL_ID_POLICY`: **REVIEW_REQUIRED** - Human names and technical-ID leak prevention require one contract.
- `UNLOCK_AND_LEVEL_POLICY`: **REVIEW_REQUIRED** - Level thresholds and unavailable-location behavior require resolution.
- `GRAPH_TRAVEL_AND_RESTART_POLICY`: **REVIEW_REQUIRED** - Graph, travel destinations and static restart semantics require resolution.
- `MOB_NPC_QUEST_REFERENCE_POLICY`: **REVIEW_REQUIRED** - Mob, NPC and quest references plus validation require resolution.
- `CONSUMER_ALLOWLIST_AND_SHADOW_CATALOGS`: **REVIEW_REQUIRED** - Allowed consumers, duplicate catalogs and presentation boundaries require resolution.

## Unresolved contracts

- `LOCATION_CATALOG_SCHEMA`
- `LOCALIZED_NAME_AND_TECHNICAL_ID_POLICY`
- `UNLOCK_AND_LEVEL_POLICY`
- `GRAPH_TRAVEL_AND_RESTART_POLICY`
- `MOB_NPC_QUEST_REFERENCE_POLICY`
- `CONSUMER_ALLOWLIST_AND_SHADOW_CATALOGS`

Implementation remains unauthorized until catalog schema, localized-name policy, unlock levels, graph/travel, content references and shadow catalogs are resolved from V1 evidence.
