# Stage 19.25.14a: Hierarchy status-reader recovery

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Root cause

The hierarchy adapter called `build_production_story_quest_detail` without the required database connection and canonical player-level inputs. The actual production contract is `(connection, user_id, quest_id, player_level, page=0)`.

## Fix

The adapter now passes `db.conn`, resolves the player level through `resolve_story_quest_player_level(get_player_stats(user_id) or {})`, and reads the canonical `status` field from the production detail snapshot.

## Manual check

Restart the bot and open `Персонаж → 📜 Квести`. Confirm the stories screen opens and that section/quest statuses are correct.
