# Stage 21.8.6b - Resolved status effect parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **4**
- Unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Binding resolutions

- `CROSS_CONTEXT_PARITY`: **V1_CONFIRMED_CONTEXT_SPECIFIC**. Preserve one canonical lifecycle vocabulary and ordering API, but parameterize context-owned application/reapplication details. Do not force byte-identical PvE, PvP, boss and simulator behavior where V1 owners differ.
- `GENERAL_RESIST_IMMUNITY`: **V1_CONFIRMED_ABSENT_IN_SCOPE**. The Stage 21.8.6 Effect Engine has no general resist/immunity layer. Do not invent one. Only explicit future V1-backed per-effect gates may be added by a separately audited stage.
- `EFFECT_PERSISTENCE_RESTART`: **V1_CONFIRMED_TRANSIENT**. Combat effects are transient battle state for this stage. The V2 Effect Engine remains persistence-agnostic and does not survive battle reconstruction/restart unless a later audited persistence contract explicitly requires it.
- `FAILURE_ATOMICITY`: **V1_BOUNDARY_RESOLVED**. Implement the V2 engine as a pure transition: validate and calculate the complete next effect state/events before the caller commits it. Rejected/invalid transitions return unchanged state. Context adapters own external HP/resource persistence and compensation, preserving the confirmed V1 victory HoT compensation as an adapter concern.

## Implementation boundary

The next patch may implement only a pure, persistence-agnostic V2 Effect Engine API. It must preserve context-specific policies, must not invent general resistance/immunity, and must not connect Telegram/runtime dispatch or production persistence.
