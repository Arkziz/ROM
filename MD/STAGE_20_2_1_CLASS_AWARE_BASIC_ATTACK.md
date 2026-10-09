# Stage 20.2.1 — аудит class-aware basic attack

- Статус: **PASS**
- Рішення: **CONDITIONAL_GO**
- Baseline: `1b919ab2e1f603bc674ccac3fbc694825722b611`

## Гарантії виконання

- Production-файли та БД не змінювалися.
- `game.db` відкрито лише в `mode=ro`.
- WAL/SHM не маніпулювалися.

## Затверджений цільовий контракт

| Клас | Basic attack | Stat | Defense | MP cost |
|---|---|---|---|---:|
| warrior | physical | PATK | PDEF | 0 |
| knight | physical | PATK | PDEF | 0 |
| scout | physical | PATK | PDEF | 0 |
| rogue | physical | PATK | PDEF | 0 |
| mage | magical | MATK | MDEF | 0 |
| priest | magical | MATK | MDEF | 0 |

## Canonical owners

- `systems/combat_system.py`
- `handlers/combat.py`
- `db_modules/player.py`
- `systems/pvp_round_engine.py`
- `systems/simulation/combat_actor_stats.py`
- `data/equipment_profiles.py`

## Runtime functions

- `db_modules/player.py:231` — `get_player_attack_profile(user_id)`
- `handlers/combat.py:508` — `get_effective_mob_def(mob, attack_type)`
- `systems/combat_system.py:42` — `roll_player_normal_attack_hit(player_dex, mob_dex, rng)`
- `systems/combat_system.py:248` — `calculate_player_attack(player_stat_attack, mob_def, dex, wis, level, attack_type, weapon_min_damage, weapon_max_damage, weapon_subtype)`
- `systems/pvp_round_engine.py:99` — `_base_damage(attacker, defender, attack_type, rng)`

## Current class evidence

- `warrior`: **EVIDENCE_FOUND**, evidence=29
- `knight`: **EVIDENCE_FOUND**, evidence=34
- `scout`: **EVIDENCE_FOUND**, evidence=38
- `rogue`: **EVIDENCE_FOUND**, evidence=44
- `mage`: **EVIDENCE_FOUND**, evidence=93
- `priest`: **EVIDENCE_FOUND**, evidence=62

## Findings

### DEFAULT_PHYSICAL_FALLBACK_REVIEW
- Severity: **HIGH**
- Physical defaults exist in basic-attack paths; Stage 20.2.2 must make class routing explicit and fail-safe.
- Next stage: `20.2.2`

### PVP_SIMULATOR_PARITY_GATE
- Severity: **MEDIUM**
- PvP and simulator already contain attack-type logic, but final parity must follow the canonical Stage 20.2.2 implementation.
- Next stage: `20.2.3`

### ZERO_MP_BASIC_ATTACK_CONTRACT
- Severity: **MEDIUM**
- Basic attacks must remain cost 0 for all classes; implementation should assert no player resource debit.
- Next stage: `20.2.2`

## Audit decision

**CONDITIONAL_GO**

Canonical owners and current distributed behavior are mapped. Stage 20.2.2 may implement one explicit six-class resolver; PvP/simulator parity remains gated to Stage 20.2.3.

## Наступний порядок

1. Stage 20.2.2 — implement canonical class basic-attack type.
2. Stage 20.2.3 — PvP and simulator parity.
3. Stage 20.2.6 — accept class combat baseline after Priest lifecycle stages.

## Ручна перевірка

**Не потрібна.** Це read-only audit.

