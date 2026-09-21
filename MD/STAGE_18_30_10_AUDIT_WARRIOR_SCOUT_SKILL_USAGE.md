# Stage 18.30.10

Adds a read-only audit of Warrior and Scout skill selection. The audit inspects the production selector AST, evaluates resource thresholds from 0 to 100, and executes deterministic 30-turn action sequences. It confirms whether the Warrior rage finisher and Scout poison skill are selected, while preserving all gameplay owners unchanged.

Command: `python .\tools\audit_warrior_scout_skill_usage.py --report .\reports\simulation\stage_18_30_warrior_scout_skill_usage_audit.json`.
