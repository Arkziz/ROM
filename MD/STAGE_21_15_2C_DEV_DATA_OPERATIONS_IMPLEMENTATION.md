# Stage 21.15.2c — DEV data operations implementation

- Status: **API_READY_IMPLEMENTED**
- Layout: flat `rom_v2/domain/dev_data_operations.py`
- Operations: generic Give / Reset / Set application boundary only
- Authorization: required before lookup or side effects
- Mutation: delegated to application/repository ports, never direct SQL
- Atomicity: explicit Unit of Work commit/rollback
- Replay: operation receipt prevents duplicate mutation
- Runtime, Telegram and production persistence: **NOT CONNECTED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

No V1 operation names, quantities, caps, reset scopes, repositories or SQL statements are invented here. Concrete adapters remain outside this API-ready stage.
