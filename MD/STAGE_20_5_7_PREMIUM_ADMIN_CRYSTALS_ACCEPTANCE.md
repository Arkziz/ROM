# Stage 20.5.7 — Premium and Admin Crystals Acceptance

## Decision

**Stage 20.5 ACCEPTED**

Accepted configuration:

- Premium 15 days: **100 crystals**
- Premium 30 days: **180 crystals**
- Premium benefit: **+25% experience and +25% combat gold** for normal, elite and boss victories
- Other crystal item prices and bag expansion prices remain unchanged
- `/admin_crystals` credit, debit, recipient notification, history and details are manually confirmed
- Admin audit schema is initialized before handler registration

Automated acceptance covers maintained Premium and admin-crystal smoke suites, canonical prices, source isolation, startup order, wallet/ledger behavior, idempotency, clamped debit, authorization, schema objects and database integrity on an isolated production snapshot.

Production code and production database were not changed by this acceptance patch. No additional manual verification is required for Stage 20.5.7.
