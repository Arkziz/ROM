## Stage 21.9.6c - Post-combat hooks implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Runtime integration: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

Implemented a V2 post-combat application API with an immutable settled-victory event, canonical durable consumer order, explicit consumer and Unit-of-Work ports, exact-once consumer skipping, one hook commit, rollback on durable failure, and no reward mutation commands.

SQLite, production consumer adapters, reward-settlement wiring, runtime, Telegram, and notifications remain excluded.
