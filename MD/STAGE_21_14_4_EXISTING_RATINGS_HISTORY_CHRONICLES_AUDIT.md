# Stage 21.14.4 — Existing V1 ratings, history and chronicles audit

- Status: **PASS**
- Conclusion: **PASS_REVIEW_REQUIRED**
- Next action: **GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW**
- Branch: `rewrite/rom-v2`
- HEAD before audit: `d7dd7d5a3b044731fa481a5324731f6de5f7b651`
- Production source mutation: **NO**
- Production SQLite opened: **NO**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**
- Manual in-game verification: **NOT REQUIRED**

## Evidence coverage

- `chronicles`: 95 occurrences
- `history`: 386 occurrences
- `ordering_tiebreak`: 4035 occurrences
- `pagination`: 1647 occurrences
- `persistence`: 1470 occurrences
- `presentation`: 2722 occurrences
- `rating_categories`: 49349 occurrences
- `ratings`: 67 occurrences
- `retention`: 17 occurrences
- `scope_identity`: 4911 occurrences

## Strong candidate owners

### `systems/profile_history_system.py`
- Evidence score: 41
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, rating_categories, retention, scope_identity
- Candidate symbol `localize_pvp_reason` (FunctionDef) at line 20
- Candidate symbol `init_profile_history` (FunctionDef) at line 38
- Candidate symbol `get_trade_history` (FunctionDef) at line 44
- Candidate symbol `get_trade_history_detail` (FunctionDef) at line 61
- Candidate symbol `get_pvp_history` (FunctionDef) at line 66
- Candidate symbol `get_pvp_history_detail` (FunctionDef) at line 77
- Candidate symbol `cleanup_history_retention` (FunctionDef) at line 80

### `systems/player_interaction_system.py`
- Evidence score: 38
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity
- Candidate symbol `_init_player_trade_schema` (FunctionDef) at line 870
- Candidate symbol `init_player_trade_foundation` (FunctionDef) at line 956
- Candidate symbol `_trade_event` (FunctionDef) at line 968
- Candidate symbol `_write_trade_history` (FunctionDef) at line 975
- Candidate symbol `create_player_trade_from_accepted_request` (FunctionDef) at line 987
- Candidate symbol `recover_active_player_trades_after_restart` (FunctionDef) at line 1034
- Candidate symbol `get_player_trade` (FunctionDef) at line 1098
- Candidate symbol `get_active_player_trade` (FunctionDef) at line 1108
- Candidate symbol `get_player_trade_events` (FunctionDef) at line 1122
- Candidate symbol `get_player_trade_history` (FunctionDef) at line 1130
- Candidate symbol `cancel_player_trade` (FunctionDef) at line 1142
- Candidate symbol `expire_stale_player_trades` (FunctionDef) at line 1169
- Candidate symbol `init_player_trade_item_policy_and_reservations` (FunctionDef) at line 1222
- Candidate symbol `_trade_policy_result` (FunctionDef) at line 1283
- Candidate symbol `_trade_base_build_item_snapshot_12_6_3` (FunctionDef) at line 1327
- Candidate symbol `get_item_trade_policy` (FunctionDef) at line 1380
- Candidate symbol `reserve_inventory_for_trade` (FunctionDef) at line 1469
- Candidate symbol `release_trade_inventory_reservations` (FunctionDef) at line 1501
- Candidate symbol `_trade_offer_actor` (FunctionDef) at line 1550
- Candidate symbol `_trade_actor_offer_locked_12_7_0` (FunctionDef) at line 1560

### `handlers/world_chronicles.py`
- Evidence score: 35
- Groups: chronicles, ordering_tiebreak, pagination, presentation, rating_categories, scope_identity
- Candidate symbol `_format_world_chronicle_time` (FunctionDef) at line 40
- Candidate symbol `_world_chronicle_event_text` (FunctionDef) at line 53
- Candidate symbol `build_world_chronicles_text` (FunctionDef) at line 77
- Candidate symbol `world_chronicles_kb` (FunctionDef) at line 89
- Candidate symbol `_show_world_chronicles` (FunctionDef) at line 108
- Candidate symbol `register_world_chronicle_handlers` (FunctionDef) at line 125
- Candidate symbol `open_world_chronicles` (FunctionDef) at line 127
- Candidate symbol `world_chronicles_callback` (FunctionDef) at line 131

### `systems/world_chronicle_system.py`
- Evidence score: 35
- Groups: chronicles, ordering_tiebreak, pagination, persistence, presentation, rating_categories, retention, scope_identity
- Candidate symbol `init_world_chronicle_system` (FunctionDef) at line 29
- Candidate symbol `record_world_chronicle_event` (FunctionDef) at line 56
- Candidate symbol `get_world_chronicle_page` (FunctionDef) at line 126

### `handlers/player_interaction.py`
- Evidence score: 30
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity
- Candidate constant `PAGE_SIZE` at line 31: `8`
- Candidate symbol `_is_trade_request_callback` (FunctionDef) at line 115
- Candidate symbol `_trade_offer_name` (FunctionDef) at line 127
- Candidate symbol `_trade_offer_lines` (FunctionDef) at line 133
- Candidate symbol `_trade_inventory_text` (FunctionDef) at line 147
- Candidate symbol `_trade_inventory_kb` (FunctionDef) at line 151
- Candidate symbol `_trade_item_kb` (FunctionDef) at line 173
- Candidate symbol `_send_trade_editor` (FunctionDef) at line 185
- Candidate symbol `_trade_ux_offer_name` (FunctionDef) at line 563
- Candidate symbol `_trade_ux_is_equipment` (FunctionDef) at line 569
- Candidate symbol `_trade_ux_mine_text` (FunctionDef) at line 579
- Candidate symbol `_trade_ux_stack_kb` (FunctionDef) at line 588
- Candidate symbol `_trade_ux_equipment_kb` (FunctionDef) at line 602
- Candidate symbol `_trade_ux_show_mine` (FunctionDef) at line 609
- Candidate symbol `_register_player_trade_offer_editor_ux_handlers` (FunctionDef) at line 617
- Candidate symbol `_trade_money_12_6_2` (FunctionDef) at line 757
- Candidate symbol `_trade_editor_text` (FunctionDef) at line 763
- Candidate symbol `_trade_preview_text_12_6_2` (FunctionDef) at line 786
- Candidate symbol `_trade_preview_equipment_kb_12_6_2` (FunctionDef) at line 810
- Candidate symbol `_trade_show_preview_12_6_2` (FunctionDef) at line 821
- Candidate symbol `_trade_gold_text_12_6_2` (FunctionDef) at line 833

### `systems/auction_house_system.py`
- Evidence score: 28
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, rating_categories, retention, scope_identity
- Candidate symbol `add_auction_history` (FunctionDef) at line 240
- Candidate symbol `get_user_auction_history` (FunctionDef) at line 4584
- Candidate symbol `format_auction_history_date` (FunctionDef) at line 4772
- Candidate symbol `_auction_trade_reserved_quantity_12_6_3c` (FunctionDef) at line 5426

### `systems/pvp_system.py`
- Evidence score: 28
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity
- Candidate symbol `configure_pvp_connection_factory` (FunctionDef) at line 54
- Candidate symbol `init_pvp_foundation` (FunctionDef) at line 94
- Candidate symbol `get_pvp_battle` (FunctionDef) at line 199
- Candidate symbol `get_pvp_participants` (FunctionDef) at line 208
- Candidate symbol `create_pvp_battle` (FunctionDef) at line 240
- Candidate symbol `add_pvp_event` (FunctionDef) at line 306
- Candidate symbol `submit_pvp_action` (FunctionDef) at line 330
- Candidate symbol `get_pvp_round_actions` (FunctionDef) at line 384
- Candidate symbol `claim_pvp_round_resolution` (FunctionDef) at line 407
- Candidate symbol `release_pvp_round_resolution` (FunctionDef) at line 427
- Candidate symbol `complete_pvp_battle` (FunctionDef) at line 450
- Candidate symbol `get_pvp_recovery_plan` (FunctionDef) at line 475
- Candidate symbol `recover_pvp_after_restart` (FunctionDef) at line 499
- Candidate symbol `get_pvp_events` (FunctionDef) at line 520
- Candidate symbol `resolve_persisted_pvp_round` (FunctionDef) at line 532
- Candidate symbol `list_active_pvp_battles` (FunctionDef) at line 583
- Candidate symbol `get_active_pvp_battle_for_user` (FunctionDef) at line 590
- Candidate symbol `cleanup_terminal_pvp_activity_sessions` (FunctionDef) at line 607

### `handlers/player_rankings.py`
- Evidence score: 26
- Groups: pagination, presentation, rating_categories, ratings, scope_identity
- Candidate symbol `player_rankings_exit_kb` (FunctionDef) at line 8
- Candidate symbol `player_rankings_category_inline_kb` (FunctionDef) at line 13
- Candidate symbol `register_player_rankings_handlers` (FunctionDef) at line 38
- Candidate symbol `rankings_menu` (FunctionDef) at line 40
- Candidate symbol `rankings_back` (FunctionDef) at line 44
- Candidate symbol `ranking_callback` (FunctionDef) at line 48

### `systems/guild_system.py`
- Evidence score: 26
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, rating_categories, ratings, scope_identity
- Candidate symbol `_init_guild_membership_history_17_21_1` (FunctionDef) at line 566
- Candidate symbol `get_guild_ranking` (FunctionDef) at line 957
- Candidate symbol `get_guild_season_history` (FunctionDef) at line 1005
- Candidate symbol `get_guild_contribution_ranking` (FunctionDef) at line 2314

### `systems/player_rankings_system.py`
- Evidence score: 26
- Groups: pagination, persistence, presentation, rating_categories, ratings, scope_identity
- Candidate constant `TOP_LIMIT` at line 8: `100`
- Candidate constant `PAGE_SIZE` at line 9: `20`
- Candidate symbol `get_player_ranking_categories` (FunctionDef) at line 21
- Candidate symbol `get_player_ranking_page` (FunctionDef) at line 34
- Candidate symbol `get_player_ranking_position` (FunctionDef) at line 42

### `systems/pvp_anti_stall_survivability_candidate_sandbox.py`
- Evidence score: 22
- Groups: ordering_tiebreak, presentation, rating_categories, ratings, scope_identity

### `handlers/auction_house.py`
- Evidence score: 21
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity
- Candidate symbol `auction_history_reply_kb_v1` (FunctionDef) at line 4387
- Candidate symbol `auction_history_inline_kb_v1` (FunctionDef) at line 4401
- Candidate symbol `_auction_history_row_to_line_v1` (FunctionDef) at line 4421
- Candidate symbol `build_auction_history_text_v1` (FunctionDef) at line 4446
- Candidate symbol `_auction_register_history_market_prices_handlers_v1` (FunctionDef) at line 4611
- Candidate symbol `_auction_open_history_screen_v1` (FunctionDef) at line 4725
- Candidate symbol `_auction_register_history_keyboard_restore_v1` (FunctionDef) at line 4753
- Candidate symbol `auction_history_placeholder` (FunctionDef) at line 311
- Candidate symbol `auction_history_start_section_cleanup_v1` (FunctionDef) at line 3983
- Candidate symbol `auction_history_start_v1` (FunctionDef) at line 4614
- Candidate symbol `auction_history_page_callback_v1` (FunctionDef) at line 4625
- Candidate symbol `auction_market_price_back_history_v1` (FunctionDef) at line 4653
- Candidate symbol `auction_lot_price_history_callback_v1` (FunctionDef) at line 4687
- Candidate symbol `auction_history_back_restore_keyboard_v1` (FunctionDef) at line 4756

### `handlers/story_quests.py`
- Evidence score: 21
- Groups: history, ordering_tiebreak, pagination, presentation, rating_categories, scope_identity

### `systems/pvp_primary_stat_scaling_combat_pacing_sandbox.py`
- Evidence score: 21
- Groups: ordering_tiebreak, rating_categories, ratings, scope_identity

### `db_modules/dev_compat.py`
- Evidence score: 20
- Groups: history, persistence, presentation, rating_categories, scope_identity

### `handlers/profile.py`
- Evidence score: 20
- Groups: history, ordering_tiebreak, pagination, presentation, rating_categories, scope_identity
- Candidate symbol `_history_menu_kb` (FunctionDef) at line 813
- Candidate symbol `_history_list_kb` (FunctionDef) at line 827
- Candidate symbol `_history_list_text` (FunctionDef) at line 851
- Candidate symbol `profile_history_reply_message_17_24_1_1` (FunctionDef) at line 897
- Candidate symbol `profile_history_callback` (FunctionDef) at line 1123

### `systems/admin_crystal_credit_system.py`
- Evidence score: 20
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, scope_identity
- Candidate symbol `get_admin_adjustment_history` (FunctionDef) at line 55

### `systems/crystal_wallet_system.py`
- Evidence score: 20
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity

### `systems/pvp_adaptive_balance_optimizer.py`
- Evidence score: 20
- Groups: history, ordering_tiebreak, rating_categories, scope_identity

### `systems/pvp_policy_balance_candidate_sandbox.py`
- Evidence score: 20
- Groups: ordering_tiebreak, pagination, rating_categories, ratings, scope_identity

### `systems/pvp_targeted_mechanics_candidate_sandbox.py`
- Evidence score: 20
- Groups: ordering_tiebreak, pagination, rating_categories, ratings, scope_identity

### `systems/rune_system.py`
- Evidence score: 20
- Groups: ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity

### `handlers/city.py`
- Evidence score: 19
- Groups: chronicles, ordering_tiebreak, pagination, presentation, rating_categories, scope_identity
- Candidate symbol `build_trade_district_text` (FunctionDef) at line 52
- Candidate symbol `trade_district_submenu_kb_17_11_1` (FunctionDef) at line 485
- Candidate symbol `send_trade_district_submenu_17_11_1` (FunctionDef) at line 492
- Candidate symbol `show_trade_district` (FunctionDef) at line 537
- Candidate symbol `back_to_trade_district_message` (FunctionDef) at line 562
- Candidate symbol `back_to_trade_district` (FunctionDef) at line 686
- Candidate symbol `back_to_trader_callback` (FunctionDef) at line 692
- Candidate symbol `alchemist_trade_17_19_3` (FunctionDef) at line 707

### `handlers/guild.py`
- Evidence score: 19
- Groups: ordering_tiebreak, pagination, persistence, presentation, rating_categories, ratings, scope_identity
- Candidate symbol `build_guild_ranking_text` (FunctionDef) at line 342
- Candidate symbol `guild_monthly_ranking_message` (FunctionDef) at line 746
- Candidate symbol `guild_total_ranking_message` (FunctionDef) at line 750

### `systems/equipment_system.py`
- Evidence score: 19
- Groups: ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity
- Candidate symbol `sell_inventory_item_to_trader` (FunctionDef) at line 550
- Candidate symbol `buy_common_equipment_from_trader` (FunctionDef) at line 562
- Candidate symbol `_trader_db_9_0_12h3` (FunctionDef) at line 3573
- Candidate symbol `_trader_wallet_9_0_12h3` (FunctionDef) at line 3583
- Candidate symbol `_trader_bag_state_9_0_12h3` (FunctionDef) at line 3593
- Candidate symbol `_trader_display_name_9_0_12h3` (FunctionDef) at line 3619
- Candidate symbol `sell_inventory_item_to_trader` (FunctionDef) at line 3691
- Candidate symbol `buy_common_equipment_from_trader` (FunctionDef) at line 3935

### `db_modules/quests.py`
- Evidence score: 18
- Groups: ordering_tiebreak, persistence, presentation, rating_categories, scope_identity

### `db_modules/systems_wrappers.py`
- Evidence score: 18
- Groups: history, pagination, persistence, presentation, rating_categories, ratings, scope_identity
- Candidate symbol `get_guild_ranking` (FunctionDef) at line 159
- Candidate symbol `get_guild_season_history` (FunctionDef) at line 163
- Candidate symbol `get_guild_contribution_ranking` (FunctionDef) at line 318
- Candidate symbol `add_auction_history` (FunctionDef) at line 393
- Candidate symbol `get_user_auction_history` (FunctionDef) at line 575
- Candidate symbol `format_auction_history_date` (FunctionDef) at line 591
- Candidate symbol `init_player_trade_foundation` (FunctionDef) at line 875
- Candidate symbol `create_player_trade_from_accepted_request` (FunctionDef) at line 879
- Candidate symbol `get_player_trade` (FunctionDef) at line 883
- Candidate symbol `get_active_player_trade` (FunctionDef) at line 887
- Candidate symbol `get_player_trade_events` (FunctionDef) at line 891
- Candidate symbol `get_player_trade_history` (FunctionDef) at line 895
- Candidate symbol `cancel_player_trade` (FunctionDef) at line 899
- Candidate symbol `expire_stale_player_trades` (FunctionDef) at line 903
- Candidate symbol `init_player_trade_item_policy_and_reservations` (FunctionDef) at line 907
- Candidate symbol `get_item_trade_policy` (FunctionDef) at line 911
- Candidate symbol `build_trade_item_snapshot` (FunctionDef) at line 915
- Candidate symbol `reserve_inventory_for_trade` (FunctionDef) at line 927
- Candidate symbol `release_trade_inventory_reservations` (FunctionDef) at line 933
- Candidate symbol `get_player_trade_offers` (FunctionDef) at line 945

### `systems/event_statistics_system.py`
- Evidence score: 18
- Groups: ordering_tiebreak, pagination, persistence, presentation, ratings, scope_identity
- Candidate symbol `get_event_kill_leaderboard` (FunctionDef) at line 25

### `systems/name_rune_system.py`
- Evidence score: 18
- Groups: ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity

### `systems/pvp_production_calibration.py`
- Evidence score: 18
- Groups: ordering_tiebreak, rating_categories, scope_identity

### `handlers/combat.py`
- Evidence score: 17
- Groups: chronicles, ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity

### `handlers/pvp_round_ui.py`
- Evidence score: 17
- Groups: history, presentation, rating_categories, scope_identity
- Candidate symbol `pvp_active_reply_kb` (FunctionDef) at line 28
- Candidate symbol `_pvp_terminal` (FunctionDef) at line 53
- Candidate symbol `_localized_pvp_action_error` (FunctionDef) at line 61
- Candidate symbol `send_pvp_round_panel` (FunctionDef) at line 82
- Candidate symbol `broadcast_pvp_round_log` (FunctionDef) at line 99
- Candidate symbol `broadcast_pvp_state` (FunctionDef) at line 113
- Candidate symbol `activate_pvp_battle_ui` (FunctionDef) at line 123
- Candidate symbol `register_pvp_round_ui_handlers` (FunctionDef) at line 131
- Candidate symbol `pvp_status_message` (FunctionDef) at line 137
- Candidate symbol `pvp_round_callback` (FunctionDef) at line 145
- Candidate symbol `pvp_surrender_callback` (FunctionDef) at line 182

### `systems/premium_item_policy_system.py`
- Evidence score: 17
- Groups: ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity

### `systems/pvp_balance_simulator.py`
- Evidence score: 17
- Groups: ordering_tiebreak, presentation, rating_categories, scope_identity

### `systems/pvp_battle_factory.py`
- Evidence score: 17
- Groups: history, presentation, rating_categories, scope_identity
- Candidate symbol `build_production_pvp_snapshot` (FunctionDef) at line 41
- Candidate symbol `prepare_pvp_duel_snapshots` (FunctionDef) at line 82
- Candidate symbol `create_pvp_battle_from_accepted_duel` (FunctionDef) at line 95

### `systems/pvp_completion_service.py`
- Evidence score: 17
- Groups: history, pagination, presentation, rating_categories, scope_identity
- Candidate symbol `release_pvp_activity_sessions` (FunctionDef) at line 37
- Candidate symbol `complete_pvp_battle_once` (FunctionDef) at line 48
- Candidate symbol `surrender_pvp_battle` (FunctionDef) at line 61
- Candidate symbol `render_pvp_terminal_text` (FunctionDef) at line 79
- Candidate symbol `cleanup_all_terminal_pvp_sessions` (FunctionDef) at line 98

### `systems/pvp_policy_metrics_audit.py`
- Evidence score: 17
- Groups: ordering_tiebreak, presentation, rating_categories, scope_identity

### `systems/pvp_production_fixture_audit.py`
- Evidence score: 17
- Groups: ordering_tiebreak, presentation, rating_categories

### `systems/pvp_real_actor_root_cause_audit.py`
- Evidence score: 17
- Groups: ordering_tiebreak, pagination, presentation, rating_categories, scope_identity

### `systems/pvp_request_service.py`
- Evidence score: 17
- Groups: history, persistence, presentation, rating_categories, scope_identity
- Candidate symbol `create_pvp_duel_request` (FunctionDef) at line 14
- Candidate symbol `respond_to_pvp_duel_request` (FunctionDef) at line 22
- Candidate symbol `cancel_failed_accepted_pvp_duel_request` (FunctionDef) at line 34

### `systems/pvp_round_engine.py`
- Evidence score: 17
- Groups: pagination, presentation, rating_categories, scope_identity
- Candidate symbol `PvpRoundError` (ClassDef) at line 24
- Candidate symbol `resolve_pvp_round` (FunctionDef) at line 224

### `systems/refine_system.py`
- Evidence score: 17
- Groups: chronicles, ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity

### `main.py`
- Evidence score: 16
- Groups: chronicles, history, ordering_tiebreak, pagination, persistence, rating_categories, ratings, scope_identity

### `migrations/051_event_shop_exchange.py`
- Evidence score: 16
- Groups: ordering_tiebreak, persistence, scope_identity

### `systems/crystal_bag_expansion_system.py`
- Evidence score: 16
- Groups: ordering_tiebreak, persistence, presentation, rating_categories, scope_identity

### `systems/pvp_knight_judgement_terminal_audit.py`
- Evidence score: 16
- Groups: ordering_tiebreak, persistence, presentation, rating_categories, scope_identity

### `systems/pvp_real_actor_state_replay.py`
- Evidence score: 16
- Groups: ordering_tiebreak, rating_categories, scope_identity

### `systems/pvp_round_ui.py`
- Evidence score: 16
- Groups: presentation, rating_categories, scope_identity
- Candidate symbol `render_pvp_round_text` (FunctionDef) at line 39
- Candidate symbol `build_pvp_action_keyboard` (FunctionDef) at line 54

### `tests_v2/test_pvp.py`
- Evidence score: 16
- Groups: history, rating_categories
- Candidate symbol `PvpTest` (ClassDef) at line 7
- Candidate symbol `test_timeout_exact_once_history` (FunctionDef) at line 16

### `db_modules/story_quests.py`
- Evidence score: 15
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity

### `handlers/pvp_interaction.py`
- Evidence score: 15
- Groups: history, presentation, rating_categories, scope_identity
- Candidate symbol `register_pvp_interaction_handlers` (FunctionDef) at line 50
- Candidate symbol `pvp_duel_request` (FunctionDef) at line 56
- Candidate symbol `pvp_duel_response` (FunctionDef) at line 90

### `systems/crystal_shop_system.py`
- Evidence score: 15
- Groups: ordering_tiebreak, pagination, persistence, presentation, scope_identity

### `systems/fatigue_artifact_system.py`
- Evidence score: 15
- Groups: ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity

### `systems/pvp_models.py`
- Evidence score: 15
- Groups: presentation, rating_categories, scope_identity
- Candidate symbol `PvpActionIntent` (ClassDef) at line 8
- Candidate symbol `PvpActorState` (ClassDef) at line 16
- Candidate symbol `PvpActionOutcome` (ClassDef) at line 72
- Candidate symbol `PvpRoundResult` (ClassDef) at line 90

### `systems/pvp_real_equipment_fixture_audit.py`
- Evidence score: 15
- Groups: ordering_tiebreak, presentation, rating_categories

### `systems/pvp_timer_service.py`
- Evidence score: 15
- Groups: history, presentation, rating_categories, scope_identity
- Candidate symbol `start_pvp_timer_worker` (FunctionDef) at line 44

### `systems/travel_system.py`
- Evidence score: 15
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity

### `tests_v2/test_guild_contract_history.py`
- Evidence score: 15
- Groups: history, pagination, rating_categories
- Candidate symbol `ContractHistoryTest` (ClassDef) at line 6
- Candidate symbol `test_history_permissions_and_paging` (FunctionDef) at line 15

### `handlers/admin_crystal_credit.py`
- Evidence score: 14
- Groups: history, ordering_tiebreak, pagination, presentation, scope_identity
- Candidate symbol `_format_history_time` (FunctionDef) at line 14
- Candidate symbol `_history_text` (FunctionDef) at line 37
- Candidate symbol `_history_kb` (FunctionDef) at line 47
- Candidate symbol `history` (FunctionDef) at line 65

### `handlers/dev.py`
- Evidence score: 14
- Groups: history, ordering_tiebreak, pagination, presentation, rating_categories, scope_identity
- Candidate symbol `_register_pvp_production_calibration_handlers_14_6_2` (FunctionDef) at line 985
- Candidate symbol `_register_pvp_fixture_audit_handlers_14_6_2a` (FunctionDef) at line 1027
- Candidate symbol `dev_pvp` (FunctionDef) at line 828
- Candidate symbol `dev_pvp_all` (FunctionDef) at line 841
- Candidate symbol `dev_pvp_audit` (FunctionDef) at line 855
- Candidate symbol `dev_pvp_prod_14_6_2` (FunctionDef) at line 987
- Candidate symbol `dev_pvp_prod_all_14_6_2` (FunctionDef) at line 996
- Candidate symbol `dev_pvp_calibrate_14_6_2` (FunctionDef) at line 1005
- Candidate symbol `dev_pvp_fixture_audit_14_6_2a` (FunctionDef) at line 1029
- Candidate symbol `crystal_history_17_25_1` (FunctionDef) at line 1113

### `systems/pvp_combat_log.py`
- Evidence score: 14
- Groups: presentation, rating_categories, scope_identity
- Candidate symbol `render_pvp_round_combat_log` (FunctionDef) at line 86

### `db_modules/__init__.py`
- Evidence score: 13
- Groups: history, persistence, presentation, rating_categories, ratings, scope_identity

### `handlers/inventory.py`
- Evidence score: 13
- Groups: ordering_tiebreak, pagination, persistence, presentation, rating_categories, scope_identity

### `handlers/runes.py`
- Evidence score: 13
- Groups: pagination, persistence, presentation, rating_categories, scope_identity

### `migrations/044_attribute_respec_foundation.py`
- Evidence score: 13
- Groups: ordering_tiebreak, persistence, rating_categories, scope_identity

### `systems/contract_system.py`
- Evidence score: 13
- Groups: ordering_tiebreak, pagination, persistence, rating_categories, scope_identity

### `systems/pve_auto_escape_system.py`
- Evidence score: 13
- Groups: history, ordering_tiebreak, pagination, persistence, presentation, scope_identity

### `systems/pvp_config.py`
- Evidence score: 13
- Groups: pagination, rating_categories

### `systems/pvp_root_cause_metric_semantics.py`
- Evidence score: 13
- Groups: pagination, rating_categories

### `systems/pvp_skill_adapter.py`
- Evidence score: 13
- Groups: presentation, rating_categories
- Candidate symbol `PvpSkillCatalogError` (ClassDef) at line 10
- Candidate symbol `load_production_pvp_skill_catalog` (FunctionDef) at line 14
- Candidate symbol `get_production_pvp_skill` (FunctionDef) at line 37

### `systems/timed_exp_bonus_system.py`
- Evidence score: 13
- Groups: ordering_tiebreak, persistence, presentation, rating_categories, scope_identity

### `systems/player_system.py`
- Evidence score: 12
- Groups: chronicles, persistence, presentation, rating_categories, retention, scope_identity

### `systems/pvp_action_validation.py`
- Evidence score: 12
- Groups: rating_categories
- Candidate symbol `get_pvp_effective_skill_cost` (FunctionDef) at line 17
- Candidate symbol `validate_pvp_action_choice` (FunctionDef) at line 31
- Candidate symbol `pvp_skill_button_state` (FunctionDef) at line 97

## Mandatory semantic-refinement questions

1. Which files are authoritative owners versus presentation adapters, tests, fixtures, legacy or superseded paths?
2. What rating categories, formulas, top limit, page size and deterministic tie-breaks are actually canonical?
3. How is the current player's own position calculated and shown outside the visible top page?
4. Which completed trade and result-bearing PvP records are eligible for history, and what is their scope?
5. Which event types enter Chronicles, and are Chronicles account-level, character-level or mixed?
6. Is retention count-based, age-based, or both, and where is pruning enforced?
7. What is the stable ordering key when timestamps are equal?
8. Which navigation labels and empty states belong only to presentation rather than the domain contract?

## Restrictions

- This audit does not authorize mutation.
- Candidate numeric values are evidence only until Stage 21.14.4a reconciles their semantics.
- No new rating, history item, chronicle event, retention policy or compatibility rule may be invented.
- Runtime, Telegram dispatch and production persistence remain disconnected.
