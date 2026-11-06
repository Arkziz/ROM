# Stage 22.3.3 guarded route cohort 10 mutation

- Status: **PASS_MUTATION**
- Patch revision: **1**
- Parent: `ee108ef98d3f7beec0d5f47c72beb92cefeee28f`
- Mutated file: `handlers/player_interaction.py`
- Retired route: **duel_placeholder**, former order **288**
- Preserved owner: `handlers/pvp_interaction.py:pvp_duel_request`, order **336**
- Removed source lines: **3**
- Production SQLite opened: **false**
- Manual game check: **REQUIRED**

## Manual acceptance

1. Start the bot through the normal operator-controlled launch path.
2. Open another player's interaction screen and press the duel action that emits `pi:duel:<user_id>`.
3. Confirm exactly one visible result from `pvp_duel_request`: request success or one explicit validation failure.
4. Confirm no silent callback, duplicate message, or duplicate callback answer.
5. Verify trade and unrelated player-interaction callbacks still behave unchanged.

## Decision

`MANUAL_GAME_CHECK_REQUIRED_BEFORE_COHORT_10_ACCEPTANCE`
