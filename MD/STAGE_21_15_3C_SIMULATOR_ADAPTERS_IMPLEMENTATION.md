# Stage 21.15.3c — Simulator adapters implementation

## Result

- Status: **API_READY_IMPLEMENTED**
- Layout: **flat** `rom_v2/domain/simulator_adapters.py`
- Clock: injected deterministic UTC clock, forward-only
- RNG: seeded `random.Random` instance with draw accounting; no global reseeding
- Repository: isolated deep-copy in-memory store with explicit begin/commit/rollback
- Gameplay formulas: **NOT DUPLICATED**
- Production SQLite / `.env`: **NOT OPENED**
- Runtime, Telegram and production persistence: **NOT CONNECTED**
- Simulator run: **NOT EXECUTED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

The module is an API-ready adapter boundary. Production application/domain
services remain responsible for combat, stats, rewards, loot, progression and
equipment formulas. The sandbox repository never opens a path or database.
