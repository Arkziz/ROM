# Stage 19.27.9: аудит контенту сюжетних квестів 41–50

## Рішення

**CONTENT_REWRITE_REQUIRED**

Аудит є read-only щодо production-контенту. Наступний patch має змінювати лише presentation content і canonical navigation data, не торкаючись механіки, нагород, цілей або boss lifecycle.

## Зафіксований gameplay-контракт

- квести 41–50 залишаються strict chain після квесту 40;
- типи квестів, нагороди, цілі 15/15/10 і шанс предметів 15% не змінюються;
- предметні пари 43→44 та 46→47 зберігаються;
- квест 49 залишається BOSS із deferred NPC report Голові Найманців;
- квест 50 залишається itemless TURN_IN до Старости;
- квест 51 не активується.

## Загальні результати

- перевірено квестів: 10;
- квестів, що потребують редактури: 10;
- точних повторів presentation fields: 8;
- полів нижче baseline глибини 31–40: 32;
- навігаційних дефектів: 0.

## Результат за квестами

### 41. Рада перед походом
- **HIGH** `EXACT_PRESENTATION_DUPLICATE`: `description=acceptance_text`
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `description` (7 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `acceptance_text` (7 words; expected at least 20)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `progress_text` (8 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `completion_text` (9 words; expected at least 14)

### 42. Підступи до лігва
- **HIGH** `EXACT_PRESENTATION_DUPLICATE`: `description=acceptance_text`
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `description` (5 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `acceptance_text` (5 words; expected at least 20)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `progress_text` (5 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `completion_text` (8 words; expected at least 14)

### 43. Печатка зграї
- **HIGH** `EXACT_PRESENTATION_DUPLICATE`: `description=acceptance_text`
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `description` (7 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `acceptance_text` (7 words; expected at least 20)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `completion_text` (3 words; expected at least 14)

### 44. Знак Ватажка
- **HIGH** `EXACT_PRESENTATION_DUPLICATE`: `description=acceptance_text`
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `description` (9 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `acceptance_text` (9 words; expected at least 20)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `progress_text` (6 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `completion_text` (6 words; expected at least 14)

### 45. Охорона лігва
- **HIGH** `EXACT_PRESENTATION_DUPLICATE`: `description=acceptance_text`
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `description` (5 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `acceptance_text` (5 words; expected at least 20)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `progress_text` (4 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `completion_text` (3 words; expected at least 14)

### 46. Шерсть Ватажка
- **HIGH** `EXACT_PRESENTATION_DUPLICATE`: `description=acceptance_text`
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `description` (7 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `acceptance_text` (7 words; expected at least 20)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `completion_text` (4 words; expected at least 14)

### 47. Остання перевірка
- **HIGH** `EXACT_PRESENTATION_DUPLICATE`: `description=acceptance_text`
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `description` (7 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `acceptance_text` (7 words; expected at least 20)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `progress_text` (8 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `completion_text` (9 words; expected at least 14)

### 48. Останній периметр
- **HIGH** `EXACT_PRESENTATION_DUPLICATE`: `description=acceptance_text`
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `description` (9 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `acceptance_text` (9 words; expected at least 20)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `progress_text` (4 words; expected at least 10)
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `completion_text` (4 words; expected at least 14)

### 49. Ватажок зграї
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `description` (9 words; expected at least 10)

### 50. Дорога далі
- **MEDIUM** `BELOW_BASELINE_DEPTH`: `acceptance_text` (13 words; expected at least 20)

## Обов’язкова policy наступного content patch

1. `description` має бути стислим переказом ситуації, а не реплікою NPC.
2. `acceptance_text` має бути окремою живою сценою прийняття, з голосом конкретного NPC.
3. `progress_text` має пояснювати незавершений стан без повтору objective text.
4. `completion_text` має показувати наслідок виконання і природно вести до наступного квесту.
5. `objective_text` залишається чіткою механічною метою.
6. `navigation.objective_hint` і `navigation.next_step_hint` містять лише canonical локалізовані маршрути NPC.
7. Усі українські тексти використовують «розділ», а локацію показують як «Початок Шляху».
8. Тексти не повинні розкривати назви прихованих quest items до першого успішного випадіння.
9. Наступний patch повинен додати regression на відсутність exact duplicates і objective-as-navigation.
10. Після content patch потрібна ручна перевірка журналу, NPC-карток, прийняття, progress і completion для 41–50.
