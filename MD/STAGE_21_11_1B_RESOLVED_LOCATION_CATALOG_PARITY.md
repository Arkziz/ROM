# Stage 21.11.1b - Resolved Location Catalog parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **6/6**
- Remaining unresolved contracts: **0**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Canonical V1 catalog

The V2 implementation is authorized for exactly two locations, in this order:

1. `start_path` - **🌿 Початок Шляху**, levels 1-5, unlock level 1.
2. `dark_forest` - **🌲 Темний Бір**, levels 6-10, unlock level 6.

No third location, placeholder, inferred node, renamed ID or new content is authorized.

## Resolutions

### LOCATION_CATALOG_SCHEMA

The canonical V2 catalog contains exactly two records in V1 order: start_path then dark_forest. Required immutable fields are location_id, localized name, description, level_min, level_max, unlock_level, boss name and mob-name references. Unknown IDs fail closed; no fabricated fallback record is created.

### LOCALIZED_NAME_AND_TECHNICAL_ID_POLICY

Technical IDs remain start_path and dark_forest. User-visible resolvers return 🌿 Початок Шляху and 🌲 Темний Бір. Technical IDs must never be title-cased or exposed as fallback presentation; unknown IDs use an explicit unavailable result.

### UNLOCK_AND_LEVEL_POLICY

Початок Шляху covers levels 1-5 and unlocks at level 1. Темний Бір covers levels 6-10 and unlocks at level 6. Unlock enumeration preserves catalog order and does not skip the level gate.

### GRAPH_TRAVEL_AND_RESTART_POLICY

The world graph contains city, start_path and dark_forest. Edges are city<->start_path<->dark_forest, symmetric and duplicate-free. Catalog and graph are static declarative content, so restart rebuilds the same values without migration or runtime mutation.

### MOB_NPC_QUEST_REFERENCE_POLICY

Location references use only stable technical IDs and must resolve against the two-location catalog. Mob lists and the two boss names are copied from V1 catalog evidence. NPC and quest catalogs remain separate owners and must pass referential validation; this parity stage invents no NPC, quest, mob or location.

### CONSUMER_ALLOWLIST_AND_SHADOW_CATALOGS

Allowed consumers are world/travel, map presentation, hunting/mob selection, story navigation, quest/NPC validation and test fixtures. The V2 catalog is the single definition owner. Presentation aliases, graph nodes and content references are consumers, not parallel editable catalogs.

## Implementation boundary

Only a pure immutable V2 catalog, typed lookup/unlock/graph API, validation and focused fixtures are authorized. SQLite, production adapters, runtime/Telegram wiring and any new content remain forbidden.

## Next patch

`patch_21_11_1c_implement_location_catalog.py`
