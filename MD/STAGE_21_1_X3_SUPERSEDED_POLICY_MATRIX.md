# ROM Stage 21.1.X3 - current and superseded policy matrix

- **Canonical revision:** `Stage 21.1.X3a`
- **Статус:** `GO`
- **Candidates before scope filtering:** `699`
- **Policy-only candidates:** `267`
- **Excluded non-policy records:** `432`
- **Active canonical:** `202`
- **Superseded explicit:** `0`
- **Historical only:** `0`
- **Shadow candidates:** `2`
- **Active/shadow conflicts:** `0`
- **Owner review required:** `63`

## Marker scope

Policy markers are read only from the symbol name, assignment line, immediately preceding comment block, and module docstring. Neighboring assignments cannot contribute markers.

## Migration rules

- Only `ACTIVE_CANONICAL` may migrate automatically.
- `ACTIVE_SHADOW_CONFLICT` is never auto-migrated.
- Supersession requires explicit replacement/deprecation evidence.
- Non-policy runtime state is excluded from the migration allowlist.
- Every matrix row preserves source, lines, hashes, scoped evidence, classification reasons and value fingerprint.

## Review queues

- Multiple active groups: **1**.
- Groups without active owner: **43**.
- Active/shadow conflicts: **0**.
- Owner-review groups: **45**.
- Superseded without replacement evidence: **0**.

Production code and DB/WAL/SHM were not opened or modified.

## Наступний етап

Stage 21.1.9 - observability, logging, errors and audit trails inventory.
