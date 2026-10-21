# Stage 21.8.1b — Battle Aggregate implementation

- Status: **PASS**
- Evidence: **API_READY**
- Runtime/Telegram: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

Implemented one canonical V2 damage engine for future PvE, PvP and simulator consumers. It owns defense reduction, minimum damage, crit/evasion curves, RNG ordering, critical multiplier and final rounding. Rewards, persistence and presentation remain external.
