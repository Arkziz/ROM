# ROM Stage 18.29.1b: політика тестового івенту та архіву

Marker: `ROM_STAGE_18_29_1B_TEST_EVENT_AND_ARCHIVE_POLICY`

## Тестовий івент

- Назва: `🧪 Тестовий івент`
- `EVENT_KEY`: `test_event_2026`
- Постійний блок під час створення content package: `4000..4024`
- Бізнес-час: `Europe/Kyiv`
- `START_LOCAL`: `PENDING`
- `END_LOCAL`: `PENDING`
- Початок включний, завершення виключне
- Runtime на цьому підетапі не активується

## Encounter

- `mob_key`: `test_slime`
- Назва: `🧪 Нестабільний слизень`
- Тип: normal physical event mob
- Локації: усі canonical huntable-локації без обходу штатних guards
- Рівень: рівень гравця через canonical normal-mob pipeline
- Шанс зустрічі: `25%`
- Event elite та event boss відсутні

## Валюта і нагорода

- `test_token`, ID `4000`, `🧪 Експериментальний жетон`, max stack `999`
- Drop з `test_slime`: `100%`, кількість `1`
- `test_reward`, ID `4001`, `🎁 Пам’ятний знак випробування`, collectible, max stack `10`
- Обидва предмети character-bound, non-tradeable, non-sellable, non-auctionable
- Після завершення предмети залишаються resolvable та не видаляються

## Крамниця

- `offer_key`: `test_reward_exchange`
- `operation_kind`: `exchange`
- `reward_kind`: `static_item`
- Ціна: 3 жетони
- Нагорода: 1 пам’ятний знак
- Ліміт: відсутній
- Обмін atomic, idempotent, restart-safe і fail-closed
- Lifecycle, ціна, незарезервована кількість і фінальна місткість сумки перевіряються в транзакції
- Stale callback не списує валюту і не видає нагороду

## Рейтинг мисливців

- Метрика: exactly-once terminal victory над `test_slime`
- Top size: `100`
- Page size: `10`
- Сортування: kills DESC, `first_reached_at` ASC, `user_id` ASC
- Особиста позиція показується також поза top-100
- Поразка, втеча, незавершений бій і повторний terminal callback не враховуються
- Після завершення рейтинг доступний read-only

## Архів івентів

- Точка входу: `🎉 Івенти`
- Archive page size: `5`
- Status order: `active`, `upcoming`, `completed`
- Усередині статусу: `START_AT DESC`, `END_AT DESC`, `EVENT_KEY ASC`
- Статуси: `🟢 Активний`, `🟡 Незабаром`, `⚫ Завершений`
- Завершені production events залишаються зареєстрованими
- Завершений івент доступний read-only: інформація, правила, фінальний рейтинг
- `ARCHIVE_VISIBLE` не залежить від runtime `ENABLED`
- `_template`, DEV fixtures та події, які не запускалися в production, приховані
- Навігація: previous, next, refresh, back
- Refresh зберігає валідну сторінку, а завелику сторінку обмежує останньою

## Відкладені vertical slices

- `generated_equipment_purchase` з `reward_kind=generated_equipment`
- multi-ingredient `recipe` для static event items або унікальних зіль
- event elite, event boss і прямий unique-item drop

Непідтримувані operation/reward kinds завершуються fail-closed.
