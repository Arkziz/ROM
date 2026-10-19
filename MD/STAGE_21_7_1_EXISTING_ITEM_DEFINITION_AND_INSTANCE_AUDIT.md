# Stage 21.7.1 — Existing V1 item definition and instance audit

## Decision

- Status: `PASS`
- Conclusion: `GO`
- V1 Python files scanned: `1010`
- Candidate functions: `3007`
- Candidate constants: `5665`
- SQL evidence records: `1461`

## Safety and authority

V1 modules were not imported or executed. SQLite was not opened. The existing V2 item/equipment/reservation tables remain `PROVISIONAL_RESERVED` and were used only as comparison targets, never as proof of V1 semantics.

## Evidence categories

- `ITEM_DEFINITION`: 884 functions, 960 constants, 346 files
- `ITEM_INSTANCE_IDENTITY`: 433 functions, 556 constants, 94 files
- `ID_NAMESPACE`: 335 functions, 203 constants, 197 files
- `STACK_QUANTITY`: 479 functions, 617 constants, 198 files
- `OWNERSHIP`: 1952 functions, 2654 constants, 399 files
- `BINDING_POLICY`: 211 functions, 201 constants, 140 files
- `GENERATED_EQUIPMENT`: 207 functions, 261 constants, 129 files
- `DURABILITY`: 235 functions, 213 constants, 102 files
- `RUNE_ATTACHMENT`: 284 functions, 484 constants, 144 files
- `ENHANCEMENT`: 369 functions, 415 constants, 199 files
- `RESERVATION`: 803 functions, 1211 constants, 170 files
- `QUEST_ITEM_STORAGE`: 120 functions, 110 constants, 87 files
- `PERSISTENCE_SQL`: 745 functions, 665 constants, 219 files

## Required interpretation before mutation

The JSON report contains exact source bodies, line numbers, literals, SQL fragments, dependencies, and consumers. Stage 21.7.1a must use that evidence to produce one explicit parity matrix covering definition identity, permanent instance identity, generated/preview identity, namespaces, stacking, ownership, binding, reservation, quest-item storage, runes, enhancement, durability, and schema differences.

No value discovered by broad category search is automatically authoritative. If owners conflict or a semantic rule remains ambiguous, implementation must stop and request a decision rather than inventing a contract.

## Provisional schema rule

Migration `001_v2_baseline` is not rewritten. If the audited V1 contract differs from provisional item tables, Stage 21.7.1a must add a new forward migration and update the provisional governance state only after parity tests pass.

## Manual game check

`NOT_REQUIRED`. This patch is a static, read-only audit.
