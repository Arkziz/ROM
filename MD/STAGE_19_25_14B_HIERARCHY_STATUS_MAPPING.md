# Stage 19.25.14b: Hierarchy status mapping recovery

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Root cause

`build_production_story_quest_detail` returns a presentation dictionary containing `text` and `keyboard`. It does not return `status` or `status_key`. The hierarchy adapter therefore parsed an empty value and marked every quest as locked.

## Fix

The hierarchy adapter now calls the UI-neutral canonical `get_story_quest_view` and maps its exact lifecycle values: completed and skipped count as completed, while active, available, and locked preserve their states. Unknown values fail closed with an exception instead of silently becoming locked.

## Manual check

Restart the bot and open `Персонаж → 📜 Квести → 🌿 Початок Шляху`. Confirm the completed count and all three section counts are correct.
