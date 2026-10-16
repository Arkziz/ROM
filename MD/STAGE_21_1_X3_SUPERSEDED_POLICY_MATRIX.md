# ROM Stage 21.1.X3 - current and superseded policy matrix

- **Статус:** `GO`
- **Policy candidates:** `699`
- **Policy groups:** `619`
- **Git policy evidence records:** `187`
- **Active canonical:** `433`
- **Superseded explicit:** `0`
- **Historical only:** `0`
- **Shadow candidates:** `115`
- **Owner review required:** `151`

## Classification rules

- `ACTIVE_CANONICAL` requires positive runtime-owner evidence.
- `SUPERSEDED_EXPLICIT` requires an explicit superseded/deprecated/obsolete/do-not-migrate marker.
- `HISTORICAL_ONLY` is non-runtime evidence retained for reference.
- `SHADOW_CANDIDATE` is never migrated without an owner decision.
- Mere duplication or a differing value never proves which policy is current.
- Ambiguous groups remain `OWNER_REVIEW_REQUIRED`.

## V2 migration contract

- Only `ACTIVE_CANONICAL` policies may migrate automatically.
- Superseded, historical and shadow values are excluded from V2 runtime.
- Owner-review groups block automatic policy migration, not this read-only audit.
- Behavioral authority from Stage 21.1.X2a may support a decision but cannot override explicit canonical ownership by itself.
- Production code and DB/WAL/SHM were not opened or modified.

## Review queues

- Multiple active candidates: **4**.
- Groups without active canonical owner: **195**.
- Explicit superseded without replacement evidence: **0**.
- Ambiguous owner groups: **114**.

## Наступний етап

Stage 21.1.9 - observability, logging, errors and audit trails inventory.
