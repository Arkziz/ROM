# Stage 21.15.2 — Existing DEV data operations audit

- Status: **PASS**
- Conclusion: **PASS_REVIEW_REQUIRED**
- Next action: **GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW**
- Production mutation: **NO**
- DEV operations executed: **NO**
- Production SQLite / `.env`: **NOT OPENED**
- `main.py` started: **NO**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Evidence coverage

- `application_service`: 567
- `audit`: 416
- `authorization`: 151
- `dev_mode`: 76
- `direct_sql`: 2891
- `give`: 70
- `idempotency`: 179
- `notification`: 3959
- `repository`: 264
- `reset`: 233
- `set`: 430
- `target_identity`: 7014
- `transaction`: 1167
- `validation`: 2604

## Authoritative candidate owners

### `handlers/dev.py`
- Exists: True
- Direct SQL candidate: False
- DEV_MODE candidate: True
- Audit candidate: True
- Transaction candidate: True
- `FunctionDef parse_dev_rune_request` at line 64
- `FunctionDef parse_dev_quantity_request` at line 110
- `FunctionDef parse_dev_drop_sim_request` at line 149
- `FunctionDef register_dev_handlers` at line 184
- `FunctionDef register_dev_handlers` at line 1019
- `FunctionDef register_dev_handlers` at line 1049
- `FunctionDef register_dev_handlers` at line 1058
- `FunctionDef give_item` at line 191
- `FunctionDef set_level` at line 257
- `FunctionDef reset_level` at line 291
- `FunctionDef reset_hero` at line 309
- `FunctionDef set_energy` at line 408
- `FunctionDef set_gold` at line 454
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
- `FunctionDef set_exp_17_14_1_1` at line 1062
- `FunctionDef crystal_credit_17_25_1` at line 1089
- `FunctionDef crystal_debit_17_25_1` at line 1101
- `FunctionDef dev_premium_item_17_26_1` at line 1123

### `db_modules/dev_compat.py`
- Exists: True
- Direct SQL candidate: True
- DEV_MODE candidate: False
- Audit candidate: True
- Transaction candidate: True
- `FunctionDef set_player_level_for_test` at line 120
- `FunctionDef reset_player_level_for_test` at line 204
- `FunctionDef set_gold_for_test` at line 207
- `FunctionDef _get_dev_reset_hero_lock` at line 258
- `FunctionDef _dev_reset_table_exists` at line 265
- `FunctionDef _dev_reset_table_columns` at line 272
- `FunctionDef _dev_reset_delete_by_user_columns` at line 277
- `FunctionDef reset_hero_for_test` at line 289
- `FunctionDef seed_class_reset_sphere_item` at line 735
- `FunctionDef normalize_dev_rarity` at line 1166
- `FunctionDef create_dev_armor_item_for_test` at line 1194
- `FunctionDef create_dev_weapon_item_for_test` at line 1367
- `FunctionDef set_current_exp_for_test_17_14_1_1` at line 1589

### `systems/admin_crystal_credit_system.py`
- Exists: True
- Direct SQL candidate: True
- DEV_MODE candidate: False
- Audit candidate: True
- Transaction candidate: True
- `FunctionDef is_admin` at line 11
- `FunctionDef init_admin_crystal_credit_system` at line 12
- `FunctionDef preview_admin_adjustment` at line 17
- `FunctionDef execute_admin_adjustment` at line 35
- `FunctionDef get_admin_adjustment_history` at line 55
- `FunctionDef get_admin_adjustment_detail` at line 62

### `systems/premium_item_policy_system.py`
- Exists: True
- Direct SQL candidate: True
- DEV_MODE candidate: True
- Audit candidate: False
- Transaction candidate: True
- `FunctionDef _dev_enabled` at line 58
- `FunctionDef can_grant_item_from_source` at line 124
- `FunctionDef _grant_stack` at line 181
- `FunctionDef grant_item_from_source` at line 205
- `FunctionDef get_premium_item_grants` at line 265

### `handlers/guild.py`
- Exists: True
- Direct SQL candidate: True
- DEV_MODE candidate: False
- Audit candidate: False
- Transaction candidate: False
- `FunctionDef reset_guild_browse_state` at line 145
- `FunctionDef set_selected_guild` at line 153
- `FunctionDef reset_guild_create_state` at line 180
- `FunctionDef reset_guild_application_review_state` at line 876
- `FunctionDef reset_guild_member_manage_state` at line 1166
- `FunctionDef _guild_safe_reset_other_states_for_members_v2` at line 1477
- `FunctionDef _guild_progress_reset_navigation_states_v1` at line 2063
- `FunctionDef _guild_progress_handle_dev_command_v1` at line 2075
- `FunctionDef reset_guild_logs_state` at line 2267
- `FunctionDef _guild_contracts_reset_guild_states_v1` at line 2535
- `FunctionDef reset_all_guild_ui_states` at line 2657

### `handlers/fatigue_artifact.py`
- Exists: True
- Direct SQL candidate: False
- DEV_MODE candidate: True
- Audit candidate: False
- Transaction candidate: False
- `FunctionDef dev_grant` at line 20

### `handlers/auction_house.py`
- Exists: True
- Direct SQL candidate: False
- DEV_MODE candidate: False
- Audit candidate: True
- Transaction candidate: False
- `FunctionDef _auction_get_admin_ids_v1` at line 4977
- `FunctionDef _auction_is_admin_v1` at line 5000
- `FunctionDef _auction_admin_denied_text_v1` at line 5004
- `FunctionDef _auction_register_admin_command_guard_v1` at line 5025
- `FunctionDef auction_sanity_admin_guard_v1` at line 5028
- `FunctionDef auction_debug_admin_guard_v1` at line 5036
- `FunctionDef auction_fix_admin_guard_v1` at line 5044
- `FunctionDef auction_cleanup_admin_guard_v1` at line 5070

### `config.py`
- Exists: True
- Direct SQL candidate: False
- DEV_MODE candidate: False
- Audit candidate: False
- Transaction candidate: False
- `FunctionDef _admin_ids_env` at line 15

### `main.py`
- Exists: True
- Direct SQL candidate: False
- DEV_MODE candidate: False
- Audit candidate: True
- Transaction candidate: False

## Required semantic refinement

- What is the complete effective Give/Reset/Set operation inventory after Python shadowing and handler registration are resolved?
- Which handler, application service and repository own each operation?
- Which V1 paths perform direct SQL or bypass domain invariants?
- What target identity is canonical for each operation: account, user, character, item definition or inventory instance?
- What exact quantity, range, cap, floor and validation rules apply?
- Which reset fields are character-level and which are account-level and must survive reset?
- Where are transaction, rollback, audit and idempotency boundaries established?
- Which V2 application services and repositories already exist and can be reused without introducing a compatibility bypass?
- Which operations send notifications or append history/domain events after success?

## Explicit prohibitions

- Do not execute any DEV operation.
- Do not open production SQLite or .env.
- Do not invent operation names, identities, quantities, caps, reset scope, audit fields or idempotency policy.
- Do not authorize direct SQL or db_modules/dev_compat.py as the V2 application-service boundary solely because V1 uses it.
- Do not create a nested rom_v2/domain/dev_data_operations package; future implementation must preserve the flat domain layout.

This audit is evidence inventory only. It does not authorize implementation or direct database access.
