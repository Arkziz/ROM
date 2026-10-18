# ROM Stage 21.6 — Complete Domain Foundation Documentation

## Closure status

Stage 21.6 is formally closed as `PASS / GO` after the complete prerequisite chain, focused regression, canonical six-gate CI, ownership inspection, and protected-runtime isolation check.

- Branch: `rewrite/rom-v2`
- Parent before closure: `5c25bdfc22810b1180dc04c5aa2dd718dabea6f0`
- Manual game check: `NOT_REQUIRED`
- V1 database opened: `False`
- V1 WAL/SHM manipulated: `False`

## Completed canonical sub-stages

- `21.6.X1`: PASS / REVIEW_REQUIRED
- `21.6.X1a`: PASS / GO
- `21.6.1`: PASS / GO
- `21.6.2`: PASS / GO
- `21.6.3`: PASS / GO
- `21.6.3a`: PASS / GO
- `21.6.4`: PASS / GO
- `21.6.4a`: PASS / GO
- `21.6.5`: PASS / GO
- `21.6.5a`: PASS / GO
- `21.6.5b`: PASS / GO
- `21.6.5c`: PASS / GO
- `21.6.6`: PASS / GO
- `21.6.6a`: PASS / GO

## Implemented systems

### Account domain

The V2 account owner represents the account-level identity and state separated from character-owned progression. Account and character parity were reconciled against V1 before completing later domain work.

### Character lifecycle

The character aggregate owns character identity, class, level, experience, location, current HP, and current MP. The unconfirmed optimistic-version contract was removed during V1 parity reconciliation. Character reset semantics remain separate from account-level entitlements.

### Class catalog

The canonical class catalog contains only classes verified in V1. The Stage 21.6 implementation does not invent classes, aliases, resource types, or compatibility rules.

### Primary stats

Canonical keys:

```text
str
dex
int
wis
sta
```

Base formula:

```text
base_primary_value = 10 + level - 1
```

Attribute points:

```text
total_earned = max(0, level - 1) * 5

total_earned = free_points + allocated.str + allocated.dex
              + allocated.int + allocated.wis + allocated.sta
```

Allocation is atomic, non-negative, bounded by free points, and supports stale-state protection. Allocated-stat respec returns allocated points to free points without changing total earned.

### Derived stat engine

Max HP:

```text
Max HP = 60 + level * 20 + STA * 5
```

Max MP for mana classes:

```text
Max MP = 100 + level * 20 + INT * 1 + WIS * 4
```

Non-mana classes have `Max MP = 0`.

PATK coefficients:

```text
warrior = STR * 1.00 + DEX * 0.20
knight  = STR * 1.10 + DEX * 0.10
scout   = STR * 0.65 + DEX * 0.55
rogue   = STR * 0.40 + DEX * 0.80
mage    = STR * 0.20
priest  = STR * 0.20
```

MATK coefficients:

```text
warrior = INT * 0.20
knight  = INT * 0.20
scout   = INT * 0.20
rogue   = INT * 0.20
mage    = INT * 1.05 + WIS * 0.15
priest  = INT * 0.90 + WIS * 0.30
```

Defense:

```text
PDEF = int(equipment_or_resolved_pdef + STA * 0.35)
MDEF = int(equipment_or_resolved_mdef + WIS * 0.35)
```

Critical chance uses the audited linear segment followed by diminishing returns. Physical critical chance uses DEX; magical critical chance uses WIS. Dodge uses defender-versus-attacker DEX difference, a 1% floor, a linear segment through +40 DEX, and diminishing returns thereafter.

### Resource lifecycle

Persistent current resources obey:

```text
maximum increases  -> current value is preserved
maximum decreases  -> current value is clamped to the new maximum
non-mana class     -> current MP = 0 and Max MP = 0
explicit restore   -> cannot exceed maximum
PvE terminal defeat -> current HP = 1
```

Increasing maximum HP or MP does not provide free healing or restoration. HP/MP persistence uses the existing character storage and does not duplicate derived maximums as a second source of truth.

### Canonical full stat snapshot

Canonical owner:

```text
rom_v2.domain.full_stat_snapshot
```

Application owner:

```text
rom_v2.application.full_stat_snapshot_service.FullStatSnapshotService
```

Input layers remain visible and are applied once:

```text
total primary = base + allocated + active equipment + runes
```

Resolved equipment and enhancement outputs are maintained as separate derived layers. Only equipped items with durability greater than zero contribute. Duplicate inventory IDs fail closed.

Snapshot outputs:

```text
STR, DEX, INT, WIS, STA
Max HP, Max MP
PATK, MATK
PDEF, MDEF
physical critical chance
magical critical chance
dodge
```

Profile, combat, and simulator application entrypoints all delegate to the same snapshot builder. This establishes one canonical API. Later feature stages may connect their concrete UI/combat/simulator flows to this API, but must not create competing formulas.

## Ownership boundaries

The snapshot does not redefine:

```text
item generation formulas
rune-level formulas
refinement formulas
class-equipment compatibility
loot generation
combat damage resolution
```

Those values must be supplied by their own audited subsystems. Stage 21.6 only composes the resolved inputs into one immutable stat result.

## Data structures

Key immutable structures:

```text
Account
Character
ClassDefinition / class catalog values
PrimaryStats
AttributePointState
DerivedStats
ResourceState
DerivedBonusLayer
EquippedStatInput
FullStatSnapshotInput
FullStatSnapshot
```

Application boundaries use explicit services and ports. SQLite adapters remain in the infrastructure layer.

## Interactions

```text
class + level
  -> base primary stats
allocated points
  -> allocated primary layer
equipment subsystem
  -> active non-broken equipment inputs
rune subsystem
  -> rune primary layer
refinement/enhancement subsystem
  -> resolved derived bonus layer
all layers
  -> canonical FullStatSnapshot
snapshot
  -> profile / combat / simulator consumers
snapshot maximums + persistent current resources
  -> ResourceState lifecycle
```

## Constraints and fail-closed behavior

- Levels below 1 are invalid.
- Primary stats and attribute-point balances cannot be negative.
- Attribute-point invariant violations are rejected.
- Unknown primary-stat aliases are rejected.
- Broken and unequipped items do not contribute.
- Duplicate equipment inventory IDs are rejected.
- Non-mana classes cannot retain MP.
- Current resources cannot exceed maximum resources.
- The closure does not migrate or open V1 databases.
- `game.db-wal` and `game.db-shm` are never deleted, cleared, or used for rollback.

## Automated regression

Focused Stage 21.6 regression:

```text
................................
----------------------------------------------------------------------
Ran 32 tests in 0.858s

OK
```

Canonical six-gate CI status:

```text
status: PASS
failed_checks: []
```

## Known nuances and deferred integration

- Profile, combat, and simulator share one application API contract; concrete feature-flow wiring is validated again when those roadmap systems are implemented.
- Equipment generation, rune progression, refinement calculation, regeneration timers, skill costs, potions, rage, combat energy, and combo-point orchestration are outside Stage 21.6.
- Test fixture numbers that are not documented formulas are scenario inputs only and are not gameplay constants.
- The Stage 21.6 domain foundation is accepted without an in-game manual check because no Telegram/gameplay presentation flow is connected by this closure.

## Acceptance decision

All mandatory prerequisite reports are `PASS / GO`, focused regression is successful, full CI is successful, canonical ownership checks are successful, and protected runtime evidence is unchanged. Stage 21.6 is therefore `CLOSED / ACCEPTED`.
