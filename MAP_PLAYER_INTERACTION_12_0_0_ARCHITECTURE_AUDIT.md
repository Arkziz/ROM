# Stage 12.0.0: Map Player Interaction Architecture Audit

## 1. Статус

- Версія: `12.0.0`
- Режим: **read-only architecture audit**
- Gameplay-файли змінено: **0**
- `game.db` змінено: **ні**
- Синтаксичних помилок у перевірених Python-файлах: **0**
- SQLite quick check: **ok**
- Foreign-key issues: **0**

## 2. Затверджений продуктний напрямок

Точка входу:

```text
Мапа
→ Гравці локації
→ вибір онлайн-гравця з тієї самої локації
→ Запропонувати обмін / Викликати на дуель / Назад
```

Stage 12 реалізує прямий обмін і спільний фундамент player interaction. Кнопка дуелі та історія дуелей закладаються архітектурно, але PvP-бій не входить у Stage 12.

## 3. Presence і зайнятість

### 3.1 Presence

Рекомендовано додати до `users`:

```text
last_activity_at TEXT NULL
```

Канонічні параметри:

```text
online timeout: 300 секунд
heartbeat write throttle: 30 секунд
```

Гравець вважається онлайн, якщо `last_activity_at >= now - 5 minutes`.

### 3.2 Persistent activity sessions

Для trade та майбутнього PvP рекомендується окрема таблиця `player_activity_sessions`, а не process-memory state. Це забезпечує recovery після restart, timeout cleanup та взаємне блокування trade/duel.

Типи:

- `trade_request`
- `trade`
- `duel_request`
- `pvp_battle`

PvE-бій не дублюється в цій таблиці. Availability resolver повинен перевіряти одночасно наявний PvE battle state та `player_activity_sessions`.

## 4. Поточна Map-архітектура

Виявлені функції `handlers/map.py`:

- `back_to_main_from_map`
- `build_location_info_text`
- `build_world_map_text`
- `get_player_level_from_stats`
- `register_map_handlers`
- `show_map`
- `show_map_from_city`
- `travel_dark_forest`
- `travel_start_path`

Поточні сигнали location у БД:

- `current_location`

Потрібний API Stage 12:

```text
touch_player_activity(user_id)
is_player_online(user_id, now=None)
get_online_players_in_same_location(user_id, page=0, page_size=8)
get_public_player_interaction_profile(viewer_id, target_id)
check_player_interaction_availability(user_a, user_b, request_type)
```

Список повинен виключати самого користувача, offline-гравців, незареєстрованих персонажів та всіх з іншої локації.

## 5. Поточна бойова зайнятість

Battle-related tables:

- не знайдено

Виявлені функції `handlers/combat.py`:

- `__init__`
- `_combat_callback_allowed_11_3_1`
- `_combat_extract_retry_after_11_3_1`
- `_combat_message_allowed_11_3_1`
- `_install_combat_safe_send_11_3_1`
- `add_enemy_effect`
- `add_player_effect`
- `add_rage_for_damage_taken`
- `add_rage_for_player_attack`
- `add_rogue_combo_point`
- `append_effects_to_combat_text`
- `append_mp_restore_text`
- `apply_extra_rage_from_skill`
- `apply_player_shield_absorb`
- `apply_skill_special_effect`
- `attack`
- `build_combat_potion_kb`
- `build_death_text`
- `build_skill_menu_text`
- `build_victory_text`
- `choose_potion_in_combat`
- `combat_attack_callback`
- `combat_back`
- `combat_flee_callback`
- `combat_placeholder`
- `combat_potion_callback`
- `combat_skill_locked_callback`
- `combat_use_skill_callback`
- `consume_rogue_combo_points`
- `escape`
- `escape_no`
- `escape_yes`
- `finalize_combat_state_before_victory`
- `format_combat_turns_uk`
- `get_class_resource_line`
- `get_effective_mob_def`
- `get_effective_player_defenses`
- `get_enemy_effects_text`
- `get_player_class_skill`
- `get_player_class_skills`
- `get_player_effects_text`
- `get_player_skill_by_key`
- `get_potion_cooldown_turns_by_inventory_id`
- `get_skill_cooldown`
- `hunt`
- `init_class_combat_resource`
- `init_combat_effects`
- `init_skill_cooldowns`
- `patch_combat_bot_rate_limit_safe_send`
- `process_enemy_turn_start_effects`
- `process_player_turn_start_effects`
- `process_victory`
- `regenerate_class_resource_at_player_turn`
- `register_combat_handlers`
- `remove_enemy_effect`
- `remove_player_effect`
- `roll_skill_stun`
- `rollback_turn_start_hot_heal_on_victory`
- `safe_send_message`
- `set_skill_cooldown`

Stage 12 не має створювати другу незалежну ознаку PvE-бою. Аудит рекомендує канонічний resolver, який використовує поточну бойову модель та повертає `in_pve_battle`.

Перед створенням і прийняттям запрошення перевіряти:

```text
обидва online
обидва в одній location
обидва не в PvE battle
обидва без активної interaction session
request не expired
request revision актуальна
```

## 6. Profile History

Виявлені функції `handlers/profile.py`:

- `back_from_profile`
- `build_character_text`
- `build_equipment_text`
- `build_skills_text`
- `build_stats_text`
- `equipment`
- `format_equipment_bonuses`
- `format_resource_line`
- `profile`
- `profile_character_callback`
- `profile_equipment_callback`
- `profile_inline_kb`
- `profile_skills_callback`
- `profile_stats_callback`
- `register_profile_handlers`
- `skills`
- `stats`

Затверджена навігація:

```text
Профіль
→ Історія
   → Обміни
   → Дуелі
```

`Обміни` читають immutable snapshots із `player_trade_history`. `Дуелі` на Stage 12 показують порожній стан і майбутній PvP placeholder. Таблицю повної duel history доцільно створити в PvP stage після визначення результатів, рейтингу та нагород.

## 7. Trade policy

### 7.1 Дозволено

- звичайні руни `501-525`;
- Камінь Посилення `401`;
- зілля;
- Простий Екстрактор `527`;
- справне неекіпіроване спорядження;
- спорядження зі вставленими рунами;
- золото;
- інші предмети з `tradeable=True`.

### 7.2 Заборонено

- сірий лут категорії `trash`;
- Сфера нового шляху `301`;
- Руна Успіху `402`;
- Жетон Фіріуса `526`;
- Досконалий Екстрактор `528`;
- екіпіровані предмети;
- предмети в активному Auction lot;
- спорядження з durability `0`;
- quest-bound, DEV-only, premium-bound;
- `tradeable=False`;
- предмети, зарезервовані іншою операцією.

Hard-coded protected item map:

```json
{
  "301": "Сфера нового шляху",
  "402": "Руна Успіху",
  "526": "Жетон Фіріуса",
  "528": "Досконалий Екстрактор рун"
}
```

Allowed exceptions:

```json
{
  "401": "Камінь Посилення",
  "527": "Простий Екстрактор рун"
}
```

Рекомендовано створити один resolver:

```text
get_item_trade_policy(user_id, inventory_id, requested_quantity)
```

Він має повертати `tradeable`, machine reason і localized message.

## 8. Auction та reservation conflicts

Виявлені Auction-related tables/columns:

```json
{
  "auction_history": [
    "id",
    "lot_id",
    "event_type",
    "actor_user_id",
    "seller_user_id",
    "buyer_user_id",
    "item_name",
    "category",
    "quantity",
    "price",
    "status_before",
    "status_after",
    "details_json",
    "created_at"
  ],
  "auction_lots": [
    "id",
    "seller_user_id",
    "buyer_user_id",
    "item_type",
    "item_source",
    "item_ref_id",
    "item_snapshot_json",
    "item_name",
    "item_name_norm",
    "category",
    "rarity",
    "level",
    "enhancement_level",
    "durability_current",
    "durability_max",
    "quantity",
    "price",
    "status",
    "created_at",
    "expires_at",
    "sold_at",
    "claimed_at",
    "delete_after",
    "updated_at"
  ],
  "equipment_slots": [
    "user_id",
    "slot_key",
    "inventory_id"
  ]
}
```

Рекомендовано використовувати окрему `inventory_reservations`, оскільки stackable rows потребують часткового quantity reservation. Один універсальний guard повинні викликати trader sell, Auction listing, equip, refine, rune insertion, rune extraction і trade editor.

## 9. Запропонована схема БД

```json
{
  "users_addition": [
    "last_activity_at TEXT NULL"
  ],
  "player_activity_sessions": [
    "id INTEGER PRIMARY KEY AUTOINCREMENT",
    "user_id INTEGER NOT NULL UNIQUE",
    "activity_type TEXT NOT NULL CHECK(activity_type IN ('trade_request','trade','duel_request','pvp_battle'))",
    "reference_id INTEGER NULL",
    "status TEXT NOT NULL",
    "created_at TEXT NOT NULL",
    "updated_at TEXT NOT NULL",
    "expires_at TEXT NULL",
    "FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE"
  ],
  "player_interaction_requests": [
    "id INTEGER PRIMARY KEY AUTOINCREMENT",
    "request_type TEXT NOT NULL CHECK(request_type IN ('trade','duel'))",
    "initiator_user_id INTEGER NOT NULL",
    "recipient_user_id INTEGER NOT NULL",
    "location_snapshot TEXT NOT NULL",
    "status TEXT NOT NULL CHECK(status IN ('pending','accepted','declined','cancelled','expired'))",
    "revision INTEGER NOT NULL DEFAULT 1",
    "created_at TEXT NOT NULL",
    "updated_at TEXT NOT NULL",
    "expires_at TEXT NOT NULL"
  ],
  "player_trades": [
    "id INTEGER PRIMARY KEY AUTOINCREMENT",
    "request_id INTEGER NULL",
    "initiator_user_id INTEGER NOT NULL",
    "recipient_user_id INTEGER NOT NULL",
    "status TEXT NOT NULL",
    "revision INTEGER NOT NULL DEFAULT 1",
    "initiator_ready INTEGER NOT NULL DEFAULT 0",
    "recipient_ready INTEGER NOT NULL DEFAULT 0",
    "initiator_confirmed INTEGER NOT NULL DEFAULT 0",
    "recipient_confirmed INTEGER NOT NULL DEFAULT 0",
    "created_at TEXT NOT NULL",
    "updated_at TEXT NOT NULL",
    "expires_at TEXT NOT NULL",
    "completed_at TEXT NULL",
    "cancelled_at TEXT NULL",
    "cancel_reason TEXT NULL"
  ],
  "player_trade_offers": [
    "id INTEGER PRIMARY KEY AUTOINCREMENT",
    "trade_id INTEGER NOT NULL",
    "owner_user_id INTEGER NOT NULL",
    "asset_type TEXT NOT NULL CHECK(asset_type IN ('stack','equipment','gold'))",
    "inventory_id INTEGER NULL",
    "item_id INTEGER NULL",
    "quantity INTEGER NULL",
    "gold_amount REAL NULL",
    "snapshot_json TEXT NOT NULL",
    "created_at TEXT NOT NULL",
    "updated_at TEXT NOT NULL"
  ],
  "inventory_reservations": [
    "id INTEGER PRIMARY KEY AUTOINCREMENT",
    "inventory_id INTEGER NOT NULL",
    "user_id INTEGER NOT NULL",
    "quantity INTEGER NOT NULL",
    "reservation_type TEXT NOT NULL",
    "reference_id INTEGER NOT NULL",
    "created_at TEXT NOT NULL",
    "expires_at TEXT NOT NULL",
    "UNIQUE(inventory_id, reservation_type, reference_id)"
  ],
  "player_trade_events": [
    "id INTEGER PRIMARY KEY AUTOINCREMENT",
    "trade_id INTEGER NOT NULL",
    "actor_user_id INTEGER NULL",
    "event_type TEXT NOT NULL",
    "revision INTEGER NOT NULL",
    "payload_json TEXT NOT NULL",
    "created_at TEXT NOT NULL"
  ],
  "player_trade_history": [
    "id INTEGER PRIMARY KEY AUTOINCREMENT",
    "trade_id INTEGER NOT NULL UNIQUE",
    "initiator_user_id INTEGER NOT NULL",
    "recipient_user_id INTEGER NOT NULL",
    "status TEXT NOT NULL",
    "initiator_offer_snapshot TEXT NOT NULL",
    "recipient_offer_snapshot TEXT NOT NULL",
    "summary_json TEXT NOT NULL",
    "created_at TEXT NOT NULL",
    "completed_at TEXT NULL",
    "cancelled_at TEXT NULL"
  ]
}
```

Обов'язкові indexes:

```text
users(last_activity_at)
player_activity_sessions(user_id UNIQUE)
player_activity_sessions(expires_at)
player_interaction_requests(recipient_user_id, status, expires_at)
player_trades(initiator_user_id, status)
player_trades(recipient_user_id, status)
player_trade_offers(trade_id, owner_user_id)
inventory_reservations(inventory_id)
inventory_reservations(reference_id, reservation_type)
player_trade_events(trade_id, id)
player_trade_history(initiator_user_id, id DESC)
player_trade_history(recipient_user_id, id DESC)
```

## 10. Trade state machine

Статуси:

- `pending`
- `editing`
- `confirming`
- `committing`
- `completed`
- `declined`
- `cancelled`
- `expired`
- `failed`

Допустимий основний шлях:

```text
pending request
→ editing
→ confirming
→ committing
→ completed
```

Будь-яка зміна offer:

```text
revision += 1
ready обох = false
confirmed обох = false
```

Повторний commit після `completed` повинен бути idempotent no-op.

## 11. Atomic commit

Фінальний transfer виконується однією транзакцією `BEGIN IMMEDIATE`:

1. Перевірити status, revision і confirmations.
2. Перевірити ownership, reservations і quantities.
3. Перевірити gold balances.
4. Перевірити equipped, broken, auction та trade policy.
5. Перевірити socketed-rune snapshot.
6. Симулювати bag capacity обох сторін з урахуванням відданих stacks.
7. Передати stack quantities.
8. Передати generated inventory rows шляхом зміни owner.
9. Зберегти `inventory_runes` разом із тим самим `inventory_id`.
10. Передати золото.
11. Видалити reservations.
12. Створити immutable history snapshot та completed event.
13. COMMIT.

При будь-якій помилці: ROLLBACK.

## 12. Telegram та stale callback safety

- Callback перевіряє actor, trade ID, status та revision.
- 429 після commit не повинен повторювати transfer.
- Кнопка `Оновити стан` читає поточний статус із БД.
- Global Telegram 429 guard Stage 11 залишається presentation layer.
- Trade completion є domain transaction, не Telegram transaction.

## 13. Timeout і cleanup

```text
invite: 120 секунд
editing: 600 секунд
final confirmation: 120 секунд
```

Cleanup:

```text
expire_stale_player_activity_sessions()
expire_stale_interaction_requests()
expire_stale_player_trades()
release_orphan_inventory_reservations()
```

Виклики: startup maintenance, notification worker, відкриття Map player list, створення request, DEV diagnostics.

## 14. Історія

Профільна історія використовує immutable completed/cancelled/expired snapshots. Рекомендована пагінація: 10 записів. Технічний `player_trade_events` потрібен незалежно від UI для anti-duplication та діагностики.

## 15. Patch-план Stage 12

```text
12.0.0  Map Player Interaction architecture audit
12.1.0  Player presence and persistent activity sessions
12.2.0  Same-location online player discovery through Map
12.3.0  Shared interaction requests for trade and future duel
12.4.0  Player trade database and history foundation
12.5.0  Trade item policy, locks and reservations
12.6.0  Trade offer editor for items and gold
12.7.0  Dual ready and final confirmation
12.8.0  Atomic trade commit and bag simulation
12.9.0  Telegram UX, timeout and recovery
12.10.0 Profile history for trades and future duels
12.11.0 Security, concurrency and conservation audit
12.12.0 Final Stage 12 audit and complete documentation
```

## 16. Findings

- **INFO** `presence_column_missing`: У users поки немає last_activity_at; очікувана міграція 12.1.0.
- **INFO** `missing_player_activity_sessions`: Таблиця player_activity_sessions відсутня, що очікувано до Stage 12 migrations.
- **INFO** `missing_player_interaction_requests`: Таблиця player_interaction_requests відсутня, що очікувано до Stage 12 migrations.
- **INFO** `missing_player_trades`: Таблиця player_trades відсутня, що очікувано до Stage 12 migrations.
- **INFO** `missing_player_trade_offers`: Таблиця player_trade_offers відсутня, що очікувано до Stage 12 migrations.
- **INFO** `missing_inventory_reservations`: Таблиця inventory_reservations відсутня, що очікувано до Stage 12 migrations.
- **INFO** `missing_player_trade_events`: Таблиця player_trade_events відсутня, що очікувано до Stage 12 migrations.
- **INFO** `missing_player_trade_history`: Таблиця player_trade_history відсутня, що очікувано до Stage 12 migrations.


## 17. Final architecture decision

- Presence timestamp: `users.last_activity_at`.
- Busy interaction state: persistent `player_activity_sessions` with expiry and cleanup.
- PvE battle state: reuse current canonical battle model.
- Player discovery: Map, same location, online only.
- Interaction actions: trade active, duel reserved.
- Trade history: Profile → History → Trades.
- Duel history: Profile → History → Duels placeholder until PvP stage.
- Reservations: dedicated table with quantity-aware stack reservations.
- Trade commit: one `BEGIN IMMEDIATE`, all-or-nothing.
- History/event log: mandatory from first release.

`12.0.0` is architecture-only. No manual in-game test is required.
