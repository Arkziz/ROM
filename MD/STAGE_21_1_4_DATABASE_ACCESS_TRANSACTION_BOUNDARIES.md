# ROM Stage 21.1.4 - database access і transaction boundaries

- **Статус:** `GO`
- **Проаналізовано runtime/content/manual-review модулів:** `244`
- **Модулів із DB activity:** `59`
- **Direct connection calls:** `21`
- **SQL operations:** `1224`
- **DB facade calls:** `318`
- **Commit/Rollback calls:** `532`

## Review queues

- Handler direct SQL: **13** contexts.
- System direct SQL: **448** contexts.
- Mutation without explicit boundary: **43** contexts.
- Partial mutation risk: **46** contexts.
- Commit without observed rollback: **84** contexts.
- Exact-once relevant paths: **119** contexts.
- Dynamic SQL: **145** operations.

## V2 contract

- SQL дозволений тільки в `infrastructure/database` repositories та migration/bootstrap tools.
- handlers, domain і application services не відкривають SQLite connection і не виконують raw SQL.
- Multi-step mutation виконується в одній Unit of Work з явним commit/rollback contract.
- Ledger, reservations, purchases, rewards, trades, auctions і settlement мають idempotency/exact-once contract.
- Static findings є audit candidates; вони не доводять runtime defect без contract/runtime verification.
- Production DB/WAL/SHM не відкривалися та не змінювалися.

## Наступний етап

Stage 21.1.5 - доменні контракти account, character, stats, combat, inventory, economy та social systems.
