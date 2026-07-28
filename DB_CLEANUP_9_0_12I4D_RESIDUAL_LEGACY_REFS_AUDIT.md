# ROM 9.0.12i4d - Residual Legacy References Audit

## Scope

Read-only audit. No gameplay code, tools, database rows, or legacy variables were changed.

## Readiness result under investigation

- `legacy_refs`: 2
- `unsafe_delete`: 0
- Readiness regex line: 80

## Findings

### `_legacy_equipment_to_slots`

- Classification: `false_positive`
- Explanation: The identifier is part of the normal migration API name migrate_legacy_equipment_to_slots; it is not a _legacy_* capture. The current regex starts matching inside a longer identifier.
- Repository Python files containing the exact text: ['db.py', 'tools/audit_residual_legacy_refs.py']
- Occurrences:
  - line 307; context=Substring; statement=IdentifierSubstring; `migrate_legacy_equipment_to_slots(user_id)`
  - line 328; context=Substring; statement=IdentifierSubstring; `def migrate_legacy_equipment_to_slots(user_id):`
  - line 5227; context=Substring; statement=IdentifierSubstring; `migrate_legacy_equipment_to_slots(user_id)`
  - line 9441; context=Substring; statement=IdentifierSubstring; `migrate_legacy_equipment_to_slots(user_id)`

### `_legacy_process_passive_regeneration_before_hp_dynamic_max_fix_v1`

- Classification: `write_only_capture`
- Explanation: The variable is assigned in a compatibility try/except block but is never loaded. Current regen wrappers delegate directly to systems.regen_system.
- Repository Python files containing the exact text: ['db.py', 'tools/audit_residual_legacy_refs.py']
- Occurrences:
  - line 11656; context=Store; statement=Try; `_legacy_process_passive_regeneration_before_hp_dynamic_max_fix_v1 = process_passive_regeneration`
  - line 11658; context=Store; statement=Assign; `_legacy_process_passive_regeneration_before_hp_dynamic_max_fix_v1 = None`

## Runtime path confirmation

- Final `db.process_passive_regeneration` delegates to `systems.regen_system`.
- The dynamic-max regen compatibility capture has no AST Load usage.
- `migrate_legacy_equipment_to_slots` is a valid migration function and must not be removed or renamed.

## Conclusion

The readiness value `legacy_refs: 2` does not represent two active runtime legacy dependencies.
One match is a regex false positive inside `migrate_legacy_equipment_to_slots`.
One match is an unused write-only compatibility capture left from the historical HP dynamic-max fix.

## Recommended next step

9.0.12i4e should:
1. remove only the unused regen capture try/except block from `db.py`;
2. fix `tools/db_cleanup_readiness.py` to match `_legacy_` identifiers only at a valid identifier boundary;
3. preserve `migrate_legacy_equipment_to_slots` unchanged;
4. rerun regen, equipment migration, core, import, and readiness tests.

Expected readiness after i4e: `legacy_refs: 0`, `unsafe_delete: 0`.
