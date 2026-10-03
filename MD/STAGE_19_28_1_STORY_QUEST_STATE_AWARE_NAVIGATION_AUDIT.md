# Stage 19.28.1: аудит state-aware навігації сюжетних квестів 1–50

**Рішення:** `STATE_AWARE_NAVIGATION_MUTATION_REQUIRED`

Аудит read-only. Production-код, definitions і база не змінюються.

## Підсумок

- Перевірено квестів: 50.
- Перевірено synthetic lifecycle states: 177.
- Квестів із navigation mismatch: 50.
- Номери: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50.

## Причина

Production journal переважно використовує статичний `next_step_hint`. Він не розрізняє незавершену ціль, готовність до здачі та завершений стан. QUEST_ITEM до випадіння вже має окрему гілку, але KILL/KILL_REGION/BOSS її не мають.

## Обов’язковий контракт наступного patch

1. `AVAILABLE` → маршрут до giver NPC.
2. `ACTIVE` і прогрес нижче цілі → маршрут виконання в локації.
3. `QUEST_ITEM` до випадіння → маршрут полювання без назви прихованого предмета.
4. `BOSS` до перемоги → маршрут виклику/довідки в локації.
5. `ACTIVE` і ціль виконана → маршрут до completion NPC.
6. `COMPLETED` → жодного активного маршруту.
7. Реалізація через один canonical resolver, без ручного форматування квестів.

## Квести з проблемами

### 1. Патруль не повернувся (`TALK`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Поговорити зі Старостою про зникнення патруля.
  - Очікуване: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
  - Очікуване: None

### 2. Перевірка стежки (`KILL_REGION`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Перемогти 3 будь-яких істот у локації Початок Шляху.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 3. Останній слід (`TALK`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Отримати від Голови Найманців відомості про останній маршрут патруля.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 4. Клапоть форми (`QUEST_ITEM`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Шукати під час полювання докази, пов’язані зі зниклим патрулем.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 5. Доказ із хащі (`TURN_IN`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Передати Старості клапоть форми вартового.
  - Очікуване: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
  - Очікуване: None

### 6. Старий міст (`KILL_REGION`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Перемогти 5 будь-яких істот у локації Початок Шляху.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 7. Згаслий ліхтар (`QUEST_ITEM`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Шукати під час полювання предмети або сліди, які могли належати зниклому патрулю.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 8. Сліди на металі (`TURN_IN`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Передати Ковалю зламаний ліхтар вартового.
  - Очікуване: 🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль
  - Очікуване: None

### 9. Шлях до печер (`KILL_REGION`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Перемогти 6 будь-яких істот у локації Початок Шляху.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 10. Розслідування починається (`TURN_IN`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Доповісти Старості про дорогу до печер.
  - Очікуване: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
  - Очікуване: None

### 11. Неспокійне світіння (`TALK`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Поговорити з Рунним Майстром про аномальне світіння.
  - Очікуване: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
  - Очікуване: None

### 12. Осередки аномалії (`KILL_REGION`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Перемогти 6 будь-яких істот у локації Початок Шляху.
  - Очікуване: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
  - Очікуване: None

### 13. Уламок аномалії (`QUEST_ITEM`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Шукати під час полювання нестабільний матеріальний слід рунічної аномалії.
  - Очікуване: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
  - Очікуване: None

### 14. Кристал під склом (`TURN_IN`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Передати Алхіміку уламок рунічного кристала.
  - Очікуване: 🏙️ Місто → ⚒️ Ремісничий квартал → 🧪 Алхімік
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 🧪 Алхімік
  - Очікуване: None

### 15. Рунічний пил (`QUEST_ITEM`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Шукати під час полювання пробу рунічного пилу біля осередків аномалії.
  - Очікуване: 🏙️ Місто → ⚒️ Ремісничий квартал → 🧪 Алхімік
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 🧪 Алхімік
  - Очікуване: None

### 16. Неприродний слід (`TURN_IN`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Передати Алхіміку пробу рунічного пилу та отримати результати дослідження.
  - Очікуване: 🏙️ Місто → ⚒️ Ремісничий квартал → 🧪 Алхімік
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 🧪 Алхімік
  - Очікуване: None

### 17. Заражені стежки (`KILL_REGION`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Перемогти 8 будь-яких істот у локації Початок Шляху.
  - Очікуване: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
  - Очікуване: None

### 18. Світло після заходу (`TALK`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Отримати від Рунного Майстра результати спостережень за аномалією.
  - Очікуване: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
  - Очікуване: None

### 19. Записка при світлі рун (`QUEST_ITEM`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Шукати під час полювання сліди зниклого патруля біля найсильнішого рунічного осередку.
  - Очікуване: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
  - Очікуване: None

### 20. Патруль знав (`TURN_IN`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Передати Старості записку зниклого вартового.
  - Очікуване: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
  - Очікуване: None

### 21. Пошуковий загін (`TALK`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Поговорити з Головою Найманців і отримати маршрут пошуку.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 22. Вхід до печер (`KILL_REGION`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Перемогти 8 будь-яких істот у локації Початок Шляху.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 23. Перстень вартового (`QUEST_ITEM`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Знайти особистий перстень одного зі зниклих вартових.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `ACTIVE_READY` `READY_ROUTE_NOT_COMPLETION_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🏙️ Місто → 🛒 Торговий ряд → 🧙 Торговець
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 24. Остання покупка (`TALK`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Показати Торговцю перстень вартового та дізнатися про останню покупку патрульного.
  - Очікуване: 🏙️ Місто → 🛒 Торговий ряд → 🧙 Торговець
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 🛒 Торговий ряд → 🧙 Торговець
  - Очікуване: None

### 25. Сліди біля мосту (`KILL_REGION`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Перемогти 10 будь-яких істот у локації Початок Шляху.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 26. Розбитий захист (`QUEST_ITEM`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Знайти пошкоджений щит зниклого вартового.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 27. Виття за стінами (`TALK`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Розпитати Бармена про чутки щодо вовків.
  - Очікуване: 🏙️ Місто → 🍺 Таверна → 🍺 Бармен
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 🍺 Таверна → 🍺 Бармен
  - Очікуване: None

### 28. Стежка переслідування (`KILL_REGION`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Перемогти 10 будь-яких істот у локації Початок Шляху.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 29. Подертий плащ (`QUEST_ITEM`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Знайти подертий клапоть плаща зниклого вартового.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 30. Картина нападу (`TURN_IN`)
- `AVAILABLE` `AVAILABLE_ROUTE_NOT_GIVER`
  - Поточне: Передати Голові Найманців перстень, пошкоджений щит і клапоть плаща.
  - Очікуване: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 31. Зграя на підступах (`TALK`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 32. Перша лінія оборони (`KILL_REGION`)
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 33. Захист для мисливців (`TALK`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль
  - Очікуване: None

### 34. Хутро зі слідами рун (`QUEST_ITEM`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль
  - Очікуване: None

### 35. Посилення загону (`TURN_IN`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль
  - Очікуване: None

### 36. За межею безпечних стежок (`KILL_REGION`)
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 37. Слід до лігва (`QUEST_ITEM`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
  - Очікуване: None

### 38. Серце впливу (`TURN_IN`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер
  - Очікуване: None

### 39. Дорога до лігва (`KILL_REGION`)
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 40. Перед вирішальним походом (`TURN_IN`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
  - Очікуване: None

### 41. Рада перед походом (`TALK`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
  - Очікуване: None

### 42. Підступи до лігва (`KILL_REGION`)
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 43. Печатка зграї (`QUEST_ITEM`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 44. Знак Ватажка (`TURN_IN`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 45. Охорона лігва (`KILL_REGION`)
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 46. Шерсть Ватажка (`QUEST_ITEM`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 47. Остання перевірка (`TURN_IN`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль
  - Очікуване: None

### 48. Останній периметр (`KILL_REGION`)
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 49. Ватажок зграї (`BOSS`)
- `ACTIVE_INCOMPLETE` `INCOMPLETE_OBJECTIVE_ROUTES_TO_NPC`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: 🌿 Початок Шляху → 🔎 Полювання
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців
  - Очікуване: None

### 50. Дорога далі (`TURN_IN`)
- `COMPLETED` `COMPLETED_STATE_STILL_SHOWS_ACTIVE_ROUTE`
  - Поточне: 🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста
  - Очікуване: None
