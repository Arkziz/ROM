# Stage 21.13.3b - Resolved NPC/dialogue model parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Contract matrix: **9/9 RESOLVED**
- Generic dialogue graph: **NOT_AUTHORIZED**
- Content-independence gate: **REQUIRED**
- External service mutation: **NOT_AUTHORIZED**
- Runtime integration: **NOT_AUTHORIZED**
- Production persistence: **NOT_AUTHORIZED**
- Manual game check: **NOT_REQUIRED**

## Resolved contracts

### DIALOGUE_NODE_AND_ACTION_SCHEMA

V2 parity is a bounded immutable NPC presentation/action model, not a generic branching dialogue graph. The canonical identity is npc_id. An NPC view may expose only V1-confirmed story-quest actions with stable action keys derived from action kind plus referenced quest identity. No persistent dialogue_node_id, arbitrary graph edges or invented universal action kinds are introduced.

Typed reasons: unknown_npc, action_not_available, malformed_action

### NPC_AVAILABILITY_AND_CONDITION_POLICY

Availability is evaluated fail-closed in this order: resolve npc_id, verify the NPC canonical location/route, verify the player is in that location, query Quest Engine for the referenced quest state and prerequisites, then materialize visible actions. Unknown NPC, wrong location, unavailable quest and stale action remain distinct typed results. No additional level or condition rules are duplicated outside Quest Engine.

Typed reasons: unknown_npc, wrong_location, npc_unavailable, stale_action

### QUEST_AND_NPC_INTERACTION_BOUNDARY

The immutable NPC registry owns NPC identity, localized metadata and location assignment. NPC application query maps registry plus Quest Engine results into a view. Quest Engine exclusively owns quest availability, acceptance, progress, turn-in and rewards. An accept command carries npc_id, quest_id and expected quest revision; NPC service validates the NPC-to-quest reference then delegates the mutation exactly once.

Typed reasons: quest_not_linked, quest_unavailable, stale_revision, already_active

### SHOP_SERVICE_AND_OTHER_ACTION_BOUNDARIES

Stage 21.13.3 authorizes only story-quest NPC presentation and quest-linked actions proven by V1. Shop, guild, crafting, auction, daily and rune behavior remain external application services and are not added to the NPC domain. Future NPC links may reference a typed external action only after a separate V1 audit and parity authorization; the NPC model never owns those business mutations.

Typed reasons: unsupported_action, external_service_not_authorized

### LOCALIZATION_AND_TECHNICAL_ID_NON_DISCLOSURE

User-visible NPC names and labels come only from canonical registry metadata and localized presentation. Technical npc_id, quest_id and location_id are allowed in DTO identity, callback payloads, logs and tests but never rendered as fallback text. Unknown IDs fail closed; underscore replacement, title-casing and raw-ID display are prohibited.

Typed reasons: unknown_npc, missing_localized_name, presentation_unavailable

### PERSISTENCE_RESTART_AND_CONTENT_INDEPENDENCE

NPC definitions are immutable content registry data and require no independent runtime persistence. Restart stability is validated by deterministic registry load plus duplicate-ID, location-route and quest-reference validation. Reusable domain/application modules cannot branch on concrete NPC IDs, quest IDs, NPC names or localized dialogue strings; an executable content-independence gate is mandatory for implementation.

Typed reasons: duplicate_npc_id, invalid_location_reference, invalid_quest_reference, content_dependency_violation

## Next patch

`patch_21_13_3c_implement_npc_dialogue_model.py`
