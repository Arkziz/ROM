# Stage 19.25.14d: Hierarchy quest detail snapshot recovery

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

The hierarchy callback now uses the canonical production detail snapshot directly. The snapshot already contains rendered text and a UI-neutral keyboard, so no second rendering pass is performed. The keyboard is converted to Telegram markup and receives the return button for the current розділ.
