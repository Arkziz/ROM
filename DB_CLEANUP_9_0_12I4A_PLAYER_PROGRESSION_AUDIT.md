# ROM 9.0.12i4a - Player Progression Legacy Audit

## Scope

Read-only audit. No gameplay code, database rows, or legacy captures were changed.

## Confirmed legacy references

### `add_exp`

- Capture: `_legacy_add_exp_before_player_system_v1`
- db.py definitions at lines: [1266, 11666]
- player_system.py definitions at lines: [110]
- Public signature: `(user_id, amount)`
- System signature: `(user_id: 'int', amount)`
- Legacy signature: `(user_id, amount)`

### `get_user_progress`

- Capture: `_legacy_get_user_progress_before_player_system_v1`
- db.py definitions at lines: [1331, 11676]
- player_system.py definitions at lines: [138]
- Public signature: `(user_id)`
- System signature: `(user_id: 'int')`
- Legacy signature: `(user_id)`

## Runtime contracts

- Existing users compared for `get_user_progress`: 5
- Public/system/legacy mismatches: 0
- Required progress keys: daily_hunts, exp, exp_to_next, gold, kills, level
- Missing-user behavior is equivalent across public/system/legacy paths.
- `add_exp` was not executed because i4a is strictly read-only.
- Legacy `add_exp` structurally includes level thresholds, level-up count, stat updates, max-HP synchronization, and result metadata.

## Consumers

### `add_exp`

- `db.py:11667`
- `db.py:3244`
- `systems/contract_system.py:503`
- `systems/reward_system.py:411`

### `get_user_progress`

- `db.py:11677`
- `handlers/dev.py:224`
- `handlers/profile.py:163`
- `tools/smoke_test_player_contracts.py:17`

## Conclusion

Both remaining legacy refs are confirmed as Player Progression dependencies.
`get_user_progress` is safe to reimplement directly if its six-key dictionary contract is preserved.
`add_exp` requires a transactional equivalence test because it mutates EXP, level, five base stats, and stored max HP.

## Recommended next step

9.0.12i4b: implement direct Player Progression logic in systems/player_system.py while preserving both captures for rollback and equivalence testing on an isolated temporary user or rollback transaction.
