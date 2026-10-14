# Stage 20.4.3 — Potion Affordability Audit After Mana Changes

## Decision
`PASS / NO_PRICE_CHANGE_INSTRUMENTATION_REQUIRED`. Production code is unchanged. Current potion prices must not be changed from invalid zero-spend simulation output.

## Canonical catalog
- Small HP: restore 50, buy 5.00, sell 1.00.
- Medium HP: restore 120, buy 15.00, sell 3.00.
- Small MP: restore 40, buy 4.00, sell 0.80.
- Medium MP: restore 100, buy 12.50, sell 2.50.
All sell prices are 20% of buy prices.

## Blocking findings
1. `world_progression.py` builds `hp_potions` from IDs 401 and 402. ID 402 is a Mana potion; medium HP 403 is omitted.
2. The behavior policy always receives an empty MP-potion list, so Mage/Priest MP use is not simulated after the Mana rework.
3. The simulator consumes owned/dropped potions but does not buy replacements at Alchemist prices. Therefore potion spend equals zero by construction and is not affordability evidence.
4. Economy reporting does not expose potion purchases/costs, so typical, poor-luck and repair-coexistence ratios cannot be calculated.

## Recommendation
Do not change prices in Stage 20.4.4 yet. First complete Stage 20.4.3a simulator instrumentation, then rerun the official six-class levels 1–10 audit. The repeated audit must separate free/dropped/bought/used potions and report potion spend as a percentage of mob gold, total income, and income after repairs.
