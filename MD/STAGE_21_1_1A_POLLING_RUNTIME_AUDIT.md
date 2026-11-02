# Stage 21.1.1a — Polling runtime audit

- Status: **PASS_READ_ONLY**
- Parent: `e69fe3ec050eb239c5617e07f6dce160047e6fd5`
- `main.py` SHA-256: `a7edf7a3b99437d04329201be44d7bace83668c1cd15edf7be720d529927ea59`
- Canonical polling supervisor definitions: `1`
- Polling-related calls: `2`
- Confirmed self-recursive calls: `1`
- Production mutations: **NONE**
- Manual game check: **NOT REQUIRED**

## Confirmed defect

`run_bot_polling_resilient` directly invokes itself instead of invoking the Telegram polling primitive. A top-level direct `bot.infinity_polling()` call also exists, so implementation must establish one external polling owner without starting network traffic in tests.

## Implementation boundary

Owner: `main.py`. Add bounded exponential backoff with jitter, transient/fatal classification, shutdown propagation, an AST owner verifier, and isolated no-network smoke coverage. Do not change handlers, gameplay, production SQLite, or user-facing texts.

## Decision

`GO_TO_21_1_1B_POLLING_IMPLEMENTATION`
