# Stage 20.5.3 — Аудит цін магазину кристалів

Статус: **PASS**  
Кількість пропозицій: **8**  
Production-код і база даних не змінювалися.

## Поточні ціни

- `item:501` — **🔮 Сфера нового шляху**: **150 💎**; owner: `systems/crystal_shop_system.py::CRYSTAL_SHOP_CATALOG`.
- `item:502` — **✍️ Руна імені**: **50 💎**; owner: `systems/crystal_shop_system.py::CRYSTAL_SHOP_CATALOG`.
- `item:602` — **🍀 Руна Успіху**: **35 💎**; owner: `systems/crystal_shop_system.py::CRYSTAL_SHOP_CATALOG`.
- `item:728` — **💠 Досконалий Екстрактор**: **20 💎**; owner: `systems/crystal_shop_system.py::CRYSTAL_SHOP_CATALOG`.
- `bag:60->80` — **Розширення сумки 60→80**: **75 💎**; owner: `systems/crystal_bag_expansion_system.py::BAG_EXPANSION_TIERS`.
- `bag:80->100` — **Розширення сумки 80→100**: **150 💎**; owner: `systems/crystal_bag_expansion_system.py::BAG_EXPANSION_TIERS`.
- `premium:15d` — **Premium на 15 днів**: **70 💎**; owner: `systems/timed_exp_bonus_system.py::PLANS`.
- `premium:30d` — **Premium на 30 днів**: **120 💎**; owner: `systems/timed_exp_bonus_system.py::PLANS`.

## Контракт Stage 20.5.4

Цей аудит не обирає нові ціни. Власник проєкту має надати точні нові значення для потрібних `offer_key`. Неперелічені позиції залишаються без змін.

Рекомендований формат рішення:
```text
item:501 = 150  # замінити на бажану ціну або залишити
item:502 = 50  # замінити на бажану ціну або залишити
item:602 = 35  # замінити на бажану ціну або залишити
item:728 = 20  # замінити на бажану ціну або залишити
bag:60->80 = 75  # замінити на бажану ціну або залишити
bag:80->100 = 150  # замінити на бажану ціну або залишити
premium:15d = 70  # замінити на бажану ціну або залишити
premium:30d = 120  # замінити на бажану ціну або залишити
```

## Перевірені price paths

- `premium_items`: CRYSTAL_SHOP_CATALOG → preview_crystal_shop_purchase → purchase_crystal_shop_item
- `bag_expansion`: BAG_EXPANSION_TIERS → preview_crystal_bag_expansion → purchase_crystal_bag_expansion
- `premium_duration`: PLANS → preview_exp_bonus_purchase → purchase_exp_bonus
- `wallet`: crystal_wallets + crystal_transactions; atomic debit and nonnegative balance
- `ui`: catalog/bag preview dynamic; Premium tariff buttons contain duplicated literals

## Findings

- **CONFIRMED · PRICE_001** — Eight crystal-priced offers exist: four items, two bag tiers, two Premium durations.
- **CONFIRMED · PRICE_002** — Item, bag and Premium purchases debit canonical prices atomically and store price snapshots in purchase history.
- **FOLLOW_UP_20_5_4 · PRICE_003** — Premium tariff reply buttons duplicate 70/120 as user-facing literals and must be updated with PLANS if changed.
- **OWNER_DECISION_REQUIRED · PRICE_004** — No new price is selected by this audit; Stage 20.5.4 must apply exact owner-approved values.
- **OUT_OF_SCOPE · PRICE_005** — Premium loot remains undecided and is not part of crystal price mutation.

## Обмеження

- Premium loot залишається `UNDECIDED` і не впливає на цей аудит.
- Stage 20.5.4 має змінювати canonical owner, user-facing тексти, preview, фактичне списання та regression contracts одним узгодженим patch.
- Ручна перевірка цього read-only audit не потрібна.
