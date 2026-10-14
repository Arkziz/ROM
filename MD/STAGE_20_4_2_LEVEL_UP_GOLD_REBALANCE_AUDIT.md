# Stage 20.4.2 — Level-up Gold Rebalance Audit

## Decision
`PASS / VALUES_APPROVAL_REQUIRED`. Production code is unchanged.

## Current formula
- Normal reached level: `level × 8`.
- Milestone level divisible by 5: `level × 12`.
- Levels 2–10 award `492` gold in total.
- Stage 20.1.2 measured story gold 1–10: `208.18`.
- Current level-up faucet is `236.33%` of that story baseline.

## Candidate values
### A — Recommended
- Normal: `level × 2`.
- Milestone: `level × 4`.
- Total levels 2–10: `138`.
- `66.29%` of story baseline; `71.95%` reduction from current.
- Keeps milestones at double the normal gold rate.

### B — Conservative
- Normal: `level × 3`; milestone: `level × 5`.
- Total: `192`, or `92.23%` of story baseline.

### C — Minimal faucet
- Normal: `level × 2`; milestone: `level × 3`.
- Total: `123`, or `59.08%` of story baseline.

## Protected contracts
Exact-once ledger, multi-level ordering, residual EXP, all item rewards, crystals disabled, quest and mob gold, premium policy, existing claimed rows and wallet balances must remain unchanged. No retroactive debit or credit is allowed.

## Mutation scope after approval
Stage 20.4.2a may change only the gold formula in `systems/level_up_reward_system.py`, plus focused tests/docs.

## Manual verification
Required after mutation: selected normal level, milestone level, multi-level transition, exact wallet delta and no duplicate after restart.
