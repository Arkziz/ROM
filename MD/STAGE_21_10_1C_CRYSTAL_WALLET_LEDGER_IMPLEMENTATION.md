# Stage 21.10.3c - Base Equipment Shop implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Canonical owner: `BaseEquipmentShopService`
- Class-aware offers with stable technical keys
- Non-negative balance: **enforced**
- Stable operation key and immutable preview snapshot: **implemented**
- Quoted-price purchase with idempotent replay: **idempotent**
- Changed-payload replay: **conflict**
- Single caller-owned commit and atomic rollback: **implemented**
- SQLite / production persistence: **NOT_CONNECTED**
- Runtime / Telegram: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

The implementation is API-ready only. Production adapters and runtime wiring remain outside Stage 21.10.3c.
