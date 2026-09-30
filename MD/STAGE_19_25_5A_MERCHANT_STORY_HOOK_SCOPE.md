# Stage 19.25.5a: Merchant story hook scope recovery

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Root cause

The Stage 19.25.5 hook was inserted into `build_trade_district_text`, a pure text builder that has no `bot` or `message` variables. Opening Trade Row therefore raised `NameError: name 'bot' is not defined`.

## Fix

The single Merchant story hook is moved to `show_trade_district`, immediately after the canonical Trade Row service message.

## Manual checks

1. Open `🛒 Торговий ряд`; no traceback must occur.
2. Confirm the normal Trade Row service menu appears first.
3. Confirm the Merchant quest 23 card appears second.
4. Complete quest 23 and confirm the ring is retained.
5. Confirm quest 24 becomes available and does not consume the ring.
