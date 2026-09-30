# Stage 19.25.7a: Restore readable story module format

## Decision

`PASS_PENDING_MANUAL_SMOKE_CHECK`

## Change

`data/story_quests/start_path_21_30.py` is reformatted from a single huge `QUEST_ROWS` line into a readable multiline Python literal.

## Guarantees

- Exact semantic equality before and after formatting.
- Quest numbers remain 21-30.
- No dialogue, mechanics, rewards, navigation, item contracts, or DB values change.
- Candidate JSON is unchanged because it was already readable.

## Manual check

Open quests 25 and 26 after restart and confirm their updated texts still render correctly.
