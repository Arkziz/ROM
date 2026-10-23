# Stage 21.10.4c - Potion Trading implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Canonical owner: `PotionTradingService`
- Typed potion keys with accepted buy/sell prices
- Non-negative balance: **enforced**
- Stable operation key and deterministic stack plan: **implemented**
- Reservation-aware atomic trade with idempotent replay: **idempotent**
- Changed-payload replay: **conflict**
- Single caller-owned commit and atomic rollback: **implemented**
- SQLite / production persistence: **NOT_CONNECTED**
- Runtime / Telegram: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

The implementation is API-ready only. Production adapters and runtime wiring remain outside Stage 21.10.4c.
