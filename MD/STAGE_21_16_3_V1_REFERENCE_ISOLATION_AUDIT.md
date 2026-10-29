# Stage 21.16.3 - V1 reference isolation audit

- Status: **PASS**
- Mode: **READ_ONLY**
- Decision: **REFINEMENT_REQUIRED**
- Runtime blockers: **0**
- Review-required references: **5**
- Production code mutation: **NO**
- Production SQLite / `.env`: **NOT OPENED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**
- Manual game check: **NOT_REQUIRED**

## Mandatory 21.16.3a contract
1. V1 remains a read-only source for audits, confirmed behavior, formulas, rules, content evidence and parity fixtures.
2. ROM V2 runtime must not import, call, register, instantiate or fall back to V1 or future `legacy/v1`.
3. Audit tools may read V1 files explicitly, but must not execute V1 runtime modules or open production SQLite.
4. The future production check must pass with V1/legacy import roots blocked or absent from `sys.path`.
5. Missing V2 capability fails closed; it is never silently delegated to V1.

## Findings
- `rom_v2/content/story_start_path_41_50.py:13` textual_runtime_reference -> `V2StoryQuestContentRecord('start_path_049_pack_leader', 49, 'Ватажок зграї', 'BOSS', 'start_path', 5, 'start_path_048_final_perimeter', 'mercenary_head', None, 1, 'Герой перемагає Ватажка через RNG encounter або гарантований виклик.', 'Пере`: **REVIEW_REQUIRED**
- `rom_v2/domain/full_stat_snapshot.py:38` textual_runtime_reference -> `"""Precomputed flat outputs owned by equipment/refinement subsystems."""`: **REVIEW_REQUIRED**
- `rom_v2/infrastructure/telegram/adapter.py:81` textual_runtime_reference -> `handler = self._command_handlers.get(command_key)`: **REVIEW_REQUIRED**
- `rom_v2/infrastructure/telegram/callback_registry.py:50` textual_runtime_reference -> `handler = self._handlers.get(decoded.route)`: **REVIEW_REQUIRED**
- `rom_v2/structured_logging.py:64` textual_runtime_reference -> `logger.handlers.clear()`: **REVIEW_REQUIRED**

## Next action
Create `patch_21_16_3a_refine_v1_reference_isolation_contract.py`. It must convert this evidence into an enforceable direct-code/import-isolation contract without moving V1 files early.
