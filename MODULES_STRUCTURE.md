# 📦 Структура Модулів DB_MODULES

## 🗂️ Всі Модулі (13 файлів)

### 1. **connection.py** (216 рядків)
**Призначення:** База даних, підключення, константи

**Експортує:**
- `conn` - SQLite connection
- `cursor` - DB cursor
- `SLOT_ORDER` - порядок слотів екіпірування
- `DEFAULT_BAG_SLOTS` - розмір сумки за замовчуванням (40)
- `init_db()` - ініціалізація БД
- `seed_items()` - наповнення БД предметами

**Ключові таблиці:**
- users, inventory, user_equipment_slots
- user_energy, user_guild_profiles, guilds
- auction_listings, user_runes, user_contracts
- user_daily_quests, shop_previews

---

### 2. **player.py** (305+ рядків)
**Призначення:** Гравець - статистика, HP, gold, attack

**Експортує (20 функцій):**

#### Stats:
- `get_player_level(user_id)` - рівень гравця
- `get_player_stats(user_id)` - tuple(STR, DEX, INT, WIS, STA, level)
- `get_user_progress(user_id)` - level + exp
- `add_exp(user_id, amount)` - додати досвід

#### Gold:
- `get_wallet(user_id)` - кількість золота
- `add_gold(user_id, amount)` - додати золото
- `add_kill(user_id)` - +1 вбивство

#### Combat Stats:
- `get_attack(user_id)` - фізична атака
- `get_magic_attack(user_id)` - магічна атака
- `get_physical_defense(user_id)` - фіз. захист
- `get_magic_defense(user_id)` - маг. захист
- `get_physical_crit_chance_display(user_id)` - шанс фіз. криту
- `get_magical_crit_chance_display(user_id)` - шанс маг. криту
- `get_base_dodge_chance_display(user_id)` - шанс ухилення
- `get_enemy_crit_chance_against_player(user_id)` - шанс криту ворога

#### HP:
- `get_max_hp(user_id)` - макс. HP
- `get_current_hp_raw(user_id)` - поточне HP (raw int)
- `get_current_hp(user_id)` - поточне HP (formatted)
- `set_current_hp(user_id, hp)` - встановити HP
- `sync_user_max_hp(user_id, heal_to_full=False)` - синхронізувати макс. HP

#### Combat:
- `get_player_attack_profile(user_id)` - повний профіль атаки (type, stat, weapon dmg)

#### User:
- `create_user(user_id)` - створити користувача
- `get_user(user_id)` - отримати всі дані користувача

**Wrappers для:** systems.player_system

---

### 3. **character.py** (190+ рядків)
**Призначення:** Персонаж - класи, імена, MP, ресурси

**Експортує (21 функція + 1 константа):**

#### Constant:
- `CLASS_CONFIGS` - конфігурація класів (з data.classes)

#### Init:
- `init_character_class_system()` - ініціалізація системи класів

#### Names:
- `normalize_character_name(name)` - нормалізувати ім'я
- `validate_character_name(name)` - валідувати ім'я
- `get_character_name(user_id)` - отримати ім'я
- `set_character_name(user_id, name)` - встановити ім'я
- `is_character_name_taken(name)` - перевірити чи ім'я зайняте
- `needs_character_name(user_id)` - чи потрібно ім'я
- `needs_character_class(user_id)` - чи потрібен клас

#### Classes:
- `get_character_class(user_id)` - клас персонажа
- `set_character_class(user_id, class_key)` - встановити клас
- `get_character_class_display(user_id)` - назва класу для відображення
- `get_character_resource_type(user_id)` - тип ресурсу (mana/energy/rage)

#### MP (Mana Points):
- `get_user_mp(user_id)` - поточна та макс. мана
- `set_user_mp(user_id, mp)` - встановити ману
- `spend_user_mp(user_id, amount)` - витратити ману
- `restore_user_mp_to_full(user_id)` - відновити ману повністю
- `get_max_mp(user_id)` - макс. мана
- `refresh_user_mp(user_id)` - оновити ману

#### Class Change Tokens:
- `grant_class_change_available(user_id, amount=1)` - дати токен зміни класу
- `consume_class_change_available(user_id)` - використати токен
- `get_class_change_available(user_id)` - кількість токенів
- `has_class_change_available(user_id)` - чи є токени

#### Profile:
- `get_character_profile_summary(user_id)` - зведення профілю (ім'я, клас, ресурс, MP)

**Wrappers для:** systems.character_system

---

### 4. **equipment.py** (295+ рядків)
**Призначення:** Екіпірування, зброя, броня, ремонт

**Експортує (43 функції + 4 константи):**

#### Constants:
- `EQUIPMENT_SLOTS` - всі слоти (main_hand, off_hand, helmet, etc.)
- `ARMOR_SLOTS` - тільки броня (helmet, shoulders, chest, gloves, legs, boots)
- `ARMOR_TYPE_LABELS` - назви типів броні
- `ITEM_SUBTYPE_LABELS` - назви підтипів предметів

#### Utilities:
- `normalize_equipment_restriction_value(value)` - нормалізувати обмеження
- `is_armor_slot(slot)` - чи це слот броні
- `get_armor_type_label(armor_type)` - назва типу броні
- `get_item_subtype_label(item_subtype)` - назва підтипу

#### Slots:
- `ensure_equipment_slots(user_id)` - створити слоти екіпірування
- `get_all_equipped_items(user_id)` - всі екіпіровані предмети
- `get_all_equipped_slots(user_id)` - dict {slot: inventory_id}

#### Repair:
- `get_equipped_items_for_repair(user_id)` - предмети для ремонту
- `get_total_repair_cost(user_id)` - загальна вартість ремонту
- `repair_equipped_item(user_id, slot)` - полагодити предмет
- `repair_all_equipped(user_id)` - полагодити все
- `calculate_repair_cost(current_dur, max_dur, base_price)` - розрахунок вартості

#### Info:
- `get_inventory_detailed(user_id)` - детальна інвентар
- `get_inventory_entry(inventory_id)` - запис інвентаря
- `get_item_by_inventory_id(inventory_id)` - предмет за ID
- `get_item_by_inventory_id_full(inventory_id)` - повна інфо про предмет
- `get_item_bonuses(inventory_id)` - бонуси предмета
- `get_equipped_item_defenses(user_id)` - захист від екіпірування
- `get_sellable_equipment_items(user_id)` - предмети для продажу

#### Weapon Damage:
- `init_weapon_damage_system()` - ініціалізація системи шкоди
- `calculate_weapon_damage_by_values(...)` - розрахунок шкоди
- `get_weapon_damage_by_inventory_id(inv_id)` - шкода зброї
- `get_inventory_weapon_damage_display(inv_id)` - текст шкоди для відображення

#### Refine Display:
- `get_inventory_refine_level(inv_id)` - рівень покращення
- `get_inventory_refined_display_name(inv_id)` - назва з покращенням
- `format_refined_item_name(name, refine_level)` - форматування назви

#### Class Restrictions:
- `can_equip_item_by_class(class_key, item_data)` - чи може клас екіпірувати
- `can_equip_inventory_item_by_class(class_key, inv_id)` - перевірка екіпірування
- `is_inventory_item_class_compatible(user_id, inv_id)` - сумісність з класом

#### Equip/Unequip:
- `equip_inventory_item(user_id, inv_id)` - екіпірувати
- `unequip_inventory_item(user_id, slot)` - зняти
- `unequip_incompatible_items_after_class_change(user_id, new_class)` - зняти несумісне

#### Durability:
- `damage_equipped_items_on_death(user_id)` - пошкодження при смерті
- `apply_random_durability_wear_on_victory(user_id, chance=25)` - зношування після перемоги

#### Buy/Sell:
- `sell_inventory_item_to_trader(user_id, inv_id)` - продати торговцю
- `buy_common_equipment_from_trader(user_id, item_id)` - купити у торговця
- `buy_item_for_gold(user_id, item_id, quantity=1)` - купити за золото

**Wrappers для:** systems.equipment_system

---

### 5. **inventory.py** (390+ рядків)
**Призначення:** Інвентар, предмети, стеки

**Експортує (10 функцій):**

#### Capacity:
- `get_bag_capacity(user_id)` - місткість сумки
- `get_inventory_used_slots(user_id)` - зайняті слоти

#### Items:
- `get_inventory(user_id)` - весь інвентар
- `get_item(item_id)` - предмет за ID

#### Add/Consume:
- `add_item(user_id, item_id, quantity=1, **kwargs)` - додати предмет
- `consume_inventory_item(user_id, inv_id, quantity=1)` - використати предмет

#### Count:
- `count_user_item(user_id, item_id)` - порахувати предмети
- `consume_user_item_by_item_id(user_id, item_id, quantity=1)` - використати за ID
- `find_first_item_stack_by_type(user_id, item_type)` - знайти стек

#### Trash:
- `sell_all_trash(user_id)` - продати весь мотлох (повертає gold та slots)

**Real DB logic** - прямі SQL запити до inventory table

---

### 6. **location.py** (60 рядків)
**Призначення:** Локації та переміщення

**Експортує (4 функції):**
- `get_current_location(user_id)` - поточна локація
- `set_current_location(user_id, location)` - встановити локацію
- `is_user_in_city(user_id)` - чи в місті
- `get_location_display_name(location)` - назва локації

**Real DB logic** - управління location в users table

---

### 7. **utils.py** (75 рядків)
**Призначення:** Утиліти, форматування

**Експортує (2 функції):**
- `format_gold(amount)` - форматування золота з емоджі
- `format_number(num)` - форматування чисел з розділювачами

**Utility functions** - допоміжні функції форматування

---

### 8. **migrations.py** (180 рядків)
**Призначення:** Міграції БД, версіонування

**Експортує (6 функцій):**
- `expand_bag_slots_to_40(user_id)` - розширити сумку до 40
- `seed_location_trash_items(location, item_ids)` - додати мотлох в локацію
- `init_migration_system()` - ініціалізація системи міграцій
- `run_pending_migrations()` - запустити міграції
- `get_migration_status()` - статус міграцій
- `run_db_startup_maintenance()` - обслуговування БД при старті

**Real DB logic** - управління версіями та міграціями

---

### 9. **refine.py** (278 рядків)
**Призначення:** Система покращення/заточки

**Експортує (11 функцій + 2 константи):**

#### Constants:
- `REFINE_STONE_ITEM_ID` = 1001 - камінь заточки
- `SUCCESS_RUNE_ITEM_ID` = 1002 - руна успіху

#### Init:
- `init_refine_system()` - ініціалізація
- `seed_refine_items()` - додати предмети заточки

#### Refine:
- `get_inventory_item_refine_info(inv_id)` - інфо про заточку
- `set_inventory_refine_level(inv_id, level)` - встановити рівень

#### Resources:
- `get_refine_resource_counts(user_id)` - кількість ресурсів

#### Effects:
- `get_refine_total_armor_hp_bonus_percent(user_id)` - бонус HP від заточки
- `get_refine_effects_summary_for_user(user_id)` - зведення ефектів
- `get_inventory_refine_display_line(inv_id)` - рядок відображення

#### Maintenance:
- `ensure_refine_material_stack_sizes()` - перевірка розмірів стеків
- `get_refine_material_stack_debug()` - відладка матеріалів

**Real DB logic** - управління refine_level в inventory

---

### 10. **quests.py** (280+ рядків)
**Призначення:** Щоденні завдання

**Експортує (7 функцій):**

#### Init:
- `init_daily_quest_system()` - ініціалізація

#### Quests:
- `get_user_daily_quest(user_id)` - завдання користувача
- `add_daily_quest_progress(user_id, amount=1)` - додати прогрес

#### Status:
- `is_daily_quest_complete(user_id)` - чи виконано
- `claim_daily_quest_reward(user_id)` - забрати нагороду
- `get_daily_quest_progress_text(user_id)` - текст прогресу

#### Maintenance:
- `cleanup_old_daily_quests(days_to_keep=7)` - очистка старих

#### Combat Integration:
- `process_daily_quest_progress_on_kill(user_id, mob=None)` - прогрес при вбивстві

**Real DB logic** - управління user_daily_quests table

---

### 11. **shop.py** (680+ рядків)
**Призначення:** Магазин, обмеження класів, превью

**Експортує (20+ функцій):**

#### Prices:
- `get_common_equipment_price_for_slot(slot)` - ціна за слот

#### Class Restrictions:
- `get_allowed_main_hand_subtypes_for_class(class_key)` - дозволені типи головної руки
- `get_allowed_off_hand_subtypes_for_class(class_key)` - дозволені типи другої руки
- `get_allowed_shop_main_hand_profiles(class_key)` - профілі головної руки
- `get_allowed_shop_off_hand_profiles(class_key)` - профілі другої руки

#### Shop Offers:
- `get_common_equipment_shop_offer(user_id)` - пропозиція магазину
- `get_common_equipment_shop_suboffers(user_id, slot)` - підпропозиції

#### Preview System:
- `create_common_equipment_shop_preview(user_id, slot, offer_index)` - створити превью
- `get_shop_preview_item(user_id)` - отримати превью
- `get_shop_preview_weapon_damage_text(user_id)` - текст шкоди зброї
- `confirm_common_equipment_shop_preview(user_id)` - підтвердити покупку
- `cancel_common_equipment_shop_preview(user_id)` - скасувати

#### Preview Management:
- `cleanup_shop_previews_for_user(user_id)` - очистити превью
- `is_shop_profile_allowed_for_user(user_id, profile)` - чи дозволений профіль
- `init_shop_preview_system()` - ініціалізація
- `get_shop_preview_items(user_id)` - всі превью
- `get_shop_preview_item_by_id(preview_id)` - превью за ID
- `purchase_shop_preview_item(user_id, preview_id)` - купити
- `clear_shop_preview_items(user_id)` - очистити

#### Class Reset Sphere:
- `init_class_reset_sphere()` - ініціалізація сфери скидання класу
- `use_class_reset_sphere(user_id)` - використати сферу

#### Equipment Generation:
- `can_class_equip_item(class_key, item)` - перевірка екіпірування
- `get_equippable_class_items(class_key, slot)` - предмети для класу
- `generate_class_shop_equipment(class_key, slot, rarity)` - генерувати екіпірування
- `populate_class_shop_for_user(user_id)` - наповнити магазин

**Mix:** Real DB logic + imports from data.equipment_profiles

---

### 12. **systems_wrappers.py** (980+ рядків)
**Призначення:** Обгортки для всіх systems/*

**Експортує (~200+ функцій) для:**

#### Energy System (6 функцій):
- init_energy_system, get_user_energy, consume_energy_for_hunt
- restore_energy_for_test, get_users_for_energy_full_notification
- reset_daily_hunts_if_needed

#### Regen System (5 функцій):
- init_hp_regen_system, init_passive_regen_system
- process_passive_regeneration, reset_hp_regen_timers_now
- apply_passive_hp_regen

#### Guild System (~80 функцій):
- init_guild_system, create_guild, get_guild_by_name
- add_guild_member, remove_guild_member, set_guild_role
- get_user_guild, get_user_guild_profile, get_user_guild_profile_line
- guild_bank_*, guild_upgrade_*, guild_battle_*
- (багато функцій для гільдій)

#### Auction System (~60 функцій):
- init_auction_system, create_auction_listing
- get_auction_listings, place_bid, buy_now
- cancel_auction, expire_auctions, process_auction_completion
- (багато функцій для аукціону)

#### Rune System (~30 функцій):
- init_rune_system, get_user_runes, activate_rune
- deactivate_rune, upgrade_rune, combine_runes
- (функції для рун)

#### Contract System (4 функції):
- init_contract_system, get_contract_status
- claim_contract_reward, process_contract_progress_on_kill

#### Player Interaction (~50 функцій):
- init_player_interaction_foundation
- touch_player_activity, get_player_last_activity
- is_player_online, acquire_player_activity_session
- create_player_interaction_request, accept_request
- (багато функцій для взаємодії гравців)

**Pure wrappers** - всі функції викликають systems/*

---

### 13. **__init__.py** (355+ рядків)
**Призначення:** Центральна точка експорту

**Структура:**
```python
# Imports (рядки 1-140)
from .connection import ...
from .player import ...
from .character import ...
from .equipment import ...
from .inventory import ...
from .location import ...
from .utils import ...
from .migrations import ...
from .refine import ...
from .quests import ...
from .shop import ...
from .systems_wrappers import *

# __all__ list (рядки 141-355+)
__all__ = [
    # Connection (6)
    # Player (20)
    # Character (21 + 1 const)
    # Equipment (43 + 4 const)
    # Inventory (10)
    # Location (4)
    # Utils (2)
    # Migrations (6)
    # Refine (11 + 2 const)
    # Quests (7)
    # Shop (20+)
    # Systems (~200+)
]
```

**Роль:** Агрегує всі експорти з модулів

---

## 📊 Загальна Статистика

| Модуль | Рядків | Функцій | Тип |
|--------|--------|---------|-----|
| connection.py | 216 | 6 | Real DB |
| player.py | 305+ | 20 | Mixed |
| character.py | 190+ | 21+1 | Wrappers |
| equipment.py | 295+ | 43+4 | Mixed |
| inventory.py | 390+ | 10 | Real DB |
| location.py | 60 | 4 | Real DB |
| utils.py | 75 | 2 | Utilities |
| migrations.py | 180 | 6 | Real DB |
| refine.py | 278 | 11+2 | Real DB |
| quests.py | 280+ | 7 | Real DB |
| shop.py | 680+ | 20+ | Mixed |
| systems_wrappers.py | 980+ | 200+ | Wrappers |
| __init__.py | 355+ | - | Aggregator |
| **ВСЬОГО** | **~3,500+** | **330+** | - |

---

## 🎯 Типи Коду

### Real DB Logic (SQL запити):
- connection, inventory, location, migrations, refine, quests
- Прямо працюють з conn, cursor

### Wrappers (обгортки):
- character, systems_wrappers
- Викликають функції з systems/*

### Mixed (змішані):
- player, equipment, shop
- Частина SQL, частина wrappers

### Utilities:
- utils
- Допоміжні функції

### Aggregator:
- __init__.py
- Збирає всі експорти

---

**Створено:** 2026-08-17  
**Статус:** Актуально
