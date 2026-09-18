# ROM Stage 18.29.1a: Event item blocks of 25 IDs

## Canonical policy

- Static event namespace: `4000..9999`.
- Block size: 25 consecutive IDs.
- Block count: 240.
- First block: `4000..4024`.
- Last block: `9975..9999`.
- One `EVENT_KEY` initially receives one explicit permanent block.
- If 25 IDs are insufficient, the same `EVENT_KEY` may later receive another explicitly assigned free block.
- Expansion is never automatic.
- Assigned blocks and IDs are never reused by another event.
- Unused IDs remain reserved for the owner event.
- Generated equipment continues to use the existing generated namespace.

This stage assigns no production event block and creates no item row in `game.db`.
