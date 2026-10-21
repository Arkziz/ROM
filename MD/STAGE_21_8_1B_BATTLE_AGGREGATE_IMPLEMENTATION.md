# Stage 21.8.1b — Battle Aggregate implementation

- Status: **PASS**
- Evidence: **API_READY**
- Runtime/Telegram: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

Implemented one pure deterministic V2 battle aggregate. It owns battle identity, immutable actor snapshots, mutable current resources, explicit turn/round ordering, idempotent action application, domain events, restart snapshots and single-claim terminal status. Damage, skills, effects, rewards, persistence and presentation remain external roadmap stages.
