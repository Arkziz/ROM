# Stage 21.9.1b - Resolved EXP and level-up parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Input unresolved contracts: **5**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolution principle

The implementation contract is source-bound to the exact V1 progression configuration, pure award transition, transactional owner and level-reward calculator. No formulas, caps, point grants, event order or universal idempotency ledger may be invented.

## Resolved contracts

- `LEVEL_CAP_EXACT_SEMANTICS`: **SOURCE_BOUND_TO_CONFIGURATION_AND_PURE_TRANSITION** - Gameplay cap and EXP-at-cap behavior must be copied from the exact V1 configuration and apply_exp_award control flow; configured levels above a runtime cap do not by themselves raise the gameplay cap.
- `LEVEL_UP_POINT_AWARD`: **SOURCE_BOUND_TO_TRANSACTION_OWNER** - Point types, quantities and per-level multiplication must be taken only from apply_exp_in_transaction and its explicit callees; no generic point award may be invented.
- `MULTI_LEVEL_EVENT_ORDER`: **PURE_RESULT_THEN_SINGLE_TRANSACTIONAL_SIDE_EFFECT_SEQUENCE** - apply_exp_award calculates the complete level transition first; apply_exp_in_transaction then owns persistence and downstream side effects in its existing source order, including any per-level reward calculation.
- `INVALID_AND_BOUNDARY_INPUTS`: **MIRROR_EXACT_PURE_FUNCTION_BRANCHES** - Zero, negative, threshold, large-award and cap-boundary behavior must mirror the explicit branches, loops and return shape of apply_exp_award; V2 must add no implicit clamping or correction absent from V1.
- `IDEMPOTENCY_BOUNDARY`: **NO_UNIVERSAL_EXP_OPERATION_ID_IN_V1** - The canonical EXP entrypoint has no newly inferred universal delivery ledger. Duplicate prevention remains the responsibility of existing upstream producer contracts unless exact V1 operation-id evidence is present.

## Authorized implementation boundary

Allowed:
- pure V2 EXP-threshold and award transition matching V1
- residual EXP and multi-level result matching V1
- explicit gameplay-cap behavior matching V1
- pure result fields needed by later application adapters

Forbidden:
- runtime or Telegram wiring
- SQLite repository or UoW integration
- invented EXP table, cap, point award, event order or idempotency ledger
- changes to accepted V1 formulas or prepared configuration ranges

## Safety

V1 was inspected only as source text/AST. SQLite was not opened. `game.db-wal` and `game.db-shm` were not deleted, cleared, modified, or used for rollback.

## Next patch

`patch_21_9_1c_implement_exp_and_level_up.py`
