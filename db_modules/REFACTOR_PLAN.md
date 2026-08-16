# План розбиття db.py на модулі

## Статус: Етап 1 - Створення структури

### connection.py ✅
- conn, cursor
- SLOT_ORDER
- init_db()
- seed_items()

### user.py (буде створено)
Функції роботи з користувачами:
- create_user()
- get_user()
- get_player_level()
- get_player_stats()
- get_max_hp()
- update_player_stats()
- level_up()
- add_exp()
- add_gold()
- subtract_gold()
- get_character_name()
- set_character_name()
- needs_character_name()
- needs_character_class()
- get_character_profile_summary()
- та інші user-related функції

### inventory.py (буде створено)
Функції інвентарю:
- get_inventory()
- add_item()
- consume_inventory_item()
- get_inventory_entry()
- get_inventory_used_slots()
- get_bag_capacity()
- get_item()
- get_item_full()
- get_item_by_inventory_id()
- find_first_item_stack_by_type()
- та інші inventory функції

### equipment.py (буде створено)
Функції спорядження:
- equip_item()
- unequip_slot()
- get_equipped_slot()
- set_equipped_slot()
- get_all_equipped_slots()
- is_inventory_item_equipped()
- ensure_equipment_slots()
- migrate_legacy_equipment_to_slots()
- get_equipped_items()
- apply_random_durability_wear_on_victory()
- та інші equipment функції

### combat.py (буде створено)
Бойові розрахунки:
- get_physical_attack()
- get_magical_attack()
- get_physical_defense()
- get_magical_defense()
- get_defense()
- get_player_attack_profile()
- get_enemy_crit_chance_against_player()
- calculate_damage()
- та інші combat функції

### economy.py (буде створено)
Економічна система:
- sell_all_trash()
- buy_item_for_gold()
- get_total_repair_cost()
- get_rarity_repair_multiplier()
- format_gold()
- get_common_equipment_shop_offer()
- get_common_equipment_price_for_slot()
- та інші economy функції

### quests.py (буде створено)
Квести та контракти:
- init_contract_system()
- get_active_contract()
- create_daily_contract()
- abandon_active_contract()
- process_contract_progress_on_kill()
- get_contract_status()
- reset_daily_contracts_if_needed()
- init_daily_quest_system()
- get_daily_quest_status()
- process_daily_quest_progress_on_kill()
- claim_daily_quest_reward()
- reset_daily_quest_if_needed()
- та інші quest функції

### character_class.py (буде створено)
Система класів:
- init_character_class_system()
- get_character_class()
- set_character_class()
- get_character_class_display()
- seed_class_reset_sphere_item()
- use_class_reset_sphere_from_inventory()
- is_class_reset_sphere_inventory_item()
- has_class_change_available()
- consume_class_change_available()
- unequip_incompatible_items_after_class_change()
- та інші class функції

### runes.py (буде створено)
Система рун:
- init_rune_system()
- apply_rune_to_equipment()
- get_rune_stats()
- remove_rune_from_equipment()
- fuse_runes()
- та інші rune функції

### regeneration.py (буде створено)
Регенерація ресурсів:
- apply_passive_hp_regen()
- update_last_regen_timestamp()
- init_hp_regen_system()
- process_passive_regeneration()
- get_users_for_hp_full_notification()
- spend_user_mp()
- restore_user_mp_to_full()
- та інші regen функції

### shop_preview.py (буде створено)
Система попереднього перегляду в магазині:
- init_shop_preview_system()
- create_common_equipment_shop_preview()
- get_shop_preview_item()
- cancel_common_equipment_shop_preview()
- confirm_common_equipment_shop_preview()
- cleanup_shop_previews_for_user()
- get_shop_preview_weapon_damage_text()
- та інші shop preview функції

### testing.py (буде створено)
Тестові утиліти:
- set_player_level_for_test()
- reset_player_level_for_test()
- set_gold_for_test()
- reset_hero_for_test()
- _get_dev_reset_hero_lock()
- _dev_reset_table_exists()
- _dev_reset_table_columns()
- та інші dev функції

### migrations.py (буде створено)
Міграції бази даних:
- run_pending_migrations()
- run_db_startup_maintenance()
- expand_bag_slots_to_40()
- seed_location_trash_items()
- init_dynamic_equipment_system()
- init_class_equipment_restrictions_system()
- та інші migration функції

### location.py (буде створено)
Локації:
- get_current_location()
- set_current_location()

## Наступні кроки

Етап 2: Створення модулів user.py, inventory.py, equipment.py
Етап 3: Створення модулів combat.py, economy.py, quests.py
Етап 4: Створення модулів character_class.py, runes.py, regeneration.py
Етап 5: Створення модулів shop_preview.py, testing.py, migrations.py, location.py + compatibility layer
