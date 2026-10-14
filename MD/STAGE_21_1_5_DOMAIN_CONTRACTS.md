# ROM Stage 21.1.5 - доменні контракти V1 для V2

- **Статус:** `GO`
- **Проаналізовано модулів:** `244`
- **Проаналізовано symbols:** `2939`
- **Контрактних доменів:** `10`
- **Cross-domain modules:** `86`
- **Owner review modules:** `24`

## Домени

### `account`

- Modules: **14**
- Public symbols: **64**
- Persistence contexts: **30**
- Invariants: capacity, idempotency, level_gate, non_negative_balance, ownership, state_transition, transactionality
- V2 package: `rom_v2/domain/account`

### `character`

- Modules: **39**
- Public symbols: **319**
- Persistence contexts: **125**
- Invariants: capacity, idempotency, level_gate, non_negative_balance, ownership, reservation, state_transition, transactionality
- V2 package: `rom_v2/domain/character`

### `stats`

- Modules: **38**
- Public symbols: **245**
- Persistence contexts: **46**
- Invariants: capacity, idempotency, level_gate, non_negative_balance, ownership, reservation, state_transition, transactionality
- V2 package: `rom_v2/domain/stats`

### `combat`

- Modules: **60**
- Public symbols: **327**
- Persistence contexts: **35**
- Invariants: capacity, idempotency, level_gate, non_negative_balance, ownership, reservation, state_transition, transactionality
- V2 package: `rom_v2/domain/combat`

### `inventory_equipment`

- Modules: **62**
- Public symbols: **925**
- Persistence contexts: **304**
- Invariants: capacity, idempotency, level_gate, non_negative_balance, ownership, reservation, state_transition, transactionality
- V2 package: `rom_v2/domain/inventory`

### `economy`

- Modules: **18**
- Public symbols: **551**
- Persistence contexts: **170**
- Invariants: capacity, idempotency, level_gate, non_negative_balance, ownership, reservation, state_transition, transactionality
- V2 package: `rom_v2/domain/economy`

### `quests_progression`

- Modules: **66**
- Public symbols: **460**
- Persistence contexts: **59**
- Invariants: capacity, idempotency, level_gate, non_negative_balance, ownership, reservation, state_transition, transactionality
- V2 package: `rom_v2/domain/quests`

### `world_travel`

- Modules: **43**
- Public symbols: **98**
- Persistence contexts: **25**
- Invariants: capacity, idempotency, level_gate, non_negative_balance, ownership, reservation, state_transition, transactionality
- V2 package: `rom_v2/domain/world`

### `social`

- Modules: **11**
- Public symbols: **213**
- Persistence contexts: **74**
- Invariants: capacity, idempotency, level_gate, non_negative_balance, ownership, reservation, state_transition, transactionality
- V2 package: `rom_v2/domain/social`

### `cross_cutting`

- Modules: **0**
- Public symbols: **0**
- Persistence contexts: **0**
- Invariants: не визначено статично
- V2 package: `rom_v2/application`

## Загальний V2 contract

- Domain logic не імпортує Telegram SDK, sqlite3, V1 `db` або `db_modules`.
- Application use cases оркеструють domain services через ports та Unit of Work.
- Infrastructure реалізує repositories, Telegram adapters, clock, random і persistence.
- Content проходить schema validation і не містить runtime mutation logic.
- Accepted V1 поведінка переноситься як explicit contract tests, а не як імпорт V1 runtime.
- Cross-domain операції мають одного application owner і не дублюють authoritative formulas.
- Production DB/WAL/SHM не відкривалися та не змінювалися.

## Review queues

- Owner review: **24** modules.
- Cross-domain: **86** modules.
- Persistence-coupled domain candidates: **59** modules.
- Missing-doc public symbols: **1549** symbols.

## Наступний етап

Stage 21.1.6 - dependency graph, cycles і заборонені V2 dependency directions.
