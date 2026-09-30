# Stage 19.25.14: Story quest hierarchy UI

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Hierarchy

`📜 Сюжетні історії → 🌿 Початок Шляху → розділи → квести → деталі квесту`

## Contracts

- Only production quests 1-30 are visible.
- Sections are 1-10, 11-20, and 21-30.
- The canonical Ukrainian term is `розділ`; the new UI does not use `глава`.
- Existing legacy page/detail callbacks remain registered for old Telegram messages.
- Completed quests remain readable.
- The database and quest-state semantics are unchanged.
