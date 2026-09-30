# Stage 19.25.14e: Hierarchy Telegram types scope recovery

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

The story quest module now imports `types` from `telebot` at module scope before the hierarchy callback constructs the `🔙 Квести розділу` button. The production detail snapshot and status mapping remain unchanged.
