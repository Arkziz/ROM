# Stage 18.16: Attribute Points System

## Production Closure

**Status:** CLOSED after automated closure verification and the approved manual runtime checks performed throughout Stage 18.16.

## 1. Purpose

Stage 18.16 replaces the historical automatic `+1` increase to all five primary attributes at every level with a player-controlled attribute-point system. Each new level awards five points that may be distributed among Strength, Dexterity, Intelligence, Wisdom, and Stamina.

The implementation uses the canonical Stage 18.15 stat aggregation path. Allocated points are included in effective primary statistics exactly once and are not duplicated in PATK, MATK, defense, resource, critical-hit, dodge, PvE, PvP, worker, or simulator formulas.

## 2. Persistent Data Model

The `users` table contains:

- `free_attribute_points`: unspent points available to the player.
- `total_attribute_points_earned`: permanent ledger total.
- `allocated_strength`.
- `allocated_dexterity`.
- `allocated_intelligence`.
- `allocated_wisdom`.
- `allocated_stamina`.
- `attribute_points_migrated_at`: one-time existing-character migration marker.
- `pending_class_change_inventory_id`: exact New Path Sphere reserved for final class-change confirmation.

The permanent invariant is:

```text
total_attribute_points_earned
=
free_attribute_points
+ allocated_strength
+ allocated_dexterity
+ allocated_intelligence
+ allocated_wisdom
+ allocated_stamina
```

## 3. Progression Contract

For every gained level:

```text
free_attribute_points += 5
total_attribute_points_earned += 5
```

Multi-level awards grant `5 × levels gained`. EXP awards without a level increase grant no points. The legacy automatic increase of all primary attributes is absent from the active level-up route.

## 4. Existing-Character Migration, Policy C

Existing characters were migrated using the neutral Policy C conversion:

```text
legacy uniform growth per primary stat = level - 1
level-derived points = (level - 1) × 5
```

The old uniform level growth was removed from the five base-stat columns and converted into the attribute-point ledger. The migration is marker-protected and idempotent. Excess or adjusted ledger values are preserved rather than blindly overwritten.

## 5. Allocation Domain

`systems/attribute_allocation_system.py` owns the canonical allocation workflow:

- balance and allocated-stat reads;
- in-memory allocation draft;
- increment and decrement actions;
- explicit cancel;
- atomic confirm;
- stale-state rejection;
- restart-safe behavior, because an unconfirmed draft does not mutate the database.

Confirmation uses `BEGIN IMMEDIATE`, re-reads authoritative balance and allocation values, validates the pending delta, applies a single atomic update, and preserves the ledger invariant.

## 6. Effective Statistics

Allocated values participate in the canonical primary-stat aggregation:

```text
effective primary stat
= legacy/base stat
+ allocated stat
+ active equipment bonuses
+ active rune bonuses
```

The resulting effective values feed all dependent systems, including PATK, MATK, PDEF, MDEF, Max HP, Max MP, critical hit, dodge, profile display, PvE, PvP, notifications, and simulation.

## 7. Resource Semantics

Allocating STA, INT, or WIS can change resource maxima. Increasing a maximum does not instantly heal or restore mana. When a reset or class change lowers a maximum:

```text
current_hp = min(current_hp, new_max_hp)
current_mp = min(current_mp, new_max_mp)
```

No reset operation provides free healing or mana restoration.

## 8. Player Interface

The inline profile contains the `⭐ Характеристики` section. The player can adjust a draft with plus and minus controls, inspect free and pending values, explicitly confirm, cancel, or return. Database values change only after a successful confirmation.

Level-up messages use the authoritative result of the EXP operation and report points awarded for one or multiple gained levels.

## 9. Canonical Reset Audit

`attribute_respec_events` stores exact-once reset history:

- user;
- operation type;
- old and new class where relevant;
- returned total and per-stat values;
- source inventory and item IDs;
- idempotency key;
- timestamp.

Supported operation types are `attribute_respec` and `class_change`.

## 10. New Path Sphere, ID 501

The New Path Sphere is premium-bound and character-bound.

- Changes the character class.
- Resets all allocated attribute points in the same final workflow.
- Is consumed only after successful final confirmation.
- Is not consumed when the player cancels or leaves the flow.
- Cannot be transferred, auctioned, sold, or dropped by mobs.
- Remains eligible for the Crystal Shop.
- Uses the exact selected `inventory_id` to avoid consuming a different item.

## 11. Rebirth Sphere, ID 504

The Rebirth Sphere resets allocated attributes without changing class.

- Category: consumable.
- Standard stack limit: 10.
- Double confirmation.
- Atomic consumption of one sphere.
- Returns all allocated points to the free balance.
- Does not change `total_attribute_points_earned`.
- Tradeable and auctionable.
- Not premium-bound or character-bound.
- Not sold in the Crystal Shop.
- NPC `sell_price` currently remains `0.0`; player-market sale is supported.

## 12. Rebirth Sphere Drop Balance

Approved initial Scenario B:

```text
Normal mob: 0.02%  (1 in 5,000)
Elite mob:  0.10%  (1 in 1,000)
Boss:        1.00%  (1 in 100)
```

The rule is independent, awards one sphere, permits at most one per victory, and uses `stack_or_lose`. The rule is centralized in `data/drop_tables.py` and is part of the canonical victory plan. The New Path Sphere remains excluded from enabled enemy-drop rules.

These values may be recalibrated later together with other permitted drop items.

## 13. Safety and Idempotency

The implementation protects against:

- duplicate confirmations;
- stale Telegram callbacks;
- parallel windows;
- restart before confirmation;
- missing or changed inventory ownership;
- repeated migrations;
- partial class-change/reset state;
- item loss before successful mutation;
- ledger drift.

Patch automation does not delete, clear, or force-manipulate `game.db-wal` or `game.db-shm`.

## 14. Verification Coverage

The closure verifier executes the maintained Stage 18.16 smoke tests for:

- schema foundation;
- level-up awards;
- allocation domain;
- effective-stat integration;
- profile UI and navigation;
- resource/notification parity;
- level-up messages;
- existing-character Policy C;
- reset domain;
- New Path Sphere class change;
- Max MP getter recovery;
- Rebirth Sphere UI;
- category and stacking;
- economic policy;
- unified cards;
- stack limit 10;
- production mob drop.

Two historical point-in-time smoke tests are intentionally excluded from closure:

- Stage 18.16.1 required every attribute ledger field for every user to remain zero. That was correct immediately after schema foundation, but Policy C, level rewards, and player allocation intentionally superseded that state. Closure instead validates the live schema and ledger invariant for every user.
- Stage 18.16.10e asserted that no production Rebirth Sphere drop rule existed. Stage 18.16.10f superseded that condition.

## 15. Known Nuances

- Natural drop rates are intentionally too low for practical manual hit testing. Deterministic boundary tests verify normal, elite, and boss hit/miss behavior.
- The Rebirth Sphere is sellable to other players through trade and auction. Its NPC `sell_price` is still `0.0`.
- A full inventory can lose a `stack_or_lose` drop when no compatible stack or free slot exists.
- Drop chances are initial balance values and may be recalibrated later.

## 16. Closure Verdict

Stage 18.16 is closed when the closure verifier reports:

- all maintained smoke tests PASS;
- all required imports PASS;
- `PRAGMA quick_check = ok`;
- no foreign-key violations;
- no ledger invariant failures;
- production database SHA-256 unchanged by verification;
- correct sphere policy;
- correct Scenario B drop rule and canonical victory plan.
