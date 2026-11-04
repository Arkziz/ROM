# ROM V1 Operator Release Checklist

## A. Preconditions

- [ ] Bot process is stopped before DB snapshot or file-level release checks.
- [ ] Current branch is `develop`.
- [ ] Current HEAD is `e7e78f6642ded791e43e82b0b340422abe998dc3`.
- [ ] `origin/develop` is an ancestor of current HEAD.
- [ ] Staging area is empty.
- [ ] Tracked worktree is clean, excluding the documented operator-controlled dump file.
- [ ] Required configuration is present without printing or copying secret values.

## B. Evidence review

- [ ] Stage 21.9.1 audit status is `PASS_READ_ONLY`.
- [ ] Stage 21.9.2 matrix status is `PASS_READ_ONLY`.
- [ ] Stage 21.9.3 status is `PASS_AUTOMATED_RELEASE_ACCEPTANCE`.
- [ ] Stage 21.9.4 status is `PASS_RUNTIME_AND_OPERATOR_ACCEPTANCE`.
- [ ] Production source count is 184 and all hashes/compile checks passed.
- [ ] Blocking tool cohort is 13/13 PASS.
- [ ] Release blockers and review findings are both zero.
- [ ] The single deferred dev-wrapper finding is acknowledged as non-blocking.

## C. SQLite and recovery

- [ ] Preserve `game.db`, `game.db-wal`, and `game.db-shm` together for any backup.
- [ ] Never delete, truncate, checkpoint, rename, or edit production WAL/SHM to make checks pass.
- [ ] Validate integrity only on an isolated snapshot while the bot is stopped.
- [ ] Confirm snapshot `integrity_check=ok` and zero foreign-key violations.
- [ ] Record production DB/WAL/SHM SHA-256, size, and `mtime_ns` before and after acceptance.
- [ ] Confirm a restore procedure exists for the complete DB/WAL/SHM set.

## D. Runtime and observability

- [ ] Startup log reaches `BOT STARTED`.
- [ ] Notification worker reports DB connection ready.
- [ ] Normal navigation and callback dispatch work.
- [ ] Normal PvE and skill PvE flows are accepted.
- [ ] Reward and persistent progress occur once.
- [ ] No duplicate response, callback loop, `database is locked`, unhandled traceback, or Telegram 429 storm is present.
- [ ] Preserve the release log used for operator sign-off.

## E. Explicit release decision

- [ ] No source/evidence drift occurred after Stage 21.9.4.
- [ ] No new blocking finding exists.
- [ ] No production or SQLite mutation was performed by documentation/closure patches.
- [ ] Operator decision is explicitly recorded as `GO` or `NO-GO`.

### GO condition

All checkboxes above are satisfied, release blockers are zero, and formal closure evidence is committed.

### NO-GO condition

Any mandatory checkbox fails, any accepted hash drifts, any blocking tool fails, or any runtime/SQLite blocker is observed.

## F. Actions not performed by Stage 21

The Stage 21 patches do not perform merge, rebase, push, force-push, deployment, release tagging, or modification of `master`. Those actions require a separate explicit operator command and their own change control.
