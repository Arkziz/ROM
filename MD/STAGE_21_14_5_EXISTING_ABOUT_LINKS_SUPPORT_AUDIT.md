# Stage 21.14.5 — Existing About, useful links and support audit

- Status: **PASS**
- Conclusion: **PASS_REVIEW_REQUIRED**
- Next action: **GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW**
- Production mutation: **NO**
- Production SQLite opened: **NO**
- `.env` opened: **NO**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Evidence groups

- `about`: 55
- `configuration`: 40
- `navigation`: 2845
- `support`: 27
- `useful_links`: 12
- `validation`: 182

## Candidate owners

### `config.py`
- Groups: configuration, support, useful_links
- `FunctionDef _validated_external_https_url` at line 34
- `FunctionDef get_external_links_config` at line 67

### `data/about_game.py`
- Groups: about, support
- `FunctionDef get_about_game_section` at line 98
- `FunctionDef build_about_game_section_text` at line 99

### `data/classes.py`
- Groups: navigation, support

### `data/equipment_profiles.py`
- Groups: navigation

### `data/guild_resource_policy.py`
- Groups: navigation

### `data/mana_skill_presentation.py`
- Groups: validation

### `data/mobs.py`
- Groups: navigation

### `data/story_quest_hierarchy.py`
- Groups: validation

### `data/story_quests/dark_forest_61_70.py`
- Groups: support

### `data/story_quests/dark_forest_71_80.py`
- Groups: support

### `data/story_quests/dark_forest_91_100.py`
- Groups: navigation, support

### `data/story_quests/start_path_01_10.py`
- Groups: navigation

### `data/story_quests/start_path_21_30.py`
- Groups: navigation

### `db.py`
- Groups: navigation

### `db_modules/dev_compat.py`
- Groups: navigation

### `db_modules/inventory.py`
- Groups: navigation

### `db_modules/inventory_compat.py`
- Groups: navigation

### `db_modules/migrations.py`
- Groups: navigation

### `db_modules/quests.py`
- Groups: navigation

### `db_modules/shop.py`
- Groups: navigation

### `db_modules/story_quests.py`
- Groups: navigation

### `db_modules/systems_wrappers.py`
- Groups: navigation

### `events/__init__.py`
- Groups: validation

### `events/test_event_2026/config.py`
- Groups: navigation

### `handlers/about_game.py`
- Groups: about, navigation, validation
- `FunctionDef _about_menu_kb` at line 8
- `FunctionDef _return_account_menu` at line 18
- `FunctionDef register_about_game_handlers` at line 23
- `FunctionDef open_about` at line 25
- `FunctionDef about_callback` at line 29

### `handlers/admin_crystal_credit.py`
- Groups: navigation, validation
- `FunctionDef _menu` at line 11

### `handlers/attribute_allocation.py`
- Groups: navigation, validation

### `handlers/auction_house.py`
- Groups: configuration, navigation, validation
- `FunctionDef _auction_main_menu_text_v1` at line 3114
- `FunctionDef _auction_register_back_to_menu_callback_v1` at line 3144
- `FunctionDef _auction_main_menu_text_v2` at line 3217
- `FunctionDef _auction_main_menu_text_v1` at line 5187
- `FunctionDef _auction_main_menu_text_v2` at line 5193
- `FunctionDef auction_inline_menu_callback_v1` at line 1642
- `FunctionDef auction_back_to_menu_callback_v1` at line 3147

### `handlers/blacksmith.py`
- Groups: navigation, validation
- `FunctionDef _blacksmith_show_repair_menu_v2` at line 74
- `FunctionDef _blacksmith_show_repair_menu_v3` at line 319

### `handlers/blacksmith_repair_confirm.py`
- Groups: navigation, validation
- `FunctionDef _brc_show_repair_menu_after_action_v1` at line 319

### `handlers/city.py`
- Groups: about, navigation, useful_links, validation
- `FunctionDef build_main_menu_text` at line 118
- `FunctionDef trade_district_submenu_kb_17_11_1` at line 485
- `FunctionDef send_trade_district_submenu_17_11_1` at line 492
- `FunctionDef build_main_menu_text` at line 1145
- `FunctionDef build_main_menu_text` at line 1232
- `FunctionDef build_account_menu_text_17_30_1_4` at line 1367
- `FunctionDef account_menu_kb_17_30_1_4` at line 1378
- `FunctionDef build_main_menu_text` at line 1395
- `FunctionDef open_main_menu_17_30_1_3` at line 1359

### `handlers/combat.py`
- Groups: navigation, validation
- `FunctionDef build_skill_menu_text` at line 1110

### `handlers/contracts.py`
- Groups: navigation

### `handlers/crystal_shop.py`
- Groups: navigation, validation
- `FunctionDef _menu_kb` at line 8

### `handlers/daily.py`
- Groups: navigation

### `handlers/dev.py`
- Groups: configuration

### `handlers/event_ui.py`
- Groups: navigation, validation

### `handlers/external_links.py`
- Groups: navigation, support, useful_links
- `FunctionDef _external_links_text` at line 11
- `FunctionDef _external_links_kb` at line 20
- `FunctionDef _return_account_menu` at line 33
- `FunctionDef register_external_links_handlers` at line 46
- `FunctionDef open_external_links` at line 50
- `FunctionDef close_external_links` at line 61

### `handlers/fatigue_artifact.py`
- Groups: configuration, navigation, validation

### `handlers/guild.py`
- Groups: navigation, support, validation
- `FunctionDef guild_applicant_profile_link_kb` at line 1006

### `handlers/inventory.py`
- Groups: navigation, support, validation

### `handlers/map.py`
- Groups: navigation, validation

### `handlers/name_rune.py`
- Groups: navigation, validation

### `handlers/player_interaction.py`
- Groups: navigation, validation
- `FunctionDef _trade_gold_menu_kb_12_6_3` at line 941

### `handlers/player_rankings.py`
- Groups: navigation, validation
- `FunctionDef rankings_menu` at line 40

### `handlers/profile.py`
- Groups: navigation, validation
- `FunctionDef _history_menu_kb` at line 813

### `handlers/pvp_interaction.py`
- Groups: navigation, validation

### `handlers/pvp_round_ui.py`
- Groups: navigation, validation

### `handlers/refine.py`
- Groups: navigation, validation
- `FunctionDef open_refine_menu` at line 389
- `FunctionDef refine_menu_callback` at line 442

### `handlers/runes.py`
- Groups: navigation, validation

### `handlers/start.py`
- Groups: navigation, validation

### `handlers/story_boss_invocation_wiring.py`
- Groups: navigation, validation
- `FunctionDef _invoke_supported` at line 58

### `handlers/story_quest_hierarchy_ui.py`
- Groups: navigation, validation

### `handlers/story_quest_npc_runtime.py`
- Groups: navigation, validation

### `handlers/story_quests.py`
- Groups: navigation, validation

### `handlers/timed_exp_bonus.py`
- Groups: navigation, validation

### `handlers/world_chronicles.py`
- Groups: navigation, validation

### `keyboards.py`
- Groups: navigation

### `main.py`
- Groups: about

### `migrations/030_static_item_namespace.py`
- Groups: navigation

### `migrations/052_registration_date_pipeline.py`
- Groups: navigation

### `migrations/053_story_quest_persistence_schema.py`
- Groups: navigation

### `migrations/runner.py`
- Groups: navigation, validation

### `systems/admin_crystal_credit_system.py`
- Groups: navigation

### `systems/attribute_allocation_system.py`
- Groups: navigation

### `systems/attribute_respec_system.py`
- Groups: navigation

### `systems/auction_house_system.py`
- Groups: navigation

### `systems/boss_system.py`
- Groups: navigation

### `systems/character_system.py`
- Groups: navigation

### `systems/combat_system.py`
- Groups: navigation, validation

### `systems/contract_system.py`
- Groups: validation

### `systems/crystal_bag_expansion_system.py`
- Groups: navigation, support

### `systems/crystal_shop_system.py`
- Groups: navigation

### `systems/crystal_wallet_system.py`
- Groups: navigation

### `systems/drop_system.py`
- Groups: navigation

### `systems/equipment_system.py`
- Groups: navigation

### `systems/event_item_catalog_system.py`
- Groups: navigation

### `systems/event_shop_system.py`
- Groups: navigation

### `systems/event_statistics_system.py`
- Groups: navigation

### `systems/fatigue_artifact_system.py`
- Groups: navigation

### `systems/guild_system.py`
- Groups: navigation, support, validation

### `systems/inactivity_reminder_system.py`
- Groups: navigation

### `systems/level_up_reward_system.py`
- Groups: navigation

### `systems/name_rune_system.py`
- Groups: navigation

### `systems/player_interaction_system.py`
- Groups: navigation

### `systems/player_system.py`
- Groups: navigation, support

### `systems/potion_system.py`
- Groups: navigation, support

### `systems/premium_item_policy_system.py`
- Groups: configuration, navigation

### `systems/production_logging.py`
- Groups: configuration, navigation, validation

### `systems/profile_history_system.py`
- Groups: navigation

### `systems/pve_auto_escape_system.py`
- Groups: navigation

### `systems/pve_skill_action_state.py`
- Groups: navigation

### `systems/pvp_anti_stall_survivability_candidate_sandbox.py`
- Groups: navigation

### `systems/pvp_battle_factory.py`
- Groups: navigation

### `systems/pvp_completion_service.py`
- Groups: navigation

### `systems/pvp_request_service.py`
- Groups: navigation

### `systems/pvp_root_cause_metric_semantics.py`
- Groups: validation

### `systems/pvp_round_ui.py`
- Groups: navigation

### `systems/pvp_system.py`
- Groups: navigation

### `systems/refine_system.py`
- Groups: navigation

### `systems/rune_system.py`
- Groups: navigation

### `systems/simulation/clock.py`
- Groups: navigation

### `systems/simulation/meta_progression.py`
- Groups: navigation

### `systems/simulation/progression_economy_reporting.py`
- Groups: validation

### `systems/simulation/rng_adapter.py`
- Groups: navigation

### `systems/stat_system.py`
- Groups: navigation

### `systems/story_boss_invocation_adapter.py`
- Groups: navigation

### `systems/story_quest_boss_call_system.py`
- Groups: navigation

### `systems/story_quest_completion_system.py`
- Groups: navigation

### `systems/story_quest_npc_acceptance_system.py`
- Groups: navigation

### `systems/story_quest_player_level.py`
- Groups: navigation

### `systems/story_quest_reward_system.py`
- Groups: navigation

### `systems/story_quest_system.py`
- Groups: navigation

### `systems/telegram_rate_limit.py`
- Groups: navigation

### `systems/timed_exp_bonus_system.py`
- Groups: navigation

### `systems/travel_system.py`
- Groups: navigation

### `systems/world_chronicle_system.py`
- Groups: navigation

### `tests_v2/test_admin_crystals.py`
- Groups: navigation

### `tests_v2/test_bag_expansion.py`
- Groups: navigation

### `tests_v2/test_base_equipment_shop.py`
- Groups: navigation

### `tests_v2/test_callback_codec_registry.py`
- Groups: navigation

### `tests_v2/test_crystal_wallet_ledger.py`
- Groups: navigation

### `tests_v2/test_daily_reward.py`
- Groups: navigation

### `tests_v2/test_equipment_slots.py`
- Groups: navigation

### `tests_v2/test_gold_wallet.py`
- Groups: navigation

### `tests_v2/test_inventory_service.py`
- Groups: navigation

### `tests_v2/test_map_presentation.py`
- Groups: navigation

### `tests_v2/test_overlevel_policy.py`
- Groups: navigation

### `tests_v2/test_post_combat_hooks.py`
- Groups: navigation

### `tests_v2/test_potion_trading.py`
- Groups: navigation

### `tests_v2/test_premium_shop.py`
- Groups: navigation

### `tests_v2/test_reward_settlement.py`
- Groups: navigation

### `tests_v2/test_telegram_adapter_skeleton.py`
- Groups: navigation

### `tests_v2/test_v2_repository_base.py`
- Groups: navigation

### `tests_v2/test_v2_unit_of_work.py`
- Groups: navigation

### `tests_v2/test_world_graph.py`
- Groups: navigation

## Audit boundaries

- Do not copy secret values from .env into reports or source.
- Do not invent About content, URLs, providers, payment destinations, validation rules, button order or callback identifiers.
- Treat configuration names and source defaults separately from runtime environment values.
- Preserve HTTPS fail-closed and hide-unconfigured behavior only where authoritative V1 evidence confirms it.

This audit records source evidence only. It does not authorize runtime, Telegram, URL, provider, payment or configuration mutation.
