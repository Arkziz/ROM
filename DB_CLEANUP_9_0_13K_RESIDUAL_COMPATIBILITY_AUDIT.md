# ROM 9.0.13k — Residual Compatibility Audit

Generated: `2026-07-30T06:49:54`

## Safety

- Gameplay files changed: **0**
- Real database rows changed: **0**
- Real database SHA/size/mtime unchanged: **True**
- Runtime globals inspected through a sandbox copy of `game.db`.

## Legacy and base captures

- Static source findings: **23**
- Runtime `_legacy_*` / `_base_*` globals: **8**
- Unique capture names classified: **9**
- Classification counts: `{'capture_only_or_unreferenced': 9}`
- Sandbox import stdout: ``
- Sandbox import stderr: ``

### `_base_get_inventory_detailed_before_refine_display_v1`

- Runtime present: **True**
- Classification: **capture_only_or_unreferenced**
- Reads in `db.py`: `[]`
- Reads outside `db.py`: `[]`

### `_base_get_inventory_entry_before_refine_display_v1`

- Runtime present: **True**
- Classification: **capture_only_or_unreferenced**
- Reads in `db.py`: `[]`
- Reads outside `db.py`: `[]`

### `_base_get_item_by_inventory_id_before_refine_display_v1`

- Runtime present: **True**
- Classification: **capture_only_or_unreferenced**
- Reads in `db.py`: `[]`
- Reads outside `db.py`: `[]`

### `_base_get_item_by_inventory_id_full_before_refine_display_v1`

- Runtime present: **True**
- Classification: **capture_only_or_unreferenced**
- Reads in `db.py`: `[]`
- Reads outside `db.py`: `[]`

### `_base_get_max_hp_before_refine_v1`

- Runtime present: **True**
- Classification: **capture_only_or_unreferenced**
- Reads in `db.py`: `[]`
- Reads outside `db.py`: `[]`

### `_base_get_sellable_equipment_items_before_refine_display_v1`

- Runtime present: **True**
- Classification: **capture_only_or_unreferenced**
- Reads in `db.py`: `[]`
- Reads outside `db.py`: `[]`

### `_base_get_weapon_damage_by_inventory_id_before_refine_v1`

- Runtime present: **True**
- Classification: **capture_only_or_unreferenced**
- Reads in `db.py`: `[{'file': 'db.py', 'line': 6304, 'function': None}]`
- Reads outside `db.py`: `[]`

### `_base_get_weapon_damage_for_refine_hotfix_v1`

- Runtime present: **True**
- Classification: **capture_only_or_unreferenced**
- Reads in `db.py`: `[]`
- Reads outside `db.py`: `[]`

### `_legacy_`

- Runtime present: **False**
- Classification: **capture_only_or_unreferenced**
- Reads in `db.py`: `[]`
- Reads outside `db.py`: `[]`

## Canonical configuration overlap

- Overlapping top-level names: **26**
- Classification counts: `{'same_name_as_canonical_export': 26}`

### `ARMOR_ALLOWED_BY_CLASS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 4039, 'literal': {'mage': 'cloth', 'priest': 'cloth', 'scout': 'leather', 'rogue': 'leather', 'warrior': 'chain', 'knight': 'plate'}}]`
- Canonical exports: `{'data.equipment_profiles': {'line': 93, 'literal': {'mage': 'cloth', 'priest': 'cloth', 'scout': 'leather', 'rogue': 'leather', 'warrior': 'chain', 'knight': 'plate'}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 4152, 'function': 'get_allowed_armor_type_for_class'}, {'file': 'handlers/inventory.py', 'line': 156, 'function': 'build_item_allowed_classes_text'}]`

### `ARMOR_EXTRA_STATS_BY_SLOT`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 2453, 'literal': {'helmet': ['sta', 'wis', 'dex'], 'shoulders': ['sta', 'str'], 'chest': ['sta'], 'gloves': ['dex', 'str'], 'legs': ['sta', 'dex'], 'boots': ['dex'], 'necklace': ['wis', 'int'], 'ring': ['str', 'dex', 'int', 'wis', 'sta']}}]`
- Canonical exports: `{'data.equipment_profiles': {'line': 82, 'literal': {'helmet': ['sta', 'wis', 'dex'], 'shoulders': ['sta', 'str'], 'chest': ['sta'], 'gloves': ['dex', 'str'], 'legs': ['sta', 'dex'], 'boots': ['dex'], 'necklace': ['wis', 'int'], 'ring': ['str', 'dex', 'int', 'wis', 'sta']}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 2600, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2606, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2613, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2620, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2627, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2634, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2644, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2651, 'function': 'generate_dynamic_equipment_stats'}]`

### `ARMOR_TYPE_LABELS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 4075, 'literal': {'cloth': 'Тканина', 'leather': 'Шкіра', 'chain': 'Кольчуга', 'plate': 'Лати', '': 'Універсальний'}}]`
- Canonical exports: `{'data.equipment_profiles': {'line': 142, 'literal': {'cloth': 'Тканина', 'leather': 'Шкіра', 'chain': 'Кольчуга', 'plate': 'Лати', '': 'Універсальний'}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 4135, 'function': 'get_armor_type_label'}]`

### `CLASS_CONFIGS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 3558, 'literal': {'warrior': {'name': '🛡️ Воїн', 'resource': 'rage', 'description': 'Фізичний боєць ближнього бою.\nОсновні характеристики: Сила, Витривалість.\nРесурс у бою: 🔴 Лютість.'}, 'knight': {'name': '⚔️ Лицар', 'resource': 'rage', 'description': 'Захисник із високим фізичним захистом і щитом.\nОсновні характеристики: Витривалість, Фіз. захист.\nРесурс у бою: 🔴 Лютість.'}, 'scout': {'name': '🏹 Скаут', 'resource': 'combat_energy', 'description': 'Дистанційний фізичний боєць із пастками та точними пострілами.\nОсновні характеристики: Спритність, Сила.\nРесурс у бою: 🟡 Енергія.'}, 'rogue': {'name': '🗡️ Розбійник', 'resource': 'combat_energy_combo', 'description': 'Швидкий боєць ближнього бою з майбутньою механікою комбо.\nОсновні характеристики: Спритність, Сила.\nРесурс у бою: 🟡 Енергія + комбо-очки.'}, 'mage': {'name': '🔮 Маг', 'resource': 'mana', 'description': 'Магічний боєць із високим вибуховою шкодою.\nОсновні характеристики: Інтелект, Мудрість.\nРесурс у бою: 🔵 Мана.'}, 'priest': {'name': '⚕️ Жрець', 'resource': 'mana', 'description': 'Магічний клас підтримки з лікуванням і захистом.\nОсновні характеристики: Мудрість, Інтелект.\nРесурс у бою: 🔵 Мана.'}}}]`
- Canonical exports: `{'data.classes': {'line': 9, 'literal': {'warrior': {'name': '🛡️ Воїн', 'resource': 'rage', 'description': 'Фізичний боєць ближнього бою.\nОсновні характеристики: Сила, Витривалість.\nРесурс у бою: 🔴 Лютість.'}, 'knight': {'name': '⚔️ Лицар', 'resource': 'rage', 'description': 'Захисник із високим фізичним захистом і щитом.\nОсновні характеристики: Витривалість, Фіз. захист.\nРесурс у бою: 🔴 Лютість.'}, 'scout': {'name': '🏹 Скаут', 'resource': 'combat_energy', 'description': 'Дистанційний фізичний боєць із пастками та точними пострілами.\nОсновні характеристики: Спритність, Сила.\nРесурс у бою: 🟡 Енергія.'}, 'rogue': {'name': '🗡️ Розбійник', 'resource': 'combat_energy_combo', 'description': 'Швидкий боєць ближнього бою з майбутньою механікою комбо.\nОсновні характеристики: Спритність, Сила.\nРесурс у бою: 🟡 Енергія + комбо-очки.'}, 'mage': {'name': '🔮 Маг', 'resource': 'mana', 'description': 'Магічний боєць із високим вибуховою шкодою.\nОсновні характеристики: Інтелект, Мудрість.\nРесурс у бою: 🔵 Мана.'}, 'priest': {'name': '⚕️ Жрець', 'resource': 'mana', 'description': 'Магічний клас підтримки з лікуванням і захистом.\nОсновні характеристики: Мудрість, Інтелект.\nРесурс у бою: 🔵 Мана.'}}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 4145, 'function': 'get_class_display_name_by_key'}, {'file': 'db.py', 'line': 3994, 'function': 'restore_user_mp_to_full'}, {'file': 'handlers/inventory.py', 'line': 186, 'function': 'build_item_allowed_classes_text'}, {'file': 'handlers/start.py', 'line': 45, 'function': 'build_class_selection_kb'}, {'file': 'handlers/start.py', 'line': 93, 'function': 'build_class_selection_text'}, {'file': 'systems/character_system.py', 'line': 166, 'function': 'set_character_class'}, {'file': 'systems/character_system.py', 'line': 99, 'function': 'get_character_class_display'}, {'file': 'systems/character_system.py', 'line': 104, 'function': 'get_character_resource_type'}, {'file': 'systems/character_system.py', 'line': 174, 'function': 'set_character_class'}, {'file': 'tools/smoke_test_character_mutation_contracts.py', 'line': 91, 'function': 'main'}, {'file': 'tools/smoke_test_character_mutation_contracts.py', 'line': 83, 'function': 'main'}, {'file': 'tools/smoke_test_character_mutation_contracts.py', 'line': 84, 'function': 'main'}]`

### `CLASS_RESET_SPHERE_ITEM_ID`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 3616, 'literal': 301}]`
- Canonical exports: `{'data.classes': {'line': 66, 'literal': 301}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 3815, 'function': 'is_class_reset_sphere_inventory_item'}, {'file': 'db.py', 'line': 3854, 'function': 'use_class_reset_sphere_from_inventory'}, {'file': 'db.py', 'line': 3684, 'function': 'seed_class_reset_sphere_item'}, {'file': 'handlers/dev.py', 'line': 649, 'function': 'give_class_reset_sphere'}, {'file': 'handlers/inventory.py', 'line': 653, 'function': 'build_item_details'}, {'file': 'systems/character_system.py', 'line': 225, 'function': 'get_class_reset_sphere_item_id'}]`

### `CONTRACTS_UNLOCK_LEVEL`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1260, 'literal': 5}]`
- Canonical exports: `{'data.balance': {'line': 16, 'literal': 5}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 1499, 'function': 'create_daily_contract'}, {'file': 'db.py', 'line': 1474, 'function': 'get_contract_status'}, {'file': 'db.py', 'line': 1503, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 254, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 230, 'function': 'get_contract_status'}, {'file': 'systems/contract_system.py', 'line': 258, 'function': 'create_daily_contract'}]`

### `CONTRACT_MOBS_EQUIVALENT`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 871, 'literal': 20}, {'line': 1263, 'literal': 20}]`
- Canonical exports: `{'data.balance': {'line': 17, 'literal': 20}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 887, 'function': 'get_contract_exp_for_level'}, {'file': 'systems/contract_system.py', 'line': 25, 'function': 'get_contract_mobs_equivalent'}]`

### `CONTRACT_TARGET_KILLS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1262, 'literal': 5}, {'line': 7027, 'literal': 5}]`
- Canonical exports: `{'data.balance': {'line': 18, 'literal': 5}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 1485, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 240, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 22, 'function': 'get_contract_target_kills'}, {'file': 'tools/smoke_test_contract_contracts.py', 'line': 15, 'function': None, 'attribute': True}]`

### `DAILY_CONTRACT_LIMIT`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1261, 'literal': 5}]`
- Canonical exports: `{'data.balance': {'line': 19, 'literal': 5}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 1476, 'function': 'get_contract_status'}, {'file': 'db.py', 'line': 1508, 'function': 'create_daily_contract'}, {'file': 'db.py', 'line': 1513, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 232, 'function': 'get_contract_status'}, {'file': 'systems/contract_system.py', 'line': 263, 'function': 'create_daily_contract'}, {'file': 'systems/contract_system.py', 'line': 268, 'function': 'create_daily_contract'}]`

### `DAILY_QUEST_ID_KILL_MONSTERS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1923, 'literal': 'kill_25_monsters'}]`
- Canonical exports: `{'data.balance': {'line': 20, 'literal': 'kill_25_monsters'}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 1987, 'function': 'reset_daily_quest_if_needed'}, {'file': 'db.py', 'line': 2012, 'function': 'reset_daily_quest_if_needed'}]`

### `DAILY_QUEST_REWARD_ITEM_ID`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1925, 'literal': 201}]`
- Canonical exports: `{'data.balance': {'line': 21, 'literal': 201}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 2060, 'function': 'get_daily_quest_status'}, {'file': 'db.py', 'line': 2165, 'function': 'claim_daily_quest_reward'}]`

### `DAILY_QUEST_REWARD_QUANTITY`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1926, 'literal': 3}]`
- Canonical exports: `{'data.balance': {'line': 22, 'literal': 3}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 2061, 'function': 'get_daily_quest_status'}, {'file': 'db.py', 'line': 2166, 'function': 'claim_daily_quest_reward'}]`

### `DAILY_QUEST_TARGET_KILLS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1924, 'literal': 25}]`
- Canonical exports: `{'data.balance': {'line': 23, 'literal': 25}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 2057, 'function': 'get_daily_quest_status'}, {'file': 'db.py', 'line': 1989, 'function': 'reset_daily_quest_if_needed'}, {'file': 'db.py', 'line': 2013, 'function': 'reset_daily_quest_if_needed'}]`

### `ENERGY_MAX`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1704, 'literal': 40}]`
- Canonical exports: `{'data.balance': {'line': 24, 'literal': 40}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 5869, 'function': 'create_user'}, {'file': 'systems/energy_system.py', 'line': 34, 'function': 'consume_energy_for_hunt'}, {'file': 'systems/energy_system.py', 'line': 69, 'function': 'consume_energy_for_hunt'}, {'file': 'systems/energy_system.py', 'line': 99, 'function': 'restore_energy_for_test'}, {'file': 'systems/energy_system.py', 'line': 296, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 37, 'function': 'consume_energy_for_hunt'}, {'file': 'systems/energy_system.py', 'line': 38, 'function': 'consume_energy_for_hunt'}, {'file': 'systems/energy_system.py', 'line': 83, 'function': 'restore_energy_for_test'}, {'file': 'systems/energy_system.py', 'line': 235, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 243, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 256, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 100, 'function': 'restore_energy_for_test'}, {'file': 'systems/notifications.py', 'line': 134, 'function': 'apply_energy_regen'}, {'file': 'systems/notifications.py', 'line': 89, 'function': 'apply_energy_regen'}]`

### `ENERGY_REGEN_MINUTES`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1705, 'literal': 5}]`
- Canonical exports: `{'data.balance': {'line': 25, 'literal': 5}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'systems/energy_system.py', 'line': 266, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 236, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 257, 'function': 'get_user_energy'}, {'file': 'systems/energy_system.py', 'line': 272, 'function': 'get_user_energy'}, {'file': 'systems/notifications.py', 'line': 109, 'function': 'apply_energy_regen'}, {'file': 'systems/notifications.py', 'line': 114, 'function': 'apply_energy_regen'}]`

### `EQUIPMENT_SLOTS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 16, 'literal': {'main_hand': '🗡️ Зброя', 'off_hand': '🛡️ Друга рука', 'helmet': '🪖 Голова', 'shoulders': '🦾 Плечі', 'chest': '🥋 Тіло', 'gloves': '🧤 Руки', 'legs': '👖 Ноги', 'boots': '👟 Взуття', 'necklace': '📿 Шия', 'ring': '💍 Кільце'}}]`
- Canonical exports: `{'data.equipment_profiles': {'line': 150, 'literal': {'main_hand': '🗡️ Зброя', 'off_hand': '🛡️ Друга рука', 'helmet': '🪖 Голова', 'shoulders': '🦾 Плечі', 'chest': '🥋 Тіло', 'gloves': '🧤 Руки', 'legs': '👖 Ноги', 'boots': '👟 Взуття', 'necklace': '📿 Шия', 'ring': '💍 Кільце'}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 1233, 'function': 'get_common_equipment_shop_offer'}, {'file': 'db.py', 'line': 5235, 'function': 'create_dev_armor_item_for_test'}, {'file': 'db.py', 'line': 5429, 'function': 'create_dev_weapon_item_for_test'}, {'file': 'handlers/city.py', 'line': 658, 'function': 'build_common_shop_preview_text'}, {'file': 'handlers/inventory.py', 'line': 70, 'function': 'get_slot_label'}, {'file': 'handlers/profile.py', 'line': 279, 'function': 'build_equipment_text'}]`

### `HP_REGEN_MINUTES`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1715, 'literal': 1}]`
- Canonical exports: `{'data.balance': {'line': 26, 'literal': 1}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'systems/notifications.py', 'line': 338, 'function': 'apply_hp_regen'}, {'file': 'systems/notifications.py', 'line': 780, 'function': 'apply_hp_regen'}, {'file': 'systems/notifications.py', 'line': 352, 'function': 'apply_hp_regen'}, {'file': 'systems/notifications.py', 'line': 804, 'function': 'apply_hp_regen'}, {'file': 'systems/regen_system.py', 'line': 292, 'function': 'process_passive_regeneration'}, {'file': 'systems/regen_system.py', 'line': 198, 'function': 'apply_passive_hp_regen'}, {'file': 'systems/regen_system.py', 'line': 209, 'function': 'apply_passive_hp_regen'}, {'file': 'systems/regen_system.py', 'line': 300, 'function': 'process_passive_regeneration'}]`

### `HP_REGEN_PERCENT`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 1714, 'literal': 0.1}]`
- Canonical exports: `{'data.balance': {'line': 27, 'literal': 0.1}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'systems/notifications.py', 'line': 346, 'function': 'apply_hp_regen'}, {'file': 'systems/notifications.py', 'line': 799, 'function': 'apply_hp_regen'}, {'file': 'systems/regen_system.py', 'line': 207, 'function': 'apply_passive_hp_regen'}, {'file': 'systems/regen_system.py', 'line': 297, 'function': 'process_passive_regeneration'}]`

### `ITEM_SUBTYPE_LABELS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 4084, 'literal': {'sword_1h': 'Одноручний меч', 'sword_2h': 'Дворучний меч', 'dagger_1h': 'Кинджал', 'wand_1h': 'Жезл', 'staff_2h': 'Дворучний посох', 'bow_2h': 'Лук', 'crossbow_2h': 'Арбалет', 'shield': 'Щит', 'talisman': 'Магічний талісман', 'dagger': 'Кинджал для другої руки', '': 'Універсальний'}}]`
- Canonical exports: `{'data.equipment_profiles': {'line': 126, 'literal': {'sword_1h': 'Одноручний меч', 'sword_2h': 'Дворучний меч', 'dagger_1h': 'Кинджал', 'wand_1h': 'Жезл', 'staff_2h': 'Дворучний посох', 'bow_2h': 'Лук', 'crossbow_2h': 'Арбалет', 'shield': 'Щит', 'talisman': 'Магічний талісман', 'dagger': 'Кинджал для другої руки', '': 'Універсальний'}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 4140, 'function': 'get_item_subtype_label'}]`

### `MAIN_HAND_ALLOWED_BY_CLASS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 4051, 'literal': {'mage': ['wand_1h', 'staff_2h'], 'priest': ['wand_1h', 'staff_2h'], 'scout': ['bow_2h', 'crossbow_2h'], 'rogue': ['dagger_1h'], 'warrior': ['sword_1h', 'sword_2h'], 'knight': ['sword_1h']}}]`
- Canonical exports: `{'data.equipment_profiles': {'line': 104, 'literal': {'mage': ['wand_1h', 'staff_2h'], 'priest': ['wand_1h', 'staff_2h'], 'scout': ['bow_2h', 'crossbow_2h'], 'rogue': ['dagger_1h'], 'warrior': ['sword_1h', 'sword_2h'], 'knight': ['sword_1h']}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 4156, 'function': 'get_allowed_main_hand_subtypes_for_class'}, {'file': 'handlers/inventory.py', 'line': 164, 'function': 'build_item_allowed_classes_text'}]`

### `MAIN_HAND_PROFILES`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 2385, 'literal': {'sword_1h': {'name': 'Одноручний меч', 'hands': 1, 'attack_type': 'physical', 'main_stats': ['str'], 'extra_stats': ['str', 'sta']}, 'wand_1h': {'name': 'Жезл', 'hands': 1, 'attack_type': 'magical', 'main_stats': ['int'], 'extra_stats': ['int', 'wis']}, 'sword_2h': {'name': 'Дворучний меч', 'hands': 2, 'attack_type': 'physical', 'main_stats': ['str'], 'extra_stats': ['str', 'sta']}, 'staff_2h': {'name': 'Дворучний посох', 'hands': 2, 'attack_type': 'magical', 'main_stats': ['int'], 'extra_stats': ['int', 'wis']}, 'bow_2h': {'name': 'Лук', 'hands': 2, 'attack_type': 'physical', 'main_stats': ['dex'], 'extra_stats': ['dex', 'str']}, 'crossbow_2h': {'name': 'Арбалет', 'hands': 2, 'attack_type': 'physical', 'main_stats': ['dex'], 'extra_stats': ['dex', 'str']}}}, {'line': 2907, 'literal': {'sword_1h': {'name': 'Одноручний меч', 'hands': 1, 'attack_type': 'physical', 'main_stats': ['str'], 'extra_stats': ['str', 'sta']}, 'dagger_1h': {'name': 'Кинджал', 'hands': 1, 'attack_type': 'physical', 'main_stats': ['dex'], 'extra_stats': ['dex', 'str']}, 'wand_1h': {'name': 'Жезл', 'hands': 1, 'attack_type': 'magical', 'main_stats': ['int'], 'extra_stats': ['int', 'wis']}, 'sword_2h': {'name': 'Дворучний меч', 'hands': 2, 'attack_type': 'physical', 'main_stats': ['str'], 'extra_stats': ['str', 'sta']}, 'staff_2h': {'name': 'Дворучний посох', 'hands': 2, 'attack_type': 'magical', 'main_stats': ['int'], 'extra_stats': ['int', 'wis']}, 'bow_2h': {'name': 'Лук', 'hands': 2, 'attack_type': 'physical', 'main_stats': ['dex'], 'extra_stats': ['dex', 'str']}, 'crossbow_2h': {'name': 'Арбалет', 'hands': 2, 'attack_type': 'physical', 'main_stats': ['dex'], 'extra_stats': ['dex', 'str']}}}]`
- Canonical exports: `{'data.equipment_profiles': {'line': 9, 'literal': {'sword_1h': {'name': 'Одноручний меч', 'hands': 1, 'attack_type': 'physical', 'main_stats': ['str'], 'extra_stats': ['str', 'sta']}, 'dagger_1h': {'name': 'Кинджал', 'hands': 1, 'attack_type': 'physical', 'main_stats': ['dex'], 'extra_stats': ['dex', 'str']}, 'wand_1h': {'name': 'Жезл', 'hands': 1, 'attack_type': 'magical', 'main_stats': ['int'], 'extra_stats': ['int', 'wis']}, 'sword_2h': {'name': 'Дворучний меч', 'hands': 2, 'attack_type': 'physical', 'main_stats': ['str'], 'extra_stats': ['str', 'sta']}, 'staff_2h': {'name': 'Дворучний посох', 'hands': 2, 'attack_type': 'magical', 'main_stats': ['int'], 'extra_stats': ['int', 'wis']}, 'bow_2h': {'name': 'Лук', 'hands': 2, 'attack_type': 'physical', 'main_stats': ['dex'], 'extra_stats': ['dex', 'str']}, 'crossbow_2h': {'name': 'Арбалет', 'hands': 2, 'attack_type': 'physical', 'main_stats': ['dex'], 'extra_stats': ['dex', 'str']}}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 2688, 'function': 'is_weapon_profile_magical'}, {'file': 'db.py', 'line': 5265, 'function': 'create_dev_weapon_item_for_test'}, {'file': 'db.py', 'line': 2506, 'function': 'get_profile_for_generated_item'}, {'file': 'db.py', 'line': 2730, 'function': 'create_generated_equipment_item_for_slot'}, {'file': 'db.py', 'line': 3199, 'function': 'create_common_equipment_shop_preview'}, {'file': 'db.py', 'line': 3230, 'function': 'create_common_equipment_shop_preview'}, {'file': 'db.py', 'line': 5267, 'function': 'create_dev_weapon_item_for_test'}, {'file': 'db.py', 'line': 5607, 'function': 'create_generated_equipment_item'}, {'file': 'db.py', 'line': 5610, 'function': 'create_generated_equipment_item'}, {'file': 'db.py', 'line': 2525, 'function': 'get_dynamic_weapon_name'}, {'file': 'db.py', 'line': 2525, 'function': 'get_dynamic_weapon_name'}, {'file': 'db.py', 'line': 2553, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2553, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 4904, 'function': 'get_allowed_shop_main_hand_profiles'}, {'file': 'db.py', 'line': 2497, 'function': 'get_random_main_hand_profile'}, {'file': 'db.py', 'line': 2689, 'function': 'is_weapon_profile_magical'}, {'file': 'db.py', 'line': 2875, 'function': 'get_common_equipment_shop_suboffers'}, {'file': 'db.py', 'line': 2876, 'function': 'get_common_equipment_shop_suboffers'}, {'file': 'db.py', 'line': 2877, 'function': 'get_common_equipment_shop_suboffers'}]`

### `OFF_HAND_ALLOWED_BY_CLASS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 4063, 'literal': {'mage': ['talisman'], 'priest': ['talisman'], 'scout': [], 'rogue': ['dagger'], 'warrior': [], 'knight': ['shield']}}]`
- Canonical exports: `{'data.equipment_profiles': {'line': 115, 'literal': {'mage': ['talisman'], 'priest': ['talisman'], 'scout': [], 'rogue': ['dagger'], 'warrior': [], 'knight': ['shield']}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 4160, 'function': 'get_allowed_off_hand_subtypes_for_class'}, {'file': 'handlers/inventory.py', 'line': 172, 'function': 'build_item_allowed_classes_text'}]`

### `OFF_HAND_PROFILES`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 2431, 'literal': {'shield': {'name': 'Щит', 'attack_type': 'defense', 'main_stats': ['sta'], 'extra_stats': ['sta', 'wis']}, 'talisman': {'name': 'Магічний талісман', 'attack_type': 'magical', 'main_stats': ['wis'], 'extra_stats': ['wis', 'int']}, 'dagger': {'name': 'Кинджал для другої руки', 'attack_type': 'physical', 'main_stats': ['dex'], 'extra_stats': ['dex', 'str']}}}]`
- Canonical exports: `{'data.equipment_profiles': {'line': 61, 'literal': {'shield': {'name': 'Щит', 'attack_type': 'defense', 'main_stats': ['sta'], 'extra_stats': ['sta', 'wis']}, 'talisman': {'name': 'Магічний талісман', 'attack_type': 'magical', 'main_stats': ['wis'], 'extra_stats': ['wis', 'int']}, 'dagger': {'name': 'Кинджал для другої руки', 'attack_type': 'physical', 'main_stats': ['dex'], 'extra_stats': ['dex', 'str']}}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 2512, 'function': 'get_profile_for_generated_item'}, {'file': 'db.py', 'line': 3205, 'function': 'create_common_equipment_shop_preview'}, {'file': 'db.py', 'line': 5272, 'function': 'create_dev_weapon_item_for_test'}, {'file': 'db.py', 'line': 2530, 'function': 'get_dynamic_weapon_name'}, {'file': 'db.py', 'line': 2530, 'function': 'get_dynamic_weapon_name'}, {'file': 'db.py', 'line': 2737, 'function': 'create_generated_equipment_item_for_slot'}, {'file': 'db.py', 'line': 3237, 'function': 'create_common_equipment_shop_preview'}, {'file': 'db.py', 'line': 4915, 'function': 'get_allowed_shop_off_hand_profiles'}, {'file': 'db.py', 'line': 5274, 'function': 'create_dev_weapon_item_for_test'}, {'file': 'db.py', 'line': 5629, 'function': 'create_generated_equipment_item'}, {'file': 'db.py', 'line': 5632, 'function': 'create_generated_equipment_item'}, {'file': 'db.py', 'line': 2501, 'function': 'get_random_off_hand_profile'}, {'file': 'db.py', 'line': 2572, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2572, 'function': 'generate_dynamic_equipment_stats'}, {'file': 'db.py', 'line': 2891, 'function': 'get_common_equipment_shop_suboffers'}, {'file': 'db.py', 'line': 2893, 'function': 'get_common_equipment_shop_suboffers'}]`

### `RARITY_REPAIR_MULTIPLIERS`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 44, 'literal': {'common': 1.0, 'uncommon': 2.5, 'rare': 7.0, 'epic': 18.0}}]`
- Canonical exports: `{'data.balance': {'line': 28, 'literal': {'common': 1.0, 'uncommon': 2.5, 'rare': 7.0, 'epic': 18.0}}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 985, 'function': 'get_rarity_repair_multiplier'}]`

### `REFINE_MATERIAL_MAX_STACK`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 6545, 'literal': 999}]`
- Canonical exports: `{'data.balance': {'line': 29, 'literal': 999}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 6564, 'function': 'ensure_refine_material_stack_sizes'}]`

### `REFINE_STONE_ITEM_ID`

- Classification: **same_name_as_canonical_export**
- Local `db.py` definitions: `[{'line': 5965, 'literal': 401}]`
- Canonical exports: `{'data.balance': {'line': 30, 'literal': 401}}`
- Canonical imports into `db.py`: `[]`
- Project reads: `[{'file': 'db.py', 'line': 6014, 'function': 'seed_refine_items'}, {'file': 'db.py', 'line': 6102, 'function': 'get_refine_resource_counts'}, {'file': 'systems/refine_system.py', 'line': 127, 'function': 'perform_refine_attempt'}, {'file': 'systems/refine_system.py', 'line': 123, 'function': 'perform_refine_attempt'}, {'file': 'systems/reward_system.py', 'line': 469, 'function': 'roll_refine_stone_drop'}]`

## Cleanup groups

- Capture-only/unreferenced candidates: `['_base_get_inventory_detailed_before_refine_display_v1', '_base_get_inventory_entry_before_refine_display_v1', '_base_get_item_by_inventory_id_before_refine_display_v1', '_base_get_item_by_inventory_id_full_before_refine_display_v1', '_base_get_max_hp_before_refine_v1', '_base_get_sellable_equipment_items_before_refine_display_v1', '_base_get_weapon_damage_by_inventory_id_before_refine_v1', '_base_get_weapon_damage_for_refine_hotfix_v1', '_legacy_']`
- Captures requiring dependency review: `[]`
- Local config definitions shadowed/replaced by canonical imports: `[]`

## Recommended next steps

1. Do not mass-delete all `_legacy_*` or `_base_*` symbols.
2. Remove only capture-only/unreferenced names after a targeted runtime contract test.
3. Preserve captures with reads in `db.py` until their callers are redirected to direct system APIs.
4. Treat any external read as a compatibility contract requiring a dedicated migration.
5. Move canonical `data.*` imports before consumers, then remove only local definitions that are demonstrably shadowed.
6. Split the physical cleanup into small patches by domain: Player, Refine/Equipment, and constants.
7. Finish with compile/import, gameplay contracts, and real-user snapshot checks.

## Suggested patch sequence

- `patch_9_0_13l_capture_only_cleanup.py`
- `patch_9_0_13m_constants_canonicalization_audit.py`
- `patch_9_0_13n_final_closure_audit.py`
