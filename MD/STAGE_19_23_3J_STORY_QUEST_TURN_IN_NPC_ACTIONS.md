# Stage 19.23.3j: story quest turn-in NPC actions

ACTIVE quests are now visible to both the giver and canonical receiver. Only the canonical receiver can offer completion. Cross-NPC QUEST_ITEM handoffs show the acquired item and receiver route. Quest-item retention remains unchanged.

## Encoding

All changed Python, JSON, Markdown, and text files use UTF-8. Existing Python is read with `utf-8-sig`; changed files are written as UTF-8 without BOM with LF newlines. JSON uses `ensure_ascii=False`, and Unicode round-trip is verified before commit.
