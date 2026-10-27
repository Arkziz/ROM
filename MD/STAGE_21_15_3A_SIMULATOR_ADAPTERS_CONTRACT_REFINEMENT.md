# Stage 21.15.3a — Simulator adapters contract refinement

- Status: **PASS**
- Decision: **REFINED_PARITY_RESOLUTION_REQUIRED**
- Next action: **GO_TO_PARITY_RESOLUTION**
- Production mutation: **NO**
- Simulator executed: **NO**
- Production SQLite / `.env`: **NOT OPENED**
- Manual verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Refined contract

### clock_boundary
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Simulator time must be supplied through an injected deterministic clock. SimulationClock is V1 evidence; V2 already owns a Clock port. Stage 21.15.3b must resolve the adapter mapping and enumerate any simulator path that still reads wall-clock time directly.
- Owners: `systems/simulation/clock.py`, `rom_v2/application/ports/clock.py`, `systems/simulation/parity_foundation.py`

### rng_boundary
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: One caller-supplied seed must determine a run. SimulationRng owns seeded draws, draw count and state evidence in V1; V2 RandomSource remains the application port. Global/module random injection is compatibility evidence and must be scoped and restored, not treated as a preferred V2 boundary.
- Owners: `systems/simulation/rng.py`, `systems/simulation/rng_adapter.py`, `rom_v2/application/ports/random_source.py`

### sandbox_isolation
- Status: **REFINED**
- Contract: A simulation run must use isolated state or explicit in-memory/fake repositories and must not open accumulated production game.db state. No adapter may silently fall back to production SQLite, shared mutable globals, or live Telegram/runtime state.
- Owners: `systems/simulation/parity_foundation.py`, `rom_v2/application/ports/repositories.py`

### repository_and_uow
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Simulator repositories must satisfy existing V2 repository and Unit-of-Work contracts. A run has explicit begin/commit-or-rollback semantics in its sandbox; production repository adapters and direct SQL are not simulator defaults.
- Owners: `rom_v2/application/ports/repositories.py`, `rom_v2/infrastructure/persistence`

### production_domain_reuse
- Status: **REFINED**
- Contract: Simulator adapters orchestrate production domain/application services. They must not duplicate combat, derived-stat, equipment-generation, enhancement, durability, EXP, reward, loot or repair formulas when an authoritative production owner exists.
- Owners: `systems/simulation/canonical_rules.py`, `rom_v2/domain/damage_engine.py`, `rom_v2/domain/equipment_generation.py`, `rom_v2/domain/full_stat_snapshot.py`, `rom_v2/domain/enhancement.py`

### simulator_factories
- Status: **REFINED**
- Contract: Existing for_simulator factories are approved reuse seams only for the behavior they explicitly construct. They do not authorize parallel formula implementations or production persistence access.
- Owners: `rom_v2/application/equipment_generation_service.py`, `rom_v2/application/full_stat_snapshot_service.py`

### fixtures
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Fixtures must be deterministic, minimal and explicit for accounts, characters, primary stats, equipment, runes, resources and encounters. Existing numeric fixture values are evidence, not new production content or balance policy.
- Owners: `systems/simulation/models.py`, `systems/simulation/config.py`, `tests_v2`

### repeatability_and_recovery
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Same configuration, seed, clock and fixture must reproduce the same result and draw/state evidence. Failed runs must discard sandbox mutations; retries must start from a fresh fixture rather than partially reused state.
- Owners: `systems/simulation/rng.py`, `systems/simulation/parity_foundation.py`, `systems/simulation/reporting.py`

### reporting_boundary
- Status: **REFINED**
- Contract: Reports may describe deterministic inputs, outputs, seed, clock, draw counts and warnings. Reporting must not mutate production state or promote sandbox candidate settings to canonical gameplay policy.
- Owners: `systems/simulation/reporting.py`, `systems/simulation/production_parity.py`

### flat_domain_layout
- Status: **REFINED**
- Contract: Any Stage 21.15.3 implementation must use the flat module rom_v2/domain/simulator_adapters.py. A nested rom_v2/domain/simulator_adapters package is not authorized.
- Owners: `rom_v2/domain`

## Unresolved for parity resolution

- **clock_adapter_mapping**: Resolve exact SimulationClock-to-Clock semantics, start instant, advance rules and all remaining wall-clock reads used by simulator paths.
- **rng_adapter_coverage**: Resolve the exact seeded source, supported draw methods, draw-count/state-digest contract, and every global/module random compatibility injection that must be eliminated or safely restored.
- **sandbox_repository_inventory**: Map each simulator state mutation to an isolated repository/UoW or pure state owner and prove that production SQLite cannot be selected implicitly.
- **formula_reuse_matrix**: For combat, stats, equipment, enhancement, loot, EXP, rewards, repair and survival, identify the exact authoritative production callable and every simulator duplicate or compatibility copy.
- **fixture_contract**: Resolve canonical deterministic fixture builders and which numeric values are parity fixtures rather than production defaults or new content.
- **run_transaction_and_recovery**: Resolve run begin, success, failure, rollback, retry and report-write boundaries, including whether reports survive a failed sandbox run.
- **candidate_sandbox_separation**: Identify candidate-only PvP/balance sandboxes and prevent their parameters from being interpreted as approved live policy.

## Superseded interpretations

- Keyword evidence alone does not establish simulator ownership.
- Direct SQL in legacy systems is not an approved simulator repository adapter.
- Global random or temporary module injection is not the preferred V2 RNG boundary.
- Sandbox candidate parameters are not canonical live balance policy.
- Simulator-local formula copies are not authoritative where production domain/application owners exist.

## Flat-domain policy

- Required future module: `rom_v2/domain/simulator_adapters.py`
- Nested package: **NOT AUTHORIZED**

Stage 21.15.3b must resolve every listed parity question before implementation authorization.
