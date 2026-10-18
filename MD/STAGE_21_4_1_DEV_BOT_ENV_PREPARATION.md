# Stage 21.4.1 — Development bot isolated V2 environment preparation

- **Status:** `PREPARED_AWAITING_MANUAL_TOKEN`
- **Local file:** `ROM\rom_v2\.env`
- **Variable:** `ROM_V2_BOT_TOKEN`
- **Git policy:** `.env` is ignored and must never be committed

## Manual action

Create the separate development bot through BotFather. Paste the token only after the equals sign in the isolated `rom_v2/.env` file:

```dotenv
ROM_V2_BOT_TOKEN=PASTE_TOKEN_HERE
```

Do not paste the token into chat, reports, Markdown, console commands, commits, or `.env.example`.

## Preparation evidence

- `rom_v2/.env` existed before patch: **False**.
- `rom_v2/.env` created by patch: **True**.
- Token key added by patch: **True**.
- Token currently populated: **False**.

## Follow-up

After the token is entered locally, run Stage 21.4.1a acceptance. The follow-up must verify presence and isolation without printing, masking, hashing, or otherwise recording the token value.
