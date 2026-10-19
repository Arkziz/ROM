# Stage 21.7.5a - Refined V1 rune-lifecycle contract

## Decision

- Status: PASS
- Conclusion: GO_TO_IMPLEMENTATION
- Semantic rows: 21
- Unresolved rows: 0
- Runtime authority: `systems/rune_system.py`
- Definition authority: `data/runes.py`
- Persistence facade: `db_modules/systems_wrappers.py`

## Resolved lifecycle

Runes remain item definitions plus owned inventory quantities until insertion. Socket capacity is equipment-dependent. Insertion and extraction operate on an exact owned `inventory_id`, reject occupied or invalid sockets, preserve class/equipment compatibility, and must commit inventory, socket, extractor/gold and stat-visible state atomically. Simple and perfect extractor behavior remains separate. Equipped state controls stat contribution through the V1 equipment/stat pipeline; durability interaction must be preserved exactly rather than invented.

## Authority boundaries

- `systems/rune_system.py` owns rune lifecycle rules and mutations.
- `data/runes.py` owns rune definitions, rune IDs, socket limits and extractor constants.
- `db_modules/systems_wrappers.py` is a compatibility/persistence facade, not a second rules owner.
- handlers orchestrate presentation and callbacks only.
- inventory/equipment services own exact instance, ownership and equipment integration boundaries.
- auction/trade modules own reservations, not rune formulas.
- drop, DEV and simulator modules are consumers and must not maintain parallel rune rules.

## Implementation gate

Implementation is allowed only when every semantic row is resolved. It must preserve exact V1 identity, ownership, reservation, compatibility, socket occupancy, extractor consumption, atomic rollback, restart persistence, stat contribution, and failure semantics. No V1 module was imported or executed and SQLite was not opened.

## Manual game check

NOT_REQUIRED. This patch is read-only semantic refinement.
