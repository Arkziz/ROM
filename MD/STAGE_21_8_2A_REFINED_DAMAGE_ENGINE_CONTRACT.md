# Stage 21.8.2a — Refined V1 damage engine contract

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Explicit owner files: **12**
- Semantic rows: **26**
- Unresolved rows: **0**
- Database opened: **False**
- Production changed: **False**
- Manual game check: **NOT_REQUIRED**

## Authority

- `systems/combat_system.py`: authoritative V1 PvE combat-formula orchestration candidate.
- `data/defense_policy.py`: authoritative defense reduction and minimum-damage policy owner.
- `data/player_combat_chances.py`: authoritative crit/evasion chance and RNG policy owner; `systems/pvp_round_engine.py` is the PvP formula consumer requiring parity.
- handlers, boss, simulator, player-stat and reward modules remain consumers or adjacent boundaries; reward settlement stays outside damage resolution.

## Semantic matrix

- `CANONICAL_COMBAT_FORMULA_OWNER`: **V1_CONFIRMED**
- `CANONICAL_DEFENSE_POLICY`: **V1_CONFIRMED**
- `PHYSICAL_DAMAGE_USES_PATK_PDEF`: **V1_CONFIRMED**
- `MAGICAL_DAMAGE_USES_MATK_MDEF`: **V1_CONFIRMED**
- `DEFENSE_HALF_REDUCTION`: **V1_CONFIRMED**
- `MINIMUM_DAMAGE_ONE`: **V1_CONFIRMED**
- `CRITICAL_CHANCE_SOFT_CAP`: **V1_CONFIRMED**
- `EVASION_CHANCE_SOFT_CAP`: **V1_CONFIRMED**
- `ENEMY_CRIT_POLICY`: **V1_CONFIRMED**
- `RNG_ROLL_POLICY`: **V1_CONFIRMED**
- `PVE_HIT_ROUTING`: **V1_CONFIRMED**
- `CRITICAL_MULTIPLIER_APPLICATION`: **V1_CONFIRMED**
- `DAMAGE_TYPE_ROUTING`: **V1_CONFIRMED**
- `PVP_BASE_DAMAGE_OWNER`: **V1_CONFIRMED**
- `PVE_RUNTIME_IS_CONSUMER`: **V1_CONFIRMED**
- `SIMULATOR_PARITY_CONSUMER`: **V1_CONFIRMED**
- `ACTOR_STATS_PROVIDED_EXTERNALLY`: **V1_CONFIRMED**
- `ELITE_MODIFIER_BOUNDARY`: **V1_CONFIRMED**
- `BOSS_MODIFIER_BOUNDARY`: **V1_CONFIRMED**
- `BOSS_DAMAGE_REQUEST_CONSUMER`: **V1_CONFIRMED**
- `NO_WEAKER_FLOOR_POLICY`: **V1_CONFIRMED**
- `ROUNDING_POLICY_EXPLICIT`: **V1_CONFIRMED**
- `REWARD_SETTLEMENT_OUTSIDE_ENGINE`: **V1_CONFIRMED**
- `FAILURE_SEMANTICS`: **V1_CONFIRMED**
- `PVE_PVP_SIMULATOR_PARITY_REQUIRED`: **V1_CONFIRMED**
- `NO_PARALLEL_FORMULA_OWNER`: **V1_CONFIRMED**

## Boundary

No implementation is permitted unless every semantic row is resolved. Exact formulas, constants, rounding order and modifier layering remain bound to the V1 owner evidence and must be consumed without reinterpretation by the implementation patch.

## Suggested next patch

`patch_21_8_2b_implement_damage_engine.py`
