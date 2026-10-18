# Stage 21.4.4 — Callback codec/registry

- **Status:** `IMPLEMENTED`
- **Canonical codec owner:** `rom_v2.infrastructure.telegram.CallbackCodec`
- **Canonical registry owner:** `rom_v2.infrastructure.telegram.CallbackRegistry`
- **Supported version:** `v1`
- **Maximum encoded size:** `64 UTF-8 bytes`

## Canonical grammar

```text
v<version>:<namespace>:<action>?<sorted_key>=<encoded_value>&...
```

- Namespace and action are stable lower-case machine keys.
- Parameters are sorted before encoding.
- Alternate non-canonical encodings are rejected.
- Duplicate parameter keys are rejected.
- Unsupported versions are rejected fail-closed.
- A route has exactly one handler owner.
- Unknown routes are rejected and never use fallback mutation.

## Isolation

This stage does not read the bot token, contact Telegram, start polling,
start gameplay, or open SQLite. V1 and V2 local `.env` files are hash-preserved.

## Manual verification

Not required. The codec and registry are covered by deterministic unit and CI checks.

## Next stage

Stage 21.5.1 — V2 database schema design.
