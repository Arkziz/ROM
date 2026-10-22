# Stage 21.9.4b - Resolved central loot pipeline parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolved contracts

- `AUTHORITATIVE_V2_LOOT_PLANNER`: **PURE_IMMUTABLE_CENTRAL_PLAN** - V2 implements one pure planner mirroring the source-backed V1 plan boundary; mutation remains outside the planner.
- `EXACT_NORMAL_ELITE_BOSS_GROUP_CHANCES`: **SOURCE_BOUND_TABLES_NO_REBALANCE** - All normal/elite/boss chances are extracted from V1 source constants and rule structures; no inferred or recalculated values are authorized.
- `INDEPENDENT_VS_EXCLUSIVE_ROLL_ORDER`: **SOURCE_ORDER_IS_CONTRACT** - Rule and group traversal, independent draws and exclusive weighted choice retain exact V1 source order.
- `INTERNAL_WEIGHT_TABLES`: **SOURCE_BOUND_WEIGHTED_SELECTION** - Candidate lists, weights, zero/empty behavior and fallback are copied from V1 evidence only.
- `RARITY_AND_EQUIPMENT_HANDOFF`: **PLAN_REQUEST_THEN_GENERATION_PORT** - The planner emits an equipment-generation request; generated stats, rarity materialization and IDs remain delegated.
- `CONSUMABLE_RUNE_STONE_TROPHY_RULES`: **SEPARATE_SOURCE_RULE_GROUPS** - Consumable, rune, refine-stone and trophy groups retain their independent V1 rules and order.
- `EVENT_AND_QUEST_ITEM_SCOPE`: **SEPARATE_EVENT_AND_STORY_BOUNDARIES** - Event plans and story quest item processing remain separate from ordinary victory loot.
- `INVENTORY_FULL_AND_PARTIAL_OUTCOME`: **EXPLICIT_ATOMIC_REPOSITORY_OUTCOME** - Application returns applied/pending/rejected; silent partial success is forbidden and stacking/capacity remain repository concerns.
- `GENERATED_ID_LIFECYCLE`: **GENERATION_PORT_OWNS_IDENTITY** - Preview, promotion, permanent allocation and never-reuse remain outside the pure planner and require the generated-equipment port.
- `RNG_PORT_AND_DRAW_ORDER`: **EXPLICIT_RANDOM_SOURCE_EXACT_DRAW_ORDER** - V2 uses an injected RNG port while preserving V1 call count and draw order.
- `SIMULATOR_PARITY_BOUNDARY`: **SIMULATOR_DELEGATES_TO_SAME_PLANNER** - Simulator adapters may supply RNG but may not own alternate loot rules.
- `SETTLEMENT_LOOT_COMMAND_SHAPE`: **IMMUTABLE_PLANNED_LOOT_COMMANDS** - Planner output is immutable commands containing source group, item/equipment request and quantity, consumed by settlement without rerolling.
- `PREMIUM_EXCLUSION_FROM_LOOT`: **NO_PREMIUM_INPUT_OR_MODIFIER** - Premium is absent from the planner input and cannot change chances, weights, rarity, quantities or RNG order.
- `PRESENTATION_AFTER_PLAN_AND_SETTLEMENT`: **DTO_AFTER_DURABLE_OUTCOME** - Messages are derived only from plan and settlement result; presentation performs no roll or mutation.
- `LEGACY_WRAPPERS_AND_SHADOW_OWNERS`: **CENTRAL_DELEGATION_REQUIRED** - Legacy, DEV and simulator helpers may delegate for compatibility but cannot become parallel production owners.

## V2 central loot contract

- Planner: `CentralLootPlanner`
- RNG injected: `True`
- Inventory mutation: `False`
- Premium input: `False`
- Inputs: `enemy_class, enemy_level, player_class, location_key, rules, rng`
- Outputs: `immutable_loot_commands, equipment_generation_requests, roll_trace`

## Implementation boundary

Allowed:
- pure planner DTOs and RNG protocol
- source-faithful rule tables and roll ordering
- equipment-generation request boundary
- unit and parity fixtures

Forbidden:
- SQLite and production inventory adapters
- runtime or Telegram wiring
- chance/weight/rarity rebalance
- Premium loot modifiers
- event or story quest merger
- PvP loot

## Safety

V1 was inspected only as source text and AST. SQLite was not opened. `game.db-wal` and `game.db-shm` were not deleted, cleared, modified, or used for rollback.

## Next patch

`patch_21_9_4c_implement_central_loot_pipeline.py`
