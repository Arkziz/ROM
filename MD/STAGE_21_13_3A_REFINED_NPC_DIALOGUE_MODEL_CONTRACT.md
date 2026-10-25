# Stage 21.13.3a - Refined NPC/dialogue model contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Contract matrix: **3 confirmed / 6 review-required / 9 total**
- Generic dialogue graph confirmed: **False**
- Story quest NPC registry confirmed: **True**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Refined unresolved contracts

### DIALOGUE_NODE_AND_ACTION_SCHEMA

Confirmed:

- V1 has a typed StoryQuestNpcDefinition and STORY_QUEST_NPCS registry
- the acceptance system builds NPC story-quest presentation
- runtime callbacks are registered outside the registry
- the audited sources contain dialogue mentions but no confirmed generic conversation graph owner

Remaining question: Determine whether V1 parity is a bounded NPC action/presentation model rather than a generic branching dialogue graph; identify stable action identity, allowed action kinds and whether any dialogue node IDs persist across callbacks.

### NPC_AVAILABILITY_AND_CONDITION_POLICY

Confirmed:

- NPC definitions are assigned to locations
- quest definitions reference NPC identity
- acceptance resolves an NPC story quest before mutation
- runtime checks whether a story NPC is present

Remaining question: Resolve the exact order of location, route, quest-state, level, prerequisite and visibility checks; define unknown NPC, unavailable NPC and stale callback results without adding conditions absent from V1.

### QUEST_AND_NPC_INTERACTION_BOUNDARY

Confirmed:

- data/story_quest_npcs.py owns static NPC content
- systems/story_quest_npc_acceptance_system.py owns find, presentation and accept orchestration
- Quest Engine remains the owner of quest availability and acceptance state
- handlers consume the acceptance API

Remaining question: Define the typed query/command boundary so NPC interaction never duplicates Quest Engine prerequisites, progress or reward rules; identify expected quest/NPC identity and revision inputs for stale interaction protection.

### SHOP_SERVICE_AND_OTHER_ACTION_BOUNDARIES

Confirmed:

- the authoritative NPC registry is story-quest specific
- broad discovery produced unrelated auction, daily and rune token matches
- handlers/city.py contains placeholder presentation
- no audited evidence establishes the NPC registry as owner of shop, guild or crafting mutations

Remaining question: Classify non-story NPC actions as external application-service links rather than NPC-owned business logic; enumerate only V1-confirmed action targets and explicitly reject invented universal shop/service action types.

### LOCALIZATION_AND_TECHNICAL_ID_NON_DISCLOSURE

Confirmed:

- stable NPC IDs exist separately from definitions
- presentation is built by the acceptance system and handlers
- technical IDs are required for quest references and callbacks
- user-facing story terminology must use localized human names

Remaining question: Locate the canonical NPC display-name resolver and define fail-closed behavior for unknown IDs; prohibit raw NPC IDs, auto title-casing and technical location IDs in user-visible text while allowing IDs in DTO identity, callbacks, logs and tests.

### PERSISTENCE_RESTART_AND_CONTENT_INDEPENDENCE

Confirmed:

- NPC definitions are represented by a static registry
- quest state persists outside the NPC registry
- handlers do not own the registry
- registry and quest references have validators

Remaining question: Resolve whether NPC/dialogue content is immutable and needs no independent persistence; define restart stability, validation of duplicate IDs/routes/references and an executable gate preventing reusable model code from branching on concrete NPC IDs, quest IDs or localized content.

No production mutation, NPC content change, quest acceptance, database access or runtime wiring is authorized.

## Next patch

`patch_21_13_3b_resolve_npc_dialogue_model_parity.py`
