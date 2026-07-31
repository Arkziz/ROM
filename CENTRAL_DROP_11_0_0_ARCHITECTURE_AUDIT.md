# CENTRAL DROP 11.0.0 ARCHITECTURE AUDIT

## 1. Результат

- Статус: **PASS, mutation-isolated architecture baseline created**
- Дата: `2026-07-31T23:06:47`
- SQLite quick_check: `ok`
- Foreign-key issues: `0`
- Gameplay-файли змінено: **0**
- Gameplay-дані game.db змінено: **ні**
- Validation tests: **8/8 PASS**

Цей етап не централізує дроп і не змінює шанси. Smoke-тести можуть тимчасово створювати та очищувати fixture-рядки, через що байти SQLite-файлу або `sqlite_sequence` можуть змінитися. Аудит контролює незмінність усіх логічних gameplay-рядків до і після suite. Він фіксує фактичний runtime перед міграцією в `data/drop_tables.py` та `systems/drop_system.py`.

## 2. Поточний reward chain

```text
handlers/combat.py
-> process_victory()
-> systems.reward_system.process_victory_reward()
-> базові EXP / Gold / Kill
-> roll_loot()
   -> equipment roll
   -> trophy/simple loot roll
   -> refine stone wrapper
   -> guild elite reward wrapper
-> rune wrapper навколо process_victory_reward()
-> refresh bag counters
```

Guild elite progress є reward hook, але не предметним дропом. Його не слід переносити до item drop tables.

## 3. Виявлені багатошарові overrides

### `roll_loot()`

- `roll_loot()` lines 376-393
- `roll_loot()` lines 484-503
- `roll_loot()` lines 527-546

### `process_victory_reward()`

- `process_victory_reward()` lines 400-427
- `process_victory_reward()` lines 554-570

Base captures:

```text
_base_roll_loot_before_guild_elite_reward_v1
_base_roll_loot_before_refine_stone_drop_v1
```

Висновок: фізичне очищення старої системи не можна виконувати в одному патчі з підключенням central drop. Спочатку потрібні wrappers і equivalence tests.

## 4. Фактичний баланс до міграції

### Спорядження

```text
Normal: 20%
Elite:  45%
```

Class-aware chance визначається окремо в reward/equipment flow і має бути зафіксований під час `11.4.0` без зміни генератора предметів.

### Камінь Посилення

```text
Item ID: 401
Normal: 8%
Elite:  20%
```

Критичний висновок: поточний Stone classifier перевіряє тільки `is_elite`. Окремої boss-таблиці немає. Бос без `is_elite=True` отримує normal chance 8%; бос з `is_elite=True` отримує elite chance 20%. У central config це треба зробити явною політикою, а не випадковим наслідком прапорця.

### Руни

```text
Normal: 5% -> I 100%
Elite:  12% -> I 80%, II 20%
Boss:   35% -> I 60%, II 35%, III 5%
Max per kill: 1
Direct max level: 3
Stats: STR/STA/DEX/INT/WIS по 20%
```

Rune classifier уже має канонічний пріоритет `boss > elite > normal` і є найкращим шаблоном для загального enemy classifier.

### Трофейний лут

- Mob templates знайдено: **20**.
- Поточні `loot_chance`: `{"0.45": 4, "0.48": 2, "0.5": 2, "0.52": 2, "0.54": 2, "0.55": 2, "0.56": 2, "0.58": 2, "0.6": 2}`.
- Static trophy item IDs: `[107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126]`.
- Elite modifier: `loot_chance + 0.20`, максимум 100%.
- Якщо є `loot_table` або `loot`, використовується table path; інакше `trash_items` / simple keys.

### Зілля

Поточний potion runtime має definitions та use logic, але не має централізованого mob-drop runtime.

```json
{
  "201": {
    "name": "🔴 Мале зілля здоров’я",
    "resource": null,
    "restore": 50,
    "buy_price": 5.0,
    "sell_price": 1.0,
    "max_stack": 10
  },
  "203": {
    "name": "🔴 Середнє зілля здоров’я",
    "resource": null,
    "restore": 120,
    "buy_price": 15.0,
    "sell_price": 3.0,
    "max_stack": 10
  },
  "202": {
    "name": "🔵 Мале зілля мани",
    "resource": null,
    "restore": 40,
    "buy_price": 6.0,
    "sell_price": 1.2,
    "max_stack": 10
  },
  "204": {
    "name": "🔵 Середнє зілля мани",
    "resource": null,
    "restore": 100,
    "buy_price": 18.0,
    "sell_price": 3.6,
    "max_stack": 10
  }
}
```

Зілля треба додавати тільки в окремому балансному патчі після створення central engine. Рекомендовано один mutually-exclusive potion group, а не чотири незалежні rolls.

## 5. Enemy classification

Поточні сигнали в rune classifier:

```json
{
  "is_boss": true,
  "boss": true,
  "mob_type": true,
  "enemy_type": true
}
```

Сигнали, фактично присутні в mob templates:

```json
{}
```

Канонічне правило для Етапу 11:

```text
boss -> elite -> normal
```

Central classifier повинен розуміти `is_boss`, `boss`, `mob_type`, `enemy_type`, `is_elite`, `elite`, але повертати рівно одну категорію.

## 6. Item namespace baseline

- `201` 🔴 Мале зілля здоров’я | type=`potion_hp` | category=`potion` | stack=`10`
- `202` 🔵 Мале зілля мани | type=`potion_mp` | category=`potion` | stack=`10`
- `203` 🔴 Середнє зілля здоров’я | type=`potion_hp_medium` | category=`potion` | stack=`10`
- `204` 🔵 Середнє зілля мани | type=`potion_mp_medium` | category=`potion` | stack=`10`
- `301` 🔮 Сфера нового шляху | type=`class_reset` | category=`potion` | stack=`10`
- `401` 🪨 Камінь Посилення | type=`refine_stone` | category=`material` | stack=`999`
- `402` 💎 Руна Успіху | type=`success_rune` | category=`material` | stack=`999`
- `501` 💠 Руна Сили I | type=`rune_str_1` | category=`rune` | stack=`999`
- `526` 🪙 Жетон Фіріуса | type=`firius_token` | category=`material` | stack=`999`
- `527` 🧰 Екстрактор рун | type=`rune_extractor` | category=`material` | stack=`999`
- `528` ✨ Досконалий Екстрактор рун | type=`rune_extractor_perfect` | category=`material` | stack=`999`

Політика:

- `401` можна переносити до material drop table.
- `402` має залишатися disabled/premium source і не випадати з мобів.
- `201-204` можна підключати тільки після окремого potion balance patch.
- `527` може бути disabled boss candidate, але крамниця за золото залишається основним джерелом.
- `528` не включати в mob drop; майбутнє джерело за кристали.

## 7. Bag-full policy

Рекомендована schema:

```text
stack_or_lose          stackable materials, runes, potions
require_space          generated equipment
currency_direct        EXP/Gold
mail_if_full           future premium/event rewards, not in Stage 11 MVP
```

Central award result має повертати `rolled`, `awarded`, `lost`, `reason`, `message`, а не тільки текст.

## 8. Незалежні та взаємовиключні групи

Поточні незалежні rolls:

```text
equipment
trophy/refine chain
rune
```

Майбутня модель:

```text
independent: equipment, trophy, refine material, rune
exclusive: potion group
hooks outside item drop: guild progress, contract progress, daily progress
```

Не вводити global hard cap у першій міграції, інакше зміниться чинна економіка.

## 9. Call-site inventory

### `add_item()`
- `db.py:2157`
- `handlers/dev.py:181`
- `handlers/dev.py:659`
- `handlers/dev.py:682`
- `handlers/dev.py:705`
- `handlers/dev.py:724`
- `handlers/dev.py:847`
- `systems/reward_system.py:318`
- `systems/reward_system.py:361`
- `systems/reward_system.py:469`
- `systems/rune_system.py:1302`
- `tools/smoke_test_perfect_rune_extractor.py:134`
- `tools/smoke_test_perfect_rune_extractor.py:96`
- `tools/smoke_test_rune_fusion_with_firius_tokens.py:36`
- `tools/smoke_test_simple_rune_extractor.py:23`
- `tools/smoke_test_simple_rune_extractor.py:23`
### `award_rune_drop()`
- `systems/reward_system.py:559`
### `create_generated_equipment_item()`
- `handlers/dev.py:496`
- `systems/reward_system.py:274`
- `tools/smoke_test_dynamic_equipment_repair_contracts.py:139`
### `process_victory_reward()`
- `handlers/combat.py:1599`
### `roll_equipment_drop()`
- `systems/reward_system.py:388`
### `roll_loot()`
- `systems/reward_system.py:415`
### `roll_refine_stone_drop()`
- `systems/reward_system.py:498`
### `roll_rune_drop()`
- `systems/rune_system.py:1298`
- `systems/rune_system.py:1333`
- `tools/smoke_test_rune_drop_and_balance.py:15`
- `tools/smoke_test_rune_drop_and_balance.py:17`
- `tools/smoke_test_rune_drop_and_balance.py:19`
- `tools/smoke_test_rune_drop_and_balance.py:21`

## 10. Ризики подвійного нарахування

1. У `reward_system.py` є кілька визначень `roll_loot()` і base captures.
2. Rune drop підключений wrapper-ом навколо `process_victory_reward()`.
3. Новий central engine не можна викликати паралельно зі старими refine/rune wrappers.
4. Guild elite reward не є loot item і не повинен випадково виконуватися двічі.
5. Equipment generator створює DB row, тому read-only simulator не може викликати production creator.
6. Boss semantics різняться між rune та refine stone flow.
7. Старі `loot_table`, `loot`, `trash_items` мають бути підтримані під час перехідного періоду.

## 11. Канонічна майбутня модель

### `data/drop_tables.py`

Має описувати:

```text
rule_id
group
mode: independent | exclusive
enabled
enemy normal/elite/boss config
chance
quantity min/max
item/pool/resolver
weights
max_per_kill
bag_policy
message policy
premium/bound flags
balance version
```

### `systems/drop_system.py`

Має реалізувати:

```text
classify_enemy()
validate_drop_tables()
roll_drop_group()
roll_enemy_drops()
award_drop_results()
format_drop_messages()
simulate_drop_tables()
```

## 12. Затверджена послідовність Етапу 11

```text
11.0.0  Architecture audit, цей файл
11.1.0  Central config model + pure drop engine
11.2.0  Rune migration with exact equivalence
11.3.0  Refine Stone migration and explicit boss policy
11.4.0  Equipment migration
11.5.0  Trophy/location loot migration
11.6.0  Potion drop balance
11.7.0  Premium/special material policy
11.8.0  Universal read-only DEV simulator
11.9.0  Final Victory Reward integration
11.10.0 Legacy physical cleanup
11.11.0 Balance/economy audit
11.12.0 Final central drop audit and documentation
```

## 13. Exact-equivalence gates

До перемикання production flow кожна міграція має довести:

- однаковий результат для однакового deterministic random stream;
- однакову кількість `random` draws;
- однаковий item ID/rarity/quantity;
- однаковий bag-full outcome;
- відсутність додаткового DB row;
- відсутність подвійного повідомлення;
- відсутність змін real users під час smoke tests.

## 14. Validation suite

- PASS `tools/smoke_test_rune_drop_and_balance.py`
- PASS `tools/smoke_test_inventory_refine_contracts.py`
- PASS `tools/smoke_test_weapon_damage_contracts.py`
- PASS `tools/smoke_test_combat_mana_potion_contracts.py`
- PASS `tools/smoke_test_combat_potion_cooldown_menu_ux.py`
- PASS `tools/smoke_test_equipment_readonly_core.py`
- PASS `tools/smoke_test_rom_core.py`
- PASS `tools/check_imports.py`

## 15. Рішення аудиту

- Починати `11.1.0` безпечно.
- Не змінювати шанси у `11.1.0-11.5.0`; лише переносити чинну поведінку.
- Potion balance вводити окремо в `11.6.0`.
- Boss chance Каменя Посилення визначити явним рішенням у `11.3.0`.
- Simple Extractor boss candidate зберегти disabled до gold economy audit.
- Perfect Extractor і Rune of Success залишити disabled для mob drop.
- Етап 12 після завершення 11 присвятити прямому обміну.
