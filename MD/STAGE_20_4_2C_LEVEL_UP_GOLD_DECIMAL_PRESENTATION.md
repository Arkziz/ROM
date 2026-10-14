# Stage 20.4.2c — Level-up Gold Decimal Presentation

Level-up reward messages now display gold with exactly two decimal places. Examples: `0.45`, `1.43`, `34.40`, `479.19`, `881.25`. The wallet credit, frozen reward matrix, exact-once ledger, item rewards, database schema and existing balances are unchanged.

Manual verification: complete one previously unclaimed level-up and confirm the reward message shows the exact two-decimal amount; verify the wallet delta and no duplicate after restart.
