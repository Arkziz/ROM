# Stage 19.25.4: Common equipment hand-slot text

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Change

The main-hand and off-hand selection screens now render `title` and `description` as text. Only the gold value keeps numeric two-decimal formatting.

## Scope

- `handlers/city.py`
- no price, purchase, preview, inventory, quest, or database mutation

## Manual checks

1. Open the common equipment shop and choose main hand.
2. Confirm the screen shows `🗡️ Вибір зброї` without traceback.
3. Choose off hand and confirm `🛡️ Вибір другої руки` without traceback.
4. Complete one valid main-hand purchase and one valid off-hand purchase if affordable.
5. Confirm armor purchases remain unchanged.
6. Confirm the bot continues polling after both screens.
