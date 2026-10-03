# Stage 19.28.5: аудит спойлерів у назвах QUEST_ITEM-квестів

**Рішення:** `QUEST_ITEM_TITLE_REVEAL_POLICY_REQUIRED`

Read-only аудит canonical назв, item display names і всіх presentation surfaces до та після випадіння предмета.

## Підсумок

- QUEST_ITEM-квестів: 12.
- Назви спойлерять предмет до reveal: 10.
- Номери: 4, 7, 13, 19, 23, 29, 34, 37, 43, 46.

## Presentation surfaces

- `hierarchy` → `handlers/story_quest_hierarchy_ui.py`; canonical title: `True`; item display name: `False`
- `journal_detail` → `handlers/story_quests.py`; canonical title: `True`; item display name: `True`
- `npc_card` → `handlers/story_quest_npc_runtime.py`; canonical title: `True`; item display name: `True`
- `next_quest_announcement` → `handlers/story_quest_npc_runtime.py`; canonical title: `True`; item display name: `True`
- `drop_reveal` → `systems/story_quest_item_drop_system.py`; canonical title: `False`; item display name: `True`

## Квести

### 4. Клапоть форми

- Предмет: Клапоть форми вартового
- Token overlap: клапоть, форми
- Pre-reveal leaks: hierarchy, journal_detail, npc_card, next_quest_announcement
- Рекомендована прихована назва: **Слід патруля**
- Mutation required: `True`

### 7. Згаслий ліхтар

- Предмет: Зламаний ліхтар вартового
- Token overlap: ліхтар
- Pre-reveal leaks: hierarchy, journal_detail, npc_card, next_quest_announcement
- Рекомендована прихована назва: **Знахідка біля мосту**
- Mutation required: `True`

### 13. Уламок аномалії

- Предмет: Уламок рунічного кристала
- Token overlap: уламок
- Pre-reveal leaks: hierarchy, journal_detail, npc_card, next_quest_announcement
- Рекомендована прихована назва: **Матеріальний слід аномалії**
- Mutation required: `True`

### 15. Рунічний пил

- Предмет: Проба рунічного пилу
- Token overlap: немає
- Pre-reveal leaks: немає
- Рекомендована прихована назва: **Сліди рунічного світіння**
- Mutation required: `False`

### 19. Записка при світлі рун

- Предмет: Записка вартового
- Token overlap: записка
- Pre-reveal leaks: hierarchy, journal_detail, npc_card, next_quest_announcement
- Рекомендована прихована назва: **Слід зниклого патруля**
- Mutation required: `True`

### 23. Перстень вартового

- Предмет: Перстень вартового
- Token overlap: вартового, перстень
- Pre-reveal leaks: hierarchy, journal_detail, npc_card, next_quest_announcement
- Рекомендована прихована назва: **Особиста річ вартового**
- Mutation required: `True`

### 26. Розбитий захист

- Предмет: Пошкоджений щит вартового
- Token overlap: немає
- Pre-reveal leaks: немає
- Рекомендована прихована назва: **Слід сутички біля мосту**
- Mutation required: `False`

### 29. Подертий плащ

- Предмет: Подертий клапоть плаща
- Token overlap: подертий
- Pre-reveal leaks: hierarchy, journal_detail, npc_card, next_quest_announcement
- Рекомендована прихована назва: **Слід нападу**
- Mutation required: `True`

### 34. Хутро зі слідами рун

- Предмет: Вовче хутро підвищеної якості
- Token overlap: хутро
- Pre-reveal leaks: hierarchy, journal_detail, npc_card, next_quest_announcement
- Рекомендована прихована назва: **Матеріал для Коваля**
- Mutation required: `True`

### 37. Слід до лігва

- Предмет: Рунічно позначений уламок із лігва
- Token overlap: лігва
- Pre-reveal leaks: hierarchy, journal_detail, npc_card, next_quest_announcement
- Рекомендована прихована назва: **Слід до лігва**
- Mutation required: `True`

### 43. Печатка зграї

- Предмет: Печатка Ватажка зграї
- Token overlap: зграї, печатка
- Pre-reveal leaks: hierarchy, journal_detail, npc_card, next_quest_announcement
- Рекомендована прихована назва: **Незвичайна мітка**
- Mutation required: `True`

### 46. Шерсть Ватажка

- Предмет: Клоччя шерсті Ватажка
- Token overlap: ватажка
- Pre-reveal leaks: hierarchy, journal_detail, npc_card, next_quest_announcement
- Рекомендована прихована назва: **Матеріал зі слідом Ватажка**
- Mutation required: `True`

## Контракт наступного patch

1. Не змінювати canonical `title`, `quest_id`, предмети або lifecycle.
2. Додати presentation metadata `pre_reveal_title` лише для QUEST_ITEM.
3. До фактичного отримання предмета всі UI surfaces використовують нейтральну назву.
4. Drop message уперше відкриває точну назву предмета.
5. Після reveal та в completed history показується canonical title.
6. Один resolver має обслуговувати hierarchy, journal, NPC card і next-quest announcement.
