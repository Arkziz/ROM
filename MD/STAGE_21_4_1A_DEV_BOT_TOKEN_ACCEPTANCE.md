# Stage 21.4.1a — Development bot token acceptance

- **Status:** `ACCEPTED`
- **Local owner:** `ROM\rom_v2\.env`
- **Variable:** `ROM_V2_BOT_TOKEN`
- **V1 environment:** `ROM\.env` remains separate and untouched

## Acceptance guarantees

- The V2 token assignment exists exactly once and is non-empty.
- The value has the structural form expected for a Telegram bot token, including optional dotenv quotes.
- The token was not printed, masked, hashed, written to reports, or committed.
- `rom_v2/.env` is ignored and untracked.
- The tracked `.env.example` retains a blank placeholder.
- The V1 root `.env` was not modified.
- No Telegram request or polling process was started.

## Limitation

This acceptance verifies local presence, structural format, and isolation only. It does not contact Telegram and therefore does not prove that BotFather currently recognizes the token.

## Next stage

Stage 21.4.2 — allowlist for test accounts.
