# ROM 10.1.0 — Аудит архітектури системи рун

Згенеровано: `2026-07-30T14:57:21`

## Підсумкове рішення

**Систему рун можна впроваджувати на поточному baseline 9.0.13o без попереднього рефакторингу.**

Рекомендована архітектура: окремий `systems/rune_system.py`, канонічні rune constants у `data/runes.py`, нормалізована таблиця `inventory_runes`, stackable rune/token/extractor items у `items` та `inventory`, UI через `handlers/runes.py`, а `db.py` залишається тонким compatibility facade.

## Безпека аудиту

- Gameplay-файли змінено: **0**
- Рядки реальної БД змінено: **0**
- SQLite `PRAGMA quick_check`: **ok**
- Логічний snapshot БД незмінний: **True**
- SHA/size/mtime файла БД незмінні: **True**
- БД відкрито через `mode=ro` та `PRAGMA query_only=ON`.

## Затверджені бізнес-правила

- Характеристики: `['STR', 'STA', 'DEX', 'INT', 'WIS']`.
- Рівні: `[1, 2, 3, 4, 5]`; бонус дорівнює рівню, тобто I=+1 … V=+5.
- Кількість rune item definitions: **25**.
- Rune slot map: `{'main_hand': 2, 'off_hand': 1, 'helmet': 1, 'shoulders': 1, 'chest': 3, 'gloves': 1, 'legs': 2, 'boots': 1, 'necklace': 1, 'ring': 1}`.
- Загальна кількість слотів на повному комплекті: **14**.
- Fusion: `3 однакові руни того самого stat/level + 1 Жетон Фіріуса → 1 руна наступного рівня`.
- Fusion success: **100%**.
- Rune V не може бути fusion source.
- Жорсткого денного fusion-ліміту немає.
- За успішний claim щоденного завдання: **10 Жетонів Фіріуса**.
- Жетони накопичуються і не мають daily reset.
- Один успішний fusion витрачає рівно 1 жетон.
- Простий екстрактор повертає одну випадкову вставлену руну та знищує equipment.
- Досконалий екстрактор повертає всі вставлені руни та знищує equipment.

## Поточна схема, важлива для рун

- `items` columns: `['id', 'name', 'type', 'rarity', 'category', 'slot_key', 'weapon_hands', 'max_stack', 'sell_price', 'bonus_str', 'bonus_dex', 'bonus_int', 'bonus_wis', 'bonus_sta', 'pdef', 'mdef', 'item_level', 'is_generated', 'item_subtype', 'weapon_min_damage', 'weapon_max_damage', 'weapon_min_magic_damage', 'weapon_max_magic_damage', 'weapon_attack_type', 'shop_preview_owner', 'shop_preview_price', 'armor_type']`
- `inventory` columns: `['id', 'user_id', 'item_id', 'quantity', 'durability', 'refine_level']`
- `equipment_slots` columns: `['user_id', 'slot_key', 'inventory_id']`
- `users` columns relevant to stats/progression: `['user_id', 'hp', 'max_hp', 'level', 'current_location', 'str', 'dex', 'wis', 'sta', 'mp', 'max_mp']`

### Висновок щодо зберігання

Рекомендована таблиця: `inventory_runes`.

```text
id INTEGER PRIMARY KEY AUTOINCREMENT
inventory_id INTEGER NOT NULL
slot_index INTEGER NOT NULL
rune_item_id INTEGER NOT NULL
rune_stat TEXT NOT NULL
rune_level INTEGER NOT NULL
inserted_at TEXT NOT NULL
UNIQUE(inventory_id, slot_index)
FOREIGN KEY(inventory_id) REFERENCES inventory(id) ON DELETE CASCADE
```

- Руни належать конкретному inventory-екземпляру, а не шаблону items.
- Нормалізовані рядки простіше перевіряти, індексувати й переносити в Auction snapshot.
- JSON-поле у inventory ускладнить точкові constraints, пошук, міграції та атомарне вилучення.
- UNIQUE(inventory_id, slot_index) фізично забороняє дві руни в одному слоті.
- Каскадне видалення очищає sockets при законному знищенні equipment; extraction спершу повертає руни, потім видаляє предмет у транзакції.

Не рекомендується додавати `rune_slots` JSON у `items`, оскільки кількість слотів є правилом `slot_key`, а не властивістю кожного generated item template. Не рекомендується зберігати вставлені руни в `items`, бо generated item може мати власника, Auction snapshot і окремий inventory lifecycle.

## Запропонований namespace предметів

Запропоновано зарезервувати безперервний діапазон `501–528`:

- `501–525`: 25 рун, п’ять stats × п’ять рівнів.
- `526`: `firius_token`.
- `527`: `rune_extractor`.
- `528`: `rune_extractor_perfect`.

- Конфлікти запропонованих ID у поточній БД: `[]`
- Найбільший поточний статичний item ID: `447`
- Поточні предмети з rune-подібними назвами/типами: `[(402, '💎 Руна Успіху', 'success_rune', 'material', 999)]`

Якщо `proposed_conflicts` порожній, 10.2.0 може офіційно закріпити цей namespace. ID 402, Руна Успіху, залишається матеріалом заточки й не належить новій socket-rune системі.

## Нагорода щоденного завдання

- `db.py.claim_daily_quest_reward` definitions: `[(2131, ['user_id'])]`
- `systems.reward_system.claim_daily_quest_reward` definitions: `[]`
- Mutation markers у claim flow: `{'INSERT ': 0, 'UPDATE ': 1, 'DELETE ': 0, 'COMMIT': 1, 'ROLLBACK': 0}`

Жетони слід додавати лише всередині успішної транзакції claim, після перевірки completed/reward_claimed та перед commit. Якщо додавання жетонів не може завершитися через capacity або іншу помилку, вся нагорода має rollback. Повторний claim не повинен видавати жетони.

## Інтеграція зі статами

- `systems.player_system.get_player_stats`: `[(54, ['user_id']), (606, ['user_id'])]`
- `systems.equipment_system.get_item_bonuses`: `[(65, []), (369, ['user_id'])]`
- `systems.equipment_system.get_all_equipped_items`: `[(47, []), (337, ['user_id']), (434, ['user_id']), (461, ['user_id']), (557, ['user_id'])]`

Рекомендована точка інтеграції: `rune_system.get_equipped_rune_stat_totals(user_id)` повертає dict `{str, sta, dex, int, wis}`. `player_system.get_player_stats()` додає цей dict один раз після equipment bonuses. Це автоматично впливає на ATK, magic ATK, Max HP, PDEF, MDEF, crit, MP та regen через наявні похідні формули.

Після вставки або вилучення руни STA/WIS/INT потрібно викликати наявні sync helpers Max HP/MP. Current HP/MP clamp до нового максимуму, але вставка не повинна безкоштовно лікувати до повного.

## Інтеграція з Auction House

- Auction tables: `['auction_history', 'auction_lots']`
- Auction columns: `{'auction_history': ['id', 'lot_id', 'event_type', 'actor_user_id', 'seller_user_id', 'buyer_user_id', 'item_name', 'category', 'quantity', 'price', 'status_before', 'status_after', 'details_json', 'created_at'], 'auction_lots': ['id', 'seller_user_id', 'buyer_user_id', 'item_type', 'item_source', 'item_ref_id', 'item_snapshot_json', 'item_name', 'item_name_norm', 'category', 'rarity', 'level', 'enhancement_level', 'durability_current', 'durability_max', 'quantity', 'price', 'status', 'created_at', 'expires_at', 'sold_at', 'claimed_at', 'delete_after', 'updated_at']}`
- Snapshot function: `[(933, ['user_id', 'inventory_id'])]`
- Buy function: `[(4176, ['buyer_user_id', 'lot_id'])]`

Auction snapshot має отримати `runes_snapshot` як стабільний JSON-масив або окремі snapshot rows. Для поточної архітектури найменш ризиковий варіант: JSON у lot snapshot, бо Auction уже заморожує item instance. Під час listing живі `inventory_runes` мають бути перенесені/зарезервовані разом з item; під час cancel/expire/buy вони відновлюються для нового inventory instance. Лот не повинен залежати від видаленого seller inventory_id.

Rune items і Жетони Фіріуса можна продавати як stack items лише після окремого рішення. На першому етапі рекомендується заборонити Auction для жетонів та екстракторів; rune items дозволити пізніше окремим балансним патчем.

## Рунний Майстер і UI

- City top-level functions: `['_city_find_sellable_name_index', '_city_get_refined_name_v2', '_city_refine_display_for_row', '_city_refine_display_for_sell_row_v2', '_city_string_looks_like_item_name_v2', '_normalize_text_kb_result', 'back_to_city', 'back_to_craft_district_message', 'back_to_guild_district_message', 'back_to_main', 'back_to_trade_district', 'back_to_trade_district_message', 'back_to_trader_callback', 'blacksmith_repair_button_v2', 'build_alchemist_catalog', 'build_blacksmith_repair_text', 'build_blacksmith_text', 'build_city_text', 'build_common_equipment_shop_text', 'build_common_equipment_slot_choice_text', 'build_common_shop_preview_text', 'build_contracts_short_status', 'build_craft_district_text', 'build_guild_district_text', 'build_main_menu_text', 'build_sell_equipment_confirm_text', 'build_sell_equipment_list_text', 'build_shop_preview_display_name', 'build_tavern_text', 'build_townhall_text', 'build_trade_district_text', 'buy_potion', 'cancel_common_shop_purchase', 'common_equipment_back_to_slots', 'common_equipment_slot_choice', 'confirm_common_shop_purchase', 'format_shop_preview_bonuses', 'get_item_by_inventory_id_full', 'get_nearby_mobs_for_level', 'get_sellable_equipment_items', 'look_around', 'preview_common_equipment', 'register_blacksmith_repair_button_v2', 'register_city_handlers', 'repair_all', 'repair_one', 'sell_equipment_confirm', 'sell_equipment_do', 'sell_equipment_page', 'sell_trash', 'show_alchemist', 'show_blacksmith', 'show_city', 'show_common_equipment_shop', 'show_craft_district', 'show_guild_district', 'show_sell_equipment', 'show_tavern', 'show_townhall', 'show_trade_district']`
- Inventory top-level functions: `['_inject_refine_material_description', 'build_category_list', 'build_equipped_comparison_text', 'build_inventory_home', 'build_item_allowed_classes_text', 'build_item_button_label', 'build_item_details', 'build_item_display_name', 'equip_callback', 'format_item_bonuses', 'get_category_count', 'get_category_items', 'get_inventory_full_items', 'get_player_level', 'get_refine_material_description_text', 'get_slot_label', 'inventory_category_callback', 'inventory_home_callback', 'item_details_callback', 'register_inventory_handlers', 'show_inventory', 'unequip_callback', 'use_potion_callback']`
- DEV top-level functions: `['dev_armor', 'dev_help', 'dev_weapon', 'generate_drop', 'give_class_reset_sphere', 'give_item', 'my_id', 'progress', 'register_dev_handlers', 'reset_hero', 'reset_level', 'set_energy', 'set_gold', 'set_level']`

Рекомендовані нові файли:

- `data/runes.py`: stats, levels, item IDs, names, bonuses, slot limits, token/extractor IDs.
- `systems/rune_system.py`: schema, reads, insertion, fusion, extraction, stat totals, transactions.
- `handlers/runes.py`: Рунний Майстер, callback state machine, підтвердження та UI.
- `tools/smoke_test_rune_*.py`: ізольовані contracts.

Рунного Майстра слід додати в уже реалізований Ремісничий квартал, без створення паралельного меню. Callback namespace: `rune:*`, з короткими payload та server-side повторною перевіркою ownership/state.

## Атомарні операції

### Вставка

1. `BEGIN IMMEDIATE`.
2. Перевірити ownership equipment inventory_id та що item є equipment.
3. Заборонити preview/Auction-reserved/відсутній item.
4. Визначити slot limit за `slot_key`.
5. Перевірити вільний socket index.
6. Перевірити ownership rune stack і валідність rune item.
7. Списати 1 rune item.
8. Додати `inventory_runes` row.
9. Commit; після commit синхронізувати похідні HP/MP.

### Fusion

1. `BEGIN IMMEDIATE`.
2. Перевірити rune level < V.
3. Перерахувати 3 rune items та 1 token без довіри до callback.
4. Перевірити capacity для result stack з урахуванням того, що source stacks зменшаться.
5. Списати 3 руни та 1 token.
6. Додати 1 rune наступного рівня.
7. Commit. При будь-якій помилці rollback без часткового списання.

### Extraction

1. Заборонити extraction equipped item до явного unequip або виконати контрольоване unequip у транзакції. Рекомендація: вимагати, щоб предмет був знятий.
2. Перевірити ownership, rune count, extractor та bag capacity.
3. Простий: cryptographically не потрібно, достатньо `random.choice`, повернути одну rune item.
4. Досконалий: повернути всі rune items.
5. Списати 1 extractor.
6. Видалити equipment inventory row; CASCADE видалить socket rows.
7. Commit; rollback при будь-якій помилці.

## Взаємодія із заточкою, ремонтом і продажем

- `refine_level` та руни незалежні й належать одному inventory instance.
- Вставка/вилучення не змінює refine level, durability, rarity або item level.
- Durability=0 вимикає весь equipment contribution, включно з rune bonuses, бо предмет не дає бонусів.
- Trader sale та item deletion повинні каскадно видаляти socket rows; продаж предмета з рунами має бути заблокований або вимагати явне підтвердження втрати рун. Рекомендація 10.x: блокувати звичайний продаж предметів із рунами.
- Repair cost не залежить від рун.
- Rune slot count залежить лише від equipment slot_key, а не rarity або refine level.

## Міграційна стратегія

10.2.0 має створити `data/runes.py`, `systems/rune_system.py`, таблицю `inventory_runes`, індекси та seed items 501–528 через versioned migration/explicit init. Існуючі inventory rows не потребують backfill: відсутність rows означає 0 вставлених рун.

Рекомендовані індекси:

```text
UNIQUE inventory_runes(inventory_id, slot_index)
INDEX inventory_runes_inventory_id(inventory_id)
INDEX inventory_runes_rune_item_id(rune_item_id)
```

## Виявлені точки та залишкові назви

- `claim_daily_quest_reward`: `['db.py:2131', 'handlers/daily.py:5', 'handlers/daily.py:86', 'tools/audit_rune_system_architecture.py:248', 'tools/audit_rune_system_architecture.py:249', 'tools/audit_rune_system_architecture.py:269', 'tools/audit_rune_system_architecture.py:385', 'tools/audit_rune_system_architecture.py:386']`
- `craft`: `['keyboards.py:63', 'handlers/city.py:49', 'handlers/city.py:107', 'handlers/city.py:966', 'handlers/city.py:971', 'handlers/city.py:972', 'handlers/city.py:1016', 'handlers/city.py:1021', 'handlers/city.py:1022', 'handlers/city.py:1304', 'handlers/city.py:1366', 'systems/auction_house_system.py:1347', 'systems/notifications.py:479', 'systems/notifications.py:482', 'systems/notifications.py:502', 'tools/audit_rune_system_architecture.py:270']`
- `firius`: `['tools/audit_rune_system_architecture.py:7', 'tools/audit_rune_system_architecture.py:64', 'tools/audit_rune_system_architecture.py:264', 'tools/audit_rune_system_architecture.py:373', 'tools/audit_rune_system_architecture.py:521', 'tools/audit_rune_system_architecture.py:522', 'tools/audit_rune_system_architecture.py:527', 'tools/audit_rune_system_architecture.py:547']`
- `installed_rune`: `['tools/audit_rune_system_architecture.py:267']`
- `refine_level`: `['db.py:5722', 'db.py:5774', 'db.py:5789', 'db.py:5801', 'db.py:5804', 'db.py:5806', 'db.py:5807', 'db.py:5808', 'db.py:5810', 'db.py:5859', 'db.py:5860', 'db.py:5910', 'db.py:5922', 'db.py:5925', 'db.py:5927', 'db.py:5929', 'db.py:5934', 'db.py:5944', 'db.py:5974', 'db.py:5980', 'db.py:5986', 'db.py:6008', 'db.py:6019', 'db.py:6077', 'db.py:6081', 'db.py:6083', 'db.py:6085', 'db.py:6113', 'db.py:6119', 'db.py:6136', 'db.py:6147', 'db.py:6220', 'db.py:6222', 'db.py:6225', 'db.py:6227', 'db.py:6229', 'db.py:6232', 'db.py:7506', 'db.py:7507', 'handlers/refine.py:80', 'handlers/refine.py:160', 'handlers/refine.py:197', 'handlers/refine.py:231', 'handlers/refine.py:299', 'handlers/refine.py:300', 'systems/auction_house_system.py:770', 'systems/auction_house_system.py:857', 'systems/auction_house_system.py:859', 'systems/auction_house_system.py:861', 'systems/auction_house_system.py:863', 'systems/auction_house_system.py:866', 'systems/auction_house_system.py:951', 'systems/auction_house_system.py:953', 'systems/auction_house_system.py:967', 'systems/auction_house_system.py:1059', 'systems/auction_house_system.py:1140', 'systems/auction_house_system.py:1270', 'systems/auction_house_system.py:1815', 'systems/auction_house_system.py:1816', 'systems/auction_house_system.py:2276', 'systems/auction_house_system.py:2296', 'systems/auction_house_system.py:2297', 'systems/auction_house_system.py:2461', 'systems/auction_house_system.py:2570', 'systems/auction_house_system.py:2590', 'systems/auction_house_system.py:2591', 'systems/auction_house_system.py:2884', 'systems/auction_house_system.py:2928', 'systems/auction_house_system.py:2930', 'systems/auction_house_system.py:2984', 'systems/auction_house_system.py:3025', 'systems/auction_house_system.py:3027', 'systems/auction_house_system.py:3158', 'systems/auction_house_system.py:3168', 'systems/auction_house_system.py:3169', 'systems/auction_house_system.py:3377', 'systems/auction_house_system.py:3387', 'systems/auction_house_system.py:3388', 'systems/auction_house_system.py:3601', 'systems/auction_house_system.py:3611', 'systems/auction_house_system.py:3612', 'systems/auction_house_system.py:3842', 'systems/auction_house_system.py:3852', 'systems/auction_house_system.py:3853', 'systems/auction_house_system.py:3926', 'systems/auction_house_system.py:3936', 'systems/auction_house_system.py:3937', 'systems/auction_house_system.py:4113', 'systems/auction_house_system.py:4130', 'systems/auction_house_system.py:4131', 'systems/equipment_system.py:86', 'systems/equipment_system.py:87', 'systems/equipment_system.py:392', 'systems/equipment_system.py:481', 'systems/equipment_system.py:482', 'systems/equipment_system.py:507', 'systems/equipment_system.py:526', 'systems/equipment_system.py:581', 'systems/equipment_system.py:610', 'systems/equipment_system.py:629', 'systems/equipment_system.py:637', 'systems/equipment_system.py:660', 'systems/equipment_system.py:686', 'systems/equipment_system.py:689', 'systems/equipment_system.py:705', 'systems/equipment_system.py:708', 'systems/equipment_system.py:714', 'systems/equipment_system.py:715', 'systems/equipment_system.py:728', 'systems/equipment_system.py:737', 'systems/equipment_system.py:747', 'systems/equipment_system.py:757', 'systems/equipment_system.py:908', 'systems/equipment_system.py:911', 'systems/equipment_system.py:926', 'systems/equipment_system.py:936', 'systems/equipment_system.py:950', 'systems/equipment_system.py:965', 'systems/equipment_system.py:1082', 'systems/equipment_system.py:1092', 'systems/equipment_system.py:1358', 'systems/equipment_system.py:1417', 'systems/equipment_system.py:1435', 'systems/equipment_system.py:1455', 'systems/equipment_system.py:1839', 'systems/equipment_system.py:1848', 'systems/equipment_system.py:1884', 'systems/equipment_system.py:1932', 'systems/notifications.py:556', 'systems/notifications.py:611', 'systems/notifications.py:620', 'systems/notifications.py:634', 'systems/notifications.py:639', 'systems/notifications.py:645', 'systems/player_system.py:641', 'systems/player_system.py:654', 'systems/player_system.py:659', 'systems/refine_system.py:10', 'systems/refine_system.py:11', 'systems/refine_system.py:21', 'systems/refine_system.py:46', 'systems/refine_system.py:48', 'systems/refine_system.py:53', 'systems/refine_system.py:62', 'systems/refine_system.py:70', 'systems/refine_system.py:71', 'systems/refine_system.py:72', 'systems/refine_system.py:75', 'systems/refine_system.py:76', 'systems/refine_system.py:80', 'systems/refine_system.py:81', 'systems/refine_system.py:83', 'systems/refine_system.py:88', 'systems/refine_system.py:89', 'systems/refine_system.py:90', 'systems/refine_system.py:97', 'systems/refine_system.py:113', 'systems/refine_system.py:135', 'systems/refine_system.py:138', 'tools/audit_equipment_readonly_duplicates.py:18', 'tools/audit_equipment_readonly_duplicates.py:84', 'tools/audit_rune_system_architecture.py:268', 'tools/audit_rune_system_architecture.py:463', 'tools/smoke_test_inventory_refine_contracts.py:42', 'tools/smoke_test_inventory_refine_contracts.py:44', 'tools/smoke_test_inventory_refine_contracts.py:47', 'tools/smoke_test_inventory_refine_contracts.py:48', 'tools/smoke_test_inventory_refine_contracts.py:49', 'tools/smoke_test_inventory_refine_contracts.py:50', 'tools/smoke_test_inventory_refine_contracts.py:51', 'tools/smoke_test_inventory_refine_contracts.py:55', 'tools/smoke_test_weapon_damage_contracts.py:38', 'tools/smoke_test_weapon_damage_contracts.py:66', 'tools/smoke_test_weapon_damage_contracts.py:72']`
- `rune_slots`: `['tools/audit_rune_system_architecture.py:262', 'tools/audit_rune_system_architecture.py:366', 'tools/audit_rune_system_architecture.py:524']`
- `rune_system`: `['tools/audit_rune_system_architecture.py:23', 'tools/audit_rune_system_architecture.py:266', 'tools/audit_rune_system_architecture.py:319', 'tools/audit_rune_system_architecture.py:397', 'tools/audit_rune_system_architecture.py:421', 'tools/audit_rune_system_architecture.py:472', 'tools/audit_rune_system_architecture.py:531']`
- `socket`: `['tools/audit_rune_system_architecture.py:7', 'tools/audit_rune_system_architecture.py:263', 'tools/audit_rune_system_architecture.py:304', 'tools/audit_rune_system_architecture.py:381', 'tools/audit_rune_system_architecture.py:435', 'tools/audit_rune_system_architecture.py:458', 'tools/audit_rune_system_architecture.py:466', 'tools/audit_rune_system_architecture.py:489', 'tools/audit_rune_system_architecture.py:497', 'tools/audit_rune_system_architecture.py:505', 'tools/audit_rune_system_architecture.py:511', 'tools/audit_rune_system_architecture.py:516', 'tools/audit_rune_system_architecture.py:535']`
- `жетон фіріуса`: `['tools/audit_rune_system_architecture.py:265', 'tools/audit_rune_system_architecture.py:337']`

`Руна Успіху` у Refine System є окремим матеріалом. Назви нових socket runes повинні мати item types на кшталт `rune_str_1`, щоб не конфліктувати з `success_rune`.

## План smoke-тестів

- Schema init idempotency та відсутність змін existing equipment.
- 25 rune definitions, token, два extractors, унікальні IDs/types.
- Stack add/consume для rune/token items.
- Slot limits для всіх 10 equipment slots, загалом 14.
- Ownership, forged callback, full sockets, non-equipment rejection.
- Stat totals тільки з equipped, unbroken equipment.
- STA/INT/WIS sync для Max HP/MP без безкоштовного full heal.
- Fusion exact 3+1→1, level V rejection, insufficient source/token, rollback.
- Daily claim видає рівно 10 tokens один раз.
- Simple extractor повертає рівно одну rune, знищує item/extractor.
- Perfect extractor повертає всі runes, знищує item/extractor.
- Auction listing/buy/cancel/expire з rune snapshot без втрат/дублів.
- Trader protection для socketed equipment.
- Existing Refine, Equipment, Character, Player Stats, Daily, Auction contracts залишаються green.
- Logical real-DB snapshot незмінний для read-only audits.

## Ризики

1. **Auction inventory_id lifecycle:** високий ризик втрати socket rows, якщо snapshot не розширити до дозволу listing socketed items.
2. **Подвійне нарахування stats:** rune totals слід додавати лише в одному canonical місці.
3. **HP/MP synchronization:** зменшення rune bonuses має clamp current values без heal-to-full.
4. **Bag capacity:** fusion/extraction повинні рахувати майбутні stack slots всередині транзакції.
5. **Item ID namespace:** 501–528 треба остаточно перевіряти при кожному seed/migration і не використовувати повторно.
6. **Назва «руна»:** не змішувати socket runes з Refine `success_rune` ID 402.
7. **Concurrency:** усі mutation flows виконувати через `BEGIN IMMEDIATE` та повторну перевірку стану.

## Рекомендована послідовність версії 10

1. `patch_10_2_0_rune_and_firius_token_data_model.py`
2. `patch_10_3_0_daily_quest_firius_token_reward.py`
3. `patch_10_4_0_rune_inventory_items_and_dev_commands.py`
4. `patch_10_5_0_equipment_rune_slots.py`
5. `patch_10_6_0_rune_master_and_insertion.py`
6. `patch_10_7_0_rune_character_stat_bonuses.py`
7. `patch_10_8_0_rune_fusion_with_firius_tokens.py`
8. `patch_10_9_0_simple_rune_extractor.py`
9. `patch_10_10_0_perfect_rune_extractor.py`
10. `patch_10_11_0_rune_drops_and_balance.py`
11. `patch_10_12_0_rune_system_final_closure_audit.py`

## Висновок

Першим mutation-патчем має бути 10.2.0. Він повинен створити лише фундамент: canonical data, schema, seed items, read APIs та tests. Daily reward, sockets UI, stat effects, fusion, extraction, drops та Auction support слід підключати окремими версіями, щоб кожен ризик був ізольований і мав rollback.
