# Stage 19.25.7: Quest 25 and 26 text alignment

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Change

Quest 25 now clearly asks the player to defeat 10 creatures to secure the old bridge. Searching for patrol equipment is reserved for quest 26.

## Unchanged mechanics

- Quest 25 remains `KILL_REGION`, target `10`.
- Quest 26 remains `QUEST_ITEM`, drop chance `15%`.
- Quest 26 item remains non-consuming until quest 30.
- Rewards, NPC ownership, chain, navigation, and DB state are unchanged.

## Manual checks

1. Reopen quest 25 in the Mercenary Head card and journal.
2. Confirm both texts describe clearing the area, not searching for a shield.
3. Complete 10 victories and open quest 26.
4. Confirm quest 26 introduces the equipment search after the area is secured.
