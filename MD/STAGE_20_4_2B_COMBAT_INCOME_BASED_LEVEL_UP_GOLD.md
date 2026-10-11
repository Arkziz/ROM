# Stage 20.4.2b — Combat-Income-Based Level-up Gold

## Applied policy
Level-up gold for reached levels 2–11 is the approved frozen matrix derived from 10% of expected same-level normal-mob combat income for source levels 1–10. Values retain two decimal places.

## Matrix
`2: 0.45, 3: 1.43, 4: 4.30, 5: 11.98, 6: 34.40, 7: 69.58, 8: 130.73, 9: 255.74, 10: 479.19, 11: 881.25`.

There is no milestone multiplier for gold. Milestone item rewards remain unchanged. Reached levels outside 2–11 fail closed until a future audited matrix is added, preventing legacy or random fallback amounts.

## Compatibility and persistence
Existing claimed rewards and wallet balances are not recalculated, credited or debited. The existing exact-once `level_up_rewards` ledger, multi-level ordering, item pending flow, UI and database schema are preserved.

## Manual verification
Required: verify one normal reached level and one milestone reached level show the exact matrix gold and wallet delta; verify restart/re-entry does not award gold twice. If a controlled multi-level transition is available, verify the sum and ascending levels.
