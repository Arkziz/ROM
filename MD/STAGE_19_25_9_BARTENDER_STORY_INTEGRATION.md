# Stage 19.25.9: Bartender story integration

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Change

The Bartender introduction remains visible. The stale static no-quest message is removed, and the generic story runtime is invoked for canonical NPC `bartender` immediately after the service message.

## Contracts

- Quest 27 remains TALK.
- Quest 28 chain remains unchanged.
- No quest content, reward, progress, or database mutation occurs.

## Manual checks

1. Open Tavern and select Bartender.
2. Confirm the Bartender introduction appears without the stale no-quest sentence.
3. Confirm quest 27 appears as a second story card.
4. Complete the TALK flow and receive `42 EXP / 0.65` gold.
5. Confirm quest 28 becomes available.
6. Confirm no traceback and no duplicate reward.
