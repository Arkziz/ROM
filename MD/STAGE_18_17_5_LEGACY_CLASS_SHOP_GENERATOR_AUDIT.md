# Stage 18.17.5: Legacy Class-Shop Generator Read-only Audit

**Status:** PASS
**Production mutation:** none

## Reachability

- Definition count: `1`.
- Runtime call references: `1`.
- Direct imports: `1`.
- Exports: `2`.
- Callback registrations: `0`.
- Runtime reachable: `True`.
- Dead legacy candidate: `False`.

## Missing dependency

- The route imports `generate_equipment_item` from `systems.dynamic_equipment_system`.
- The route calls the missing dependency: `True`.

## Side effects

- SQL or inventory mutation detected inside the legacy function: `False`.
- The function appears to build and return an in-memory list, but attempts to call a missing generator dependency.

## Recommendation

- Classification: `reachable_broken_route`.
- Preferred action: replace the reachable legacy route with an explicit adapter to the canonical base-shop API after contract approval.
- Do not add a second `generate_equipment_item` implementation to the compatibility module.

## Database safety

- quick_check: `ok`.
- FK violations: `0`.
- DB unchanged: `True`.
