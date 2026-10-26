# Stage 21.14.2a: Refined Event Schedules and Rewards Contract

## Result

- Status: **PASS**
- Decision: **GO_TO_PARITY_RESOLUTION**
- Starting HEAD: `4cec994c90cd6eaad45b33f6370a33b11ca39c9d`
- Source audit: `reports/stage_21_14_2_existing_event_schedules_rewards_audit.json`
- Source audit SHA-256: `a98db02871359e49d80da1d646bbeac814725c408331a81e4ff961a30627d085`
- Refined evidence rows: **1966**
- Verified V1 source files: **409**

## Scope

This stage refines the static V1 evidence produced by Stage 21.14.2. It does not
implement event scheduling, reward delivery, claims, persistence, Telegram handlers,
or runtime adapters.

## Candidate production owners

- `data/about_game.py`
- `data/balance.py`
- `data/bosses.py`
- `data/drop_tables.py`
- `data/runes.py`
- `data/story_quest_content.py`
- `data/story_quest_definitions.py`
- `data/story_quests/dark_forest_51_60.py`
- `data/story_quests/dark_forest_61_70.py`
- `data/story_quests/dark_forest_71_80.py`
- `data/story_quests/dark_forest_81_90.py`
- `data/story_quests/dark_forest_91_100.py`
- `data/story_quests/start_path_01_10.py`
- `data/story_quests/start_path_11_20.py`
- `data/story_quests/start_path_21_30.py`
- `data/story_quests/start_path_31_40.py`
- `data/story_quests/start_path_41_50.py`
- `db_modules/__init__.py`
- `db_modules/character.py`
- `db_modules/connection.py`
- `db_modules/quests.py`
- `db_modules/shop.py`
- `db_modules/story_quests.py`
- `db_modules/systems_wrappers.py`
- `handlers/auction_house.py`
- `handlers/city.py`
- `handlers/combat.py`
- `handlers/contracts.py`
- `handlers/daily.py`
- `handlers/dev.py`
- `handlers/event_ui.py`
- `handlers/guild.py`
- `handlers/inventory.py`
- `handlers/profile.py`
- `handlers/runes.py`
- `handlers/story_quest_npc_runtime.py`
- `handlers/story_quests.py`
- `handlers/timed_exp_bonus.py`
- `systems/attribute_allocation_system.py`
- `systems/attribute_respec_system.py`
- `systems/auction_house_system.py`
- `systems/boss_system.py`
- `systems/combat_system.py`
- `systems/contract_system.py`
- `systems/drop_system.py`
- `systems/energy_system.py`
- `systems/event_item_catalog_system.py`
- `systems/event_shop_system.py`
- `systems/event_statistics_system.py`
- `systems/fatigue_artifact_system.py`
- `systems/fresh_database_bootstrap.py`
- `systems/guild_system.py`
- `systems/level_up_reward_system.py`
- `systems/player_interaction_system.py`
- `systems/player_system.py`
- `systems/premium_item_policy_system.py`
- `systems/production_logging.py`
- `systems/pve_auto_escape_system.py`
- `systems/regen_system.py`
- `systems/reward_system.py`
- `systems/rune_system.py`
- `systems/simulation/__init__.py`
- `systems/simulation/asset_valuation.py`
- `systems/simulation/canonical_rules.py`
- `systems/simulation/capacity_analysis.py`
- `systems/simulation/class_progression.py`
- `systems/simulation/drop_inventory.py`
- `systems/simulation/economic_ledger.py`
- `systems/simulation/economy_analyzer.py`
- `systems/simulation/economy_guild_acceptance.py`
- `systems/simulation/loot_equipment_city.py`
- `systems/simulation/meta_progression.py`
- `systems/simulation/models.py`
- `systems/simulation/patch_regression.py`
- `systems/simulation/progression_economy_reporting.py`
- `systems/simulation/progression_provider.py`
- `systems/simulation/rng_percentiles.py`
- `systems/simulation/world_progression.py`
- `systems/story_quest_boss_completion_system.py`
- `systems/story_quest_completion_system.py`
- `systems/story_quest_npc_acceptance_system.py`
- `systems/story_quest_overlevel_system.py`
- `systems/story_quest_reward_system.py`
- `systems/story_quest_system.py`
- `systems/world_chronicle_system.py`

## Sources containing both schedule and reward signals

- `db_modules/quests.py`
- `handlers/combat.py`
- `handlers/daily.py`
- `handlers/event_ui.py`
- `systems/attribute_allocation_system.py`
- `systems/drop_system.py`
- `systems/event_shop_system.py`
- `systems/fatigue_artifact_system.py`
- `systems/player_system.py`
- `systems/rune_system.py`
- `systems/simulation/economic_ledger.py`
- `systems/simulation/meta_progression.py`
- `systems/simulation/progression_economy_reporting.py`
- `systems/story_quest_completion_system.py`

## Confirmed signal vocabulary

- Schedule: `active_check, end, event_id, event_key, recurrence, start, timezone`
- Rewards: `claim, currency, exact_once, item_id, operation_key, quantity, reward`

## Open questions for parity resolution

- None.

## Binding refinement rules

- Only evidence tied to unchanged Stage 21.14.2 source hashes is admissible.
- Production candidates outrank tests, fixtures, historical code and supporting sources, but path classification alone does not establish canonical ownership.
- No event start/end inclusivity, timezone, recurrence or eligibility rule may be invented when explicit V1 evidence is absent.
- No reward item, currency, quantity, claim rule, operation key or exact-once behavior may be invented when explicit V1 evidence is absent.
- Conflicting V1 definitions remain unresolved until Stage 21.14.2b parity resolution selects an owner using direct source evidence.
- This refined contract authorizes parity resolution only; it does not authorize V2 implementation, runtime wiring, Telegram wiring or production persistence.

## Safety

- Database opened: **NO**
- V1 runtime imported: **NO**
- Telegram/runtime started: **NO**
- Production source modified: **NO**
- `game.db-wal` / `game.db-shm` manipulated: **NO**

## Next action

Proceed to **Stage 21.14.2b parity resolution**. That stage must resolve each open
question using direct V1 owner evidence and must not invent absent rules.

Manual in-game verification: **NOT REQUIRED**, contract refinement only.
