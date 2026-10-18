# Stage 21.6.5 — Existing V1 derived-stat engine audit

## Scope

Read-only audit of V1 Max HP, Max MP, PATK, MATK, PDEF, MDEF, physical/magical critical chance, dodge, primary-stat aggregation, and current-resource clamping. No V1 module was imported or executed and no database was opened.

## Evidence summary

- tracked V1 Python files scanned: `1010`
- candidate files: `83`
- blockers: `[]`

## Candidate owners

### MAX_HP

- `data/player_hp.py`: `['calculate_base_max_hp', 'get_starting_max_hp']`
- `data/stat_scaling.py`: `['calc_max_hp_parity']`
- `systems/stat_system.py`: `['calculate_max_hp']`

### MAX_MP

- `data/stat_system_config.py`: `['MAX_MP_SCALING']`
- `systems/stat_system.py`: `['calculate_max_mp']`

### PATK_MATK

- `data/stat_scaling.py`: `['calc_matk', 'calc_patk']`
- `systems/stat_system.py`: `['calculate_magical_attack', 'calculate_physical_attack']`

### PDEF_MDEF

- `data/stat_scaling.py`: `['calc_mdef_parity', 'calc_pdef_parity']`
- `systems/stat_system.py`: `['calculate_magical_defense', 'calculate_physical_defense']`

### CRITICAL

- `data/player_combat_chances.py`: `['calculate_magical_crit_chance', 'calculate_physical_crit_chance']`

### DODGE

- `data/player_combat_chances.py`: `['calculate_dodge_chance']`

### PRIMARY_AGGREGATION

- No exact AST owner found.

### RESOURCE_CLAMP

- `tools/smoke_test_preserve_final_turn_hot_healing_16_1_21.py`: `['current_hp', 'max_hp']`

## Decision

Conclusion: `GO`

Any future implementation must copy only formulas, coefficients, rounding, floors, caps, equipment/rune aggregation order, durability behavior, and resource-clamp semantics explicitly present in the JSON evidence. Detection of a symbol does not by itself authorize a new formula.

## Manual game check

Not required. This audit is static and read-only.
