# Stage 21.15.3b — simulator adapters parity resolution

- Status: **PASS**
- Decision: **PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED**
- Production mutation: **NO**
- Simulator executed: **NO**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Resolved parity contract

### clock_adapter_mapping
- Status: **RESOLVED**
- Contract: Use the existing V2 Clock port through a deterministic aware-UTC simulator adapter with explicit non-negative advance. No implicit wall-clock reads are authorized.
- Owners: `rom_v2/application/ports/clock.py`, `systems/simulation/clock.py`

### rng_adapter_coverage
- Status: **RESOLVED**
- Contract: One explicit seed owns one RandomSource-compatible stream and draw count. Global/module random injection is compatibility-only, scoped and restored, never the V2 default.
- Owners: `rom_v2/application/ports/random_source.py`, `systems/simulation/rng.py`, `systems/simulation/rng_adapter.py`

### sandbox_repository_inventory
- Status: **RESOLVED**
- Contract: Use explicit isolated in-memory/fake adapters satisfying existing V2 repository ports. Production SQLite, live Telegram state, shared mutable globals and implicit production fallback are forbidden.
- Owners: `rom_v2/application/ports/repositories.py`, `systems/simulation/parity_foundation.py`

### formula_reuse_matrix
- Status: **RESOLVED**
- Contract: Combat, stats, equipment, enhancement, loot, EXP, rewards, repair and survival must call authoritative production domain/application owners; simulator-local formula copies cannot become a second owner.
- Owners: `rom_v2/domain`, `rom_v2/application`

### fixture_contract
- Status: **RESOLVED**
- Contract: Deterministic fixtures are explicit run/test inputs. Their values are parity samples, not live defaults, approved balance, or new content.
- Owners: `systems/simulation/config.py`, `systems/simulation/models.py`

### run_transaction_and_recovery
- Status: **RESOLVED**
- Contract: Each run starts from fresh isolated state. Success returns an immutable result; failure discards sandbox mutations. Retry rebuilds state from the same explicit seed, clock and config.
- Owners: `systems/simulation/parity_foundation.py`, `systems/simulation/reporting.py`

### candidate_sandbox_separation
- Status: **RESOLVED**
- Contract: Candidate-only PvP/balance sandboxes remain non-production; their parameters and outcomes cannot become canonical live policy without a separate approved stage.
- Owners: `systems/simulation`

### candidate_sandbox_boundary
- Status: **RESOLVED**
- Contract: Candidate and balance sandboxes are explicitly outside production parity. Their fixtures, tuning inputs and outcomes remain isolated evidence and cannot mutate or redefine live-game policy.
- Owners: `systems/simulation`, `systems/simulation/parity_foundation.py`

### determinism_contract
- Status: **RESOLVED**
- Contract: A run is reproducible only from explicit fixture state, an aware injected clock and one explicit seeded RNG stream with deterministic draw order. Wall-clock reads, unseeded global random and hidden mutable globals are forbidden.
- Owners: `systems/simulation/clock.py`, `systems/simulation/rng.py`, `systems/simulation/rng_adapter.py`, `rom_v2/application/ports/clock.py`, `rom_v2/application/ports/random_source.py`

### production_state_isolation
- Status: **RESOLVED**
- Contract: Simulator adapters must use isolated in-memory or fake repositories implementing existing V2 ports. Production SQLite, live repositories, Telegram state and implicit fallback to production state are forbidden for reads and writes.
- Owners: `systems/simulation/parity_foundation.py`, `rom_v2/application/ports/repositories.py`

## Implementation authorization

- Flat module: `rom_v2/domain/simulator_adapters.py`
- Direct SQL: **FORBIDDEN**
- Unit of Work: **REQUIRED**
- Runtime/Telegram/production persistence: **NOT CONNECTED**

## Prohibitions

- No duplicate production formulas.
- No production SQLite or live repository fallback.
- No implicit wall clock or unseeded global RNG.
- No candidate fixture value promoted to live policy.
- No runtime, Telegram, production persistence or migration wiring in Stage 21.15.3c.
- No game.db-wal/game.db-shm manipulation.
