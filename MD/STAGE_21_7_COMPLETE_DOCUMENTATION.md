# Stage 21.7 — Complete API-level documentation and closure

## Closure status

- Status: **CLOSED_ACCEPTED_API_LEVEL**
- Commit parent: `41ef187eacd8c1ac54a5a8ffeb84ec9784ea3899`
- Runtime/Telegram dispatch: **NOT_CONNECTED**
- Production database adapter: **NOT_CONNECTED**
- End-to-end gameplay acceptance: **DEFERRED**
- Manual game check for this closure: **NOT_REQUIRED**

## Scope

Stage 21.7 establishes the V2 item and equipment foundation: item definitions and owned instances, inventory, equipment slots, equipment generation, runes, durability/repair, enhancement, and a pure presentation DTO. Closure accepts the APIs, invariants, tests and owner boundaries. It does not claim that Telegram handlers or a production persistence adapter execute these APIs.

## Canonical owners

- `item_definition_instance`: `rom_v2/domain/item.py`
- `inventory_service`: `rom_v2/application/inventory_service.py`
- `equipment_slots`: `rom_v2/domain/equipment.py`
- `equipment_generation`: `rom_v2/domain/equipment_generation.py`
- `runes`: `rom_v2/domain/runes.py`
- `durability_repair`: `rom_v2/domain/durability.py`
- `enhancement`: `rom_v2/domain/enhancement.py`
- `presentation_dto`: `rom_v2/presentation/item_dto.py`

## Durability and repair

- Persistent range: `0..100`.
- Death penalty: `5` durability for equipped items.
- At zero durability, base equipment, rune and enhancement contributions are disabled.
- Repair rate: `0.05` multiplied by missing durability and rarity multiplier.
- Rarity multipliers: `{}`.
- Repair targets an exact owned/equipped `inventory_id`.
- Repair-one and repair-all cross one atomic gateway boundary; reservations fail closed.

## Enhancement

- Material IDs: stone `601`, success rune `602`.
- Caps: weapon `+10`, armor `+6`.
- Weapon success chances: `{0: 100, 1: 100, 2: 100, 3: 80, 4: 70, 5: 60, 6: 50, 7: 40, 8: 30, 9: 20}`.
- Armor success chances: `{0: 100, 1: 100, 2: 70, 3: 50, 4: 30, 5: 20}`.
- Weapon damage multipliers: `{0: 1.0, 1: 1.05, 2: 1.1, 3: 1.15, 4: 1.22, 5: 1.3, 6: 1.4, 7: 1.52, 8: 1.66, 9: 1.82, 10: 2.0}`.
- Armor base HP bonus percentages: `{0: 0.0, 1: 0.5, 2: 1.0, 3: 1.5, 4: 2.0, 5: 3.0, 6: 4.0}`.
- Armor rarity HP multipliers: `{'common': 1.0, 'uncommon': 1.1, 'rare': 1.2, 'epic': 1.3}`.
- RNG is inclusive `1..100`; success is roll less than or equal to chance.
- Success Rune forces `100%` chance.
- Attempt identity uses `operation_id`; resource debit and result persistence belong to one atomic gateway call.

## Presentation DTO

- Canonical owner: `rom_v2/presentation/item_dto.py`.
- Typed immutable models cover item description, comparison rows and rune presentation.
- Technical identity uses `item_id`, exact `inventory_id` and stable keys; rendered names are never identifiers.
- Primary stats, defenses, damage, durability, refine level and runes follow deterministic ordering.
- The module performs no SQL, mutation, pricing, RNG, damage calculation or domain settlement.
- A separate `domain` file is intentionally absent because this is a presentation boundary, not business policy.

## Failure and atomicity semantics

- Invalid identity, unsupported item state, reservation, cap and insufficient-resource failures are machine-readable.
- Application services validate before mutation.
- Persistence implementations must atomically apply all debits and item state changes or none.
- Idempotency prevents repeated operations from consuming resources twice.
- Patch-level failure causes automatic restoration of all closure artifacts and records a recovery report.

## Verification evidence

- PASS reports discovered: **27**.
- Stage 21.7 executable checkers passed: **3**.
- V2 Python files parsed: **80**.
- Canonical six-gate CI: **PASS**.
- Protected DB/runtime files remained byte-for-byte unchanged.
- V1 WAL/SHM manipulation: **False**.

## Known boundary and deferred acceptance

1. `API_READY` does not mean Telegram runtime integration.
2. Production persistence adapters are not accepted by this closure unless already independently evidenced by their own stages.
3. Manual creation of a character is not useful for Stage 21.7 acceptance until handlers and persistence adapters are connected to these services.
4. End-to-end manual checks are deferred to the roadmap integration and acceptance blocks.
5. Runtime consumers must reuse these owners rather than create parallel formulas or presentation paths.

## Manual test timing

The first meaningful full gameplay verification occurs after Stage 21.16 handler/navigation wiring and Stage 21.17 clean-environment integration. Formal manual acceptance belongs to Stage 21.18.2. Production switching occurs only at Stage 21.19.4 after rehearsal.
