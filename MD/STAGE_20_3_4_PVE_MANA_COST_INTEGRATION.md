# Stage 20.3.4 — PvE Mana Cost Integration

## Статус
Stage 20.3.4 переводить PvE presentation, availability, server-side revalidation і фактичне списання MP на canonical hybrid calculator.

## Canonical flow
- Меню використовує `mob.player_max_mp` як battle snapshot для показу ціни.
- Кнопка доступності використовує ту саму pure-функцію.
- Перед списанням `handlers/combat.py` повторно читає fresh persisted MP/Max MP.
- Canonical cost повторно обчислюється з fresh Max MP і передається у чинний atomic `spend_user_mp`.
- Battle snapshot синхронізується з результатом списання.

## Dynamic presentation
Старе число в тексті `Витрачає N MP` замінюється фактичною ціною поточного персонажа. Catalog description залишається literal і сумісним з AST loaders.

## Mage Arcane Flow guard
`mage_arcane_flow` недоступний при повній мані. При stale callback сервер повторно відхиляє використання без витрати ходу, MP або cooldown.

## Priest Purify Faith order
Чинний порядок збережено: validate → canonical spend → cleanse → MDEF buff → restore 15% → cooldown/persist за бойовим flow. Цей patch не змінює силу restore.

## Незмінені системи
PvP, simulator, post-combat floor 30%, passive regeneration 30%, notifications, potions, Max MP і фізичні класи не змінені.

## Ручна перевірка
Потрібна після успішного patch: перевірити dynamic ціни, недостатню ману, stale/full-MP guard Магічного потоку та spend-before-restore Очищення віри.
