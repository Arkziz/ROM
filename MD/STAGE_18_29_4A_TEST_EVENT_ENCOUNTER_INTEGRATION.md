# ROM Stage 18.29.4a: Test Event Encounter Integration

The canonical hunt resolver can now build a selected event template through the normal-mob factory without changing boss, elite or ordinary fallback semantics.

- Pilot candidate: `test_event_2026:test_slime`.
- Display name: `🧪 Нестабільний слизень`.
- Type: normal physical event mob at the current player level.
- Eligible scope: canonical hunt context, player levels 1 through 30, all huntable locations.
- Selection probability contract: 25 percent.
- Priority remains event, boss, elite, normal.
- Runtime remains disabled because `test_event_2026.config.ENABLED` is false and Kyiv dates are pending.
- No drop, Telegram UI or activation-date mutation is included.
