# Stage 20.4.1a — Daily Firius Token Reward 3

## Change
The canonical daily quest reward is reduced from 5 to 3 Firius Tokens. Preview now imports and renders the canonical constant instead of hardcoding ×5.

## Preserved contracts
- Three small health potions, item 401 ×3.
- Firius Token item ID 726.
- Rune fusion token quantity 1.
- Atomic capacity planning and exact-once claim.
- Existing token balances are not debited or migrated.
- Database schema, WAL and SHM are unchanged.

## Manual verification
Required: preview shows potion ×3 and token ×3; one completed claim increases tokens by exactly 3; a second claim is rejected; pre-existing balance changes only by +3.
