# ROM Stage 18.29.3c: Atomic Event Shop Exchange

Adds a server-authoritative atomic and idempotent exchange backend for registered event offers.
The pilot offer exchanges three item-4000 tokens for one item-4001 reward. Lifecycle, canonical offer, unreserved currency and bag capacity are rechecked. A unique idempotency receipt prevents duplicate debit or award. Telegram UI and event activation remain deferred.
