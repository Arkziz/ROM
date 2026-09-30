# Stage 19.25.11: Defer quest 30 conclusion until TURN_IN

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Lifecycle

- AVAILABLE: Head of Mercenaries asks for all three collected clues.
- ACTIVE: player must hand over the three listed clues.
- Action: `📦 Передати докази` clearly communicates consuming TURN_IN semantics.
- COMPLETION: only after atomic exact-once consumption does the full wolf-pack conclusion appear.

## Guarantees

- Quest 30 remains TURN_IN.
- Three required items remain quantity 1 and consume true.
- Reward remains 42 EXP and 0.65 gold.
- Candidate and production remain synchronized.
- Readable multiline story-module formatting remains intact.
- Production DB is unchanged.
