# ROM 9.0.12i7a - Remaining Duplicates Audit

## Scope

Read-only classification of all remaining duplicate top-level definitions in `db.py`.

## Summary

- Remaining duplicate names: 17
- Legacy refs: 0
- Unsafe-delete candidates: 0
- Database mutations: 0

## Group: dynamic_equipment

### `init_dynamic_equipment_system`

- Definitions: 2; lines: [1313, 3164]
- Final node kind: `FunctionDef`
- Calls in final definition: ['commit', 'execute']
- Consumers: ['db.py:1520', 'db.py:1666', 'db.py:3430', 'db.py:3594', 'db.py:4109', 'db.py:5106', 'db.py:6152', 'db.py:6401', 'db.py:6574', 'db.py:6877', 'db.py:784']
- Final source preview: `def init_dynamic_equipment_system():     migrations = [         ("items", "item_level", "INTEGER DEFAULT 1"),         ("items", "is_generated", "INTEGER DEFAULT 0"),         ("item`

### `get_dynamic_weapon_name`

- Definitions: 2; lines: [1345, 3219]
- Final node kind: `FunctionDef`
- Calls in final definition: ['get', 'get_profile_for_generated_item']
- Consumers: ['db.py:1543', 'db.py:1547', 'db.py:1721', 'db.py:1728', 'db.py:3458', 'db.py:3465', 'db.py:3628', 'db.py:3635', 'db.py:4156', 'db.py:4163', 'db.py:6189', 'db.py:6208', 'db.py:6626', 'db.py:6931', 'db.py:6953']
- Final source preview: `def get_dynamic_weapon_name(slot_key, rarity, weapon_hands=1, item_profile=None):     icon = DYNAMIC_RARITY_ICONS.get(rarity, "⚪")      if slot_key == "main_hand":         profile_`

### `generate_dynamic_equipment_stats`

- Definitions: 2; lines: [1387, 3235]
- Final node kind: `FunctionDef`
- Calls in final definition: ['add_stat_value', 'choice', 'get', 'get_dynamic_stat_value', 'get_profile_for_generated_item', 'max', 'range']
- Consumers: ['db.py:1557', 'db.py:1740', 'db.py:3477', 'db.py:3646', 'db.py:4175', 'db.py:6234', 'db.py:6455', 'db.py:6635', 'db.py:6982']
- Final source preview: `def generate_dynamic_equipment_stats(slot_key, item_level, rarity, weapon_hands=1, item_profile=None):     stats = {         "bonus_str": 0,         "bonus_dex": 0,         "bonus_`

### `create_generated_equipment_item`

- Definitions: 4; lines: [1519, 3429, 6140, 6853]
- Final node kind: `FunctionDef`
- Calls in final definition: ['apply_armor_type_defense_profile_to_stats', 'calculate_weapon_damage_by_values', 'commit', 'execute', 'float', 'generate_dynamic_equipment_stats', 'get', 'get_bag_capacity', 'get_dynamic_armor_name', 'get_dynamic_sell_price', 'get_dynamic_weapon_name', 'get_inventory_used_slots', 'get_random_class_aware_equipment_choice', 'get_random_loot_armor_type', 'get_random_main_hand_profile', 'get_random_off_hand_profile', 'get_random_unrestricted_equipment_choice', 'init_class_equipment_restrictions_system', 'init_dynamic_equipment_system', 'init_weapon_damage_system', 'int', 'is_armor_slot', 'max', 'min', 'random']
- Consumers: ['handlers/dev.py:411', 'systems/reward_system.py:274']
- Final source preview: `def create_generated_equipment_item(     user_id,     item_level,     rarity,     class_aware_chance=0.0 ):     """     Динамічний дроп екіпірування з мобів.      class_aware_chanc`

### `create_generated_equipment_item_for_slot`

- Definitions: 2; lines: [1665, 3593]
- Final node kind: `FunctionDef`
- Calls in final definition: ['calculate_weapon_damage_by_values', 'commit', 'execute', 'generate_dynamic_equipment_stats', 'get_bag_capacity', 'get_dynamic_armor_name', 'get_dynamic_sell_price', 'get_dynamic_weapon_name', 'get_inventory_used_slots', 'get_profile_for_generated_item', 'init_dynamic_equipment_system', 'init_weapon_damage_system', 'int', 'max']
- Consumers: []
- Final source preview: `def create_generated_equipment_item_for_slot(user_id, item_level, rarity, slot_key, item_profile=None):     init_dynamic_equipment_system()     init_weapon_damage_system()      if `

### `detect_weapon_profile_from_name`

- Definitions: 2; lines: [3384, 3855]
- Final node kind: `FunctionDef`
- Calls in final definition: ['lower']
- Consumers: []
- Final source preview: `def detect_weapon_profile_from_name(name):     if not name:         return ""      lowered = name.lower()      if "дворучний посох" in lowered:         return "staff_2h"      if "ж`

### `get_random_loot_armor_type`

- Definitions: 2; lines: [6121, 6761]
- Final node kind: `FunctionDef`
- Calls in final definition: ['choice']
- Consumers: ['db.py:6226', 'db.py:6843', 'db.py:6972']
- Final source preview: `def get_random_loot_armor_type():     """     Випадковий armor_type для повністю випадкового дропу.     """      return random.choice([         "cloth",         "leather",         `

### `pick_weighted_stat`

- Definitions: 2; lines: [5490, 5747]
- Final node kind: `FunctionDef`
- Calls in final definition: ['append', 'randint', 'sum']
- Consumers: ['db.py:5646', 'db.py:5654', 'db.py:5876', 'db.py:5884']
- Final source preview: `def pick_weighted_stat(weighted_stats, exclude_stat=None):     """     Вибирає характеристику за вагами.     """      filtered = []      for stat_key, weight in weighted_stats:    `

### `get_existing_primary_stat_budget`

- Definitions: 2; lines: [5559, 5809]
- Final node kind: `FunctionDef`
- Calls in final definition: ['get', 'int']
- Consumers: ['db.py:5626', 'db.py:5856']
- Final source preview: `def get_existing_primary_stat_budget(stats):     """     Рахує поточний бюджет основних характеристик.     Наприклад chest 8 common дає bonus_sta = 4, отже budget = 4.     """     `

### `clear_primary_stat_bonuses`

- Definitions: 2; lines: [5581, 5824]
- Final node kind: `FunctionDef`
- Calls in final definition: []
- Consumers: ['db.py:5631', 'db.py:5861']
- Final source preview: `def clear_primary_stat_bonuses(stats):     """     Очищає старі slot-based характеристики.     """      stats["bonus_str"] = 0     stats["bonus_dex"] = 0     stats["bonus_int"] = 0`

### `add_primary_stat_to_stats`

- Definitions: 2; lines: [5533, 5783]
- Final node kind: `FunctionDef`
- Calls in final definition: ['int']
- Consumers: ['db.py:5659', 'db.py:5666', 'db.py:5889', 'db.py:5896']
- Final source preview: `def add_primary_stat_to_stats(stats, stat_key, value):     """     Додає основну характеристику у stats.     """      value = int(value or 0)      if value <= 0:         return    `

### `apply_armor_type_primary_stat_profile_to_stats`

- Definitions: 2; lines: [5598, 5836]
- Final node kind: `FunctionDef`
- Calls in final definition: ['add_primary_stat_to_stats', 'clear_primary_stat_bonuses', 'float', 'get', 'get_existing_primary_stat_budget', 'int', 'max', 'normalize_equipment_restriction_value', 'pick_weighted_stat', 'round']
- Consumers: ['db.py:5970']
- Final source preview: `def apply_armor_type_primary_stat_profile_to_stats(stats, armor_type):     """     Перерозподіляє основні характеристики броні залежно від armor_type.      cloth   -> INT / WIS / S`

## Group: equipment_repair_read

### `get_equipped_items_for_repair`

- Definitions: 3; lines: [1057, 7853, 9148]
- Final node kind: `FunctionDef`
- Calls in final definition: ['_equipment_system_ro_v1', 'get_equipped_items_for_repair']
- Consumers: ['db.py:1135', 'db.py:9149', 'handlers/city.py:380', 'systems/equipment_system.py:1441', 'systems/equipment_system.py:1512', 'tools/smoke_test_equipment_durability_contracts.py:13', 'tools/smoke_test_equipment_readonly_core.py:22']
- Final source preview: `def get_equipped_items_for_repair(*args, **kwargs):     return _equipment_system_ro_v1().get_equipped_items_for_repair(*args, **kwargs)`

## Group: auction_lifecycle

### `init_auction_house`

- Definitions: 2; lines: [8523, 8808]
- Final node kind: `FunctionDef`
- Calls in final definition: ['_cleanup', '_init']
- Consumers: ['handlers/auction_house.py:74', 'systems/auction_house_system.py:1019', 'systems/auction_house_system.py:1076', 'systems/auction_house_system.py:1256', 'systems/auction_house_system.py:1441', 'systems/auction_house_system.py:1509', 'systems/auction_house_system.py:1841', 'systems/auction_house_system.py:1890', 'systems/auction_house_system.py:1948', 'systems/auction_house_system.py:2257', 'systems/auction_house_system.py:2398', 'systems/auction_house_system.py:253', 'systems/auction_house_system.py:2551', 'systems/auction_house_system.py:2866', 'systems/auction_house_system.py:295', 'systems/auction_house_system.py:301', 'systems/auction_house_system.py:3095', 'systems/auction_house_system.py:3129', 'systems/auction_house_system.py:3138', 'systems/auction_house_system.py:3212', 'systems/auction_house_system.py:3315', 'systems/auction_house_system.py:3346', 'systems/auction_house_system.py:342', 'systems/auction_house_system.py:3431', 'systems/auction_house_system.py:3538', 'systems/auction_house_system.py:3569', 'systems/auction_house_system.py:3656', 'systems/auction_house_system.py:3810', 'systems/auction_house_system.py:3895', 'systems/auction_house_system.py:4023', 'systems/auction_house_system.py:4087', 'systems/auction_house_system.py:418', 'systems/auction_house_system.py:4184', 'systems/auction_house_system.py:4334', 'systems/auction_house_system.py:4451', 'systems/auction_house_system.py:4506', 'systems/auction_house_system.py:4584', 'systems/auction_house_system.py:4710', 'systems/auction_house_system.py:4899', 'systems/auction_house_system.py:4987', 'systems/auction_house_system.py:5089', 'systems/auction_house_system.py:521', 'systems/auction_house_system.py:589', 'systems/auction_house_system.py:684', 'systems/auction_house_system.py:709', 'systems/auction_house_system.py:760', 'tools/smoke_test_rom_core.py:50']
- Final source preview: `def init_auction_house():     """     Wrapper initialization.     Also runs lightweight cleanup so expiration is processed after bot start     and whenever Auction House systems in`

### `update_expired_auction_lots`

- Definitions: 2; lines: [8583, 8798]
- Final node kind: `FunctionDef`
- Calls in final definition: ['_func']
- Consumers: ['handlers/auction_house.py:4896', 'handlers/auction_house.py:4915', 'handlers/auction_house.py:5157', 'handlers/auction_house.py:75', 'systems/auction_house_system.py:3316', 'systems/auction_house_system.py:3347', 'systems/auction_house_system.py:3432', 'systems/auction_house_system.py:3539', 'systems/auction_house_system.py:3570', 'systems/auction_house_system.py:3657', 'systems/auction_house_system.py:3811', 'systems/auction_house_system.py:3896', 'systems/auction_house_system.py:4024', 'systems/auction_house_system.py:4088', 'systems/auction_house_system.py:4185', 'systems/auction_house_system.py:4335', 'systems/auction_house_system.py:4900', 'systems/auction_house_system.py:4990', 'systems/auction_house_system.py:5092']
- Final source preview: `def update_expired_auction_lots(now_iso=None):     from systems.auction_house_system import update_expired_auction_lots as _func     return _func(now_iso=now_iso)`

## Group: contract_reward

### `claim_contract_reward`

- Definitions: 2; lines: [2333, 8396]
- Final node kind: `FunctionDef`
- Calls in final definition: ['_base_claim_contract_reward_before_guild_reward_v1', '_guild_contract_reward_append_message_v1', '_guild_contract_reward_result_success_v1', 'award_guild_contract_completion', 'get', 'get_active_contract', 'print']
- Consumers: ['handlers/contracts.py:273']
- Final source preview: `def claim_contract_reward(user_id):     """     FINAL OVERRIDE:     Здача контракту + Guild reward.     """      if _base_claim_contract_reward_before_guild_reward_v1 is None:     `

## Group: user_creation

### `create_user`

- Definitions: 3; lines: [264, 3974, 7114]
- Final node kind: `FunctionDef`
- Calls in final definition: ['commit', 'ensure_equipment_slots', 'execute', 'expand_bag_slots_to_40', 'init_energy_system', 'isoformat', 'migrate_legacy_equipment_to_slots', 'now']
- Consumers: ['db.py:3058', 'handlers/start.py:256']
- Final source preview: `def create_user(user_id):     """     Фінальна версія створення користувача.      Важливо:     новий персонаж має створюватися з втомою 0/40.     """      from datetime import date`

## Recommended sequence

1. `i7b/i7c`: isolated deterministic audit and cleanup of `get_equipped_items_for_repair` plus Dynamic Equipment helpers only after random/DB contracts are fixed.
2. `i8a/i8b`: Auction lifecycle contracts and physical cleanup.
3. `i9a/i9b`: isolated `create_user` contracts and physical cleanup.
4. `i10a/i10b`: isolated `claim_contract_reward` contracts and physical cleanup.

Do not mass-delete all 17 names in one patch.
