# Stage 20.4.7 — General Economy Acceptance

## Decision
`Stage 20.4 = ACCEPTED`.

Accepted contracts:
- Daily reward: 3 Firius Tokens; item description reflects the active earning sources.
- Level-up gold: reached levels 2–11 use the frozen combat-income matrix; messages show exactly two decimal places; no retroactive credit or debit.
- Potion prices remain unchanged by owner decision: small HP 5.00/1.00, medium HP 15.00/3.00, small MP 4.00/0.80, medium MP 12.50/2.50. Stage 20.4.4 is explicitly `NOT_REQUIRED`.
- Guild creation: 50.00 gold, minimum level 3, initial limit 10; the price and limit appear on the first prompt and final confirmation; atomic debit remains canonical.
- Existing wallets, historical level rewards, existing guilds and historical guild logs are not retroactively modified.

Automated acceptance re-runs the maintained focused smoke tests and verifies the report/commit chain, canonical source contracts, clean database non-mutation and exact acceptance-only commit scope. Manual evidence for the guild first prompt was supplied on 12 October 2026 and accepted.
