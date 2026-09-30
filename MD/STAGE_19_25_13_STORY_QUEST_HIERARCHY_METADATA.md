# Stage 19.25.13: Canonical story hierarchy metadata

## Decision

`READY_FOR_STAGE_19_25_14_HIERARCHY_UI`

## Added metadata

- Story: `🌄 Початок Шляху`.
- Розділ 1. Тривога на околиці, quests 1-10, required level 1.
- Розділ 2. Рунічна аномалія, quests 11-20, required level 2.
- Розділ 3. Зниклий патруль, quests 21-30, required level 3.

## Contracts

- The localized story name is resolved through `resolve_story_quest_location_name`.
- Technical `location_id` values never become player-facing labels.
- The canonical Ukrainian term is `розділ`; new navigation must not use `глава`.
- Every production quest 1-30 belongs to exactly one section.
- No inactive quest 31+ appears in metadata.
- Section unlock levels match every quest in the section.
- Live Telegram UI and callback handlers are unchanged.
- Production DB is unchanged.
