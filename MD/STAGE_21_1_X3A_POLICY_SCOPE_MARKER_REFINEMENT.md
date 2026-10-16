# ROM Stage 21.1.X3a - policy scope and marker refinement

- **Статус:** `GO`
- **Candidates before:** `699`
- **Policy-only after:** `267`
- **Excluded non-policy:** `432`
- **Active/shadow conflicts:** `0`

## Safeguards

- `NON_POLICY_RUNTIME_STATE_EXCLUDED`
- `MARKER_SCOPED_TO_SYMBOL`
- `ACTIVE_SHADOW_CONFLICT_NOT_AUTO_MIGRATED`
- `SUPERSESSION_REQUIRES_REPLACEMENT_EVIDENCE`
- `MIGRATION_ALLOWLIST_CONTAINS_POLICY_ONLY`
- `FULL_EVIDENCE_PERSISTED_IN_JSON`

Production code and DB/WAL/SHM were not opened or modified.
