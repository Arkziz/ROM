# Stage 20.3 — Hybrid Mana Economy Final Dump

## 1. Canonical numeric policy

Authoritative module: `data/mana_policy.py`.

### Skill cost
`ROUND_HALF_UP(flat + Max MP × percent / 100)`.

| Skill | Flat | Max MP % | Cost at 170 MP |
|---|---:|---:|---:|
| Вогняна куля | 8 | 7% | 20 |
| Грозове заклинання | 15 | 18% | 46 |
| Магічний потік | 0 | 0% | 0 |
| Святий промінь | 6 | 4% | 13 |
| Благословення зцілення | 12 | 10% | 29 |
| Очищення віри | 10 | 8% | 24 |

### Restore
- Магічний потік: 25% Max MP, `ROUND_HALF_UP`.
- Очищення віри: 15% Max MP after cost payment, `ROUND_HALF_UP`.
- Passive regeneration: 30% Max MP per complete minute.
- Post-combat floor: `max(current MP, ROUND_HALF_UP(Max MP × 50%))`.

## 2. Runtime ownership
- PvE cost: `handlers/combat.py` plus PvE action-state revalidation.
- PvP cost: projected validation plus pure round-engine revalidation.
- Simulator cost: shared effective-cost helper for availability and payment.
- Production regeneration/floor: compatibility entrypoints in `systems/character_system.py`, numeric policy in `data/mana_policy.py`.
- Simulator floor: `systems/simulation/survival_state.py` delegates to canonical policy.

## 3. Ordering and invariants
- Validation never spends MP.
- Payment occurs exactly once before skill effect.
- Очищення віри follows spend-before-restore.
- Insufficient Mana does not start cooldown or mutate the round/action state.
- Floor is not additive and never reduces MP above 50%.
- Combat time is not banked as an immediate passive-regeneration tick.

## 4. Presentation
Mana skills show a clean description, effective cost and transparent formula. Free Mana skills show `Вартість: безкоштовно`. Ukrainian cooldown pluralization is preserved.

## 5. Compatibility
Literal catalog `cost` remains compatibility metadata for AST loaders and non-Mana resources. Historical public function names remain compatibility entrypoints but no longer own duplicate Mana arithmetic.

## 6. Verification coverage
- Pure policy vectors across Max MP 170/300/600/1000.
- PvE, PvP and simulator parity.
- Restore rounding and spend-before-restore.
- 50% terminal floor.
- 30% passive regeneration.
- Cross-owner legacy-path consolidation.
- Git exact scopes, fail-safe rollback and DB/WAL/SHM non-mutation.

## 7. Known boundaries
Stage 20.3 does not rebalance potion affordability, daily tokens, level-up gold or guild creation price. Those belong to Stage 20.4.
