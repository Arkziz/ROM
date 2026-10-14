# Stage 20.5.6 — Admin Crystal Schema Startup

`main.py` now imports and calls `init_admin_crystal_credit_system()` in the startup schema block before admin handler registration.

The initializer is idempotent and creates only `admin_crystal_credit_audit` plus its two indexes when absent. Credit, debit, clamped debit, zero-balance rejection, idempotent replay, history, detail, authorization, quick check and foreign keys are covered by an isolated temporary-database smoke test.

Manual verification is required after bot restart: execute one admin credit and one admin debit, verify balances, recipient notification, history and detail.
