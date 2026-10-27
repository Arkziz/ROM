# Stage 21.15.4a — Six-class simulation matrix contract refinement

- Status: **PASS**
- Decision: **REFINED_SIX_CLASS_PARITY_RESOLUTION_REQUIRED**
- Next action: **GO_TO_SIX_CLASS_PARITY_RESOLUTION**
- Simulator executed: **NO**
- Long simulation executed: **NO**
- Production SQLite / `.env`: **NOT OPENED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Canonical six-class matrix

- `warrior` — Воїн: short deterministic contracts only; long run now = **NO**
- `knight` — Лицар: short deterministic contracts only; long run now = **NO**
- `scout` — Скаут: short deterministic contracts only; long run now = **NO**
- `rogue` — Розбійник: short deterministic contracts only; long run now = **NO**
- `mage` — Маг: short deterministic contracts only; long run now = **NO**
- `priest` — Жрець: short deterministic contracts only; long run now = **NO**

## Refined contract

### class_roster
- Status: **REFINED**
- The matrix is exactly six classes: warrior, knight, scout, rogue, mage and priest. Scout is one row, not the default or sole acceptance class.

### matrix_shape
- Status: **REFINED**
- Every short contract test is parametrized over all six classes. Adding one Scout-only test does not satisfy the matrix contract.

### execution_scope
- Status: **REFINED**
- Stage 21.15.4 must not run long 1-to-target-level progression, balance calibration, performance sampling or production-sized simulation batches. Only bounded deterministic construction and short combat smoke checks are authorized.

### production_reuse
- Status: **REFINED**
- Character creation, class catalog, derived stats, combat actor stats, equipment generation and full-stat snapshots must reuse production V2 services/domain logic. Simulator-only copies of formulas or class coefficients are prohibited.

### clock_rng
- Status: **REFINED**
- Short checks use injected Clock and seeded RandomSource adapters. Wall-clock access and module-global random state are prohibited inside the matrix contract.

### repository_isolation
- Status: **REFINED**
- Fixtures use isolated in-memory or temporary sandbox repositories/UoW and never production game.db or accumulated local player state.

### combat_smoke
- Status: **REFINED**
- For each class, prepare one deterministic encounter and execute only a bounded number of turns sufficient to validate actor construction, legal skill/action selection, resource accounting and serialization. Victory, leveling or balance conclusions are not required.

### reporting
- Status: **REFINED**
- Output records one row per class with fixture creation, stats, compatibility, loadout, encounter setup, bounded-turn and serialization status. No aggregate balance ranking is authorized.

### flat_domain
- Status: **REFINED**
- Any Stage 21.15.4 implementation owner must remain a flat rom_v2/domain/*.py module or application adapter consistent with Stage 21.15.1d; no nested domain package is authorized.

## Unresolved for parity

- **exact_short_turn_bound**: Parity resolution must select the smallest deterministic turn bound supported by existing combat APIs without converting this stage into a full simulation.
- **class_specific_skill_fixture_owner**: Exact skill loadouts and mana-capable class behavior must come from authoritative production owners, not hard-coded refinement data.
- **equipment_and_rune_fixture_owner**: Exact equipment and class-rune fixtures must be resolved from production compatibility policy for all six classes.
- **sandbox_repository_implementation**: Parity resolution must identify the existing isolated UoW/repository implementation to reuse and forbid production SQLite access.
- **catalog_source_confirmation**: If static source scanning does not expose all six keys in class_catalog.py, parity resolution must use accepted class-catalog evidence without inventing aliases.

## Prohibitions

- No Scout-only acceptance path.
- No long progression simulation or six-class balance run in this stage.
- No production game.db, .env, Telegram runtime or main.py execution.
- No duplicate formulas, class stats, skills, runes, equipment compatibility or reward rules.
- No nested rom_v2/domain package.

Stage 21.15.4b must resolve these items without running a long simulation. Stage 21.15.4c may implement only a bounded deterministic six-class contract matrix.
