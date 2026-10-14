# ROM Stage 21.1.8 - background jobs, time і concurrency

- **Статус:** `GO`
- **Проаналізовано модулів:** `244`
- **Task sites:** `0`
- **Wait sites:** `9`
- **Thread/process sites:** `5`
- **Lock sites:** `8`
- **Time calls:** `140`
- **Loops:** `782`

## Review queues

- Job-like functions: **120**
- Infinite loops without wait: **1**
- Module-level tasks: **0**
- Mutable global modules: **18**
- Naive datetime sites: **109**
- Tasks without lifecycle signal: **0**

## V2 lifecycle contract

- Background jobs запускає єдиний scheduler/lifecycle manager.
- Кожна task має owner, cancellation, graceful shutdown та exception reporting.
- Busy loops без await/sleep заборонені.
- Domain отримує Clock і Random через ports.
- Persistence timestamps: UTC; presentation timezone: Europe/Kyiv.
- Shared mutable global state заборонений.
- Retry/backoff має bounded attempts, jitter та idempotency contract.
- Production DB/WAL/SHM не відкривалися і не змінювалися.

## Наступний етап

Stage 21.1.9 - inventory observability, logging, errors і audit trails.
