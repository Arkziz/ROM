# Stage 21.8.7b - Resolved terminal paths

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **7**
- Unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Binding resolutions

- `SINGLE_PVE_TERMINAL_OWNER`: **V1_CONFIRMED_SHARED_CLAIM**. Use one V2 terminal arbitration boundary for victory, defeat and escape; context adapters request an outcome, but only the first successful claim may settle.
- `PVE_DEFEAT_EXACT_PATH`: **V1_CONFIRMED_OUTCOME**. Defeat is a terminal outcome handled through the shared claim before defeat-side settlement; no victory rewards or loot are permitted.
- `PVE_MANUAL_ESCAPE_EXACT_PATH`: **V1_CONFIRMED_OUTCOME**. Manual and automatic escape converge on the shared escape claim; repeated or stale claims return without settlement.
- `PVE_SETTLEMENT_ORDERING`: **V1_BOUNDARY_RESOLVED**. V2 orders terminal claim first, then outcome-specific settlement exactly once, then downstream domain events, then presentation. Victory settlement may include state finalization, reward and drops; defeat/escape must not execute victory settlement.
- `DUPLICATE_MESSAGES_EVENTS`: **V1_BOUNDARY_RESOLVED**. A failed/already-terminal claim emits no domain settlement events. Presentation is generated from the single accepted settlement result and adapters must suppress duplicate terminal messages.
- `POST_TERMINAL_ACTION_GUARD`: **V1_BOUNDARY_RESOLVED**. Terminal state is absorbing. After acceptance, combat actions are rejected; stale/repeated callbacks may render only a non-settlement stale response.
- `PVE_PVP_BOSS_SIMULATOR_PARITY`: **V1_CONFIRMED_CONTEXT_SPECIFIC**. Share terminal outcome and exactly-once vocabulary, but keep PvE, PvP, boss/story consumers and simulator adapters context-specific. Do not force identical settlement side effects.

## Implementation boundary

The next patch may implement only a pure V2 terminal lifecycle API with an absorbing terminal state, exactly-once claim/settlement, ordered domain events, and presentation emitted only from the accepted result. Runtime/Telegram wiring remains unauthorized.
