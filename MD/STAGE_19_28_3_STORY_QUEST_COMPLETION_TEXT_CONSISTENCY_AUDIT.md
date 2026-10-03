# Stage 19.28.3: аудит consistency завершальних реплік квестів 1–50

**Рішення:** `COMPLETION_TEXT_MUTATION_REQUIRED`

Read-only аудит поточних production `STORY_QUEST_TEXT`. Історичні репліки з чату не вважаються чинними, якщо production content уже змінено.

## Підсумок

- Перевірено: 50 квестів.
- Квестів із зауваженнями: 7.
- Номери: 23, 26, 29, 34, 37, 40, 43.
- High severity: 40, 43.

## Класифікація

- `ITEM_COMPLETION_LACKS_NPC_RESOLUTION`: 5
- `REPEATS_ALREADY_COMPLETED_HANDOFF`: 2

## Деталі

### 23. Перстень вартового

- Тип: `QUEST_ITEM`
- Completion NPC: `trader`
- Наступний giver: `trader`
- Поточний текст: Перстень знайдено. Торговець може впізнати власника за міським клеймом.
- Зауваження:
  - **MEDIUM** `ITEM_COMPLETION_LACKS_NPC_RESOLUTION`: Item completion repeats acquisition but does not describe NPC verification/use.

### 26. Розбитий захист

- Тип: `QUEST_ITEM`
- Completion NPC: `mercenary_head`
- Наступний giver: `bartender`
- Поточний текст: Пошкоджений щит знайдено та збережено для фінального зіставлення доказів.
- Зауваження:
  - **MEDIUM** `ITEM_COMPLETION_LACKS_NPC_RESOLUTION`: Item completion repeats acquisition but does not describe NPC verification/use.

### 29. Подертий плащ

- Тип: `QUEST_ITEM`
- Completion NPC: `mercenary_head`
- Наступний giver: `mercenary_head`
- Поточний текст: Клапоть плаща знайдено. Тепер доказів достатньо для остаточного висновку.
- Зауваження:
  - **MEDIUM** `ITEM_COMPLETION_LACKS_NPC_RESOLUTION`: Item completion repeats acquisition but does not describe NPC verification/use.

### 34. Хутро зі слідами рун

- Тип: `QUEST_ITEM`
- Completion NPC: `blacksmith`
- Наступний giver: `blacksmith`
- Поточний текст: Вовче хутро підвищеної якості знайдено. Матеріал потрібно передати Ковалю.
- Зауваження:
  - **MEDIUM** `ITEM_COMPLETION_LACKS_NPC_RESOLUTION`: Item completion repeats acquisition but does not describe NPC verification/use.

### 37. Слід до лігва

- Тип: `QUEST_ITEM`
- Completion NPC: `rune_master`
- Наступний giver: `rune_master`
- Поточний текст: Рунічно позначений уламок знайдено. Його потрібно передати Рунному Майстру.
- Зауваження:
  - **MEDIUM** `ITEM_COMPLETION_LACKS_NPC_RESOLUTION`: Item completion repeats acquisition but does not describe NPC verification/use.

### 40. Перед вирішальним походом

- Тип: `TURN_IN`
- Completion NPC: `elder`
- Наступний giver: `elder`
- Поточний текст: Староста вислуховує доповідь. Лігво знайдено, шлях очищено, а мисливці готові. Голова Найманців розставить людей, Коваль завершить спорядження, а Рунний Майстер підготує захист від рунічного впливу. Староста скликає раду. Після неї почнеться останній етап походу.

✅ Розділ «Вовча загроза» завершено.
- Зауваження:
  - **HIGH** `REPEATS_ALREADY_COMPLETED_HANDOFF`: Imperative points to the NPC where completion has already occurred.

### 43. Печатка зграї

- Тип: `QUEST_ITEM`
- Completion NPC: `mercenary_head`
- Наступний giver: `mercenary_head`
- Поточний текст: Доказ знайдено. На ньому видно той самий знак, що й на каменях біля проходу. Віднеси знахідку Голові Найманців, щоб визначити наступний крок.
- Зауваження:
  - **HIGH** `REPEATS_ALREADY_COMPLETED_HANDOFF`: Imperative points to the NPC where completion has already occurred.

## Контракт майбутнього mutation patch

1. Не змінювати lifecycle, NPC ownership, rewards або item consumption.
2. Переписувати лише підтверджені runtime completion texts.
3. Не повторювати дію, яка вже завершилася в поточного NPC.
4. Дозволяти перехідну вказівку лише до наступного giver NPC.
5. Кожен фінал має описувати результат і сюжетний наслідок.
