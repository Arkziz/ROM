# Stage 19.24.6 — Модульна структура сюжетного контенту

## Рішення

**PASS_PENDING_MANUAL_SMOKE_CHECK**

Активний production-контент 1–20 розділено на читабельні модулі по 10 квестів. `data/story_quest_content.py` залишається стабільним публічним owner та агрегатором.

## Активні модулі

- `data/story_quests/start_path_01_10.py`
- `data/story_quests/start_path_11_20.py`

Модулі 21–50 не створювалися і не активувалися.

## Незмінність

Точні semantic snapshots `STORY_QUEST_REGISTRY` і `STORY_QUEST_TEXT` до та після refactor однакові. Production DB не змінювалася. Candidate JSON не є runtime dependency. Availability-дефект квесту 11 залишається на паузі й цим refactor не змінювався.
