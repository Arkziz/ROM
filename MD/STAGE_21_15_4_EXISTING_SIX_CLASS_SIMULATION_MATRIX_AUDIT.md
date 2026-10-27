# Stage 21.15.4 — Existing six-class simulation matrix audit

- Status: **PASS**
- Conclusion: **PASS_REVIEW_REQUIRED**
- Next action: **GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW**
- Required classes: **6/6 matrix**
- Long simulation executed: **NO**
- Simulator executed: **NO**
- Production mutation: **NO**
- Production SQLite / `.env`: **NOT OPENED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Six-class evidence matrix

### `warrior`
- Evidence findings: 60
- Candidate files: 27
- `character_creation` candidate files: 9
- `primary_stats` candidate files: 26
- `derived_stats` candidate files: 11
- `equipment` candidate files: 16
- `runes` candidate files: 9
- `skills` candidate files: 11
- `combat` candidate files: 26
- `potions` candidate files: 8
- `inventory` candidate files: 15
- `repair` candidate files: 8
- `enhancement` candidate files: 5
- `progression` candidate files: 14
- `clock_rng` candidate files: 12
- `sandbox` candidate files: 2
- `reporting` candidate files: 14

### `knight`
- Evidence findings: 31
- Candidate files: 18
- `character_creation` candidate files: 9
- `primary_stats` candidate files: 17
- `derived_stats` candidate files: 11
- `equipment` candidate files: 12
- `runes` candidate files: 7
- `skills` candidate files: 9
- `combat` candidate files: 17
- `potions` candidate files: 8
- `inventory` candidate files: 11
- `repair` candidate files: 7
- `enhancement` candidate files: 5
- `progression` candidate files: 10
- `clock_rng` candidate files: 10
- `sandbox` candidate files: 1
- `reporting` candidate files: 9

### `scout`
- Evidence findings: 42
- Candidate files: 19
- `character_creation` candidate files: 9
- `primary_stats` candidate files: 18
- `derived_stats` candidate files: 11
- `equipment` candidate files: 13
- `runes` candidate files: 7
- `skills` candidate files: 9
- `combat` candidate files: 18
- `potions` candidate files: 8
- `inventory` candidate files: 12
- `repair` candidate files: 7
- `enhancement` candidate files: 5
- `progression` candidate files: 10
- `clock_rng` candidate files: 10
- `sandbox` candidate files: 1
- `reporting` candidate files: 9

### `rogue`
- Evidence findings: 28
- Candidate files: 17
- `character_creation` candidate files: 8
- `primary_stats` candidate files: 16
- `derived_stats` candidate files: 10
- `equipment` candidate files: 11
- `runes` candidate files: 6
- `skills` candidate files: 8
- `combat` candidate files: 16
- `potions` candidate files: 8
- `inventory` candidate files: 10
- `repair` candidate files: 6
- `enhancement` candidate files: 4
- `progression` candidate files: 10
- `clock_rng` candidate files: 10
- `sandbox` candidate files: 1
- `reporting` candidate files: 9

### `mage`
- Evidence findings: 205
- Candidate files: 57
- `character_creation` candidate files: 10
- `primary_stats` candidate files: 54
- `derived_stats` candidate files: 21
- `equipment` candidate files: 27
- `runes` candidate files: 19
- `skills` candidate files: 27
- `combat` candidate files: 56
- `potions` candidate files: 11
- `inventory` candidate files: 27
- `repair` candidate files: 23
- `enhancement` candidate files: 11
- `progression` candidate files: 27
- `clock_rng` candidate files: 20
- `sandbox` candidate files: 4
- `reporting` candidate files: 31

### `priest`
- Evidence findings: 37
- Candidate files: 21
- `character_creation` candidate files: 10
- `primary_stats` candidate files: 20
- `derived_stats` candidate files: 13
- `equipment` candidate files: 13
- `runes` candidate files: 7
- `skills` candidate files: 10
- `combat` candidate files: 20
- `potions` candidate files: 10
- `inventory` candidate files: 12
- `repair` candidate files: 8
- `enhancement` candidate files: 5
- `progression` candidate files: 12
- `clock_rng` candidate files: 10
- `sandbox` candidate files: 1
- `reporting` candidate files: 10

## Required semantic refinement

- Which production owner creates each of the six classes and supplies canonical primary/derived stats?
- Which production services own PATK/MATK, HP/MP, PDEF/MDEF and class skill formulas for every class?
- Which equipment, off-hand, two-hand and class-rune compatibility rules apply to every class?
- Which skills, mana costs, cooldowns and deterministic combat decisions are available per class?
- Which simulator paths contain single-class assumptions, hard-coded class values or class-specific shortcuts?
- Which short deterministic fixture proves each class can be created, equipped, assigned skills and advanced through a controlled encounter setup?
- Which production services can be reused without copying formulas into simulator-only code?
- How will six-class result serialization identify class, fixture, seed and controlled outcome without running long progression simulations?

## Explicit prohibitions

- Do not use Scout or any other class as the sole baseline for Stage 21.15.4.
- Do not run level 1-to-10, multi-hour or other long simulations in audit/refinement/implementation checks.
- Do not invent class stats, formulas, skills, equipment compatibility, runes, potions or combat policy.
- Do not copy production formulas into simulator-only implementations when a production domain/service owner exists.
- Do not open production SQLite or .env, start main.py, connect Telegram or mutate runtime state.
- Do not create nested rom_v2/domain packages; preserve the flat-domain architecture.

This audit covers all six classes equally and does not execute a long simulation.
