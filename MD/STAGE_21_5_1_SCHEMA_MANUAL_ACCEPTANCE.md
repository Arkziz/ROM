# Stage 21.5.1a — Expert acceptance checklist

- [ ] Every column has a SQLite type, nullability, default policy, generation owner, and checks.
- [ ] Every foreign key has explicit delete/update actions.
- [ ] Account and character lifecycles are correct.
- [ ] Money, quantities, durability, versions, and event sequences cannot enter invalid ranges.
- [ ] Exact-once operations, append-only events, ledger, and outbox are sufficient.
- [ ] Indexes cover current fundamental lookup paths.
- [ ] Deferred domains are explicit and do not have premature placeholder tables.
- [ ] Clean V2 database creation is preferred over V1 test-data migration.
- [ ] The schema is acceptable as input to migration `001_v2_baseline`.

Acceptance phrase: `Приймаю Stage 21.5.1a schema design`.
