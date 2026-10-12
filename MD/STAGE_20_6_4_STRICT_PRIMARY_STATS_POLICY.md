# Stage 20.6.4 — Approved Equipment Policy

## Decision

**STRICT_PRIMARY_STATS_APPROVED**

Policy name: `STRICT_PRIMARY_STATS_WITH_WEIGHTED_EQUIPMENT_IDENTITY`.

## Approved rule

Every generated equipment item for a target character must use the canonical class-aware primary-stat matrix, regardless of `class_aware_chance`. The chance remains only for weighted slot/type/profile identity.

## Preserved randomness

- Drop chance and rarity
- Slot/type/profile and armor/subtype selection under the current weighted branch
- Primary-stat budget and numeric values
- Secondary bonuses
- Item level and sell price

## Required scope

- Normal, elite and boss loot
- Event generated equipment
- DEV generation
- Simulator canonical generation
- Forced-slot generation
- Shop preview/permanent promotion

## Required safety rules

- Unknown class fails closed; arbitrary primary stats must not be persisted.
- Existing items are not retroactively changed or rerolled.
- Shop purchase continues to promote the same preview snapshot.
- No database schema change is approved.

## Implementation

Stage 20.6.5 must implement and test this policy. Stage 20.6.4 changes no production code or database.
