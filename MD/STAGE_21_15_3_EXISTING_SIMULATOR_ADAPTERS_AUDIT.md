# Stage 21.15.3 — Existing simulator adapters audit

- Status: **PASS**
- Conclusion: **PASS_REVIEW_REQUIRED**
- Next action: **GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW**
- Production mutation: **NO**
- Simulator executed: **NO**
- Production SQLite / `.env`: **NOT OPENED**
- Manual verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Evidence coverage

- `clock`: 219
- `direct_sql`: 2091
- `formula`: 497
- `production_domain`: 531
- `repository`: 694
- `rng`: 803
- `sandbox`: 155
- `simulator`: 322
- `transaction`: 1439

## Required semantic refinement

- Which clock abstraction is canonical and which simulator paths still read wall-clock time directly?
- Which RNG source is injectable and seeded, and where are unseeded/global random calls used?
- Which sandbox repositories are isolated from production persistence and local accumulated game.db state?
- Which simulator formulas duplicate production domain calculations instead of invoking canonical services?
- Which adapters use direct SQL or compatibility helpers that bypass repositories and invariants?
- What transaction, rollback, repeat-execution and recovery guarantees exist for a simulation run?
- Which fixtures create deterministic accounts, characters, equipment, runes, resources and encounters?

## Prohibitions

- Do not run long simulations or mutate production/local game data.
- Do not open production SQLite or .env.
- Do not invent simulation formulas, clocks, RNG rules, repositories or fixtures.
- Future implementation must reuse production domain and preserve the flat domain layout.

This audit is evidence inventory only and does not authorize implementation.
