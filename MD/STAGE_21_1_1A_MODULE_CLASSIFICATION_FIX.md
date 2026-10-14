# ROM Stage 21.1.1a - виправлення false positives класифікації

- **Статус:** `GO`
- **Parent commit:** `4813dcf8542c42f765aeb0dd1fe9134f29683442`
- **Перекласифіковано модулів:** `101`
- **Semantic checks:** `7 PASS / 0 FAIL`

## Причина

Stage 21.1.1 використовував слово `contract` як надто широкий test marker та перевіряв `data/` раніше за package marker. Через це runtime contract modules і package initializers отримали неправильні категорії.

## Виправлені правила

- Test modules визначаються тільки явними test directories, prefixes та suffixes.
- Звичайні runtime-назви `contracts.py` і `contract_system.py` не є тестами.
- Усі `__init__.py` не переносяться; V2 формує package boundaries заново.
- Module set і SHA-256 metadata не змінюються; оновлюється тільки класифікаційний contract та derived queues.

## Classification delta

| Модуль | Було | Стало |
|---|---|---|
| `data/__init__.py` | `CONTENT_EXTRACT` | `DO_NOT_MIGRATE` |
| `data/story_quests/__init__.py` | `CONTENT_EXTRACT` | `DO_NOT_MIGRATE` |
| `db_modules/__init__.py` | `REWRITE` | `DO_NOT_MIGRATE` |
| `events/__init__.py` | `REWRITE` | `DO_NOT_MIGRATE` |
| `events/_template/__init__.py` | `REWRITE` | `DO_NOT_MIGRATE` |
| `events/test_event_2026/__init__.py` | `REWRITE` | `DO_NOT_MIGRATE` |
| `handlers/contracts.py` | `TEST_REFERENCE` | `REWRITE` |
| `systems/contract_system.py` | `TEST_REFERENCE` | `REWRITE` |
| `systems/simulation/__init__.py` | `REWRITE` | `DO_NOT_MIGRATE` |
| `systems/simulation/patch_regression.py` | `TEST_REFERENCE` | `REWRITE` |
| `tools/accept_stage_20_3_hybrid_mana_economy.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/acceptance_stage_20_5_7_premium_admin_crystals.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/acceptance_stage_20_6_6_travel_equipment.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_9_0_13_final_closure.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_boss_stage13_simulation_reuse_15_7_1.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_canonical_character_creation_and_player_stats_18_30_5a.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_canonical_player_stat_pipeline_18_30_5b.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_canonical_progression_mob_selection.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_canonical_refinement_lifecycle_18_30_5d.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_canonical_rune_lifecycle_18_30_5f.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_central_drop_economy.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_character_duplicates.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_combat_mana_potion.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_constants_canonicalization.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_db_startup_mutations.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_duplicate_defs.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_dynamic_equipment_compatibility_18_17_4.py` | `NEEDS_MANUAL_REVIEW` | `TEST_REFERENCE` |
| `tools/audit_elite_boss_reference_architecture_15_7_2_1.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_equipment_defense_refine_and_combat_chance_18_30_5b1.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_equipment_readonly_duplicates.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_equipment_stat_policy_18_17_0.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_equipment_write_repair_trader.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_guild_actor_name_log.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_guild_resources_and_drop_pipeline_18_30_14a.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_inline_map_and_travel_18_22_0.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_inline_map_and_travel_closure_18_22_4.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_legacy_class_shop_generator_18_17_5.py` | `NEEDS_MANUAL_REVIEW` | `TEST_REFERENCE` |
| `tools/audit_player_trade_precommit_architecture.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_pve_auto_escape_18_18_0.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_pve_effect_timing_18_19_0.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_pve_player_hit_18_21_0.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_pvp_architecture_skill_parity.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_rebirth_sphere_distribution_18_16_10e.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_refine_system_18_20_0.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_registration_date_pipeline_18_31_3.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_remaining_duplicates.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_residual_compatibility.py` | `NEEDS_MANUAL_REVIEW` | `TEST_REFERENCE` |
| `tools/audit_residual_legacy_refs.py` | `NEEDS_MANUAL_REVIEW` | `TEST_REFERENCE` |
| `tools/audit_rune_system_architecture.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_simulation_architecture_and_purity.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_static_items_and_db_init.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/audit_warrior_scout_skill_usage.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/close_equipment_stat_policy_stage_18_17.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/close_pve_auto_escape_stage_18_18.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/close_pve_effect_timeline_stage_18_19.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/close_pve_normal_attack_hit_stage_18_21.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/close_refine_system_stage_18_20.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/db_cleanup_readiness.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/final_db_cleanup_closure_audit.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/finalize_stage_20_7_3.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/manual_test_inactivity_reminder_18_6_1.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/migration_status.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/reset_story_quest_item_for_retest.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_all_class_10_day_diagnostic_matrix.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_all_class_progression_matrix.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_boss_balance_simulation_15_7_0.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_boss_encounter_distribution_audit.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_boss_production_parity_simulation_15_7_1.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_class_progression_simulation.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_economic_progression_v2.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_economy_analysis.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_economy_guild_acceptance_13_8_2.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_final_stage_18_closure_audit.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_full_production_progression_acceptance.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_guild_population_sim.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_pve_balance_analysis.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_pvp_adaptive_balance_optimizer.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_pvp_anti_stall_survivability_candidate_sandbox.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_pvp_knight_judgement_terminal_audit.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_pvp_policy_balance_candidate_sandbox.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_pvp_primary_stat_scaling_combat_pacing_sandbox.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_pvp_real_actor_root_cause_audit.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_pvp_real_equipment_fixture_audit.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_pvp_targeted_mechanics_candidate_sandbox.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_simulation_canonical_parity_report.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_single_class_progression.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_stage_20_4_3b_potion_affordability_audit.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_stage_20_4_5_level_3_guild_affordability.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/run_world_progression_sim.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/story_quest_candidate_importer.py` | `NEEDS_MANUAL_REVIEW` | `TEST_REFERENCE` |
| `tools/trace_canonical_player_stats_result.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/trace_live_player_stats_shape.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/trace_quest_11_runtime_resolver.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/validate_boss_balance_report_15_7_0.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/validate_boss_root_cause_report_15_7_1.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/validate_boss_system_final_closure_15_7_10_1.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/validate_final_simulator_acceptance.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/validate_integrated_player_resource_lifecycle.py` | `REWRITE` | `TEST_REFERENCE` |
| `tools/validate_preserved_boss_candidate_report_15_7_2_1.py` | `NEEDS_MANUAL_REVIEW` | `TEST_REFERENCE` |
| `tools/validate_preserved_short_comparison_15_7_3_2.py` | `REWRITE` | `TEST_REFERENCE` |

> Показано перші 100 із 101 змін; повний delta міститься у JSON.

## Наступний етап

Stage 21.1.2 - AST-аудит повторних визначень, alias chains і runtime overrides.
