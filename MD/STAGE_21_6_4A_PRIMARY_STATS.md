# Stage 21.6.4a — Audited primary stats

Implements only V1-confirmed STR/DEX/INT/WIS/STA semantics: base 10 + level - 1, five earned points per level after level 1, separate allocated values, exact free + allocated = total-earned invariant, atomic allocation with stale-free-point protection, and allocated-stat respec. Derived stats, equipment, runes, HP/MP, and respec-item consumption are outside this domain stage.
