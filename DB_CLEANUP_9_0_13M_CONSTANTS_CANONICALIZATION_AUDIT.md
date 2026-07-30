# ROM 9.0.13m — Constants Canonicalization Audit

Generated: `2026-07-30T07:02:02`

## Safety

- Gameplay files changed: **0**
- Real database rows changed: **0**
- Real database SHA/size/mtime unchanged: **True**
- Runtime values were inspected through a sandbox copy of `game.db`.

## Summary

- Overlapping constants: **26**
- Exact single-owner candidates: **23**
- Constants with duplicate local definitions: **3**
- Divergent/runtime-risk constants: **0**
- Candidate groups by canonical module: `{'data.equipment_profiles': ['ARMOR_ALLOWED_BY_CLASS', 'ARMOR_EXTRA_STATS_BY_SLOT', 'ARMOR_TYPE_LABELS', 'EQUIPMENT_SLOTS', 'ITEM_SUBTYPE_LABELS', 'MAIN_HAND_ALLOWED_BY_CLASS', 'OFF_HAND_ALLOWED_BY_CLASS', 'OFF_HAND_PROFILES'], 'data.classes': ['CLASS_CONFIGS', 'CLASS_RESET_SPHERE_ITEM_ID'], 'data.balance': ['CONTRACTS_UNLOCK_LEVEL', 'DAILY_CONTRACT_LIMIT', 'DAILY_QUEST_ID_KILL_MONSTERS', 'DAILY_QUEST_REWARD_ITEM_ID', 'DAILY_QUEST_REWARD_QUANTITY', 'DAILY_QUEST_TARGET_KILLS', 'ENERGY_MAX', 'ENERGY_REGEN_MINUTES', 'HP_REGEN_MINUTES', 'HP_REGEN_PERCENT', 'RARITY_REPAIR_MULTIPLIERS', 'REFINE_MATERIAL_MAX_STACK', 'REFINE_STONE_ITEM_ID']}`

## Per-constant analysis

### `ARMOR_ALLOWED_BY_CLASS`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.equipment_profiles`
- Exact owners: `['data.equipment_profiles']`
- Divergent owners: `[]`
- Local definition lines: `[4039]`
- Canonical definition lines: `{'data.equipment_profiles': 93}`
- First read in `db.py`: `4152`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 4152, 'function': 'get_allowed_armor_type_for_class'}, {'file': 'handlers/inventory.py', 'line': 156, 'function': 'build_item_allowed_classes_text'}]`

### `ARMOR_EXTRA_STATS_BY_SLOT`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.equipment_profiles`
- Exact owners: `['data.equipment_profiles']`
- Divergent owners: `[]`
- Local definition lines: `[2453]`
- Canonical definition lines: `{'data.equipment_profiles': 82}`
- First read in `db.py`: `2600`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 2600, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2606, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2613, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2620, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2627, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2634, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2644, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2651, 'function': 'generate_dynamic_equipment_stats'}]`

### `ARMOR_TYPE_LABELS`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.equipment_profiles`
- Exact owners: `['data.equipment_profiles']`
- Divergent owners: `[]`
- Local definition lines: `[4075]`
- Canonical definition lines: `{'data.equipment_profiles': 142}`
- First read in `db.py`: `4135`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 4135, 'function': 'get_armor_type_label'}]`

### `CLASS_CONFIGS`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.classes`
- Exact owners: `['data.classes']`
- Divergent owners: `[]`
- Local definition lines: `[3558]`
- Canonical definition lines: `{'data.classes': 9}`
- First read in `db.py`: `3994`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 4145, 'function': 'get_class_display_name_by_key'}, {'file': 'db.py', 'line': 3994, 'function': 'restore_user_mp_to_full'}, {'file': 'handlers/inventory.py', 'line': 186, 'function': 'build_item_allowed_classes_text'}, {'file': 'handlers/start.py', 'line': 45, 'function': 'build_class_selection_kb'}, {'file': 'handlers/start.py', 'line': 93, 'function': 'build_class_selection_text'}, {'file': 'systems/character_system.py', 'line': 166, 'function': 'set_character_class'}, {'file': 'systems/character_system.py', 'line': 99, 'function': 'get_character_class_display'}, {'file': 'systems/character_system.py', 'line': 104, 'function': 'get_character_resource_type'}, {'file': 'systems/character_system.py', 'line': 174, 'function': 'set_character_class'}, {'file': 'tools/smoke_test_character_mutation_contracts.py', 'line': 91, 'function': 'main'}, {'file': 'tools/smoke_test_character_mutation_contracts.py', 'line': 83, 'function': 'main'}, {'file': 'tools/smoke_test_character_mutation_contracts.py', 'line': 84, 'function': 'main'}]`

### `CLASS_RESET_SPHERE_ITEM_ID`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.classes`
- Exact owners: `['data.classes']`
- Divergent owners: `[]`
- Local definition lines: `[3616]`
- Canonical definition lines: `{'data.classes': 66}`
- First read in `db.py`: `3684`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 3815, 'function': 'is_class_reset_sphere_inventory_item'}, {'file': 'db.py', 'line': 3854, 'function': 'use_class_reset_sphere_from_inventory'}, {'file': 'db.py', 'line': 3684, 'function': 'seed_class_reset_sphere_item'}, {'file': 'handlers/dev.py', 'line': 649, 'function': 'give_class_reset_sphere'}, {'file': 'handlers/inventory.py', 'line': 653, 'function': 'build_item_details'}, {'file': 'systems/character_system.py', 'line': 225, 'function': 'get_class_reset_sphere_item_id'}]`

### `CONTRACTS_UNLOCK_LEVEL`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1260]`
- Canonical definition lines: `{'data.balance': 16}`
- First read in `db.py`: `1474`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 1499, 'function': 'create_daily_contract'}, {'file': 'db.py', 'line': 1474, 'function': 'get_contract_status'}, {'file': 'db.py', 'line': 1503, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 254, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 230, 'function': 'get_contract_status'}, {'file': 'systems/contract_system.py', 'line': 258, 'function': 'create_daily_contract'}]`

### `CONTRACT_MOBS_EQUIVALENT`

- Classification: **duplicate_local_definitions**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[871, 1263]`
- Canonical definition lines: `{'data.balance': 17}`
- First read in `db.py`: `887`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 887, 'function': 'get_contract_exp_for_level'}, {'file': 'systems/contract_system.py', 'line': 25, 'function': 'get_contract_mobs_equivalent'}]`

### `CONTRACT_TARGET_KILLS`

- Classification: **duplicate_local_definitions**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1262, 7027]`
- Canonical definition lines: `{'data.balance': 18}`
- First read in `db.py`: `1485`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 1485, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 240, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 22, 'function': 'get_contract_target_kills'}, {'file': 'tools/smoke_test_contract_contracts.py', 'line': 15, 'function': None, 'attribute': True}]`

### `DAILY_CONTRACT_LIMIT`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1261]`
- Canonical definition lines: `{'data.balance': 19}`
- First read in `db.py`: `1476`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 1476, 'function': 'get_contract_status'}, {'file': 'db.py', 'line': 1508, 'function': 'create_daily_contract'}, {'file': 'db.py', 'line': 1513, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 232, 'function': 'get_contract_status'}, {'file': 'systems/contract_system.py', 'line': 263, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 268, 'function': 'create_daily_contract'}]`

### `DAILY_QUEST_ID_KILL_MONSTERS`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1923]`
- Canonical definition lines: `{'data.balance': 20}`
- First read in `db.py`: `1987`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 1987, 'function': 'reset_daily_quest_if_needed'}, {'file': 'db.py', 'line': 2012, 'function': 'reset_daily_quest_if_needed'}]`

### `DAILY_QUEST_REWARD_ITEM_ID`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1925]`
- Canonical definition lines: `{'data.balance': 21}`
- First read in `db.py`: `2060`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 2060, 'function': 'get_daily_quest_status'}, {'file': 'db.py', 'line': 2165, 'function': 'claim_daily_quest_reward'}]`

### `DAILY_QUEST_REWARD_QUANTITY`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1926]`
- Canonical definition lines: `{'data.balance': 22}`
- First read in `db.py`: `2061`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 2061, 'function': 'get_daily_quest_status'}, {'file': 'db.py', 'line': 2166, 'function': 'claim_daily_quest_reward'}]`

### `DAILY_QUEST_TARGET_KILLS`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1924]`
- Canonical definition lines: `{'data.balance': 23}`
- First read in `db.py`: `1989`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 2057, 'function': 'get_daily_quest_status'}, {'file': 'db.py', 'line': 1989, 'function': 'reset_daily_quest_if_needed'}, {'file': 'db.py', 'line': 2013, 'function': 'reset_daily_quest_if_needed'}]`

### `ENERGY_MAX`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1704]`
- Canonical definition lines: `{'data.balance': 24}`
- First read in `db.py`: `5869`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 5869, 'function': 'create_user'}, {'file': 'systems/energy_system.py', 'line': 34, 'function': 'consume_energy_for_hunt'}, {'file': 'systems/energy_system.py', 'line': 69, 'function': 'consume_energy_for_hunt'}, {'file': 'systems/energy_system.py', 'line': 99, 'function': 'restore_energy_for_test'}, {'file': 'systems/energy_system.py', 'line': 296, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 37, 'function': 'consume_energy_for_hunt'}, {'file': 'systems/energy_system.py', 'line': 38, 'function': 'consume_energy_for_hunt'}, {'file': 'systems/energy_system.py', 'line': 83, 'function': 'restore_energy_for_test'}, {'file': 'systems/energy_system.py', 'line': 235, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 243, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 256, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 100, 'function': 'restore_energy_for_test'}, {'file': 'systems/notifications.py', 'line': 134, 'function': 'apply_energy_regen'}, {'file': 'systems/notifications.py', 'line': 89, 'function': 'apply_energy_regen'}]`

### `ENERGY_REGEN_MINUTES`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1705]`
- Canonical definition lines: `{'data.balance': 25}`
- First read in `db.py`: `None`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'systems/energy_system.py', 'line': 266, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 236, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 257, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 272, 'function': 'get_user_energy'}, {'file': 'systems/notifications.py', 'line': 109, 'function': 'apply_energy_regen'}, {'file': 'systems/notifications.py', 'line': 114, 'function': 'apply_energy_regen'}]`

### `EQUIPMENT_SLOTS`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.equipment_profiles`
- Exact owners: `['data.equipment_profiles']`
- Divergent owners: `[]`
- Local definition lines: `[16]`
- Canonical definition lines: `{'data.equipment_profiles': 150}`
- First read in `db.py`: `1233`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 1233, 'function': 'get_common_equipment_shop_offer'}, {'file': 'db.py', 'line': 5235, 'function': 'create_dev_armor_item_for_test'}, {'file': 'db.py', 'line': 5429, 'function': 'create_dev_weapon_item_for_test'}, {'file': 'handlers/city.py', 'line': 658, 'function': 'build_common_shop_preview_text'}, {'file': 'handlers/inventory.py', 'line': 70, 'function': 'get_slot_label'}, {'file': 'handlers/profile.py', 'line': 279, 'function': 'build_equipment_text'}]`

### `HP_REGEN_MINUTES`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1715]`
- Canonical definition lines: `{'data.balance': 26}`
- First read in `db.py`: `None`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'systems/notifications.py', 'line': 338, 'function': 'apply_hp_regen'}, {'file': 'systems/notifications.py', 'line': 780, 'function': 'apply_hp_regen'}, {'file': 'systems/notifications.py', 'line': 352, 'function': 'apply_hp_regen'}, {'file': 'systems/notifications.py', 'line': 804, 'function': 'apply_hp_regen'}, {'file': 'systems/regen_system.py', 'line': 292, 'function': 'process_passive_regeneration'}, {'file': 'systems/regen_system.py', 'line': 198, 'function': 'apply_passive_hp_regen'}, {'file': 'systems/regen_system.py', 'line': 209, 'function': 'apply_passive_hp_regen'}, {'file': 'systems/regen_system.py', 'line': 300, 'function': 'process_passive_regeneration'}]`

### `HP_REGEN_PERCENT`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[1714]`
- Canonical definition lines: `{'data.balance': 27}`
- First read in `db.py`: `None`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'systems/notifications.py', 'line': 346, 'function': 'apply_hp_regen'}, {'file': 'systems/notifications.py', 'line': 799, 'function': 'apply_hp_regen'}, {'file': 'systems/regen_system.py', 'line': 207, 'function': 'apply_passive_hp_regen'}, {'file': 'systems/regen_system.py', 'line': 297, 'function': 'process_passive_regeneration'}]`

### `ITEM_SUBTYPE_LABELS`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.equipment_profiles`
- Exact owners: `['data.equipment_profiles']`
- Divergent owners: `[]`
- Local definition lines: `[4084]`
- Canonical definition lines: `{'data.equipment_profiles': 126}`
- First read in `db.py`: `4140`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 4140, 'function': 'get_item_subtype_label'}]`

### `MAIN_HAND_ALLOWED_BY_CLASS`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.equipment_profiles`
- Exact owners: `['data.equipment_profiles']`
- Divergent owners: `[]`
- Local definition lines: `[4051]`
- Canonical definition lines: `{'data.equipment_profiles': 104}`
- First read in `db.py`: `4156`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 4156, 'function': 'get_allowed_main_hand_subtypes_for_class'}, {'file': 'handlers/inventory.py', 'line': 164, 'function': 'build_item_allowed_classes_text'}]`

### `MAIN_HAND_PROFILES`

- Classification: **duplicate_local_definitions**
- Canonical owner: `data.equipment_profiles`
- Exact owners: `['data.equipment_profiles']`
- Divergent owners: `[]`
- Local definition lines: `[2385, 2907]`
- Canonical definition lines: `{'data.equipment_profiles': 9}`
- First read in `db.py`: `2497`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 2688, 'function': 'is_weapon_profile_magical'}, {'file': 'db.py', 'line': 5265, 'function': 'create_dev_weapon_item_for_test'}, {'file': 'db.py', 'line': 2506, 'function': 'get_profile_for_generated_item'}, {'file': 'db.py', 'line': 2730, 'function': 'create_generated_equipment_item_for_slot'}, {'file': 'db.py', 'line': 3199, 'function': 'create_common_equipment_shop_preview'}, {'file': 'db.py', 'line': 3230, 'function': 'create_common_equipment_shop_preview'}, {'file': 'db.py', 'line': 5267, 'function': 'create_dev_weapon_item_for_test'}, {'file': 'db.py', 'line': 5607, 'function': 'create_generated_equipment_item'}, {'file': 'db.py', 'line': 5610, 'function': 'create_generated_equipment_item'}, {'file': 'db.py', 'line': 2525, 'function': 'get_dynamic_weapon_name'}, {'file': 'db.py', 'line': 2525, 'function': 'get_dynamic_weapon_name'}, {'file': 'db.py', 'line': 2553, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2553, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 4904, 'function': 'get_allowed_shop_main_hand_profiles'}, {'file': 'db.py', 'line': 2497, 'function': 'get_random_main_hand_profile'}, {'file': 'db.py', 'line': 2689, 'function': 'is_weapon_profile_magical'}, {'file': 'db.py', 'line': 2875, 'function': 'get_common_equipment_shop_suboffers'}, {'file': 'db.py', 'line': 2876, 'function': 'get_common_equipment_shop_suboffers'}, {'file': 'db.py', 'line': 2877, 'function': 'get_common_equipment_shop_suboffers'}]`

### `OFF_HAND_ALLOWED_BY_CLASS`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.equipment_profiles`
- Exact owners: `['data.equipment_profiles']`
- Divergent owners: `[]`
- Local definition lines: `[4063]`
- Canonical definition lines: `{'data.equipment_profiles': 115}`
- First read in `db.py`: `4160`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 4160, 'function': 'get_allowed_off_hand_subtypes_for_class'}, {'file': 'handlers/inventory.py', 'line': 172, 'function': 'build_item_allowed_classes_text'}]`

### `OFF_HAND_PROFILES`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.equipment_profiles`
- Exact owners: `['data.equipment_profiles']`
- Divergent owners: `[]`
- Local definition lines: `[2431]`
- Canonical definition lines: `{'data.equipment_profiles': 61}`
- First read in `db.py`: `2501`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 2512, 'function': 'get_profile_for_generated_item'}, {'file': 'db.py', 'line': 3205, 'function': 'create_common_equipment_shop_preview'}, {'file': 'db.py', 'line': 5272, 'function': 'create_dev_weapon_item_for_test'}, {'file': 'db.py', 'line': 2530, 'function': 'get_dynamic_weapon_name'}, {'file': 'db.py', 'line': 2530, 'function': 'get_dynamic_weapon_name'}, {'file': 'db.py', 'line': 2737, 'function': 'create_generated_equipment_item_for_slot'}, {'file': 'db.py', 'line': 3237, 'function': 'create_common_equipment_shop_preview'}, {'file': 'db.py', 'line': 4915, 'function': 'get_allowed_shop_off_hand_profiles'}, {'file': 'db.py', 'line': 5274, 'function': 'create_dev_weapon_item_for_test'}, {'file': 'db.py', 'line': 5629, 'function': 'create_generated_equipment_item'}, {'file': 'db.py', 'line': 5632, 'function': 'create_generated_equipment_item'}, {'file': 'db.py', 'line': 2501, 'function': 'get_random_off_hand_profile'}, {'file': 'db.py', 'line': 2572, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2572, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2891, 'function': 'get_common_equipment_shop_suboffers'}, {'file': 'db.py', 'line': 2893, 'function': 'get_common_equipment_shop_suboffers'}]`

### `RARITY_REPAIR_MULTIPLIERS`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[44]`
- Canonical definition lines: `{'data.balance': 28}`
- First read in `db.py`: `985`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 985, 'function': 'get_rarity_repair_multiplier'}]`

### `REFINE_MATERIAL_MAX_STACK`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[6545]`
- Canonical definition lines: `{'data.balance': 29}`
- First read in `db.py`: `6564`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 6564, 'function': 'ensure_refine_material_stack_sizes'}]`

### `REFINE_STONE_ITEM_ID`

- Classification: **exact_single_owner_candidate**
- Canonical owner: `data.balance`
- Exact owners: `['data.balance']`
- Divergent owners: `[]`
- Local definition lines: `[5965]`
- Canonical definition lines: `{'data.balance': 30}`
- First read in `db.py`: `6014`
- Existing canonical imports in `db.py`: `[]`
- Runtime value matches canonical owner: **True**
- Project reads: `[{'file': 'db.py', 'line': 6014, 'function': 'seed_refine_items'}, {'file': 'db.py', 'line': 6102, 'function': 'get_refine_resource_counts'}, {'file': 'systems/refine_system.py', 'line': 127, 'function': 'perform_refine_attempt'}, {'file': 'systems/refine_system.py', 'line': 123, 'function': 'perform_refine_attempt'}, {'file': 'systems/reward_system.py', 'line': 469, 'function': 'roll_refine_stone_drop'}]`

## Proposed physical migration plan

1. Add explicit canonical imports near the beginning of `db.py`, before the first consumer of each constant.
2. Remove only exact local definitions after asserting equality with the canonical export.
3. Handle constants with multiple local definitions separately because the earlier value may differ from the final effective value.
4. Preserve the public `db.<CONSTANT>` surface by importing canonical names directly into the `db` module namespace.
5. Verify runtime identity/value parity for `db`, `data.classes`, `data.equipment_profiles`, and `data.balance`.
6. Run class selection, equipment generation/compatibility, contract, energy/regen, repair, refine, and daily-quest contracts.
7. Compare real-user and database fingerprints before and after all tests.

## Recommended split

- Phase A, exact `data.classes` constants: `['CLASS_CONFIGS', 'CLASS_RESET_SPHERE_ITEM_ID']`
- Phase B, exact `data.equipment_profiles` constants: `['ARMOR_ALLOWED_BY_CLASS', 'ARMOR_EXTRA_STATS_BY_SLOT', 'ARMOR_TYPE_LABELS', 'EQUIPMENT_SLOTS', 'ITEM_SUBTYPE_LABELS', 'MAIN_HAND_ALLOWED_BY_CLASS', 'OFF_HAND_ALLOWED_BY_CLASS', 'OFF_HAND_PROFILES']`
- Phase C, exact `data.balance` constants: `['CONTRACTS_UNLOCK_LEVEL', 'DAILY_CONTRACT_LIMIT', 'DAILY_QUEST_ID_KILL_MONSTERS', 'DAILY_QUEST_REWARD_ITEM_ID', 'DAILY_QUEST_REWARD_QUANTITY', 'DAILY_QUEST_TARGET_KILLS', 'ENERGY_MAX', 'ENERGY_REGEN_MINUTES', 'HP_REGEN_MINUTES', 'HP_REGEN_PERCENT', 'RARITY_REPAIR_MULTIPLIERS', 'REFINE_MATERIAL_MAX_STACK', 'REFINE_STONE_ITEM_ID']`
- Manual review before deletion: `['CONTRACT_MOBS_EQUIVALENT', 'CONTRACT_TARGET_KILLS', 'MAIN_HAND_PROFILES']`

## Conclusion

The overlap is real, but canonicalization must preserve the `db` module's public constant surface and import order. No constant was removed by this audit.

Suggested next patch: `patch_9_0_13n_constants_canonicalization_cleanup.py`
