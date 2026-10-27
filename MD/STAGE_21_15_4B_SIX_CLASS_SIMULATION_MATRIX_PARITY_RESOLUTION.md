# Stage 21.15.4b — Six-class simulation matrix parity resolution

- Status: **PASS**
- Decision: **PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED**
- Simulator executed: **NO**
- Long simulation executed: **NO**
- Production SQLite / `.env`: **NOT OPENED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Canonical six-class matrix

- `warrior` — Воїн
- `knight` — Лицар
- `scout` — Скаут
- `rogue` — Розбійник
- `mage` — Маг
- `priest` — Жрець

## Resolved contracts

### matrix_scope
- Status: **RESOLVED**
- The canonical matrix contains exactly six classes: warrior, knight, scout, rogue, mage and priest. Scout is one row in the matrix, not the simulator default or sole acceptance subject.

### execution_scope
- Status: **RESOLVED**
- Stage 21.15.4c prepares and contract-tests all six class adapters but must not execute long 1-to-target-level simulations, balance calibration, large trial batches or production-duration runs.

### short_acceptance_matrix
- Status: **RESOLVED**
- Automated acceptance is a fast parameterized matrix: canonical character fixture, production stat snapshot, equipment compatibility, skill/loadout resolution, deterministic encounter construction, bounded combat turns and result serialization for each of the six classes.

### canonical_class_identity
- Status: **RESOLVED**
- Class keys remain the existing canonical English identifiers. Ukrainian labels are presentation metadata only and must not alter identity, formulas or persistence keys.

### stats_and_formulas
- Status: **RESOLVED**
- Simulation adapters must call existing production character creation, stat snapshot, HP, MP, PATK/MATK, PDEF/MDEF and combat services. Stage 21.15.4c may not copy or fork formulas into simulator-only code.

### equipment_and_runes
- Status: **RESOLVED**
- Equipment slot, hand, class compatibility and class-rune decisions come from existing production policies and services. No six-class compatibility table may be invented inside the simulator adapter.

### skills_and_mana
- Status: **RESOLVED**
- Skill availability, mana costs, cooldowns and combat decisions are resolved through existing production-domain contracts. Missing production evidence must fail closed rather than creating simulator-only skills or fallback rules.

### clock_and_rng
- Status: **RESOLVED**
- All short scenarios use injected Clock and seeded RandomSource/SimulationRng adapters. Wall-clock reads and unseeded module-global random calls are prohibited in acceptance paths.

### sandbox_repositories
- Status: **RESOLVED**
- The matrix uses isolated in-memory/sandbox repositories and an explicit Unit of Work. It must not open production game.db, inherit local player state, or commit through production persistence adapters.

### result_contract
- Status: **RESOLVED**
- Each class produces the same structural result schema with class key, fixture identity, deterministic seed, stat snapshot, equipment/skill resolution, bounded-turn trace summary and validation outcome. Numeric balance approval is explicitly out of scope.

### flat_domain_layout
- Status: **RESOLVED**
- Implementation must preserve the flat domain layout. Any new domain contract belongs in a flat rom_v2/domain/*.py module; a nested six_class_simulation_matrix package is unauthorized.

## Stage 21.15.4c authorization

### Allowed

- Flat API-ready six-class matrix contract and adapters.
- Parameterized deterministic fixtures for all six classes.
- Short bounded smoke scenarios and contract tests.
- Production-domain service reuse through existing ports.
- In-memory/sandbox repositories and explicit Unit of Work.

### Forbidden

- Long 1-to-target-level simulations.
- Large Monte Carlo or balance-calibration batches.
- Scout-only acceptance or a hard-coded default Scout path.
- New class formulas, skills, equipment compatibility, runes, items or balance values.
- Simulator-only copies of production formulas.
- Production SQLite, Telegram or runtime wiring.
- Nested rom_v2/domain package creation.

Stage 21.15.4c must prepare all six classes with short deterministic checks only. Full simulations remain deferred.
