# Stage 19.25.5: Merchant story integration

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

## Change

The canonical Trade Row service screen remains first. An eligible Merchant story card is sent immediately afterward through `send_story_npc_if_present(..., 'trader')`.

## Contracts

- Quest 23 is `QUEST_ITEM`; the ring is retained after completion.
- Quest 24 is `TALK`; any required ring reference is non-consuming.
- Trade Row selling and base-equipment services are unchanged.
- Production DB is unchanged.

## Manual checks

1. Open `🛒 Торговий ряд` while quest 23 is active with progress `1/1`.
2. Confirm the regular Trade Row menu appears first.
3. Confirm the Merchant story card appears second.
4. Complete quest 23 and confirm the ring remains stored.
5. Confirm quest 24 becomes available.
6. Confirm quest 24 does not consume the ring.
7. Confirm Trade Row selling and base equipment continue to work.
