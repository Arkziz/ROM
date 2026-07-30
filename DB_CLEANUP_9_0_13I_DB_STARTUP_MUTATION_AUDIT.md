# ROM 9.0.13i — DB Startup Mutation Audit

Generated: `2026-07-30T06:27:51`

## Safety

- Real `game.db` imported through `db.py`: **no**
- Runtime probe target: **temporary copy of game.db**
- Real database SHA/size/mtime unchanged: **True**
- Sandbox quick check before import: **ok**
- Sandbox quick check after first import: **ok**
- Sandbox quick check after second import: **ok**
- Gameplay files changed: **0**
- Real database rows changed: **0**

## Module-scope calls in db.py

- `db.py:6589` calls `ensure_refine_material_stack_sizes()` inside `Try` at module scope.
- `db.py:7059` calls `migrate_active_contracts_target_kills_to_5()` inside `Try` at module scope.

## Function mutation contracts

### `ensure_refine_material_stack_sizes()`

- Definition: `db.py:6548-6567`
- Commit calls: **1**
- Mutating SQL literals: `['UPDATE items SET max_stack=? WHERE id IN (401, 402)']`

### `migrate_active_contracts_target_kills_to_5()`

- Definition: `db.py:7035-7055`
- Commit calls: **1**
- Mutating SQL literals: `['UPDATE user_active_contracts SET target_kills=5 WHERE target_kills > 5', 'UPDATE user_active_contracts SET completed=1, current_kills=5 WHERE target_kills=5 AND current_kills >= 5 AND reward_claimed=0']`

## Project call sites

- `ensure_refine_material_stack_sizes`: `[{'file': 'db.py', 'line': 6575, 'top_level': False}, {'file': 'db.py', 'line': 6589, 'top_level': True}]`
- `migrate_active_contracts_target_kills_to_5`: `[{'file': 'db.py', 'line': 7059, 'top_level': True}, {'file': 'systems/contract_system.py', 'line': 574, 'top_level': False}]`

## Sandbox import behavior

- First import process exit code: **0**
- First import stdout: `[OK] sandbox import db`
- First import stderr: ``
- Database file fingerprint changed after first import: **False**
- Tables changed after first import: `[]`
- Second import process exit code: **0**
- Database file fingerprint changed after second import: **False**
- Tables changed after second import: `[]`
- Hidden import mutations reproduced: **False**
- Repeated-import mutations reproduced: **False**

## Explicit startup coverage

- Non-module-scope call sites: `[{'name': 'ensure_refine_material_stack_sizes', 'file': 'db.py', 'line': 6575, 'top_level': False}, {'name': 'migrate_active_contracts_target_kills_to_5', 'file': 'systems/contract_system.py', 'line': 574, 'top_level': False}]`
- Explicit startup owner currently exists for both operations: **True**

## Diagnosis

- `db.py` contains hidden maintenance execution at module scope.
- A plain `import db` can therefore perform SQL writes or commits, depending on current database state.
- The two maintenance operations have different responsibilities and should be invoked explicitly during startup after migrations and schema initialization.
- Removing only the module-scope calls without adding one explicit startup owner would silently disable maintenance.

## Recommended next patch

1. Add one public `run_db_startup_maintenance()` function in `db.py`.
2. Call `ensure_refine_material_stack_sizes()` and `migrate_active_contracts_target_kills_to_5()` from that function in a fixed order.
3. Remove their module-scope invocations from `db.py`.
4. Invoke `run_db_startup_maintenance()` explicitly from `main.py` after migration execution and before seed/handler startup.
5. Make the startup function return a structured summary for logging and tests.
6. Add a subprocess test proving plain `import db` leaves a database copy byte-for-byte unchanged.
7. Add an isolated test proving explicit startup maintenance remains idempotent.
8. Preserve the current migration and refine-material business rules.

Suggested next patch: `patch_9_0_13j_explicit_db_startup_maintenance.py`
