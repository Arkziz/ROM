# Stage 21.14.2 — Existing V1 event schedules and rewards audit

- Status: **PASS**
- Conclusion: **PASS_REVIEW_REQUIRED**
- Next action: **GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW**
- Branch: `rewrite/rom-v2`
- HEAD before audit: `678e7cc883886d7631feeda88006799473ab7b69`
- Production source mutation: **NO**
- Production SQLite connection opened: **NO**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**
- Manual in-game verification: **NOT REQUIRED**

## Evidence coverage

- `announcement`: 70 source occurrences
- `eligibility`: 228 source occurrences
- `event_identity`: 199 source occurrences
- `exact_once`: 274 source occurrences
- `lifecycle`: 2150 source occurrences
- `namespace`: 67 source occurrences
- `reward`: 50 source occurrences
- `schedule`: 22 source occurrences
- `scheduler`: 0 source occurrences
- `statistics`: 35 source occurrences
- `timezone`: 485 source occurrences

## Candidate source owners

### `data/defense_policy.py`
- AST: PASS
- Groups: lifecycle

### `data/drop_tables.py`
- AST: PASS
- Groups: eligibility, lifecycle

### `data/guild_resource_policy.py`
- AST: PASS
- Groups: eligibility, exact_once, lifecycle

### `data/mana_policy.py`
- AST: PASS
- Groups: lifecycle

### `data/player_progression.py`
- AST: PASS
- Groups: namespace

### `data/rebirth_sphere_policy.py`
- AST: PASS
- Groups: eligibility

### `data/rune_drop_balance.py`
- AST: PASS
- Groups: eligibility

### `data/story_quest_definitions.py`
- AST: PASS
- Groups: exact_once, lifecycle
- `ClassDef PersistentQuestStatus` at line 19
- `ClassDef DerivedQuestStatus` at line 22
- `FunctionDef derive_story_quest_status` at line 157

### `data/story_quest_hierarchy.py`
- AST: PASS
- Groups: eligibility, lifecycle

### `data/story_quest_item_identity.py`
- AST: PASS
- Groups: exact_once, lifecycle

### `data/story_quest_title_presentation.py`
- AST: PASS
- Groups: lifecycle

### `data/story_quests/dark_forest_51_60.py`
- AST: PASS
- Groups: exact_once

### `data/story_quests/dark_forest_61_70.py`
- AST: PASS
- Groups: exact_once

### `data/story_quests/dark_forest_71_80.py`
- AST: PASS
- Groups: exact_once

### `data/story_quests/dark_forest_81_90.py`
- AST: PASS
- Groups: exact_once

### `data/story_quests/dark_forest_91_100.py`
- AST: PASS
- Groups: exact_once

### `data/story_quests/start_path_21_30.py`
- AST: PASS
- Groups: exact_once

### `data/story_quests/start_path_31_40.py`
- AST: PASS
- Groups: exact_once

### `data/story_quests/start_path_41_50.py`
- AST: PASS
- Groups: exact_once, lifecycle

### `data/travel_presentation.py`
- AST: PASS
- Groups: lifecycle

### `db_modules/__init__.py`
- AST: PASS
- Groups: announcement, eligibility, exact_once, lifecycle

### `db_modules/connection.py`
- AST: PASS
- Groups: lifecycle, namespace

### `db_modules/daily_compat.py`
- AST: PASS
- Groups: lifecycle, reward
- `FunctionDef get_daily_quest_status` at line 111

### `db_modules/dev_compat.py`
- AST: PASS
- Groups: lifecycle

### `db_modules/inventory_compat.py`
- AST: PASS
- Groups: eligibility
- `FunctionDef get_item_required_level_by_inventory_id` at line 99

### `db_modules/migrations.py`
- AST: PASS
- Groups: exact_once, lifecycle, reward
- `FunctionDef get_migration_status` at line 102

### `db_modules/player.py`
- AST: PASS
- Groups: timezone

### `db_modules/quests.py`
- AST: PASS
- Groups: exact_once, lifecycle, reward

### `db_modules/story_quests.py`
- AST: PASS
- Groups: exact_once, lifecycle, reward, timezone
- `FunctionDef utc_now_iso` at line 23
- `FunctionDef get_active_story_quest` at line 53
- `FunctionDef skip_active_story_quest` at line 305

### `db_modules/systems_wrappers.py`
- AST: PASS
- Groups: announcement, event_identity, exact_once, lifecycle
- `FunctionDef get_users_for_energy_full_notification` at line 40
- `FunctionDef make_existing_guild_icons_unique` at line 211
- `FunctionDef ensure_unique_guild_icon_index` at line 215
- `FunctionDef get_user_active_auction_count` at line 401
- `FunctionDef mark_auction_lot_status` at line 420
- `FunctionDef cancel_active_auction_lot` at line 511
- `FunctionDef claim_expired_auction_item` at line 527
- `FunctionDef update_expired_auction_lots` at line 595
- `FunctionDef abandon_active_contract` at line 761
- `FunctionDef get_contract_status` at line 769
- `FunctionDef get_active_player_trade` at line 887
- `FunctionDef recover_active_player_trades_after_restart` at line 1005

### `events/__init__.py`
- AST: PASS
- Groups: event_identity, exact_once, lifecycle, namespace, schedule, timezone
- `FunctionDef _utc` at line 17
- `FunctionDef get_active_events` at line 73
- `FunctionDef collect_registered_event_items` at line 123
- `FunctionDef get_validated_registered_event_items` at line 156

### `events/_template/__init__.py`
- AST: PASS
- Groups: statistics

### `events/_template/config.py`
- AST: PASS
- Groups: event_identity, lifecycle, schedule, timezone
- `FunctionDef is_active` at line 8

### `events/_template/items.py`
- AST: PASS
- Groups: namespace

### `events/_template/statistics.py`
- AST: PASS
- Groups: statistics

### `events/item_namespace.py`
- AST: PASS
- Groups: event_identity, namespace
- `FunctionDef _normalize_event_key` at line 29
- `FunctionDef get_event_item_blocks` at line 77
- `FunctionDef get_event_item_block` at line 85
- `FunctionDef validate_event_item_id` at line 90
- `FunctionDef validate_event_item_definitions` at line 99

### `events/test_event_2026/__init__.py`
- AST: PASS
- Groups: event_identity, schedule, statistics, timezone

### `events/test_event_2026/config.py`
- AST: PASS
- Groups: event_identity, lifecycle, schedule, timezone
- `FunctionDef _fallback_kyiv_timezone` at line 39
- `FunctionDef is_active` at line 74
- `ClassDef ZoneInfoNotFoundError` at line 7

### `events/test_event_2026/drops.py`
- AST: PASS
- Groups: event_identity

### `events/test_event_2026/items.py`
- AST: PASS
- Groups: event_identity, namespace, reward
- `FunctionDef get_event_item_id` at line 46

### `events/test_event_2026/mobs.py`
- AST: PASS
- Groups: event_identity

### `events/test_event_2026/rewards.py`
- AST: PASS
- Groups: reward

### `events/test_event_2026/shop.py`
- AST: PASS
- Groups: event_identity

### `events/test_event_2026/statistics.py`
- AST: PASS
- Groups: event_identity, lifecycle, statistics
- `FunctionDef get_statistics_definitions` at line 18

### `handlers/admin_crystal_credit.py`
- AST: PASS
- Groups: announcement, exact_once, timezone
- `FunctionDef _notification_text` at line 23
- `ClassDef ZoneInfoNotFoundError` at line 8

### `handlers/attribute_allocation.py`
- AST: PASS
- Groups: lifecycle

### `handlers/auction_house.py`
- AST: PASS
- Groups: exact_once, lifecycle, namespace
- `FunctionDef auction_completed_sales_inline_kb_v1` at line 2597
- `FunctionDef build_auction_completed_sales_text_v1` at line 2634
- `FunctionDef auction_completed_sale_view_kb_v1` at line 2649
- `FunctionDef auction_completed_sale_claim_confirm_kb_v1` at line 2657
- `FunctionDef _auction_register_completed_sales_handlers_v1` at line 2664
- `FunctionDef auction_completed_sales_inline_kb_v1` at line 3915
- `FunctionDef auction_completed_sale_view_kb_v1` at line 3929
- `FunctionDef auction_completed_sales_start_v1` at line 2667
- `FunctionDef auction_completed_sales_page_callback_v1` at line 2673
- `FunctionDef auction_completed_sale_view_callback_v1` at line 2684
- `FunctionDef auction_completed_sale_claim_confirm_callback_v1` at line 2710
- `FunctionDef auction_completed_sale_claim_do_callback_v1` at line 2740
- `FunctionDef auction_completed_sales_start_section_cleanup_v1` at line 3970

### `handlers/blacksmith.py`
- AST: PASS
- Groups: exact_once

### `handlers/blacksmith_repair_confirm.py`
- AST: PASS
- Groups: lifecycle

### `handlers/city.py`
- AST: PASS
- Groups: eligibility, lifecycle, timezone
- `FunctionDef build_contracts_short_status` at line 101
- `FunctionDef _format_account_utc_17_30_1_1` at line 1220

### `handlers/combat.py`
- AST: PASS
- Groups: announcement, eligibility, event_identity, exact_once, lifecycle, statistics
- `FunctionDef call_active_story_boss` at line 2128

### `handlers/contracts.py`
- AST: PASS
- Groups: lifecycle

### `handlers/crystal_shop.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef _active_shop_callback` at line 56

### `handlers/daily.py`
- AST: PASS
- Groups: lifecycle, reward

### `handlers/event_ui.py`
- AST: PASS
- Groups: event_identity, lifecycle, schedule, statistics, timezone
- `FunctionDef _active` at line 8

### `handlers/guild.py`
- AST: PASS
- Groups: eligibility, event_identity, exact_once, lifecycle
- `FunctionDef get_active_guild_ui_states` at line 2676

### `handlers/inventory.py`
- AST: PASS
- Groups: eligibility, lifecycle

### `handlers/map.py`
- AST: PASS
- Groups: lifecycle, timezone

### `handlers/player_interaction.py`
- AST: PASS
- Groups: eligibility, lifecycle
- `FunctionDef player_trade_active_reply_kb_12_6_4` at line 1325
- `FunctionDef _trade_is_amount_input_active_12_6_4` at line 1444
- `FunctionDef _trade_ready_status_text_12_7_0` at line 1743
- `FunctionDef trade_status_noop` at line 1489
- `FunctionDef active_trade_message_guard` at line 1493
- `FunctionDef active_trade_callback_guard` at line 1509

### `handlers/profile.py`
- AST: PASS
- Groups: lifecycle

### `handlers/pvp_interaction.py`
- AST: PASS
- Groups: lifecycle

### `handlers/pvp_round_ui.py`
- AST: PASS
- Groups: announcement, eligibility, lifecycle
- `FunctionDef pvp_active_reply_kb` at line 28
- `FunctionDef _release_terminal_participants` at line 73
- `FunctionDef broadcast_pvp_round_log` at line 99
- `FunctionDef broadcast_pvp_state` at line 113
- `FunctionDef pvp_status_message` at line 137
- `FunctionDef _timer_broadcast` at line 216

### `handlers/refine.py`
- AST: PASS
- Groups: eligibility, exact_once, lifecycle
- `FunctionDef build_refine_idempotency_key` at line 415

### `handlers/runes.py`
- AST: PASS
- Groups: eligibility

### `handlers/story_boss_invocation_wiring.py`
- AST: PASS
- Groups: eligibility, lifecycle
- `FunctionDef _active_call` at line 74
- `FunctionDef _active_story_boss_callback_call` at line 159

### `handlers/story_quest_hierarchy_ui.py`
- AST: PASS
- Groups: eligibility, lifecycle
- `FunctionDef _completed_numbers` at line 66
- `FunctionDef _status_icon` at line 74
- `FunctionDef _section_status` at line 99

### `handlers/story_quest_npc_runtime.py`
- AST: PASS
- Groups: lifecycle

### `handlers/story_quests.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef _status_label` at line 111
- `FunctionDef _hierarchy_status_reader` at line 349

### `handlers/timed_exp_bonus.py`
- AST: PASS
- Groups: lifecycle, timezone

### `handlers/world_chronicles.py`
- AST: PASS
- Groups: event_identity, timezone
- `FunctionDef _kyiv_timezone_for_utc` at line 29

### `keyboards.py`
- AST: PASS
- Groups: lifecycle

### `main.py`
- AST: PASS
- Groups: announcement, eligibility, lifecycle

### `migrations/010_rune_system_data_model.py`
- AST: PASS
- Groups: exact_once

### `migrations/030_static_item_namespace.py`
- AST: PASS
- Groups: exact_once

### `migrations/040_generated_equipment_namespace.py`
- AST: PASS
- Groups: timezone

### `migrations/041_shop_preview_promotion_recovery.py`
- AST: PASS
- Groups: namespace

### `migrations/043_existing_character_attribute_point_policy.py`
- AST: PASS
- Groups: exact_once, timezone

### `migrations/044_attribute_respec_foundation.py`
- AST: PASS
- Groups: exact_once

### `migrations/049_persistent_location_travel.py`
- AST: PASS
- Groups: exact_once, lifecycle

### `migrations/050_event_kill_statistics.py`
- AST: PASS
- Groups: event_identity, statistics

### `migrations/051_event_shop_exchange.py`
- AST: PASS
- Groups: event_identity, exact_once

### `migrations/052_registration_date_pipeline.py`
- AST: PASS
- Groups: timezone
- `FunctionDef _utc_now` at line 8

### `migrations/053_story_quest_persistence_schema.py`
- AST: PASS
- Groups: exact_once, lifecycle, reward

### `migrations/054_story_quest_kill_target_normalization.py`
- AST: PASS
- Groups: lifecycle

### `migrations/runner.py`
- AST: PASS
- Groups: exact_once, lifecycle
- `FunctionDef get_migration_status` at line 144

### `systems/admin_crystal_credit_system.py`
- AST: PASS
- Groups: exact_once, timezone
- `FunctionDef _utc` at line 8

### `systems/attribute_respec_system.py`
- AST: PASS
- Groups: exact_once, timezone

### `systems/auction_house_system.py`
- AST: PASS
- Groups: eligibility, event_identity, exact_once, lifecycle, namespace
- `FunctionDef get_user_active_auction_count` at line 301
- `FunctionDef mark_auction_lot_status` at line 521
- `FunctionDef update_expired_auction_lots` at line 580
- `FunctionDef cancel_active_auction_lot` at line 3337
- `FunctionDef claim_expired_auction_item` at line 3557
- `FunctionDef _auction_sold_statuses_v1` at line 4577
- `FunctionDef _auction_safe_status_v2` at line 4822
- `FunctionDef update_expired_auction_lots` at line 4840
- `FunctionDef _auction_diag_statuses_v1` at line 5103

### `systems/boss_system.py`
- AST: PASS
- Groups: eligibility, event_identity, lifecycle

### `systems/contract_system.py`
- AST: PASS
- Groups: eligibility, lifecycle, reward
- `FunctionDef get_active_contract` at line 150
- `FunctionDef get_contract_status` at line 214
- `FunctionDef abandon_active_contract` at line 348
- `FunctionDef migrate_active_contracts_target_kills_to_5` at line 460

### `systems/crystal_bag_expansion_system.py`
- AST: PASS
- Groups: exact_once, timezone
- `FunctionDef _utc` at line 11

### `systems/crystal_shop_system.py`
- AST: PASS
- Groups: exact_once, timezone
- `FunctionDef _utc` at line 9

### `systems/crystal_wallet_system.py`
- AST: PASS
- Groups: exact_once, timezone
- `FunctionDef _utc` at line 10

### `systems/drop_system.py`
- AST: PASS
- Groups: event_identity, lifecycle, namespace
- `FunctionDef get_central_drop_status` at line 539

### `systems/energy_system.py`
- AST: PASS
- Groups: announcement
- `FunctionDef get_users_for_energy_full_notification` at line 103

### `systems/equipment_system.py`
- AST: PASS
- Groups: eligibility
- `FunctionDef _equipment_write_required_level_v5` at line 2249

### `systems/event_item_catalog_system.py`
- AST: PASS
- Groups: namespace
- `FunctionDef get_registered_event_item_definitions` at line 22
- `FunctionDef validate_event_item_catalog_definitions` at line 35
- `FunctionDef seed_event_item_catalog` at line 55

### `systems/event_shop_system.py`
- AST: PASS
- Groups: event_identity, exact_once, lifecycle, timezone

### `systems/event_statistics_system.py`
- AST: PASS
- Groups: event_identity, statistics, timezone

### `systems/fatigue_artifact_system.py`
- AST: PASS
- Groups: exact_once, lifecycle, timezone

### `systems/fresh_database_bootstrap.py`
- AST: PASS
- Groups: exact_once, lifecycle

### `systems/guild_resource_system.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef validate_guild_resource_feature_inactive` at line 43

### `systems/guild_system.py`
- AST: PASS
- Groups: eligibility, event_identity, exact_once, lifecycle, timezone
- `FunctionDef _guild_utc_now_17_21_1` at line 547
- `FunctionDef _guild_utc_iso_17_21_1` at line 550
- `FunctionDef _guild_parse_utc_17_21_1` at line 554
- `FunctionDef _pick_unique_guild_icon` at line 1268
- `FunctionDef make_existing_guild_icons_unique` at line 1288
- `FunctionDef ensure_unique_guild_icon_index` at line 1344
- `FunctionDef _guild_safe_set_application_status` at line 1916

### `systems/inactivity_reminder_system.py`
- AST: PASS
- Groups: eligibility, exact_once, lifecycle, timezone
- `FunctionDef _utc` at line 11
- `FunctionDef get_eligible_inactivity_users` at line 23

### `systems/item_id_allocator_system.py`
- AST: PASS
- Groups: exact_once, namespace, timezone

### `systems/level_up_reward_system.py`
- AST: PASS
- Groups: exact_once

### `systems/name_rune_system.py`
- AST: PASS
- Groups: exact_once, timezone

### `systems/notifications.py`
- AST: PASS
- Groups: announcement, lifecycle
- `FunctionDef get_users_for_energy_full_notification_worker` at line 148
- `FunctionDef get_users_for_hp_full_notification_worker` at line 364
- `FunctionDef notification_worker` at line 476
- `FunctionDef start_notification_worker` at line 516
- `FunctionDef get_users_for_mp_full_notification_worker_17_15_1` at line 909

### `systems/player_interaction_system.py`
- AST: PASS
- Groups: eligibility, event_identity, exact_once, lifecycle, timezone
- `FunctionDef recover_active_player_trades_after_restart` at line 1034
- `FunctionDef get_active_player_trade` at line 1108
- `FunctionDef _active_auction_reserved_quantity` at line 1254

### `systems/player_rankings_system.py`
- AST: PASS
- Groups: eligibility
- `FunctionDef _eligible` at line 24

### `systems/player_system.py`
- AST: PASS
- Groups: announcement, lifecycle

### `systems/potion_system.py`
- AST: PASS
- Groups: lifecycle, namespace

### `systems/premium_item_policy_system.py`
- AST: PASS
- Groups: exact_once, timezone
- `FunctionDef _utc` at line 49

### `systems/production_logging.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef logging_status` at line 50

### `systems/profile_history_system.py`
- AST: PASS
- Groups: lifecycle, timezone

### `systems/pve_auto_escape_system.py`
- AST: PASS
- Groups: exact_once, lifecycle, timezone
- `FunctionDef _utcnow` at line 14
- `FunctionDef _has_legacy_user_unique` at line 29
- `FunctionDef get_active_pve_encounter` at line 74
- `FunctionDef get_expired_active_pve_encounters` at line 93

### `systems/pvp_action_validation.py`
- AST: PASS
- Groups: eligibility

### `systems/pvp_adaptive_balance_optimizer.py`
- AST: PASS
- Groups: lifecycle, namespace

### `systems/pvp_anti_stall_survivability_candidate_sandbox.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef _scale_active_sustain` at line 66

### `systems/pvp_balance_simulator.py`
- AST: PASS
- Groups: timezone

### `systems/pvp_battle_factory.py`
- AST: PASS
- Groups: eligibility, lifecycle

### `systems/pvp_combat_log.py`
- AST: PASS
- Groups: lifecycle, timezone

### `systems/pvp_completion_service.py`
- AST: PASS
- Groups: eligibility, lifecycle
- `FunctionDef _participants_by_id` at line 33

### `systems/pvp_knight_judgement_terminal_audit.py`
- AST: PASS
- Groups: timezone

### `systems/pvp_models.py`
- AST: PASS
- Groups: timezone
- `ClassDef PvpActionOutcome` at line 72

### `systems/pvp_policy_balance_candidate_sandbox.py`
- AST: PASS
- Groups: lifecycle

### `systems/pvp_policy_metrics_audit.py`
- AST: PASS
- Groups: timezone

### `systems/pvp_primary_stat_scaling_combat_pacing_sandbox.py`
- AST: PASS
- Groups: lifecycle

### `systems/pvp_production_calibration.py`
- AST: PASS
- Groups: timezone

### `systems/pvp_real_actor_root_cause_audit.py`
- AST: PASS
- Groups: timezone

### `systems/pvp_real_actor_state_replay.py`
- AST: PASS
- Groups: timezone

### `systems/pvp_real_equipment_fixture_audit.py`
- AST: PASS
- Groups: lifecycle

### `systems/pvp_request_service.py`
- AST: PASS
- Groups: lifecycle

### `systems/pvp_root_cause_metric_semantics.py`
- AST: PASS
- Groups: lifecycle, timezone

### `systems/pvp_round_engine.py`
- AST: PASS
- Groups: lifecycle, timezone

### `systems/pvp_round_ui.py`
- AST: PASS
- Groups: eligibility, lifecycle
- `FunctionDef _participant_display_name` at line 17

### `systems/pvp_system.py`
- AST: PASS
- Groups: eligibility, event_identity, exact_once, lifecycle, timezone
- `FunctionDef _utc_now` at line 21
- `FunctionDef get_pvp_participants` at line 208
- `FunctionDef _normalized_participant` at line 224
- `FunctionDef list_active_pvp_battles` at line 583
- `FunctionDef get_active_pvp_battle_for_user` at line 590

### `systems/pvp_targeted_mechanics_candidate_sandbox.py`
- AST: PASS
- Groups: lifecycle, timezone

### `systems/pvp_timer_service.py`
- AST: PASS
- Groups: eligibility, lifecycle, timezone
- `FunctionDef _expired` at line 22
- `FunctionDef close_expired_round` at line 29

### `systems/refine_system.py`
- AST: PASS
- Groups: eligibility, exact_once, timezone
- `FunctionDef get_refine_max_level` at line 44

### `systems/regen_system.py`
- AST: PASS
- Groups: announcement, lifecycle
- `FunctionDef get_hp_regen_status` at line 349
- `FunctionDef get_mp_regen_status` at line 367

### `systems/reward_system.py`
- AST: PASS
- Groups: lifecycle

### `systems/rune_system.py`
- AST: PASS
- Groups: eligibility, exact_once, lifecycle, namespace, reward

### `systems/simulation/balance_analyzer.py`
- AST: PASS
- Groups: event_identity, exact_once, lifecycle, statistics

### `systems/simulation/class_progression.py`
- AST: PASS
- Groups: event_identity, exact_once, lifecycle, timezone

### `systems/simulation/clock.py`
- AST: PASS
- Groups: lifecycle, timezone
- `FunctionDef is_active` at line 46
- `FunctionDef next_active_start` at line 49
- `FunctionDef active_window_end` at line 58
- `FunctionDef jump_to_next_active_start` at line 64

### `systems/simulation/config.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef active_minutes` at line 22

### `systems/simulation/drop_inventory.py`
- AST: PASS
- Groups: lifecycle

### `systems/simulation/economic_ledger.py`
- AST: PASS
- Groups: event_identity

### `systems/simulation/economy_analyzer.py`
- AST: PASS
- Groups: event_identity

### `systems/simulation/economy_guild_acceptance.py`
- AST: PASS
- Groups: statistics

### `systems/simulation/excel_reporting.py`
- AST: PASS
- Groups: event_identity, lifecycle

### `systems/simulation/guild_population.py`
- AST: PASS
- Groups: event_identity

### `systems/simulation/meta_progression.py`
- AST: PASS
- Groups: eligibility, lifecycle

### `systems/simulation/metrics.py`
- AST: PASS
- Groups: event_identity

### `systems/simulation/models.py`
- AST: PASS
- Groups: lifecycle, reward

### `systems/simulation/parity_foundation.py`
- AST: PASS
- Groups: lifecycle

### `systems/simulation/patch_regression.py`
- AST: PASS
- Groups: lifecycle, timezone

### `systems/simulation/progression_economy_reporting.py`
- AST: PASS
- Groups: event_identity

### `systems/simulation/progression_models.py`
- AST: PASS
- Groups: event_identity, lifecycle

### `systems/simulation/progression_reporting.py`
- AST: PASS
- Groups: lifecycle

### `systems/simulation/reporting.py`
- AST: PASS
- Groups: lifecycle

### `systems/simulation/rng_percentiles.py`
- AST: PASS
- Groups: statistics

### `systems/simulation/world_progression.py`
- AST: PASS
- Groups: lifecycle, timezone

### `systems/stat_system.py`
- AST: PASS
- Groups: lifecycle

### `systems/story_boss_invocation_adapter.py`
- AST: PASS
- Groups: lifecycle

### `systems/story_quest_boss_call_system.py`
- AST: PASS
- Groups: eligibility, lifecycle
- `FunctionDef get_active_story_boss_call` at line 11

### `systems/story_quest_boss_completion_system.py`
- AST: PASS
- Groups: exact_once, lifecycle, reward

### `systems/story_quest_combat_progress_system.py`
- AST: PASS
- Groups: lifecycle

### `systems/story_quest_completion_system.py`
- AST: PASS
- Groups: exact_once, lifecycle, reward, timezone
- `FunctionDef complete_active_story_quest` at line 82

### `systems/story_quest_item_drop_system.py`
- AST: PASS
- Groups: lifecycle

### `systems/story_quest_npc_acceptance_system.py`
- AST: PASS
- Groups: exact_once, lifecycle

### `systems/story_quest_overlevel_system.py`
- AST: PASS
- Groups: announcement, eligibility, lifecycle
- `FunctionDef build_story_location_max_levels` at line 11

### `systems/story_quest_reward_system.py`
- AST: PASS
- Groups: exact_once, lifecycle

### `systems/story_quest_system.py`
- AST: PASS
- Groups: eligibility, exact_once, lifecycle
- `FunctionDef get_story_quest_status` at line 113
- `FunctionDef collect_active_quest_item` at line 253
- `FunctionDef skip_overlevel_active_quest` at line 322

### `systems/telegram_rate_limit.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef is_expired_callback_query_error` at line 38
- `FunctionDef get_telegram_rate_limit_status` at line 181

### `systems/timed_exp_bonus_system.py`
- AST: PASS
- Groups: exact_once, lifecycle, timezone
- `FunctionDef _utc` at line 8
- `FunctionDef get_exp_bonus_status` at line 19

### `systems/travel_system.py`
- AST: PASS
- Groups: announcement, exact_once, lifecycle, timezone
- `FunctionDef _utc` at line 20
- `FunctionDef get_active_travel` at line 46
- `FunctionDef get_due_active_travels` at line 56

### `systems/world_chronicle_system.py`
- AST: PASS
- Groups: event_identity, exact_once, lifecycle, timezone

### `tests/test_stage_21_7_7b_enhancement.py`
- AST: PASS
- Groups: eligibility, exact_once, lifecycle
- `FunctionDef test_reservation_and_idempotent_replay` at line 21
- `FunctionDef is_operation_completed` at line 7

### `tests/test_stage_21_7_8b_presentation_dto.py`
- AST: PASS
- Groups: eligibility

### `tests/test_stage_21_8_1b_battle_aggregate.py`
- AST: PASS
- Groups: lifecycle

### `tests/test_stage_21_8_5c_skill_execution.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef test_active_skill_validates_then_mutates_exactly_once` at line 14

### `tests_v2/test_account_domain.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef test_no_invented_status_or_version_contract` at line 10

### `tests_v2/test_admin_crystals.py`
- AST: PASS
- Groups: announcement

### `tests_v2/test_architecture_enforcement.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_auction.py`
- AST: PASS
- Groups: exact_once, lifecycle
- `FunctionDef test_sale_ack_exact_once` at line 16
- `FunctionDef test_cancel_exact_once` at line 20

### `tests_v2/test_base_equipment_shop.py`
- AST: PASS
- Groups: lifecycle, timezone

### `tests_v2/test_battle_persistence.py`
- AST: PASS
- Groups: exact_once, lifecycle, timezone
- `FunctionDef test_begin_and_read_active` at line 16
- `FunctionDef test_terminal_claim_is_absorbing_and_idempotent` at line 20
- `FunctionDef test_expired_selection_is_deterministic` at line 37
- `FunctionDef test_multiple_active_for_actor_fails_closed` at line 42

### `tests_v2/test_central_loot.py`
- AST: PASS
- Groups: timezone

### `tests_v2/test_character_lifecycle.py`
- AST: PASS
- Groups: exact_once, lifecycle, timezone
- `FunctionDef test_casefold_uniqueness` at line 14

### `tests_v2/test_ci_baseline.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_class_catalog.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_crystal_wallet_ledger.py`
- AST: PASS
- Groups: exact_once, timezone
- `FunctionDef get_by_idempotency_key` at line 9
- `FunctionDef test_compensation_exact_once` at line 39

### `tests_v2/test_daily_reward.py`
- AST: PASS
- Groups: reward
- `FunctionDef test_wrong_reward_key_forbidden` at line 59

### `tests_v2/test_direct_trade.py`
- AST: PASS
- Groups: eligibility, lifecycle
- `FunctionDef test_stale_and_eligibility` at line 10

### `tests_v2/test_effect_engine.py`
- AST: PASS
- Groups: lifecycle, timezone

### `tests_v2/test_equipment_generation_policy.py`
- AST: PASS
- Groups: eligibility
- `FunctionDef test_required_level_cannot_diverge` at line 30

### `tests_v2/test_equipment_slots.py`
- AST: PASS
- Groups: eligibility, lifecycle

### `tests_v2/test_full_stat_snapshot.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_gold_wallet.py`
- AST: PASS
- Groups: timezone

### `tests_v2/test_guild_management.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_inventory_service.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_item_id_namespace.py`
- AST: PASS
- Groups: exact_once, namespace
- `FunctionDef test_preview_promotion_exact_once` at line 11

### `tests_v2/test_map_presentation.py`
- AST: PASS
- Groups: lifecycle, timezone

### `tests_v2/test_overlevel_policy.py`
- AST: PASS
- Groups: exact_once, lifecycle, reward
- `FunctionDef test_idempotent` at line 12

### `tests_v2/test_post_combat_hooks.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef test_completed_consumer_is_skipped` at line 24

### `tests_v2/test_premium_combat.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef test_active_exact_25_percent` at line 6
- `FunctionDef test_inactive_is_identity` at line 11

### `tests_v2/test_premium_shop.py`
- AST: PASS
- Groups: lifecycle, timezone
- `FunctionDef now_utc` at line 22
- `FunctionDef test_extend_from_active_expiry` at line 39
- `FunctionDef test_expired_activates_from_now` at line 41

### `tests_v2/test_pvp.py`
- AST: PASS
- Groups: eligibility, exact_once, timezone
- `FunctionDef test_idempotent_create` at line 8
- `FunctionDef test_timeout_exact_once_history` at line 16

### `tests_v2/test_quest_engine.py`
- AST: PASS
- Groups: exact_once, lifecycle
- `FunctionDef test_exact_once_turn_in` at line 13

### `tests_v2/test_quest_item_store.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_retrospective_parity_reconciliation.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_reward_settlement.py`
- AST: PASS
- Groups: exact_once, lifecycle, timezone
- `FunctionDef test_exact_once_duplicate_returns_prior_result` at line 55
- `FunctionDef test_pending_loot_is_explicit_success_outcome` at line 75
- `FunctionDef completed_result` at line 32

### `tests_v2/test_runtime_paths.py`
- AST: PASS
- Groups: exact_once
- `FunctionDef test_create_is_idempotent_and_isolated` at line 14

### `tests_v2/test_schema_contract.py`
- AST: PASS
- Groups: exact_once, lifecycle, timezone
- `FunctionDef test_exact_once_dependents_reference_operation_records` at line 45

### `tests_v2/test_story_navigation.py`
- AST: PASS
- Groups: lifecycle
- `FunctionDef test_status_derivation` at line 12
- `FunctionDef test_active_target` at line 15

### `tests_v2/test_structured_logging.py`
- AST: PASS
- Groups: event_identity

### `tests_v2/test_terminal_paths.py`
- AST: PASS
- Groups: lifecycle, timezone
- `FunctionDef test_competing_terminal_outcome_is_rejected` at line 15

### `tests_v2/test_travel_aggregate.py`
- AST: PASS
- Groups: lifecycle, timezone

### `tests_v2/test_v2_baseline_migration.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_v2_connection_factory.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_v2_db_integrity_suite.py`
- AST: PASS
- Groups: lifecycle

### `tests_v2/test_v2_repository_base.py`
- AST: PASS
- Groups: lifecycle, timezone
- `FunctionDef test_repository_requires_active_unit_of_work_transaction` at line 42

### `tests_v2/test_v2_unit_of_work.py`
- AST: PASS
- Groups: lifecycle

## Confirmed boundaries

- This is evidence inventory only. It does not authorize a mutation.
- Exact schedules, rewards, event types, eligibility rules, announcements, timezone semantics and restart behavior require semantic reconciliation from authoritative V1 owners.
- Stage 21.14.1 event item namespace remains a prerequisite and is not modified here.
- Runtime, Telegram dispatch, scheduler wiring and production persistence are not connected by this audit.

## Required successor

`GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW`
