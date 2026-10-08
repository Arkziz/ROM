# Stage 19: guide for adding a third story location

## Mandatory sequence

1. Reserve canonical location_id and localized human name resolver.
2. Create sections in `data/story_quest_hierarchy.py`; use term «розділ».
3. Add content in packs of 10 under `data/story_quests/`.
4. Continue strict quest numbering from 101 and predecessor from quest 100 only when the third campaign is intentionally activated.
5. Assign package unlock levels and location ceiling.
6. Use all five objective contracts only through canonical definitions.
7. QUEST_ITEM keys must be unique lowercase namespaced snake_case; never use ordinary inventory IDs.
8. Use 15% chance and isolated storage unless a separately approved policy changes it.
9. Define rewards from canonical normal-mob calibration; boss story reward and combat reward remain separate.
10. Add NPCs and canonical route hints for cross-NPC transitions.
11. Add boss_key and deferred turn-in contract for any campaign boss.
12. Extend overlevel location ceilings and test the new boundary.
13. Extend journal hierarchy and retain section size 10 or deliberately implement pagination.
14. Add candidate/reference artifact in `Квести` and verify production sync.
15. Add migration only when persistent schema changes; content alone should not require DB migration.
16. Add maintained verifier, isolated lifecycle, fresh/existing DB checks and manual playthrough evidence.

## Required acceptance scenarios

- First quest availability only after predecessor and level gate.
- Every objective family used by the campaign.
- QUEST_ITEM drop, persistence, restart, exact-once turn-in and SKIP cleanup.
- Boss call, victory, deferred turn-in and no identity leak.
- Campaign finale, no accidental next quest, no dependency on unfinished future content.
- Overlevel boundary: completed preserved, unfinished skipped, no rewards, item cleanup, summary, idempotency.
- Journal completed/active/available/locked/skipped and Profile return.
- Fresh DB, existing DB, restart, integrity, FK and Git policy.

## Prohibited shortcuts

- Do not hand-format technical location IDs for users.
- Do not persist AVAILABLE/LOCKED.
- Do not put story items into ordinary inventory.
- Do not award rewards for SKIPPED.
- Do not create quest 101 before the third campaign is approved.
- Do not delete or manipulate WAL/SHM.
