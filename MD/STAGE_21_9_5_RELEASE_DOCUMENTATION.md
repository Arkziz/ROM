# ROM V1 Release Documentation

## Release candidate baseline

- Branch: `develop`
- Release candidate HEAD: `e7e78f6642ded791e43e82b0b340422abe998dc3`
- Release state: **GO_PENDING_FORMAL_CLOSURE**
- Programming regulation: **Update 12 PASS**
- Production source inventory: **184/184 PASS**
- Blocking maintained tools: **13/13 PASS**
- SQLite snapshot integrity: **ok**
- SQLite foreign-key violations: **0**
- Release blockers: **0**
- Review findings: **0**
- Deferred findings: **1**

## Accepted evidence chain

1. Stage 21.9.1 release-readiness audit: `PASS_READ_ONLY`.
2. Stage 21.9.2 acceptance matrix: `PASS_READ_ONLY`.
3. Stage 21.9.3 automated release acceptance: `PASS_AUTOMATED_RELEASE_ACCEPTANCE`.
4. Stage 21.9.4 runtime/operator acceptance: `PASS_RUNTIME_AND_OPERATOR_ACCEPTANCE`.
5. Stage 21.8 runtime continuity: startup PASS, two combat exports, single reward 2/2.

## Accepted runtime behavior

- Startup reaches `BOT STARTED`.
- Notification worker starts and receives a DB connection.
- Normal combat and skill combat complete.
- Victory rewards are applied once.
- Persistent EXP, gold, loot, and daily progress were observed.
- Duplicate victory/reward, callback loop, database lock, and unhandled traceback were not observed.
- Repeat runtime was not required because accepted production source hashes did not change.

## SQLite acceptance

- Production SQLite was not opened for automated integrity acceptance.
- A byte-for-byte isolated snapshot was used.
- `PRAGMA integrity_check` returned `ok`.
- `PRAGMA foreign_key_check` returned no rows.
- Migration-ledger tables found: **2**.
- Production `game.db`, `game.db-wal`, and `game.db-shm` fingerprints remained unchanged.

## Known deferred item

`handlers/dev.py` contains four historical `register_dev_handlers` definitions. Classification: **RELEASE_DEFERRED_NON_BLOCKING**. Do not canonicalize this chain without a focused command-set and registration-order audit.

## Release boundaries

This documentation does not merge, push, deploy, tag, modify `master`, or alter gameplay. Formal Stage 21 closure remains a separate evidence-only step.

## Rollback triggers

Issue immediate `NO-GO` and stop release activity if any of the following occurs before formal closure or deployment:

- HEAD or accepted source hashes drift.
- Any blocking verifier/smoke fails.
- Startup fails to reach `BOT STARTED`.
- SQLite integrity or foreign-key checks fail.
- `database is locked`, duplicate reward, callback loop, or unhandled traceback appears.
- Production DB/WAL/SHM fingerprints change outside expected gameplay activity.
- Required configuration is missing or a secret is exposed.

## Next formal step

`GO_TO_21_9_6_V1_FORMAL_ACCEPTANCE_AND_STAGE_21_CLOSURE`
