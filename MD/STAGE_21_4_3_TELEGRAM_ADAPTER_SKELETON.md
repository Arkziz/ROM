# Stage 21.4.3 — Telegram adapter skeleton

- **Status:** `IMPLEMENTED`
- **Canonical owner:** `rom_v2.infrastructure.telegram.TelegramAdapterSkeleton`
- **Boundary type:** framework-neutral and network-free

## Implemented contract

- Immutable normalized update envelope.
- Immutable outbound reply description.
- Stable slash-command registration.
- Exact one-owner duplicate rejection.
- Normalized command dispatch including `/command@bot_username` input.
- Unknown and non-command updates return `None` without fallback mutation.

## Explicitly out of scope

- Telegram polling or webhook startup.
- Reading or revealing the local bot token.
- Telegram framework dependency.
- Gameplay handlers or database access.
- Callback codec/registry, which belongs to Stage 21.4.4.
- Account allowlist, closed as `NOT_REQUIRED` in Stage 21.4.2.

## Manual verification

Not required. This stage has no external runtime dispatch or Telegram network owner.

## Next stage

Stage 21.4.4 — callback codec/registry.
