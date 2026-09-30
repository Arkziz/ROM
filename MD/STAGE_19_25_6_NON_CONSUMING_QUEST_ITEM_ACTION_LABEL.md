# Stage 19.25.6: Non-consuming quest-item action label

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Change

The retained-evidence action label changes from `✅ Передати доказ` to `🔍 Показати доказ`. Callback data and completion mechanics remain unchanged.

## Contracts

- Quest 23 retains the guard ring after completion.
- Quest 24 is TALK and does not consume the ring.
- Quest 30 remains the consuming atomic TURN_IN for all three clues.
- Production DB is unchanged.

## Manual checks

1. Open Trade Row with quest 23 active at `1/1`.
2. Confirm the button reads `🔍 Показати доказ`.
3. Use the action and confirm quest 23 completes with `42 EXP / 0.65` gold.
4. Confirm quest 24 becomes available.
5. Confirm the ring remains after quests 23 and 24.
6. Confirm no traceback and no duplicate reward.
