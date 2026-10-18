# Stage 21.5.1b — Expert acceptance checklist

- [ ] Completion timestamps are bidirectional with completed states.
- [ ] Ledger rows cannot outlive or lose exact-once operation evidence.
- [ ] Temporary reservations follow their operation lifecycle.
- [ ] All prior type, range, nullability, FK, index, and deferred-domain contracts remain intact.
- [ ] A new clean V2 database is preferred; V1 test data is not migrated.
- [ ] Revision 21.5.1b is acceptable as input to `001_v2_baseline`.

Acceptance phrase: `Приймаю Stage 21.5.1b schema design`.
