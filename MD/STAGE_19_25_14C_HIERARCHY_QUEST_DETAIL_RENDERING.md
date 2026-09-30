# Stage 19.25.14c: Hierarchy quest detail rendering recovery

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

The hierarchy callback now builds the canonical production detail item with the DB connection and resolved player level, passes that single item to the pure renderer, converts the UI-neutral keyboard to Telegram markup, and appends the return button for the current розділ.
