# Stage 19.25.8: Remove quest 26 item spoilers

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Change

Quest 25 completion now reveals only that the secured bridge can be searched. Quest 26 active objective asks for an unknown patrol-related clue. The exact shield name is first revealed by the 15% quest-item drop message.

## Unchanged

- Quest 25 remains KILL_REGION ×10.
- Quest 26 remains QUEST_ITEM with 15% drop chance.
- The shield remains non-consuming until quest 30.
- Candidate and production remain synchronized.
- The readable multiline production format is preserved.
- Production DB is unchanged.
