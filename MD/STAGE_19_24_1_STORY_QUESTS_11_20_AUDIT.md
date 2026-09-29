# Stage 19.24.1 — Read-only аудит квестів 11–20

## Рішення

**READY_FOR_STAGE_19_24_2_CONTENT_OPTIMIZATION**

Production content і production DB не змінювалися. Квести 11–20 залишаються неактивними.

## Затверджений контракт пакета

- Рівень доступу: 2.
- Послідовність: квест 11 після завершеного квесту 10, далі strict previous quest chain.
- Нагорода кожного квесту: 36 EXP і 0.43 золота.
- Квести 13, 15 і 19: QUEST_ITEM, drop chance 15%, предмет зберігається до наступної TURN_IN здачі.
- Квест 14: TURN_IN уламка рунічного кристала Алхіміку.
- Квест 16: TURN_IN проби рунічного пилу Алхіміку.
- Квест 20: TURN_IN записки вартового Старості.
- Навігація під час activation має матеріалізуватися через canonical NPC registry.

## Виявлені legacy-розбіжності авторського DOCX

- Старі орієнтовні rewards не є production policy.
- Квест 14 у DOCX позначений TALK, але approved candidate змінює його на TURN_IN.
- Формулювання квесту 16 про «обидва зразки» не відповідає затвердженому послідовному exact-once lifecycle: уламок здається у квесті 14, пил у квесті 16.

## Обов’язкові виправлення Stage 19.24.2

- Додати відсутні acceptance/completion тексти у QUEST_ITEM 13, 15 і 19.
- Переписати AVAILABLE descriptions 13, 15 і 19 так, щоб вони не повідомляли майбутню знахідку до drop.
- Явно встановити consume_on_completion=false для quest items 13, 15 і 19.
- Узгодити тексти квестів 14 і 16 з послідовною здачею окремих зразків.
- Зберегти rewards 36 EXP / 0.43 золота, drop chance 15% і canonical localized navigation.

## Наступний етап

Stage 19.24.2 має оптимізувати й зафіксувати authoritative content пакета 11–20 до production activation.
