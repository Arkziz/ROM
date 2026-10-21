# Stage 21.8.3b — Resolved Max MP terms

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Config owner: `data/stat_system_config.py:27`
- Formula consumer: `systems/stat_system.py:121`
- Resolved formula: `100 + level × 20 + INT × 1 + WIS × 4`
- Resolved rows: `MAX_MP_BASE_TERM`, `MAX_MP_LEVEL_TERM`
- Remaining unresolved rows: `0`
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

The resolution is read-only and binds the exact `MAX_MP_SCALING` dictionary to `calculate_max_mp`. No production formula was inferred or changed.
