# Stage 18.30.5b

Read-only audit of the complete player combat-stat pipeline.

The audit compares simulation snapshots with canonical production owners for all six classes at levels 1, 2, 5, and 10. It covers primary stats, Max HP, Max MP, physical and magical attack, physical and magical defense, and records canonical critical/dodge calculations. Additional Scout probes cover STA equipment, a DEX weapon, an STA rune, refined armor, and zero durability.

No production or simulation implementation is changed. The expected result is an evidence-based list of parity failures and missing canonical-owner integrations for Stage 18.30.5c.
