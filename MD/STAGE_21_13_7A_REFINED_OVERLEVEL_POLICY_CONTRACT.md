# Stage 21.13.7a - Refined Overlevel Policy Contract

- Status: **PASS**
- Conclusion: **GO_TO_PARITY_RESOLUTION**
- Policy anchor: **Stage 19.18 SKIP policy**
- Contracts: **10 refined / 0 review required**
- Implementation authorized: **False**

## Canonical behavior
- Trigger: `current_level > location_max_level`
- Max levels: `{'start_path': 5, 'dark_forest': 10}`
- Scope: entire exceeded story location
- Newly skipped quests: no rewards
- Location story quest-item rows: deleted
- Repeated reconciliation: idempotent
- Completed rows: preserved

## Next patch

`patch_21_13_7b_resolve_overlevel_policy_parity.py`
