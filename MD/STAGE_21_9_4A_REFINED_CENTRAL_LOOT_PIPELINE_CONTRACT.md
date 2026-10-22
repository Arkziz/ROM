# Stage 21.9.4a - Refined central loot pipeline contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **13**
- Review-required rows: **15**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `central_planner`: `systems/drop_system.py`
- `reward_mutation`: `systems/reward_system.py`
- `inventory`: `db_modules/inventory.py`
- `generated_equipment`: `db_modules/generated_equipment.py`
- `story_quest_items`: `systems/story_quest_item_drop_system.py`

## Contract matrix

- `ENEMY_CLASSIFICATION_OWNER`: **V1_CONFIRMED** - V1 central drop system classifies the enemy before selecting tables.
- `DROP_RULE_ROLL_OWNER`: **V1_CONFIRMED** - One rule roll is owned by the central drop system.
- `DROP_GROUP_ROLL_OWNER`: **V1_CONFIRMED** - Grouped selection and internal weighting are owned by the central drop system.
- `ENEMY_DROP_PLAN_OWNER`: **V1_CONFIRMED** - Normal, elite and boss loot planning converges on the central enemy-drop planner.
- `VICTORY_DROP_PLAN_BOUNDARY`: **V1_CONFIRMED** - Victory loot is exposed as a plan before inventory mutation.
- `EVENT_DROP_PLAN_BOUNDARY`: **V1_CONFIRMED** - Event loot uses a distinct central plan boundary.
- `INVENTORY_MUTATION_OWNER`: **V1_CONFIRMED** - Reward processing applies planned enemy drops to inventory.
- `EVENT_INVENTORY_MUTATION_OWNER`: **V1_CONFIRMED** - Event inventory mutation remains a separate V1 reward path.
- `VICTORY_REWARD_INTEGRATION`: **V1_CONFIRMED** - Combat victory owns the current integration point for reward and loot processing.
- `INVENTORY_INSERTION_PRIMITIVE`: **V1_CONFIRMED** - V1 inventory insertion is delegated to the inventory DB module.
- `GENERATED_EQUIPMENT_OWNER`: **V1_CONFIRMED** - Generated equipment creation remains outside the central roll calculator.
- `CLASS_AWARE_EQUIPMENT_OWNER`: **V1_CONFIRMED** - Class-aware equipment choice has a dedicated V1 owner.
- `STORY_QUEST_ITEM_BOUNDARY`: **V1_CONFIRMED** - Story quest item drops remain a separate subsystem boundary.
- `AUTHORITATIVE_V2_LOOT_PLANNER`: **REVIEW_REQUIRED** - The exact V2 public planner API and immutable output shape require resolution.
- `EXACT_NORMAL_ELITE_BOSS_GROUP_CHANCES`: **REVIEW_REQUIRED** - Exact per-class group chances must be extracted without changing values.
- `INDEPENDENT_VS_EXCLUSIVE_ROLL_ORDER`: **REVIEW_REQUIRED** - The exact ordering and independence of group rolls require source-level proof.
- `INTERNAL_WEIGHT_TABLES`: **REVIEW_REQUIRED** - Exact weighted candidates and fallback behavior require resolution.
- `RARITY_AND_EQUIPMENT_HANDOFF`: **REVIEW_REQUIRED** - Rarity selection and generated-equipment handoff must preserve V1 ownership and order.
- `CONSUMABLE_RUNE_STONE_TROPHY_RULES`: **REVIEW_REQUIRED** - Exact consumable, rune, enhancement-stone and trophy rules require a bounded matrix.
- `EVENT_AND_QUEST_ITEM_SCOPE`: **REVIEW_REQUIRED** - Event plans and story quest items must not be silently merged into ordinary loot.
- `INVENTORY_FULL_AND_PARTIAL_OUTCOME`: **REVIEW_REQUIRED** - Capacity, stacking, partial insertion and explicit applied/pending/rejected outcomes require proof.
- `GENERATED_ID_LIFECYCLE`: **REVIEW_REQUIRED** - Preview, permanent promotion and never-reuse identity boundaries require exact classification.
- `RNG_PORT_AND_DRAW_ORDER`: **REVIEW_REQUIRED** - A V2 RNG port must preserve exact draw order and deterministic testing without changing chances.
- `SIMULATOR_PARITY_BOUNDARY`: **REVIEW_REQUIRED** - Simulator consumers must delegate or prove parity without becoming a production owner.
- `SETTLEMENT_LOOT_COMMAND_SHAPE`: **REVIEW_REQUIRED** - The immutable loot plan handed to RewardSettlementService requires a conflict-free application DTO.
- `PREMIUM_EXCLUSION_FROM_LOOT`: **REVIEW_REQUIRED** - Premium must remain excluded from loot chances, weights, rarity and quantities.
- `PRESENTATION_AFTER_PLAN_AND_SETTLEMENT`: **REVIEW_REQUIRED** - Loot messages must be derived after planning/settlement and never own business mutation.
- `LEGACY_WRAPPERS_AND_SHADOW_OWNERS`: **REVIEW_REQUIRED** - Legacy roll helpers, DEV and simulator paths require authoritative/delegating/shadow classification.

## Unresolved contracts

- `AUTHORITATIVE_V2_LOOT_PLANNER`
- `EXACT_NORMAL_ELITE_BOSS_GROUP_CHANCES`
- `INDEPENDENT_VS_EXCLUSIVE_ROLL_ORDER`
- `INTERNAL_WEIGHT_TABLES`
- `RARITY_AND_EQUIPMENT_HANDOFF`
- `CONSUMABLE_RUNE_STONE_TROPHY_RULES`
- `EVENT_AND_QUEST_ITEM_SCOPE`
- `INVENTORY_FULL_AND_PARTIAL_OUTCOME`
- `GENERATED_ID_LIFECYCLE`
- `RNG_PORT_AND_DRAW_ORDER`
- `SIMULATOR_PARITY_BOUNDARY`
- `SETTLEMENT_LOOT_COMMAND_SHAPE`
- `PREMIUM_EXCLUSION_FROM_LOOT`
- `PRESENTATION_AFTER_PLAN_AND_SETTLEMENT`
- `LEGACY_WRAPPERS_AND_SHADOW_OWNERS`

Implementation remains unauthorized until exact group chances, roll order, weights, rarity/equipment handoff, category rules, inventory outcomes, generated IDs, RNG draw order, simulator parity, settlement DTO, Premium exclusion, presentation and shadow paths are resolved from V1 evidence.
