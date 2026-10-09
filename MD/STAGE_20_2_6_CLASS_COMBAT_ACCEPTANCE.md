# Stage 20.2.6: приймання бойової основи класів

## Автоматичний результат

- Automated status: **PASS**
- Acceptance status: **MANUAL_EVIDENCE_REQUIRED**
- Production mutation: **NONE**

- six_class_basic_attack_matrix: **PASS**
- priest_healing_contract: **PASS**
- priest_visible_cooldown_regression: **PASS**
- maintained_suite: **PASS**
- pvp_simulator_runtime_parity: **PASS**
- database_invariants: **PASS**

## Maintained suite

- `tools/verify_stage_20_2_2_class_basic_attack.py`: **PASS**
- `tools/verify_stage_20_2_2a_magical_basic_attack_stat_routing.py`: **PASS**
- `tools/verify_stage_20_2_3_pvp_simulator_basic_attack_parity.py`: **PASS**
- `tools/smoke_test_priest_healing_three_heals.py`: **PASS**
- `tools/smoke_test_priest_cooldown_display_20_2_5b.py`: **PASS**

## Manual acceptance gate

Roadmap забороняє остаточно позначати Stage 20.2 як ACCEPTED без ручних доказів Mage, Priest, physical class і PvP.

- [ ] Mage basic attack PvE
- [ ] Priest basic attack and healing PvE
- [ ] One physical class basic attack PvE
- [ ] One magical and one physical class PvP
- [ ] Simulator sanity for all six classes

Після підтвердження всіх сценаріїв потрібен короткий closure patch, який змінить acceptance status на `ACCEPTED` без production mutation.
