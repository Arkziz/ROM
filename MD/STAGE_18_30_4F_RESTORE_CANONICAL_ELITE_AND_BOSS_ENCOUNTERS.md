# Stage 18.30.4f

Simulation-only restoration of canonical elite and boss encounters.

The simulation adapter reuses production `systems.boss_system.generate_hunt_encounter`, `systems.combat_system.build_mob`, `apply_elite_modifier`, the canonical elite chance, boss enable flag, boss chance, location boss definitions, primary-stat builders, reward multipliers and central drop classification. Event encounters remain disabled for this progression scenario.

The selected canonical normal template still comes from the production-backed location and level pool. The production resolver then applies the mutually exclusive order boss, elite, or normal. Boss level remains equal to player level. The exact encounter type is passed into the simulation battle engine and reports.

No production game file, mob definition, boss definition, drop table or database file is modified.
