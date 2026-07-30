# RUNE SYSTEM 10.12.0 FINAL AUDIT

## 1. Статус аудиту

- **Версія:** `10.12.0`
- **Початок:** `2026-07-31T00:37:34`
- **Завершення:** `2026-07-31T00:37:43`
- **Статус:** **PASS**
- **Smoke/regression tests:** **23/23 PASS**
- **SQLite quick_check:** `ok`
- **Foreign-key issues:** `0`
- **Залишки fixture-користувачів:** `0`

## 2. Реалізовані компоненти

- ✅ 10.2 data model
- ✅ 10.3 daily tokens
- ✅ 10.4 inventory/dev
- ✅ 10.5 equipment slots
- ✅ 10.6 insertion
- ✅ 10.7 stat bonuses
- ✅ 10.8 fusion
- ✅ 10.9 simple extractor
- ✅ 10.10 perfect extractor
- ✅ 10.11 rune drop

Завершено повний цикл системи рун:

1. Канонічна модель 25 рун характеристик I-V.
2. Жетони Фіріуса як накопичувальний матеріал зі щоденної нагороди.
3. Рунні слоти для всіх 10 типів екіпірування.
4. Рунний Майстер, вставка рун та український UI.
5. Активація бонусів тільки на екіпірованому незламаному спорядженні.
6. Переробка `3 однакові руни + 1 Жетон Фіріуса -> 1 руна наступного рівня`.
7. Простий і Досконалий Екстрактори.
8. Реальний дроп рун із normal/elite/boss ворогів.
9. DEV-команди видачі, симуляції та тестування.

## 3. Канонічні предмети

- `501` 💠 Руна Сили I (`rune`, stack `999`)
- `502` 💠 Руна Сили II (`rune`, stack `999`)
- `503` 💠 Руна Сили III (`rune`, stack `999`)
- `504` 💠 Руна Сили IV (`rune`, stack `999`)
- `505` 💠 Руна Сили V (`rune`, stack `999`)
- `506` 💠 Руна Витривалості I (`rune`, stack `999`)
- `507` 💠 Руна Витривалості II (`rune`, stack `999`)
- `508` 💠 Руна Витривалості III (`rune`, stack `999`)
- `509` 💠 Руна Витривалості IV (`rune`, stack `999`)
- `510` 💠 Руна Витривалості V (`rune`, stack `999`)
- `511` 💠 Руна Спритності I (`rune`, stack `999`)
- `512` 💠 Руна Спритності II (`rune`, stack `999`)
- `513` 💠 Руна Спритності III (`rune`, stack `999`)
- `514` 💠 Руна Спритності IV (`rune`, stack `999`)
- `515` 💠 Руна Спритності V (`rune`, stack `999`)
- `516` 💠 Руна Інтелекту I (`rune`, stack `999`)
- `517` 💠 Руна Інтелекту II (`rune`, stack `999`)
- `518` 💠 Руна Інтелекту III (`rune`, stack `999`)
- `519` 💠 Руна Інтелекту IV (`rune`, stack `999`)
- `520` 💠 Руна Інтелекту V (`rune`, stack `999`)
- `521` 💠 Руна Мудрості I (`rune`, stack `999`)
- `522` 💠 Руна Мудрості II (`rune`, stack `999`)
- `523` 💠 Руна Мудрості III (`rune`, stack `999`)
- `524` 💠 Руна Мудрості IV (`rune`, stack `999`)
- `525` 💠 Руна Мудрості V (`rune`, stack `999`)
- `526` 🪙 Жетон Фіріуса (`material`, stack `999`)
- `527` 🧰 Екстрактор рун (`material`, stack `999`)
- `528` ✨ Досконалий Екстрактор рун (`material`, stack `999`)

Діапазони:

- `501-525`: 25 рун, 5 характеристик × 5 рівнів.
- `526`: Жетон Фіріуса.
- `527`: Простий Екстрактор рун.
- `528`: Досконалий Екстрактор рун.
- Усі предмети системи мають `max_stack = 999`.

## 4. Рунні слоти

- `main_hand`: **2**
- `off_hand`: **1**
- `helmet`: **1**
- `shoulders`: **1**
- `chest`: **3**
- `gloves`: **1**
- `legs`: **2**
- `boots`: **1**
- `necklace`: **1**
- `ring`: **1**

- **Загальна місткість повного комплекту:** `14`.
- Слот ідентифікується парою `(inventory_id, slot_index)`.
- Дублікати socket-пар у БД: `0`.
- Orphan socket rows: `0`.

## 5. Характеристики та формули

Рівні рун:

```text
I = +1
II = +2
III = +3
IV = +4
V = +5
```

Підтримувані характеристики:

```text
STR, STA, DEX, INT, WIS
```

Активний бонус рахується лише коли:

```text
предмет належить персонажу
AND предмет екіпірований
AND durability > 0
```

Похідні формули використовують канонічний `get_player_stats()`:

```text
Physical ATK <- STR
Magic ATK <- INT
Max HP = round((100 + level*20 + STA*5) * (1 + armor_refine_hp_percent/100))
PDEF = equipment_PDEF + STA*0.2
MDEF = equipment_MDEF + WIS
Max MP = 100 + level*20 + INT*3 + WIS*2  (тільки mana-класи)
Physical Crit <- DEX
Magical Crit <- WIS
```

Зміна максимуму HP/MP не виконує безкоштовне лікування. Поточне значення лише обмежується новим максимумом.

## 6. Вставка рун

Транзакція:

```text
BEGIN IMMEDIATE
-> ownership/equipment/socket/rune checks
-> consume exactly 1 rune
-> insert exactly 1 inventory_runes row
-> COMMIT
```

При помилці виконується `ROLLBACK`. Повторний callback не списує другу руну.

## 7. Переробка рун

```text
3 однакові руни одного stat і level
+ 1 Жетон Фіріуса
= 1 руна наступного рівня
```

- Шанс успіху: **100%**.
- Руна V не переробляється.
- Денний ліміт відсутній.
- Жетони накопичуються між днями.
- Операція атомарна, включно з перевіркою місця для результату.

Еквівалент повного створення з рун I:

```text
Rune II = 3 Rune I + 1 token
Rune III = 9 Rune I + 4 tokens
Rune IV = 27 Rune I + 13 tokens
Rune V = 81 Rune I + 40 tokens
```

## 8. Екстрактори

### Простий Екстрактор

```text
повертає 1 випадкову вставлену руну
знищує спорядження
знищує всі інші вставлені руни
витрачає 1 Простий Екстрактор
```

### Досконалий Екстрактор

```text
повертає всі вставлені руни
знищує спорядження
не втрачає вставлені руни
витрачає 1 Досконалий Екстрактор
```

Обидві операції дозволені тільки для знятого спорядження та виконуються в одній транзакції.

## 9. Дроп і баланс

```text
Normal: 5%  -> Rune I 100%
Elite:  12% -> Rune I 80%, Rune II 20%
Boss:   35% -> Rune I 60%, Rune II 35%, Rune III 5%
```

- Вибір `STR/STA/DEX/INT/WIS`: по **20%**.
- Максимум рун за одне завершення бою: **1**.
- Прямий максимальний рівень: **3**.
- Руни IV-V доступні тільки через fusion.
- Пріоритет класифікації: `boss > elite > normal`.
- Рунний roll не замінює досвід, золото чи звичайний лут.

## 10. UI та локалізація

- Категорія інвентаря: `Руни`.
- Матеріали показуються як `Матеріали`.
- Технічні stat-коди не показуються в інтерфейсі гравця.
- Назви броні узгоджені між Інвентарем, вставкою й Екстрактором:
  `Тканина`, `Шкіра`, `Кольчуга`, `Лати`.
- Для rune stack `×1` у мобільній кнопці приховано; для більших stack використовується `×N`.
- Рунний Майстер має окреме reply-меню: вставка, переробка, Екстрактор, повернення.

## 11. DEV-команди

```text
/dev_rune STAT LEVEL [quantity]
/dev_firius [quantity]              # типово 10
/dev_extractor [quantity]
/dev_extractor_perfect [quantity]
/dev_rune_drop_sim normal|elite|boss [trials]
```

Симулятор дропу read-only і не змінює інвентар або БД.

## 12. Стан бази даних

- `inventory_runes` rows: `3`.
- Користувачів зі вставленими рунами: `1`.
- Invalid rune item IDs: `0`.
- Invalid rune levels: `0`.
- Invalid rune stats: `0`.
- Duplicate socket pairs: `0`.
- Orphan socket rows: `0`.
- Foreign-key issues: `0`.

## 13. Виконані тести

- ✅ `tools\smoke_test_rune_data_model.py`
- ✅ `tools\smoke_test_daily_firius_token_reward.py`
- ✅ `tools\smoke_test_daily_reward_newline_hotfix.py`
- ✅ `tools\smoke_test_firius_token_inventory_description.py`
- ✅ `tools\smoke_test_rune_inventory_and_dev_commands.py`
- ✅ `tools\smoke_test_equipment_rune_slots.py`
- ✅ `tools\smoke_test_rune_master_insertion.py`
- ✅ `tools\smoke_test_rune_stat_ukrainian_labels.py`
- ✅ `tools\smoke_test_rune_character_stat_bonuses.py`
- ✅ `tools\smoke_test_rune_fusion_with_firius_tokens.py`
- ✅ `tools\smoke_test_rune_master_menu_ui.py`
- ✅ `tools\smoke_test_rune_master_inline_navigation_cleanup.py`
- ✅ `tools\smoke_test_simple_rune_extractor.py`
- ✅ `tools\smoke_test_extractor_button_rune_master_menu.py`
- ✅ `tools\smoke_test_rune_equipment_display_names.py`
- ✅ `tools\smoke_test_perfect_rune_extractor.py`
- ✅ `tools\smoke_test_rune_drop_and_balance.py`
- ✅ `tools\smoke_test_inventory_refine_contracts.py`
- ✅ `tools\smoke_test_equipment_readonly_core.py`
- ✅ `tools\smoke_test_player_combat_stats.py`
- ✅ `tools\smoke_test_character_mutation_contracts.py`
- ✅ `tools\smoke_test_rom_core.py`
- ✅ `tools\check_imports.py`

## 14. Відомі обмеження та наступні рішення

1. Шанси дропу є стартовими балансними значеннями та мають коригуватися за реальною статистикою.
2. Екстрактори поки не отримали player-facing джерело придбання або дропу, окрім DEV-команд.
3. Обмін рунами між гравцями не входить до поточного етапу.
4. Немає централізованої універсальної таблиці для всього луту. Поточний rune-drop модуль може бути шаблоном для Каменів Посилення, зіль та інших матеріалів.
5. Видалення спорядження сторонніми майбутніми функціями повинно зберігати cascade/cleanup контракт для `inventory_runes`.

## 15. Висновок

Система рун `10.1.0-10.12.0` пройшла фінальний архітектурний, DB та regression-аудит. Критичних дефектів, fixture-residue, некоректних socket rows або порушень канонічних балансних контрактів не виявлено. Система готова до ігрового тестування та подальшого балансування константами.
