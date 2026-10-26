# Stage 21.14.2a: Refined Event Schedules and Rewards Contract

## Result

- Status: **PASS**
- Decision: **GO_TO_PARITY_RESOLUTION**
- Contract state: **REFINED_EVIDENCE_BOUND_UNRESOLVED**
- Implementation authorized: **NO**
- Audit SHA-256: `a98db02871359e49d80da1d646bbeac814725c408331a81e4ff961a30627d085`
- Source candidates: **409**
- Schedule candidates: **110**
- Reward candidates: **296**
- Same-source schedule/reward candidates: **77**

## Refinement rule

This stage converts Stage 21.14.2 static evidence into an explicit resolution matrix. It does
not infer event identities, dates, timezones, recurrence, eligibility, reward values, item IDs,
quantities, currencies, operation keys, or exact-once behavior. Every candidate remains
`UNRESOLVED` until Stage 21.14.2b selects authoritative V1 owner evidence or records an explicit
approved decision.

## Confirmed invariants

- **INV-01:** V2 event schedules and rewards must reproduce authoritative V1 behavior only. Basis: project parity policy.
- **INV-02:** Static evidence is not sufficient to select an authoritative owner or value. Basis: Stage 21.14.2 audit boundary.
- **INV-03:** No runtime, Telegram, SQLite, production adapter, migration, or reward grant is authorized by this refinement. Basis: API-first stage boundary.
- **INV-04:** Event item allocation must remain compatible with the previously audited item-ID allocation contract; this stage does not allocate IDs. Basis: Stage 21.14.1 prerequisite boundary.
- **INV-05:** Reward execution requires an explicit exact-once/idempotency contract before implementation authorization. Basis: reward mutation safety boundary.

## Candidate preview

- `event-source-0001` | **REWARD_ONLY_CANDIDATE** | `config.py` | unresolved: 10
- `event-source-0002` | **REWARD_ONLY_CANDIDATE** | `data/about_game.py` | unresolved: 10
- `event-source-0003` | **SCHEDULE_AND_REWARD_CANDIDATE** | `data/balance.py` | unresolved: 20
- `event-source-0004` | **REWARD_ONLY_CANDIDATE** | `data/bosses.py` | unresolved: 10
- `event-source-0005` | **REWARD_ONLY_CANDIDATE** | `data/drop_tables.py` | unresolved: 10
- `event-source-0006` | **SCHEDULE_AND_REWARD_CANDIDATE** | `data/runes.py` | unresolved: 20
- `event-source-0007` | **REWARD_ONLY_CANDIDATE** | `data/story_quest_content.py` | unresolved: 10
- `event-source-0008` | **REWARD_ONLY_CANDIDATE** | `data/story_quest_definitions.py` | unresolved: 10
- `event-source-0009` | **REWARD_ONLY_CANDIDATE** | `data/story_quests/dark_forest_51_60.py` | unresolved: 10
- `event-source-0010` | **REWARD_ONLY_CANDIDATE** | `data/story_quests/dark_forest_61_70.py` | unresolved: 10
- `event-source-0011` | **REWARD_ONLY_CANDIDATE** | `data/story_quests/dark_forest_71_80.py` | unresolved: 10
- `event-source-0012` | **REWARD_ONLY_CANDIDATE** | `data/story_quests/dark_forest_81_90.py` | unresolved: 10
- `event-source-0013` | **REWARD_ONLY_CANDIDATE** | `data/story_quests/dark_forest_91_100.py` | unresolved: 10
- `event-source-0014` | **REWARD_ONLY_CANDIDATE** | `data/story_quests/start_path_01_10.py` | unresolved: 10
- `event-source-0015` | **REWARD_ONLY_CANDIDATE** | `data/story_quests/start_path_11_20.py` | unresolved: 10
- `event-source-0016` | **REWARD_ONLY_CANDIDATE** | `data/story_quests/start_path_21_30.py` | unresolved: 10
- `event-source-0017` | **REWARD_ONLY_CANDIDATE** | `data/story_quests/start_path_31_40.py` | unresolved: 10
- `event-source-0018` | **REWARD_ONLY_CANDIDATE** | `data/story_quests/start_path_41_50.py` | unresolved: 10
- `event-source-0019` | **SCHEDULE_ONLY_CANDIDATE** | `db.py` | unresolved: 11
- `event-source-0020` | **SCHEDULE_AND_REWARD_CANDIDATE** | `db_modules/__init__.py` | unresolved: 20
- `event-source-0021` | **REWARD_ONLY_CANDIDATE** | `db_modules/character.py` | unresolved: 10
- `event-source-0022` | **SCHEDULE_ONLY_CANDIDATE** | `db_modules/connection.py` | unresolved: 11
- `event-source-0023` | **SCHEDULE_AND_REWARD_CANDIDATE** | `db_modules/daily_compat.py` | unresolved: 20
- `event-source-0024` | **SCHEDULE_AND_REWARD_CANDIDATE** | `db_modules/dev_compat.py` | unresolved: 20
- `event-source-0025` | **REWARD_ONLY_CANDIDATE** | `db_modules/migrations.py` | unresolved: 10
- `event-source-0026` | **SCHEDULE_AND_REWARD_CANDIDATE** | `db_modules/quests.py` | unresolved: 20
- `event-source-0027` | **REWARD_ONLY_CANDIDATE** | `db_modules/shop.py` | unresolved: 10
- `event-source-0028` | **SCHEDULE_AND_REWARD_CANDIDATE** | `db_modules/story_quests.py` | unresolved: 20
- `event-source-0029` | **SCHEDULE_AND_REWARD_CANDIDATE** | `db_modules/systems_wrappers.py` | unresolved: 20
- `event-source-0030` | **SCHEDULE_ONLY_CANDIDATE** | `db_modules/utils.py` | unresolved: 11
- `event-source-0031` | **SCHEDULE_AND_REWARD_CANDIDATE** | `events/__init__.py` | unresolved: 20
- `event-source-0032` | **REWARD_ONLY_CANDIDATE** | `events/_template/__init__.py` | unresolved: 10
- `event-source-0033` | **EVENT_CONTEXT_ONLY** | `events/_template/bosses.py` | unresolved: 0
- `event-source-0034` | **SCHEDULE_ONLY_CANDIDATE** | `events/_template/config.py` | unresolved: 11
- `event-source-0035` | **REWARD_ONLY_CANDIDATE** | `events/_template/drops.py` | unresolved: 10
- `event-source-0036` | **EVENT_CONTEXT_ONLY** | `events/_template/handlers.py` | unresolved: 0
- `event-source-0037` | **EVENT_CONTEXT_ONLY** | `events/_template/items.py` | unresolved: 1
- `event-source-0038` | **EVENT_CONTEXT_ONLY** | `events/_template/mobs.py` | unresolved: 0
- `event-source-0039` | **EVENT_CONTEXT_ONLY** | `events/_template/quests.py` | unresolved: 0
- `event-source-0040` | **REWARD_ONLY_CANDIDATE** | `events/_template/rewards.py` | unresolved: 10
- `event-source-0041` | **EVENT_CONTEXT_ONLY** | `events/_template/shop.py` | unresolved: 0
- `event-source-0042` | **EVENT_CONTEXT_ONLY** | `events/_template/statistics.py` | unresolved: 0
- `event-source-0043` | **REWARD_ONLY_CANDIDATE** | `events/item_namespace.py` | unresolved: 10
- `event-source-0044` | **SCHEDULE_AND_REWARD_CANDIDATE** | `events/test_event_2026/__init__.py` | unresolved: 20
- `event-source-0045` | **EVENT_CONTEXT_ONLY** | `events/test_event_2026/bosses.py` | unresolved: 0
- `event-source-0046` | **SCHEDULE_AND_REWARD_CANDIDATE** | `events/test_event_2026/config.py` | unresolved: 20
- `event-source-0047` | **REWARD_ONLY_CANDIDATE** | `events/test_event_2026/drops.py` | unresolved: 10
- `event-source-0048` | **REWARD_ONLY_CANDIDATE** | `events/test_event_2026/items.py` | unresolved: 10
- `event-source-0049` | **EVENT_CONTEXT_ONLY** | `events/test_event_2026/mobs.py` | unresolved: 1
- `event-source-0050` | **EVENT_CONTEXT_ONLY** | `events/test_event_2026/quests.py` | unresolved: 0
- `event-source-0051` | **REWARD_ONLY_CANDIDATE** | `events/test_event_2026/rewards.py` | unresolved: 10
- `event-source-0052` | **REWARD_ONLY_CANDIDATE** | `events/test_event_2026/shop.py` | unresolved: 10
- `event-source-0053` | **EVENT_CONTEXT_ONLY** | `events/test_event_2026/statistics.py` | unresolved: 1
- `event-source-0054` | **REWARD_ONLY_CANDIDATE** | `handlers/auction_house.py` | unresolved: 10
- `event-source-0055` | **SCHEDULE_AND_REWARD_CANDIDATE** | `handlers/city.py` | unresolved: 20
- `event-source-0056` | **SCHEDULE_AND_REWARD_CANDIDATE** | `handlers/combat.py` | unresolved: 20
- `event-source-0057` | **SCHEDULE_AND_REWARD_CANDIDATE** | `handlers/contracts.py` | unresolved: 20
- `event-source-0058` | **SCHEDULE_AND_REWARD_CANDIDATE** | `handlers/daily.py` | unresolved: 20
- `event-source-0059` | **REWARD_ONLY_CANDIDATE** | `handlers/dev.py` | unresolved: 10
- `event-source-0060` | **SCHEDULE_AND_REWARD_CANDIDATE** | `handlers/event_ui.py` | unresolved: 20
- `event-source-0061` | **EVENT_CONTEXT_ONLY** | `handlers/guild.py` | unresolved: 0
- `event-source-0062` | **SCHEDULE_AND_REWARD_CANDIDATE** | `handlers/inventory.py` | unresolved: 20
- `event-source-0063` | **REWARD_ONLY_CANDIDATE** | `handlers/player_interaction.py` | unresolved: 10
- `event-source-0064` | **SCHEDULE_ONLY_CANDIDATE** | `handlers/profile.py` | unresolved: 11
- `event-source-0065` | **REWARD_ONLY_CANDIDATE** | `handlers/runes.py` | unresolved: 10
- `event-source-0066` | **REWARD_ONLY_CANDIDATE** | `handlers/story_quest_npc_runtime.py` | unresolved: 10
- `event-source-0067` | **REWARD_ONLY_CANDIDATE** | `handlers/story_quests.py` | unresolved: 10
- `event-source-0068` | **REWARD_ONLY_CANDIDATE** | `handlers/timed_exp_bonus.py` | unresolved: 10
- `event-source-0069` | **EVENT_CONTEXT_ONLY** | `handlers/world_chronicles.py` | unresolved: 0
- `event-source-0070` | **SCHEDULE_ONLY_CANDIDATE** | `keyboards.py` | unresolved: 11
- `event-source-0071` | **SCHEDULE_AND_REWARD_CANDIDATE** | `main.py` | unresolved: 20
- `event-source-0072` | **REWARD_ONLY_CANDIDATE** | `migrations/044_attribute_respec_foundation.py` | unresolved: 10
- `event-source-0073` | **EVENT_CONTEXT_ONLY** | `migrations/050_event_kill_statistics.py` | unresolved: 1
- `event-source-0074` | **REWARD_ONLY_CANDIDATE** | `migrations/051_event_shop_exchange.py` | unresolved: 10
- `event-source-0075` | **SCHEDULE_AND_REWARD_CANDIDATE** | `migrations/053_story_quest_persistence_schema.py` | unresolved: 20
- `event-source-0076` | **REWARD_ONLY_CANDIDATE** | `migrations/054_story_quest_kill_target_normalization.py` | unresolved: 10
- `event-source-0077` | **REWARD_ONLY_CANDIDATE** | `systems/attribute_allocation_system.py` | unresolved: 10
- `event-source-0078` | **EVENT_CONTEXT_ONLY** | `systems/attribute_respec_system.py` | unresolved: 0
- `event-source-0079` | **REWARD_ONLY_CANDIDATE** | `systems/auction_house_system.py` | unresolved: 10
- `event-source-0080` | **EVENT_CONTEXT_ONLY** | `systems/boss_system.py` | unresolved: 1
- `event-source-0081` | **EVENT_CONTEXT_ONLY** | `systems/character_system.py` | unresolved: 0
- `event-source-0082` | **REWARD_ONLY_CANDIDATE** | `systems/combat_system.py` | unresolved: 10
- `event-source-0083` | **SCHEDULE_AND_REWARD_CANDIDATE** | `systems/contract_system.py` | unresolved: 20
- `event-source-0084` | **REWARD_ONLY_CANDIDATE** | `systems/drop_system.py` | unresolved: 10
- `event-source-0085` | **SCHEDULE_ONLY_CANDIDATE** | `systems/energy_system.py` | unresolved: 11
- `event-source-0086` | **REWARD_ONLY_CANDIDATE** | `systems/event_item_catalog_system.py` | unresolved: 10
- `event-source-0087` | **SCHEDULE_AND_REWARD_CANDIDATE** | `systems/event_shop_system.py` | unresolved: 20
- `event-source-0088` | **SCHEDULE_ONLY_CANDIDATE** | `systems/event_statistics_system.py` | unresolved: 11
- `event-source-0089` | **SCHEDULE_AND_REWARD_CANDIDATE** | `systems/fatigue_artifact_system.py` | unresolved: 20
- `event-source-0090` | **SCHEDULE_AND_REWARD_CANDIDATE** | `systems/fresh_database_bootstrap.py` | unresolved: 20
- `event-source-0091` | **REWARD_ONLY_CANDIDATE** | `systems/guild_system.py` | unresolved: 10
- `event-source-0092` | **REWARD_ONLY_CANDIDATE** | `systems/level_up_reward_system.py` | unresolved: 10
- `event-source-0093` | **SCHEDULE_ONLY_CANDIDATE** | `systems/notifications.py` | unresolved: 11
- `event-source-0094` | **REWARD_ONLY_CANDIDATE** | `systems/player_interaction_system.py` | unresolved: 10
- `event-source-0095` | **SCHEDULE_AND_REWARD_CANDIDATE** | `systems/player_system.py` | unresolved: 20
- `event-source-0096` | **REWARD_ONLY_CANDIDATE** | `systems/premium_item_policy_system.py` | unresolved: 10
- `event-source-0097` | **REWARD_ONLY_CANDIDATE** | `systems/production_logging.py` | unresolved: 10
- `event-source-0098` | **REWARD_ONLY_CANDIDATE** | `systems/pve_auto_escape_system.py` | unresolved: 10
- `event-source-0099` | **EVENT_CONTEXT_ONLY** | `systems/pvp_balance_simulator.py` | unresolved: 0
- `event-source-0100` | **EVENT_CONTEXT_ONLY** | `systems/pvp_combat_log.py` | unresolved: 0

The complete evidence-bound resolution matrix is stored in `reports/stage_21_14_2a_refined_event_schedules_rewards_contract.json`.

## Safety

- No V1 or V2 production source was modified.
- No database was opened.
- `game.db-wal` and `game.db-shm` were not read, copied, deleted, cleared, restored, or otherwise manipulated.
- No runtime, Telegram integration, migration, persistence adapter, event schedule, or reward grant was implemented.

## Next action

**GO_TO_PARITY_RESOLUTION**. Stage 21.14.2b must resolve each material schedule/reward dimension
against authoritative V1 evidence. Manual in-game verification is **NOT REQUIRED** for this
contract-refinement-only stage.
