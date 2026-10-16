# ROM Stage 21.1.X1 - canonical content inventory

- **Canonical revision:** `Stage 21.1.X1b`
- **Статус:** `GO`
- **Content sources:** `65`
- **Definition owner candidates:** `5860`
- **Typed usage references:** `749`
- **Resolved exact:** `749`
- **Resolved alias:** `0`
- **External static definition:** `0`
- **Dynamic definition:** `0`
- **Owner review required:** `0`
- **Confirmed unresolved:** `0`

## Виправлення Stage 21.1.X1b

- Definition discovery розширено на всі non-test runtime/content modules.
- Literal mapping keys враховано як owner candidates із confidence metadata.
- `boss`/`mob` і `region`/`location` підтримують safe namespace alias resolution.
- Кожна typed reference отримує один resolution status.
- Статичний аудит не оголошує reference дефектом без authoritative proof.

## Review queues

- Duplicate canonical definitions: **137**.
- Conflicting canonical names: **2**.
- Owner review required: **0**.
- Confirmed unresolved: **0**.
- Dynamic definition symbols: **107**.
- Historical owner candidates: **63**.

## Canonical interpretation

- `RESOLVED_EXACT`: exact namespace/value owner існує.
- `RESOLVED_ALIAS`: owner знайдено через дозволений namespace alias.
- `EXTERNAL_STATIC_DEFINITION`: definition знайдено поза первинними 65 content sources.
- `DYNAMIC_DEFINITION`: відповідний namespace має dynamic catalog owner, але identity не доступна як literal.
- `OWNER_REVIEW_REQUIRED`: є неповний або неоднозначний static owner signal.
- `CONFIRMED_UNRESOLVED`: зарезервовано лише для доказово відсутніх references; static audit за замовчуванням не підвищує finding до цього статусу.

Production code та DB/WAL/SHM не змінювалися.

## Наступний етап

Stage 21.1.X2 - Behavioral fixtures ROM V1.
