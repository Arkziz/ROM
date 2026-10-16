# ROM Stage 21.1.X2 - Behavioral fixtures ROM V1

- **Canonical revision:** `Stage 21.1.X2a`
- **Статус:** `GO`
- **Source candidates classified:** `173`
- **Behavioral executable candidates:** `137`
- **Behavioral static contracts:** `12`
- **Structural source contracts:** `4`
- **Documentation acceptance:** `0`
- **Tool wrappers:** `2`
- **Helpers only:** `12`
- **Review required:** `6`

## Canonical authority rules

- Assertion alone does not make a helper behavioral.
- AST/source/document checks are structural contracts, not runtime parity fixtures.
- Executable behavioral candidates require runtime behavior evidence and an observable oracle.
- RNG dependency requires real seed evidence in source.
- Time dependency requires real Clock/frozen-time control evidence.
- Every record preserves source path, function, lines and SHA-256 authority.

## Review queues

- RNG without real seed evidence: **16**.
- Time without real Clock control: **13**.
- Review-required records: **6**.

## Usage in V2

Only behavioral executable candidates and explicitly approved behavioral static contracts may seed parity tests. Structural, documentation, wrapper and helper records remain supporting evidence and must not be counted as gameplay behavior.

Production code and DB/WAL/SHM were not opened or modified.

## Наступний етап

Stage 21.1.X3 - матриця чинних і superseded policy.
