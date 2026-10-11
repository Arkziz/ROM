# Stage 20.4.2a — Level-up Gold as 10% Combat Income Audit

## Decision
`PASS / POLICY_APPROVAL_REQUIRED`. Production code is unchanged.

## Method
Reward for reached level N uses source level N-1. Expected kills are EXP-to-next divided by expected same-level normal-mob EXP. Normal templates are uniformly selected; expected gold is the midpoint of each min/max range averaged across exact-level templates. Reward is 10%, rounded `ROUND_HALF_UP` to 0.01. No milestone gold multiplier is used; milestone items stay unchanged.

## Matrix
| Transition | EXP | Kills | Avg gold/kill | Combat gold | 10% reward | Current |
|---|---:|---:|---:|---:|---:|---:|
| 1→2 | 500 | 50 | 0.09 | 4.50 | **0.45** | 16.00 |
| 2→3 | 1200 | 100 | 0.14 | 14.25 | **1.43** | 24.00 |
| 3→4 | 2800 | 200 | 0.22 | 43.00 | **4.30** | 32.00 |
| 4→5 | 6496 | 406 | 0.30 | 119.77 | **11.98** | 60.00 |
| 5→6 | 15200 | 800 | 0.43 | 344.00 | **34.40** | 48.00 |
| 6→7 | 24992 | 1136 | 0.61 | 695.80 | **69.58** | 56.00 |
| 7→8 | 41500 | 1660 | 0.79 | 1307.25 | **130.73** | 64.00 |
| 8→9 | 68991 | 2379 | 1.08 | 2557.43 | **255.74** | 72.00 |
| 9→10 | 115005 | 3485 | 1.38 | 4791.88 | **479.19** | 120.00 |
| 10→11 | 190000 | 5000 | 1.76 | 8812.50 | **881.25** | 88.00 |

Totals: combat `18690.38`, proposed `1869.05`, current `580.00`. Current 10→11 reward is `88.00` because the legacy formula uses reached level 11; proposed 10→11 reward is deterministically `881.25` from level-10 content.

## Future levels
Source levels 11+ are deferred until their mobs/content are implemented. No random fallback or synthetic values are introduced.

## Protected contracts
Exact-once ledger, multi-level ordering, existing claims/balances, mob and quest gold, milestone items, premium and crystals remain unchanged.
