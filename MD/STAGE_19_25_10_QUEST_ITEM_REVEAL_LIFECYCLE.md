# Stage 19.25.10: Normalize quest-item reveal lifecycle

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Scope

The three quest-item chains are normalized:

- 22 → 23: unknown personal evidence, exact ring revealed by drop.
- 25 → 26: unknown equipment evidence, exact shield revealed by drop.
- 28 → 29: unknown route evidence, exact cloak revealed by drop.

## Guarantees

- KILL_REGION targets remain 8, 10, and 10.
- Quest-item drop chances remain 15%.
- All three clues remain non-consuming until quest 30.
- Quest 30 remains the atomic consuming TURN_IN.
- Candidate and production remain synchronized.
- Readable multiline production formatting is preserved.
- Production DB is unchanged.
