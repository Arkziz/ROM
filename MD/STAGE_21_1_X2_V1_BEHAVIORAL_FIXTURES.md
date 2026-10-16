# ROM Stage 21.1.X2 - Behavioral fixtures ROM V1

- **Статус:** `GO`
- **Test-reference modules parsed:** `724`
- **Behavioral fixtures:** `173`
- **Assertion contracts:** `1263`
- **Fixture helpers:** `16`
- **Fixtures with seed evidence:** `32`
- **Fixtures with DB evidence:** `81`
- **Fixtures with restart evidence:** `7`
- **Fixtures with idempotency evidence:** `31`

## Domain coverage

- `account`: **12** fixtures
- `character`: **16** fixtures
- `combat`: **31** fixtures
- `cross_cutting`: **1** fixtures
- `economy`: **6** fixtures
- `events_auxiliary`: **3** fixtures
- `inventory_equipment`: **28** fixtures
- `quests_progression`: **74** fixtures
- `social`: **9** fixtures
- `stats`: **22** fixtures
- `world_travel`: **6** fixtures

## Fixture contract

Кожний fixture містить:

- stable `fixture_id`;
- source file, function, lines і SHA-256;
- domain classification;
- initial-state contract;
- ordered call/event evidence;
- assertion fingerprints і readable previews;
- DB/restart/time/RNG/idempotency evidence;
- final-state acceptance contract.

Fixtures не запускають V1 runtime і не копіюють production state. Вони є immutable parity references для майбутніх executable V2 contract tests.

## Determinism policy

- RNG-dependent fixture без seed evidence позначається review candidate, а не deterministic PASS.
- Time-dependent fixture без Clock evidence позначається review candidate.
- DB fixture використовує тільки isolated test DB під час майбутнього executable replay.
- Production game.db/WAL/SHM не відкривалися і не змінювалися.

## Наступний етап

Stage 21.1.X3 - матриця чинних і superseded policy.
