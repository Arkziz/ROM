# Stage 20.4.1b — Firius Token Item Description

## Fix
The item description for Firius Token ID 726 no longer hardcodes “5 tokens”. It renders `FIRIUS_TOKENS_PER_DAILY_REWARD`, whose approved value is 3.

## Preserved contracts
- Daily preview and actual claim remain 3 tokens.
- Daily potion reward remains item 401 ×3.
- Rune fusion consumes 1 token and 3 identical runes.
- Existing balances, claim state, database, WAL and SHM are unchanged.

## Manual verification
Required: open Firius Token item details and confirm the description says that 3 tokens can be obtained from the daily quest. Repeating the daily claim is not required.
