# Stage 21.7.4 — V1 equipment level-policy audit

## Decision

- Status: `PASS`
- Conclusion: `GO_TO_SEMANTIC_REFINEMENT`
- V1 Python files scanned: `275`
- Candidate owner files: `182`
- Candidate functions: `1018`
- Unresolved contracts: `0`

## Contract discovery

- `GENERATOR_INPUT_LEVEL`: `EVIDENCE_FOUND` (150 evidence records, 28 files)
- `PERSISTED_LEVEL_FIELD`: `EVIDENCE_FOUND` (178 evidence records, 42 files)
- `SHOP_LEVEL_SEMANTICS`: `EVIDENCE_FOUND` (155 evidence records, 28 files)
- `LOOT_LEVEL_SEMANTICS`: `EVIDENCE_FOUND` (1124 evidence records, 125 files)
- `PREVIEW_PROMOTION_LEVEL`: `EVIDENCE_FOUND` (1314 evidence records, 140 files)
- `EQUIP_LEVEL_VALIDATION`: `EVIDENCE_FOUND` (1119 evidence records, 87 files)
- `DEV_LEVEL_PARITY`: `EVIDENCE_FOUND` (1122 evidence records, 125 files)
- `SIMULATOR_LEVEL_PARITY`: `EVIDENCE_FOUND` (1253 evidence records, 139 files)
- `SHOP_LOOT_SEMANTIC_EQUIVALENCE`: `EVIDENCE_FOUND` (1423 evidence records, 150 files)

## Audit boundary

This patch is static and read-only. V1 modules were not imported or executed, SQLite was not opened, production files were not mutated, migrations 001-004 stayed active and unchanged, and runtime generation policy remained unchanged.

This narrow audit resolves whether V1 uses item_level as the canonical generated-equipment level semantic, whether required_level is a distinct field or a presentation/validation alias, and whether shop, loot, preview promotion, equip validation, DEV and simulator preserve the same semantic.

## Manual game check

`NOT_REQUIRED`. This is a read-only audit.
