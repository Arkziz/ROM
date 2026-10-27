# Stage 21.15.1 — Existing DEV authorization audit

- Status: **PASS**
- Conclusion: **PASS_REVIEW_REQUIRED**
- Next action: **GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW**
- V1/V2 production mutation: **NO**
- Production SQLite opened: **NO**
- `.env` opened: **NO**
- `main.py` started: **NO**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Evidence coverage

- `audit`: 416
- `authorization`: 120
- `commands`: 330
- `configuration`: 328
- `database_access`: 2409
- `dev_mode`: 72
- `identity`: 31
- `safe_reset`: 5250
- `telegram_registration`: 2

## Candidate owners and commands

### `config.py`
- Groups: commands, configuration, identity, safe_reset
- `FunctionDef _admin_ids_env` at line 15

### `data/about_game.py`
- Groups: safe_reset

### `data/balance.py`
- Groups: safe_reset

### `data/bosses.py`
- Groups: safe_reset

### `data/classes.py`
- Groups: configuration, safe_reset

### `data/defense_policy.py`
- Groups: safe_reset

### `data/drop_tables.py`
- Groups: configuration, safe_reset

### `data/equipment_identity_stat_policy.py`
- Groups: safe_reset

### `data/equipment_profiles.py`
- Groups: safe_reset

### `data/equipment_stat_policy.py`
- Groups: authorization, configuration, safe_reset

### `data/guild_resource_policy.py`
- Groups: audit

### `data/location_graph.py`
- Groups: safe_reset

### `data/mobs.py`
- Groups: safe_reset

### `data/player_progression.py`
- Groups: configuration

### `data/rebirth_sphere_policy.py`
- Groups: safe_reset

### `data/runes.py`
- Groups: safe_reset

### `data/stat_scaling.py`
- Groups: safe_reset

### `data/stat_system_config.py`
- Groups: configuration, safe_reset

### `data/story_quest_content.py`
- Groups: safe_reset

### `data/story_quest_definitions.py`
- Groups: safe_reset

### `data/story_quest_hierarchy.py`
- Groups: authorization

### `data/story_quest_item_identity.py`
- Groups: authorization, database_access, safe_reset

### `data/story_quest_npcs.py`
- Groups: safe_reset

### `data/story_quest_title_presentation.py`
- Groups: authorization, safe_reset

### `data/story_quests/dark_forest_51_60.py`
- Groups: safe_reset

### `data/story_quests/dark_forest_61_70.py`
- Groups: authorization, safe_reset

### `data/story_quests/dark_forest_71_80.py`
- Groups: safe_reset

### `data/story_quests/dark_forest_81_90.py`
- Groups: safe_reset

### `data/story_quests/dark_forest_91_100.py`
- Groups: authorization, safe_reset

### `data/story_quests/start_path_01_10.py`
- Groups: authorization, database_access, safe_reset

### `data/story_quests/start_path_11_20.py`
- Groups: authorization, database_access, safe_reset

### `data/story_quests/start_path_21_30.py`
- Groups: authorization, safe_reset

### `data/story_quests/start_path_31_40.py`
- Groups: safe_reset

### `data/story_quests/start_path_41_50.py`
- Groups: authorization, safe_reset

### `db.py`
- Groups: safe_reset

### `db_modules/__init__.py`
- Groups: audit, commands, configuration, safe_reset

### `db_modules/character.py`
- Groups: configuration, database_access, safe_reset
- `FunctionDef grant_class_change_available` at line 239

### `db_modules/connection.py`
- Groups: configuration, database_access, safe_reset

### `db_modules/daily_compat.py`
- Groups: database_access, safe_reset
- `FunctionDef reset_daily_quest_if_needed` at line 51

### `db_modules/dev_compat.py`
- Groups: audit, commands, configuration, database_access, safe_reset
- `FunctionDef reset_player_level_for_test` at line 204
- `FunctionDef _get_dev_reset_hero_lock` at line 258
- `FunctionDef _dev_reset_table_exists` at line 265
- `FunctionDef _dev_reset_table_columns` at line 272
- `FunctionDef _dev_reset_delete_by_user_columns` at line 277
- `FunctionDef reset_hero_for_test` at line 289
- `FunctionDef seed_class_reset_sphere_item` at line 735
- `FunctionDef normalize_dev_rarity` at line 1166
- `FunctionDef create_dev_armor_item_for_test` at line 1194
- `FunctionDef create_dev_weapon_item_for_test` at line 1367

### `db_modules/equipment.py`
- Groups: database_access, safe_reset

### `db_modules/generated_equipment.py`
- Groups: database_access, safe_reset

### `db_modules/inventory.py`
- Groups: database_access, safe_reset

### `db_modules/inventory_compat.py`
- Groups: configuration, database_access, safe_reset
- `FunctionDef seed_class_reset_sphere_item` at line 215
- `FunctionDef is_class_reset_sphere_inventory_item` at line 349
- `FunctionDef use_class_reset_sphere_from_inventory` at line 397

### `db_modules/location.py`
- Groups: database_access

### `db_modules/migrations.py`
- Groups: database_access, safe_reset

### `db_modules/player.py`
- Groups: database_access, safe_reset

### `db_modules/quests.py`
- Groups: database_access, safe_reset
- `FunctionDef reset_daily_quest_if_needed` at line 232

### `db_modules/refine.py`
- Groups: database_access, safe_reset

### `db_modules/shop.py`
- Groups: database_access, safe_reset
- `FunctionDef init_class_reset_sphere` at line 721
- `FunctionDef use_class_reset_sphere` at line 746

### `db_modules/story_quests.py`
- Groups: audit, database_access, safe_reset

### `db_modules/systems_wrappers.py`
- Groups: audit, database_access, safe_reset
- `FunctionDef reset_daily_hunts_if_needed` at line 43
- `FunctionDef reset_hp_regen_timers_now` at line 67

### `events/__init__.py`
- Groups: configuration, safe_reset
- `FunctionDef reset_event_registry_for_tests` at line 77

### `events/_template/__init__.py`
- Groups: configuration, safe_reset

### `events/_template/items.py`
- Groups: safe_reset

### `events/item_namespace.py`
- Groups: safe_reset

### `events/test_event_2026/__init__.py`
- Groups: configuration, safe_reset

### `events/test_event_2026/drops.py`
- Groups: configuration, safe_reset

### `events/test_event_2026/items.py`
- Groups: configuration, safe_reset

### `events/test_event_2026/mobs.py`
- Groups: configuration, safe_reset

### `events/test_event_2026/shop.py`
- Groups: configuration, safe_reset

### `events/test_event_2026/statistics.py`
- Groups: configuration

### `handlers/admin_crystal_credit.py`
- Groups: audit, commands, identity, safe_reset
- `FunctionDef register_admin_crystal_credit_handlers` at line 56
- `FunctionDef open_admin` at line 58

### `handlers/attribute_allocation.py`
- Groups: safe_reset

### `handlers/auction_house.py`
- Groups: audit, authorization, commands, configuration, identity, safe_reset
- `FunctionDef _auction_get_admin_ids_v1` at line 4977
- `FunctionDef _auction_is_admin_v1` at line 5000
- `FunctionDef _auction_admin_denied_text_v1` at line 5004
- `FunctionDef _auction_register_admin_command_guard_v1` at line 5025
- `FunctionDef auction_sanity_admin_guard_v1` at line 5028
- `FunctionDef auction_debug_admin_guard_v1` at line 5036
- `FunctionDef auction_fix_admin_guard_v1` at line 5044
- `FunctionDef auction_cleanup_admin_guard_v1` at line 5070

### `handlers/blacksmith.py`
- Groups: safe_reset

### `handlers/blacksmith_repair_confirm.py`
- Groups: safe_reset

### `handlers/city.py`
- Groups: safe_reset

### `handlers/combat.py`
- Groups: authorization, database_access, safe_reset

### `handlers/contracts.py`
- Groups: safe_reset

### `handlers/crystal_shop.py`
- Groups: safe_reset

### `handlers/daily.py`
- Groups: safe_reset

### `handlers/dev.py`
- Groups: audit, commands, configuration, dev_mode, safe_reset
- `FunctionDef parse_dev_rune_request` at line 64
- `FunctionDef parse_dev_quantity_request` at line 110
- `FunctionDef parse_dev_drop_sim_request` at line 149
- `FunctionDef register_dev_handlers` at line 184
- `FunctionDef register_dev_handlers` at line 1019
- `FunctionDef register_dev_handlers` at line 1049
- `FunctionDef register_dev_handlers` at line 1058
- `FunctionDef give_item` at line 191
- `FunctionDef reset_level` at line 291
- `FunctionDef reset_hero` at line 309
- `FunctionDef dev_armor` at line 605
- `FunctionDef dev_weapon` at line 655
- `FunctionDef dev_rune` at line 705
- `FunctionDef dev_firius` at line 727
- `FunctionDef dev_extractor` at line 750
- `FunctionDef dev_extractor_perfect` at line 769
- `FunctionDef dev_drop_sim` at line 797
- `FunctionDef dev_rune_drop_sim` at line 810
- `FunctionDef dev_pvp` at line 828
- `FunctionDef dev_pvp_all` at line 841
- `FunctionDef dev_pvp_audit` at line 855
- `FunctionDef dev_help` at line 868
- `FunctionDef give_class_reset_sphere` at line 931
- `FunctionDef dev_pvp_prod_14_6_2` at line 987
- `FunctionDef dev_pvp_prod_all_14_6_2` at line 996
- `FunctionDef dev_pvp_calibrate_14_6_2` at line 1005
- `FunctionDef dev_pvp_fixture_audit_14_6_2a` at line 1029
- `FunctionDef dev_premium_item_17_26_1` at line 1123

### `handlers/event_ui.py`
- Groups: configuration, database_access

### `handlers/external_links.py`
- Groups: configuration

### `handlers/fatigue_artifact.py`
- Groups: commands, configuration, dev_mode, safe_reset
- `FunctionDef dev_grant` at line 20

### `handlers/guild.py`
- Groups: authorization, commands, database_access, safe_reset
- `FunctionDef reset_guild_browse_state` at line 145
- `FunctionDef reset_guild_create_state` at line 180
- `FunctionDef reset_guild_application_review_state` at line 876
- `FunctionDef reset_guild_member_manage_state` at line 1166
- `FunctionDef _guild_safe_reset_other_states_for_members_v2` at line 1477
- `FunctionDef _guild_progress_reset_navigation_states_v1` at line 2063
- `FunctionDef _guild_progress_handle_dev_command_v1` at line 2075
- `FunctionDef reset_guild_logs_state` at line 2267
- `FunctionDef _guild_contracts_reset_guild_states_v1` at line 2535
- `FunctionDef reset_all_guild_ui_states` at line 2657

### `handlers/inventory.py`
- Groups: configuration, database_access, safe_reset

### `handlers/name_rune.py`
- Groups: database_access, safe_reset

### `handlers/player_interaction.py`
- Groups: audit, authorization, configuration, safe_reset, telegram_registration
- `FunctionDef _install_player_trade_handler_level_navigation_guard_12_6_6` at line 1465
- `FunctionDef active_trade_message_guard` at line 1493
- `FunctionDef active_trade_callback_guard` at line 1509

### `handlers/player_rankings.py`
- Groups: safe_reset

### `handlers/profile.py`
- Groups: audit, safe_reset

### `handlers/pvp_round_ui.py`
- Groups: safe_reset

### `handlers/refine.py`
- Groups: commands, safe_reset

### `handlers/runes.py`
- Groups: authorization, safe_reset

### `handlers/start.py`
- Groups: commands, configuration, safe_reset

### `handlers/story_boss_invocation_wiring.py`
- Groups: safe_reset

### `handlers/story_quest_npc_runtime.py`
- Groups: authorization, safe_reset

### `handlers/story_quests.py`
- Groups: audit, safe_reset

### `handlers/timed_exp_bonus.py`
- Groups: safe_reset

### `handlers/world_chronicles.py`
- Groups: safe_reset

### `main.py`
- Groups: audit, authorization, commands, configuration, safe_reset

### `migrations/010_rune_system_data_model.py`
- Groups: database_access, safe_reset

### `migrations/020_fresh_database_schema_parity.py`
- Groups: database_access, safe_reset

### `migrations/030_static_item_namespace.py`
- Groups: database_access, safe_reset

### `migrations/040_generated_equipment_namespace.py`
- Groups: database_access, safe_reset

### `migrations/041_shop_preview_promotion_recovery.py`
- Groups: database_access, safe_reset

### `migrations/042_attribute_points_foundation.py`
- Groups: database_access

### `migrations/043_existing_character_attribute_point_policy.py`
- Groups: database_access

### `migrations/044_attribute_respec_foundation.py`
- Groups: audit, database_access, safe_reset

### `migrations/045_new_path_sphere_class_change.py`
- Groups: database_access

### `migrations/045a_seed_new_path_sphere_dependency.py`
- Groups: database_access, safe_reset

### `migrations/046_sphere_consumable_presentation.py`
- Groups: database_access, safe_reset

### `migrations/047_sphere_stack_and_category_fix.py`
- Groups: database_access, safe_reset

### `migrations/048_rebirth_sphere_stack_limit.py`
- Groups: database_access, safe_reset

### `migrations/049_persistent_location_travel.py`
- Groups: audit

### `migrations/050_event_kill_statistics.py`
- Groups: database_access

### `migrations/051_event_shop_exchange.py`
- Groups: database_access, safe_reset

### `migrations/052_registration_date_pipeline.py`
- Groups: database_access

### `migrations/053_story_quest_persistence_schema.py`
- Groups: database_access, safe_reset

### `migrations/054_story_quest_kill_target_normalization.py`
- Groups: database_access, safe_reset

### `migrations/runner.py`
- Groups: database_access

### `systems/admin_crystal_credit_system.py`
- Groups: audit, commands, configuration, database_access, identity, safe_reset
- `FunctionDef is_admin` at line 11
- `FunctionDef init_admin_crystal_credit_system` at line 12
- `FunctionDef preview_admin_adjustment` at line 17
- `FunctionDef execute_admin_adjustment` at line 35
- `FunctionDef get_admin_adjustment_history` at line 55
- `FunctionDef get_admin_adjustment_detail` at line 62

### `systems/attribute_allocation_system.py`
- Groups: database_access, safe_reset

### `systems/attribute_respec_system.py`
- Groups: authorization, database_access, safe_reset
- `FunctionDef reset_allocated_attributes` at line 54

### `systems/auction_house_system.py`
- Groups: audit, authorization, database_access, safe_reset

### `systems/boss_system.py`
- Groups: safe_reset

### `systems/character_system.py`
- Groups: authorization, configuration, database_access, safe_reset
- `FunctionDef grant_class_change_available` at line 415
- `FunctionDef get_class_reset_sphere_item_id` at line 485
- `FunctionDef reset_mp_regen_clock_17_15_1` at line 763

### `systems/combat_system.py`
- Groups: configuration, safe_reset

### `systems/contract_system.py`
- Groups: database_access, safe_reset
- `FunctionDef reset_daily_contracts_if_needed` at line 91
- `FunctionDef reset_daily_hunts_if_needed` at line 124
- `FunctionDef get_daily_contract_reset_info` at line 574

### `systems/crystal_bag_expansion_system.py`
- Groups: database_access, safe_reset

### `systems/crystal_shop_system.py`
- Groups: database_access, safe_reset

### `systems/crystal_wallet_system.py`
- Groups: audit, commands, database_access, safe_reset

### `systems/drop_system.py`
- Groups: authorization, configuration, safe_reset

### `systems/dynamic_equipment_system.py`
- Groups: safe_reset

### `systems/energy_system.py`
- Groups: database_access, safe_reset
- `FunctionDef reset_daily_hunts_if_needed` at line 193

### `systems/equipment_system.py`
- Groups: database_access, safe_reset

### `systems/event_item_catalog_system.py`
- Groups: database_access, safe_reset

### `systems/event_shop_system.py`
- Groups: configuration, database_access, safe_reset

### `systems/event_statistics_system.py`
- Groups: database_access

### `systems/fatigue_artifact_system.py`
- Groups: database_access, safe_reset

### `systems/fresh_database_bootstrap.py`
- Groups: safe_reset

### `systems/guild_system.py`
- Groups: audit, database_access, safe_reset
- `FunctionDef archive_and_reset_guild_monthly_stats` at line 348

### `systems/inactivity_reminder_system.py`
- Groups: database_access

### `systems/item_id_allocator_system.py`
- Groups: database_access, safe_reset

### `systems/level_up_reward_system.py`
- Groups: audit, configuration, database_access, safe_reset

### `systems/name_rune_system.py`
- Groups: database_access, safe_reset

### `systems/notifications.py`
- Groups: configuration, database_access, safe_reset
- `FunctionDef notify_daily_contracts_reset` at line 460

### `systems/player_interaction_system.py`
- Groups: audit, authorization, commands, database_access, safe_reset

### `systems/player_rankings_system.py`
- Groups: database_access, safe_reset

### `systems/player_system.py`
- Groups: configuration, database_access, safe_reset

### `systems/potion_system.py`
- Groups: configuration, database_access, safe_reset

### `systems/premium_item_policy_system.py`
- Groups: commands, configuration, database_access, dev_mode, safe_reset
- `FunctionDef _dev_enabled` at line 58
- `FunctionDef can_grant_item_from_source` at line 124
- `FunctionDef _grant_stack` at line 181
- `FunctionDef grant_item_from_source` at line 205
- `FunctionDef get_premium_item_grants` at line 265

### `systems/production_logging.py`
- Groups: audit, configuration

### `systems/profile_history_system.py`
- Groups: audit, database_access, safe_reset

### `systems/pve_auto_escape_system.py`
- Groups: audit, database_access

### `systems/pvp_action_validation.py`
- Groups: configuration

### `systems/pvp_adaptive_balance_optimizer.py`
- Groups: audit, safe_reset

### `systems/pvp_anti_stall_survivability_candidate_sandbox.py`
- Groups: audit, configuration, safe_reset

### `systems/pvp_balance_simulator.py`
- Groups: safe_reset

### `systems/pvp_battle_factory.py`
- Groups: configuration

### `systems/pvp_combat_log.py`
- Groups: safe_reset

### `systems/pvp_completion_service.py`
- Groups: safe_reset

### `systems/pvp_knight_judgement_terminal_audit.py`
- Groups: audit

### `systems/pvp_models.py`
- Groups: safe_reset

### `systems/pvp_policy_balance_candidate_sandbox.py`
- Groups: audit, configuration, safe_reset

### `systems/pvp_policy_metrics_audit.py`
- Groups: audit, safe_reset

### `systems/pvp_primary_stat_scaling_combat_pacing_sandbox.py`
- Groups: audit, configuration, safe_reset

### `systems/pvp_production_calibration.py`
- Groups: audit, safe_reset

### `systems/pvp_production_fixture_audit.py`
- Groups: audit, configuration, safe_reset

### `systems/pvp_real_actor_root_cause_audit.py`
- Groups: audit, safe_reset

### `systems/pvp_real_actor_state_replay.py`
- Groups: audit, safe_reset

### `systems/pvp_real_equipment_fixture_audit.py`
- Groups: audit, safe_reset

### `systems/pvp_request_service.py`
- Groups: database_access

### `systems/pvp_root_cause_metric_semantics.py`
- Groups: audit, safe_reset

### `systems/pvp_round_engine.py`
- Groups: configuration, safe_reset

### `systems/pvp_skill_adapter.py`
- Groups: safe_reset

### `systems/pvp_system.py`
- Groups: authorization, configuration, database_access, safe_reset

### `systems/pvp_targeted_mechanics_candidate_sandbox.py`
- Groups: audit, configuration, safe_reset

### `systems/refine_system.py`
- Groups: database_access, safe_reset

### `systems/regen_system.py`
- Groups: database_access, safe_reset
- `FunctionDef reset_hp_regen_timers_now` at line 131

### `systems/reward_system.py`
- Groups: configuration, safe_reset

### `systems/rune_system.py`
- Groups: database_access, safe_reset

### `systems/simulation/__init__.py`
- Groups: configuration, safe_reset

### `systems/simulation/asset_valuation.py`
- Groups: safe_reset

### `systems/simulation/balance_analyzer.py`
- Groups: configuration, database_access, safe_reset

### `systems/simulation/behavior_policy.py`
- Groups: safe_reset

### `systems/simulation/canonical_rules.py`
- Groups: safe_reset

### `systems/simulation/capacity_analysis.py`
- Groups: safe_reset

### `systems/simulation/class_progression.py`
- Groups: audit, configuration, safe_reset

### `systems/simulation/clock.py`
- Groups: configuration

### `systems/simulation/combat_actor_stats.py`
- Groups: configuration, safe_reset

### `systems/simulation/config.py`
- Groups: configuration

### `systems/simulation/drop_inventory.py`
- Groups: safe_reset

### `systems/simulation/economic_ledger.py`
- Groups: audit, safe_reset

### `systems/simulation/economic_progression.py`
- Groups: audit

### `systems/simulation/economy_analyzer.py`
- Groups: safe_reset

### `systems/simulation/economy_guild_acceptance.py`
- Groups: audit, safe_reset

### `systems/simulation/equipment_policy.py`
- Groups: safe_reset

### `systems/simulation/equipment_service.py`
- Groups: safe_reset

### `systems/simulation/excel_reporting.py`
- Groups: safe_reset

### `systems/simulation/guild_population.py`
- Groups: safe_reset

### `systems/simulation/inventory_engine.py`
- Groups: safe_reset

### `systems/simulation/loot_equipment_city.py`
- Groups: safe_reset

### `systems/simulation/meta_progression.py`
- Groups: database_access, safe_reset

### `systems/simulation/metrics.py`
- Groups: safe_reset

### `systems/simulation/models.py`
- Groups: configuration, safe_reset

### `systems/simulation/parity_foundation.py`
- Groups: audit, safe_reset

### `systems/simulation/patch_regression.py`
- Groups: audit, configuration, safe_reset

### `systems/simulation/population_reporting.py`
- Groups: safe_reset

### `systems/simulation/potion_affordability.py`
- Groups: audit, safe_reset

### `systems/simulation/production_parity.py`
- Groups: safe_reset

### `systems/simulation/progression_economy_reporting.py`
- Groups: database_access, safe_reset

### `systems/simulation/progression_models.py`
- Groups: safe_reset

### `systems/simulation/progression_wall_analyzer.py`
- Groups: configuration, database_access, safe_reset

### `systems/simulation/pve_battle.py`
- Groups: safe_reset

### `systems/simulation/reporting.py`
- Groups: configuration, safe_reset

### `systems/simulation/rng_percentiles.py`
- Groups: safe_reset

### `systems/simulation/skill_catalog.py`
- Groups: safe_reset

### `systems/simulation/survival_state.py`
- Groups: safe_reset

### `systems/simulation/world_progression.py`
- Groups: audit, safe_reset

### `systems/stat_system.py`
- Groups: configuration, safe_reset

### `systems/story_quest_completion_system.py`
- Groups: database_access, safe_reset

### `systems/story_quest_item_drop_system.py`
- Groups: safe_reset

### `systems/story_quest_npc_acceptance_system.py`
- Groups: safe_reset

### `systems/story_quest_overlevel_system.py`
- Groups: safe_reset

### `systems/story_quest_reward_system.py`
- Groups: database_access

### `systems/story_quest_system.py`
- Groups: database_access, safe_reset

### `systems/telegram_rate_limit.py`
- Groups: authorization
- `FunctionDef _guard_method` at line 125
- `FunctionDef install_global_telegram_rate_limit_guard` at line 165
- `FunctionDef guarded` at line 133

### `systems/timed_exp_bonus_system.py`
- Groups: database_access, safe_reset

### `systems/travel_system.py`
- Groups: audit, database_access

### `systems/world_chronicle_system.py`
- Groups: database_access, safe_reset

### `tests/test_stage_21_7_6b_durability_and_repair.py`
- Groups: safe_reset

### `tests/test_stage_21_7_7b_enhancement.py`
- Groups: commands, safe_reset

### `tests/test_stage_21_7_8b_presentation_dto.py`
- Groups: safe_reset

### `tests/unit/about_links_support/test_about_links_support.py`
- Groups: configuration
- `FunctionDef test_catalog_preserves_authoritative_order_and_exact_content` at line 17

### `tests/unit/events/test_event_schedules_rewards.py`
- Groups: safe_reset

### `tests/unit/inactivity_reminders/test_inactivity_reminders.py`
- Groups: audit

### `tests/unit/ratings_history_chronicles/test_ratings_history_chronicles.py`
- Groups: audit, safe_reset

### `tests_v2/test_account_domain.py`
- Groups: commands, database_access, safe_reset

### `tests_v2/test_admin_crystals.py`
- Groups: audit, authorization, commands, database_access, identity, safe_reset
- `FunctionDef is_admin` at line 6
- `FunctionDef test_guards_stale` at line 34

### `tests_v2/test_architecture_enforcement.py`
- Groups: configuration, safe_reset

### `tests_v2/test_auction.py`
- Groups: safe_reset

### `tests_v2/test_bag_expansion.py`
- Groups: commands, database_access, safe_reset
- `FunctionDef test_restart_replay_and_reset_survival` at line 59

### `tests_v2/test_base_equipment_shop.py`
- Groups: database_access, safe_reset

### `tests_v2/test_battle_persistence.py`
- Groups: database_access

### `tests_v2/test_callback_codec_registry.py`
- Groups: safe_reset

### `tests_v2/test_central_loot.py`
- Groups: configuration, safe_reset

### `tests_v2/test_character_lifecycle.py`
- Groups: commands, database_access, safe_reset
- `FunctionDef test_reset_removes_character_and_requires_registration` at line 17

### `tests_v2/test_class_catalog.py`
- Groups: audit, authorization, commands, database_access, safe_reset

### `tests_v2/test_crystal_wallet_ledger.py`
- Groups: audit, authorization, commands, database_access, safe_reset

### `tests_v2/test_daily_reward.py`
- Groups: authorization, commands, database_access, safe_reset

### `tests_v2/test_derived_stats.py`
- Groups: audit

### `tests_v2/test_direct_trade.py`
- Groups: safe_reset

### `tests_v2/test_equipment_generation_policy.py`
- Groups: commands, safe_reset
- `FunctionDef test_dev_and_simulator_are_consumers` at line 34

### `tests_v2/test_equipment_slots.py`
- Groups: database_access, safe_reset

### `tests_v2/test_full_stat_snapshot.py`
- Groups: safe_reset

### `tests_v2/test_gold_wallet.py`
- Groups: audit, commands, database_access

### `tests_v2/test_guild_contract_history.py`
- Groups: audit, authorization, safe_reset

### `tests_v2/test_guild_core.py`
- Groups: authorization
- `FunctionDef test_invariant_guard` at line 18

### `tests_v2/test_guild_management.py`
- Groups: authorization

### `tests_v2/test_inventory_service.py`
- Groups: database_access, safe_reset

### `tests_v2/test_item_definition_instance.py`
- Groups: database_access, safe_reset

### `tests_v2/test_item_id_namespace.py`
- Groups: safe_reset

### `tests_v2/test_level_up_gold.py`
- Groups: configuration, safe_reset

### `tests_v2/test_location_catalog.py`
- Groups: safe_reset

### `tests_v2/test_map_presentation.py`
- Groups: commands

### `tests_v2/test_npc_dialogue_model.py`
- Groups: commands

### `tests_v2/test_overlevel_policy.py`
- Groups: authorization, database_access, safe_reset
- `FunctionDef test_skipped_reward_guard` at line 24

### `tests_v2/test_player_progression.py`
- Groups: configuration

### `tests_v2/test_post_combat_hooks.py`
- Groups: authorization, database_access, safe_reset

### `tests_v2/test_potion_trading.py`
- Groups: commands, database_access

### `tests_v2/test_premium_combat.py`
- Groups: authorization

### `tests_v2/test_premium_shop.py`
- Groups: commands, database_access, safe_reset

### `tests_v2/test_pvp.py`
- Groups: audit, authorization

### `tests_v2/test_quest_item_store.py`
- Groups: database_access, safe_reset

### `tests_v2/test_retrospective_parity_reconciliation.py`
- Groups: authorization, safe_reset

### `tests_v2/test_reward_settlement.py`
- Groups: audit, commands, database_access, safe_reset

### `tests_v2/test_rune_lifecycle.py`
- Groups: authorization, database_access, safe_reset
- `FunctionDef test_guards_fail_before_mutation` at line 38

### `tests_v2/test_schema_contract.py`
- Groups: audit, safe_reset

### `tests_v2/test_settings.py`
- Groups: configuration

### `tests_v2/test_story_content_11_20.py`
- Groups: database_access

### `tests_v2/test_story_content_41_50.py`
- Groups: safe_reset

### `tests_v2/test_story_navigation.py`
- Groups: authorization

### `tests_v2/test_telegram_adapter_skeleton.py`
- Groups: commands

### `tests_v2/test_terminal_paths.py`
- Groups: authorization

### `tests_v2/test_v2_baseline_migration.py`
- Groups: audit, database_access, safe_reset

### `tests_v2/test_v2_bootstrap_smoke.py`
- Groups: configuration

### `tests_v2/test_v2_connection_factory.py`
- Groups: database_access

### `tests_v2/test_v2_db_integrity_suite.py`
- Groups: safe_reset

### `tests_v2/test_v2_repository_base.py`
- Groups: audit, authorization, database_access

### `tests_v2/test_v2_unit_of_work.py`
- Groups: audit, authorization, database_access, safe_reset

### `tests_v2/test_world_graph.py`
- Groups: safe_reset

## Required semantic questions

- Which source owns DEV_MODE and its exact disabled semantics?
- Which identity source authorizes developers or administrators?
- Does every DEV command invoke one authoritative guard before side effects?
- Which commands are read-only, controlled mutations, destructive operations, or obsolete aliases?
- Which operations have durable audit evidence and stable idempotency?
- Do any handlers perform direct SQL or bypass canonical application services?
- Are duplicate Telegram registrations or shadow command paths present?

## Explicit prohibitions

- Do not read or expose .env values.
- Do not invent developer IDs, administrator IDs, roles, command names, audit fields or safe-command policy.
- Do not execute DEV commands, open production SQLite, start main.py or connect Telegram runtime.
- Do not promote keyword matches to canonical policy without semantic refinement.

This audit is evidence inventory only and does not authorize implementation.
