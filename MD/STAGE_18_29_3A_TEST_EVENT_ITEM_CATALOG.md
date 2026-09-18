# ROM Stage 18.29.3a: Test Event Item Catalog

Persistent canonical item rows are enabled for the disabled `test_event_2026` package.

- ID 4000: `🧪 Експериментальний жетон`, material, common, stack 999, sell price 0.
- ID 4001: `🎁 Пам’ятний знак випробування`, collectible, uncommon, stack 10, sell price 0.
- Both definitions explicitly deny trade, sale and auction through event item policy.
- Startup `seed_items()` invokes the canonical event catalog adapter.
- Seeding is idempotent and uses the registered event package as source of truth.
- Items remain resolvable while the event runtime is disabled.
- No inventory quantity, event statistic, exchange or Telegram UI is created here.
