# Stage 20.4.3b — Repeated Potion Affordability Audit Through Level 5

## Decision
`PRICE_REVIEW_REQUIRED_LEVEL_1_5`. Worst mandatory spend ratio 156.19% exceeds the 35% audit ceiling.

The audit ran all six classes with three deterministic seeds each using the regular profile and target level 5. Typical is the median mandatory-spend ratio per class; poor luck is the worst of three. Repair spend comes from `city_visit.repair_cost`.

## Aggregates
- Typical total potion spend: `580.0`.
- Typical total repair spend: `869.22`.
- Typical median mandatory/mob-gold ratio: `1.435361`.
- Poor-luck total potion spend: `455.0`.
- Poor-luck total repair spend: `1046.65`.
- Poor-luck max mandatory/mob-gold ratio: `1.561912`.

## Scope limit
This conclusion applies only to progression through level 5. It must not be extrapolated to levels 6–10; those levels require a later repeated audit when longer simulation runtime is acceptable.
